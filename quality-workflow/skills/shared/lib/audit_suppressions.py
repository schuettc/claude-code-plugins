#!/usr/bin/env python3
"""Walk the now-playing repo, classify every suppression."""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path("/Users/courtschuett/GitHub/schuettc/now-playing")

# Match any of the suppression mechanisms used in this repo.
PATTERNS = {
    "skylos": re.compile(r"#\s*skylos:\s*ignore(?:-(?:start|end))?(?:\s+([A-Z]+-[A-Z]?\d+(?:\s+[A-Z]+-[A-Z]?\d+)*))?"),
    "noqa": re.compile(r"#\s*noqa(?::\s*([A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*))?"),
    "type-ignore": re.compile(r"#\s*type:\s*ignore(?:\[([^\]]+)\])?"),
    "fallow-ignore": re.compile(r"//\s*fallow-ignore(?:\s+(\S+))?|/\*\s*fallow-ignore\s*\*/"),
    "eslint-disable": re.compile(r"//\s*eslint-disable(?:-(?:next-)?line)?(?:\s+([\w/-]+(?:\s*,\s*[\w/-]+)*))?"),
}

# "Has a rationale" = either literal `# Why:` token, OR an em-dash/colon
# explanation on the same line after the suppression marker. The project
# CLAUDE.md asks for the literal token, but in-line explanation is the
# spirit of the rule.
HAS_LITERAL_WHY = re.compile(r"#\s*Why:")
HAS_INLINE_RATIONALE = re.compile(r"(?:ignore|noqa|disable)\b[^\n]*?[—\-:][^\n]+\w")


@dataclass
class Suppression:
    file: str
    line: int
    mechanism: str
    rule: str | None
    raw: str
    has_why_token: bool
    has_inline_rationale: bool


def scan() -> list[Suppression]:
    out: list[Suppression] = []
    # Use git ls-files to respect .gitignore.
    files = subprocess.check_output(
        ["git", "-C", str(REPO), "ls-files"], text=True
    ).splitlines()
    for rel in files:
        path = REPO / rel
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
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


def main() -> None:
    items = scan()
    by_mech = Counter(s.mechanism for s in items)
    by_file_top = Counter(s.file for s in items).most_common(8)
    has_token = sum(1 for s in items if s.has_why_token)
    has_inline = sum(1 for s in items if s.has_inline_rationale)
    neither = [s for s in items if not s.has_why_token and not s.has_inline_rationale]

    print(f"Total suppressions: {len(items)}")
    print(f"  with literal `# Why:` token   : {has_token}  ({has_token/len(items):.0%})")
    print(f"  with inline em-dash/colon Why : {has_inline}  ({has_inline/len(items):.0%})")
    print(f"  with NEITHER (audit candidates): {len(neither)}  ({len(neither)/len(items):.0%})")
    print()
    print("By mechanism:")
    for mech, n in by_mech.most_common():
        print(f"  {mech:16s} {n:4d}")
    print()
    print("Top 8 files by suppression density:")
    for f, n in by_file_top:
        print(f"  {n:3d}  {f}")
    print()
    print("Sample of unjustified suppressions (no Why token, no inline rationale):")
    for s in neither[:8]:
        print(f"  {s.file}:{s.line}  [{s.mechanism}] {s.raw[:90]}")
    print()
    out_path = REPO / ".claude" / "quality-snapshots"
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "suppressions-2026-05-22.json").write_text(
        json.dumps([asdict(s) for s in items], indent=2)
    )
    print(f"Wrote full report → {out_path / 'suppressions-2026-05-22.json'}")


if __name__ == "__main__":
    main()
