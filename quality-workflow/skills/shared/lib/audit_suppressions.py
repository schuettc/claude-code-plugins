#!/usr/bin/env python3
"""Walk a repo and classify every suppression comment.

Scans `.py`, `.ts`, `.tsx`, `.js`, `.jsx` files (via `git ls-files`) for inline
suppression markers (`# skylos: ignore`, `# noqa`, `# type: ignore`,
`// fallow-ignore`, `// eslint-disable`) and classifies each by whether it
carries a justification.

A suppression has a justification if EITHER:
- There's a literal `# Why:` token on the same or adjacent line, OR
- The suppression line ends with an em-dash / colon explanation

v0.2.0: ported from now-playing's 2026-05-22 handoff prototype. The hardcoded
REPO path is replaced with a `project_root` parameter. CLI entrypoint preserved.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


# Match any of the suppression mechanisms used across skylos / fallow / eslint / mypy / ruff.
PATTERNS: dict[str, re.Pattern] = {
    "skylos": re.compile(r"#\s*skylos:\s*ignore(?:-(?:start|end))?(?:\s+([A-Z]+-[A-Z]?\d+(?:\s+[A-Z]+-[A-Z]?\d+)*))?"),
    "noqa": re.compile(r"#\s*noqa(?::\s*([A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*))?"),
    "type-ignore": re.compile(r"#\s*type:\s*ignore(?:\[([^\]]+)\])?"),
    "fallow-ignore": re.compile(r"//\s*fallow-ignore(?:\s+(\S+))?|/\*\s*fallow-ignore\s*\*/"),
    "eslint-disable": re.compile(r"//\s*eslint-disable(?:-(?:next-)?line)?(?:\s+([\w/-]+(?:\s*,\s*[\w/-]+)*))?"),
}

# A "Why:" token explicitly on the same line as a suppression (Python `#` or TS/JS `//`).
HAS_LITERAL_WHY = re.compile(r"#\s*Why:|//\s*Why:")
# Em-dash followed by free text = inline justification. We require the em-dash
# specifically (not any hyphen) because rule_ids like `SKY-Q302` contain
# hyphens that would otherwise be false-matched as rationale separators.
HAS_INLINE_RATIONALE = re.compile(r"(?:ignore|noqa|disable)\b[^\n]*?—[^\n]+\w")

EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}


@dataclass
class Suppression:
    file: str
    line: int
    mechanism: str
    rule: str | None
    raw: str
    has_why_token: bool
    has_inline_rationale: bool

    @property
    def has_rationale(self) -> bool:
        return self.has_why_token or self.has_inline_rationale


def scan(project_root: Path) -> list[Suppression]:
    """Walk `project_root` (via `git ls-files`) and return every suppression.

    Args:
        project_root: path to the repo root. Must be a git repository.

    Returns:
        List of Suppression records ordered by file then line.

    Raises:
        FileNotFoundError: project_root isn't a git repo.
        RuntimeError: git ls-files failed for another reason.
    """
    project_root = project_root.resolve()
    if not (project_root / ".git").exists():
        raise FileNotFoundError(f"Not a git repo: {project_root}")

    try:
        ls_files = subprocess.check_output(
            ["git", "-C", str(project_root), "ls-files"], text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git ls-files failed in {project_root}: {e}") from e

    out: list[Suppression] = []
    for rel in ls_files.splitlines():
        path = project_root / rel
        if path.suffix not in EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for mech, pat in PATTERNS.items():
                m = pat.search(line)
                if not m:
                    continue
                rule = m.group(1) if m.groups() else None
                out.append(
                    Suppression(
                        file=rel,
                        line=lineno,
                        mechanism=mech,
                        rule=(rule or "").strip() or None,
                        raw=line.strip(),
                        has_why_token=bool(HAS_LITERAL_WHY.search(line)),
                        has_inline_rationale=bool(HAS_INLINE_RATIONALE.search(line)),
                    )
                )
                break  # one mechanism per line is enough
    return out


def summarize(items: list[Suppression]) -> dict:
    """Compute a human-scannable summary of the scan."""
    if not items:
        return {
            "total": 0,
            "by_mechanism": {},
            "with_why_token": 0,
            "with_inline_rationale": 0,
            "unjustified": 0,
            "top_files": [],
        }
    return {
        "total": len(items),
        "by_mechanism": dict(Counter(s.mechanism for s in items).most_common()),
        "with_why_token": sum(1 for s in items if s.has_why_token),
        "with_inline_rationale": sum(1 for s in items if s.has_inline_rationale),
        "unjustified": sum(1 for s in items if not s.has_rationale),
        "top_files": Counter(s.file for s in items).most_common(8),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: scan a repo, print summary, optionally write full report.

    Usage:
        audit_suppressions.py <project_root> [--output <path>]
    """
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project_root", type=Path, help="Path to the git repo to scan")
    p.add_argument(
        "--output", type=Path, default=None,
        help="Write the full suppression list as JSON to this path",
    )
    args = p.parse_args(argv)

    try:
        items = scan(args.project_root)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    summary = summarize(items)
    print(f"Total suppressions: {summary['total']}")
    if summary["total"]:
        n = summary["total"]
        print(f"  with literal `# Why:` token   : {summary['with_why_token']}  ({summary['with_why_token']/n:.0%})")
        print(f"  with inline em-dash/colon Why : {summary['with_inline_rationale']}  ({summary['with_inline_rationale']/n:.0%})")
        print(f"  unjustified (audit candidates): {summary['unjustified']}  ({summary['unjustified']/n:.0%})")
        print()
        print("By mechanism:")
        for mech, count in summary["by_mechanism"].items():
            print(f"  {mech:16s} {count:4d}")
        print()
        print("Top 8 files by suppression density:")
        for f, count in summary["top_files"]:
            print(f"  {count:3d}  {f}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps([asdict(s) for s in items], indent=2))
        print(f"\nWrote full report → {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
