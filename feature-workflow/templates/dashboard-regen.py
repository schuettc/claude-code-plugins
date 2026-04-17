#!/usr/bin/env python3
"""Regenerate docs/features/DASHBOARD.md from feature directories.

Standalone script — no dependencies beyond Python 3 stdlib.
Inlines the logic from frontmatter.py, models.py, and dashboard.py
so it can live in .github/scripts/ without the plugin installed.

Usage:
    # Plain regenerator (writes to docs/features/DASHBOARD.md)
    python3 dashboard-regen.py [project_root]

    # Git merge driver (writes result to the ancestor path)
    python3 dashboard-regen.py --merge-driver %A

The merge driver mode is used via .gitattributes:
    docs/features/DASHBOARD.md merge=regenerate-dashboard

And configured in .git/config (or via git config):
    [merge "regenerate-dashboard"]
        name = Regenerate DASHBOARD.md
        driver = python3 .github/scripts/dashboard-regen.py --merge-driver %A
"""

import sys
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Frontmatter parser (inlined from skills/shared/lib/frontmatter.py)
# ---------------------------------------------------------------------------

def parse_frontmatter(file_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown file."""
    if not file_path.exists():
        return {}
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    return _parse_frontmatter_string(content)


def _parse_frontmatter_string(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a string."""
    lines = content.split("\n")
    result: dict[str, Any] = {}

    in_frontmatter = False
    frontmatter_lines: list[str] = []
    found_closing = False

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                found_closing = True
                break
        if in_frontmatter:
            frontmatter_lines.append(line)

    if not found_closing:
        return result

    for line in frontmatter_lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # Handle YAML array syntax [item1, item2]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = (
                [item.strip().strip("'\"") for item in inner.split(",")]
                if inner else []
            )
            continue

        result[key] = value

    return result


# ---------------------------------------------------------------------------
# Feature status detection (inlined from skills/shared/lib/models.py)
# ---------------------------------------------------------------------------

class FeatureStatus(Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FeatureContext:
    """Minimal feature context parsed from a feature directory."""

    __slots__ = (
        "feature_id", "name", "category", "priority", "effort",
        "status", "created", "started", "shipped",
    )

    def __init__(
        self,
        feature_id: str,
        status: FeatureStatus,
        name: str = "",
        category: str = "general",
        priority: str = "",
        effort: str = "",
        created: Optional[date] = None,
        started: Optional[date] = None,
        shipped: Optional[date] = None,
    ):
        self.feature_id = feature_id
        self.status = status
        self.name = name
        self.category = category
        self.priority = priority
        self.effort = effort
        self.created = created
        self.started = started
        self.shipped = shipped

    @classmethod
    def from_directory(cls, feature_dir: Path) -> Optional["FeatureContext"]:
        """Create FeatureContext from a feature directory.

        Returns None if the directory has no idea.md.
        """
        idea_file = feature_dir / "idea.md"
        plan_file = feature_dir / "plan.md"
        shipped_file = feature_dir / "shipped.md"

        if not idea_file.exists():
            return None

        if shipped_file.exists():
            status = FeatureStatus.COMPLETED
        elif plan_file.exists():
            status = FeatureStatus.IN_PROGRESS
        else:
            status = FeatureStatus.BACKLOG

        idea_fm = parse_frontmatter(idea_file)
        plan_fm = parse_frontmatter(plan_file) if plan_file.exists() else {}
        shipped_fm = parse_frontmatter(shipped_file) if shipped_file.exists() else {}

        return cls(
            feature_id=feature_dir.name,
            status=status,
            name=idea_fm.get("name", feature_dir.name),
            category=idea_fm.get("category", "general") or "general",
            priority=idea_fm.get("priority", ""),
            effort=idea_fm.get("effort", ""),
            created=_parse_date(idea_fm.get("created")),
            started=_parse_date(plan_fm.get("started")),
            shipped=_parse_date(shipped_fm.get("shipped")),
        )


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None


def _fmt(d: Optional[date]) -> str:
    return str(d) if d else ""


# ---------------------------------------------------------------------------
# Dashboard generation (inlined from skills/shared/lib/dashboard.py)
# ---------------------------------------------------------------------------

def generate_dashboard(project_root: Path, output_path: Optional[Path] = None) -> None:
    """Scan docs/features/*/ and write DASHBOARD.md."""
    features_dir = project_root / "docs" / "features"
    if output_path is None:
        output_path = features_dir / "DASHBOARD.md"

    features_dir.mkdir(parents=True, exist_ok=True)

    backlog: list[FeatureContext] = []
    in_progress: list[FeatureContext] = []
    completed: list[FeatureContext] = []

    if features_dir.exists():
        for feature_dir in sorted(features_dir.iterdir()):
            if not feature_dir.is_dir():
                continue
            ctx = FeatureContext.from_directory(feature_dir)
            if ctx is None:
                continue
            if ctx.status == FeatureStatus.COMPLETED:
                completed.append(ctx)
            elif ctx.status == FeatureStatus.IN_PROGRESS:
                in_progress.append(ctx)
            else:
                backlog.append(ctx)

    content = _build_content(backlog, in_progress, completed)
    output_path.write_text(content, encoding="utf-8")

    print(f"[dashboard-regen] Generated {output_path}:", file=sys.stderr)
    print(f"  {len(in_progress)} in progress, {len(backlog)} backlog, {len(completed)} completed", file=sys.stderr)


def _build_content(
    backlog: list[FeatureContext],
    in_progress: list[FeatureContext],
    completed: list[FeatureContext],
) -> str:
    lines = [
        "# Feature Dashboard",
        "",
        "*Auto-generated by hooks. Do not edit directly.*",
        "",
        "## In Progress",
    ]

    if not in_progress:
        lines.append("*No features in progress*")
    else:
        lines.append("")
        lines.append("| ID | Name | Category | Priority | Started |")
        lines.append("|----|------|----------|----------|---------|")
        for ctx in in_progress:
            lines.append(
                f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} "
                f"| {ctx.category} | {ctx.priority} | {_fmt(ctx.started)} |"
            )

    lines.extend(["", "## Backlog"])

    if not backlog:
        lines.append("*No features in backlog*")
    else:
        lines.append("")
        lines.append("| ID | Name | Category | Priority | Effort | Added |")
        lines.append("|----|------|----------|----------|--------|-------|")
        for ctx in backlog:
            lines.append(
                f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} "
                f"| {ctx.category} | {ctx.priority} | {ctx.effort} | {_fmt(ctx.created)} |"
            )

    lines.extend(["", "## Completed"])

    if not completed:
        lines.append("*No completed features*")
    else:
        lines.append("")
        lines.append("| ID | Name | Shipped |")
        lines.append("|----|------|---------|")
        for ctx in completed:
            lines.append(
                f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | {_fmt(ctx.shipped)} |"
            )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--merge-driver":
        # Merge driver mode.  Git calls the driver *during* the merge,
        # before all files from the other branch are in the working tree.
        # We can't regenerate accurately here, so we just keep "ours" (%A)
        # and exit 0 so git records a clean merge.  The post-merge hook
        # (installed by /feature-init) regenerates from the final tree.
        #
        # %A = "ours" version — leave it as-is.  Returning 0 tells git
        # the driver handled the conflict.  The file content in %A
        # becomes the merge result.
        return 0

    # Plain regenerator mode
    project_root = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path(".")
    if not project_root.is_dir():
        print(f"Error: {project_root} is not a directory", file=sys.stderr)
        return 1

    generate_dashboard(project_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
