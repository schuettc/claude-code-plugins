#!/usr/bin/env python3
"""Strip suppressions one at a time, re-run skylos, and report which are stale.

A "stale" suppression is one where the underlying violation has been fixed
elsewhere — the suppression is still in the code but the rule no longer fires
even when the suppression is removed.

For each candidate (file, line, rule):
  1. Read the file
  2. Strip the suppression directive from that line
  3. Write the modified file, run `uvx skylos <root> -a --format json --no-upload`
  4. Compare hits — if no issue at that file+line+rule → STALE
  5. Always restore the original file

v0.2.0: ported from now-playing's 2026-05-22 prototype. The hardcoded REPO
constant is replaced with a `project_root` parameter; the candidate list
is no longer hardcoded.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SUPPRESSION_RE = re.compile(r"\s*#\s*skylos:\s*ignore[^\n]*")


@dataclass
class Candidate:
    """One suppression to test for staleness."""

    file: str           # repo-relative
    line: int           # 1-based line number
    rule: str | None    # the rule code being suppressed (e.g. "SKY-Q302"), None = blanket ignore


@dataclass
class StaleResult:
    """Outcome of one staleness test."""

    candidate: Candidate
    stale: bool         # True if the rule no longer fires when the suppression is removed
    hits: int = 0       # number of skylos issues matching after removing the suppression


def strip_suppression(text: str, lineno: int) -> str:
    """Strip the skylos suppression directive from line `lineno` of `text`.

    Returns the modified text. If lineno is out of range, returns text unchanged.
    """
    lines = text.splitlines(keepends=True)
    idx = lineno - 1
    if not (0 <= idx < len(lines)):
        return text
    stripped = SUPPRESSION_RE.sub("", lines[idx])
    if stripped and not stripped.endswith("\n"):
        stripped += "\n"
    if not stripped.strip():
        # If removing the suppression leaves an empty line, keep it (don't shift line numbers)
        stripped = "\n"
    lines[idx] = stripped
    return "".join(lines)


def run_skylos_json(project_root: Path, *, timeout: int = 180) -> dict:
    """Run skylos on `project_root`, return parsed JSON. Empty dict on failure."""
    cmd = ["uvx", "skylos", str(project_root), "-a", "--quality", "--danger",
           "--secrets", "--sca", "--format", "json", "--no-upload"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    text = result.stdout
    brace = text.find("{")
    if brace < 0:
        return {}
    try:
        return json.loads(text[brace:])
    except json.JSONDecodeError:
        return {}


def issues_in_file_at_line(report: dict, rel: str, lineno: int, rule: str | None) -> list[dict]:
    """Walk the skylos JSON and find issues matching file path + line proximity + rule code."""
    flat: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            if "location" in o or "file" in o:
                flat.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(report)

    hits: list[dict] = []
    for it in flat:
        loc = it.get("location") or it.get("file") or ""
        loc_s = str(loc)
        if rel not in loc_s:
            continue
        m = re.search(r":(\d+)", loc_s)
        if m and abs(int(m.group(1)) - lineno) > 3:
            continue
        rule_field = str(it.get("rule") or it.get("rule_id") or it.get("code") or "")
        if rule and rule not in rule_field and rule not in json.dumps(it):
            continue
        hits.append(it)
    return hits


def check_candidates(
    project_root: Path,
    candidates: list[Candidate],
    *,
    skylos_timeout: int = 180,
) -> list[StaleResult]:
    """Test each candidate for staleness. Always restores file contents.

    Args:
        project_root: repo root. Must be a git repo.
        candidates: list of suppressions to test.
        skylos_timeout: per-skylos-invocation timeout in seconds.

    Returns:
        StaleResult per candidate in input order.
    """
    project_root = project_root.resolve()
    results: list[StaleResult] = []

    for cand in candidates:
        path = project_root / cand.file
        try:
            original = path.read_text()
        except (FileNotFoundError, OSError):
            results.append(StaleResult(candidate=cand, stale=False, hits=0))
            continue

        modified = strip_suppression(original, cand.line)

        try:
            path.write_text(modified)
            report = run_skylos_json(project_root, timeout=skylos_timeout)
            hits = issues_in_file_at_line(report, cand.file, cand.line, cand.rule)
            results.append(StaleResult(
                candidate=cand,
                stale=len(hits) == 0,
                hits=len(hits),
            ))
        finally:
            path.write_text(original)

    return results


def main(argv: list[str] | None = None) -> int:
    """CLI: read candidates from a JSON file, test each, print results.

    Candidate JSON shape: a list of {"file": str, "line": int, "rule": str | null}.
    """
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_root", type=Path, help="Path to the git repo to scan")
    p.add_argument(
        "candidates_json", type=Path,
        help='Path to a JSON file with [{"file": str, "line": int, "rule": str | null}, ...]',
    )
    p.add_argument("--timeout", type=int, default=180, help="Per-skylos-run timeout in seconds")
    args = p.parse_args(argv)

    try:
        raw = json.loads(args.candidates_json.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR reading candidates: {e}", file=sys.stderr)
        return 1

    candidates = [
        Candidate(file=item["file"], line=int(item["line"]), rule=item.get("rule"))
        for item in raw
    ]

    results = check_candidates(args.project_root, candidates, skylos_timeout=args.timeout)
    print(f"Tested {len(results)} candidate(s):")
    for r in results:
        tag = "STALE " if r.stale else "needed"
        print(f"  {tag} {r.candidate.file}:{r.candidate.line} "
              f"{r.candidate.rule or '(blanket)'} (hits={r.hits})")
    stale_count = sum(1 for r in results if r.stale)
    print(f"\n{stale_count} of {len(results)} suppression(s) are stale and can be removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
