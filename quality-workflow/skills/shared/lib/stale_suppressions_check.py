#!/usr/bin/env python3
"""For each candidate suppression: strip the marker, re-run skylos, see if the rule re-fires."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path("/Users/courtschuett/GitHub/schuettc/now-playing")

# (file, line, rule-code-being-suppressed-or-None-if-blanket)
CANDIDATES = [
    ("pi/scripts/backfill_track_durations.py", 105, "SKY-D216"),
    ("pi/scripts/fingerprint_bench.py", 46, "SKY-L029"),
    ("pi/nowplaying/orchestrator/state.py", 7, "SKY-Q501"),
    ("pi/nowplaying/art_overrides.py", 202, "SKY-D215"),
    ("pi/nowplaying/orchestrator/streaming_idle.py", 130, "SKY-L029"),
]

SUPPRESSION_RE = re.compile(r"\s*#\s*skylos:\s*ignore[^\n]*")


def strip_suppression(rel: str, lineno: int) -> tuple[str, str]:
    path = REPO / rel
    original = path.read_text()
    lines = original.splitlines(keepends=True)
    idx = lineno - 1
    stripped = SUPPRESSION_RE.sub("", lines[idx])
    if not stripped.endswith("\n"):
        stripped += "\n"
    lines[idx] = stripped
    modified = "".join(lines)
    return original, modified


def run_skylos_json() -> dict:
    out = subprocess.run(
        ["uvx", "skylos", "pi/", "-a", "--format", "json", "--no-upload"],
        capture_output=True, text=True, cwd=REPO, timeout=120,
    )
    # skylos prints a banner before json; find the json start
    text = out.stdout
    brace = text.find("{")
    if brace < 0:
        return {}
    try:
        return json.loads(text[brace:])
    except json.JSONDecodeError:
        return {}


def issues_in_file_at_line(report: dict, rel: str, lineno: int, rule: str) -> list[dict]:
    """Find issues from the json report that match the location AND rule."""
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
    hits = []
    for it in flat:
        loc = it.get("location") or it.get("file") or ""
        loc_s = str(loc)
        if rel not in loc_s:
            continue
        # rough line proximity
        m = re.search(r":(\d+)", loc_s)
        if m and abs(int(m.group(1)) - lineno) > 3:
            continue
        # rule match if present
        rule_field = str(it.get("rule") or it.get("rule_id") or it.get("code") or "")
        if rule and rule not in rule_field and rule not in json.dumps(it):
            continue
        hits.append(it)
    return hits


def main() -> None:
    results = []
    for rel, lineno, rule in CANDIDATES:
        print(f"\n--- testing {rel}:{lineno} ({rule}) ---")
        original, modified = strip_suppression(rel, lineno)
        path = REPO / rel
        try:
            path.write_text(modified)
            report = run_skylos_json()
            hits = issues_in_file_at_line(report, rel, lineno, rule)
            status = "STILL FIRES" if hits else "STALE"
            print(f"  → {status}  ({len(hits)} matching issue(s))")
            for h in hits[:2]:
                print(f"      {json.dumps(h)[:160]}")
            results.append({
                "file": rel, "line": lineno, "rule": rule,
                "stale": not hits, "hits": len(hits),
            })
        finally:
            path.write_text(original)

    print("\n=== Summary ===")
    for r in results:
        tag = "STALE" if r["stale"] else "needed"
        print(f"  {tag:6s} {r['file']}:{r['line']} {r['rule']}")


if __name__ == "__main__":
    main()
