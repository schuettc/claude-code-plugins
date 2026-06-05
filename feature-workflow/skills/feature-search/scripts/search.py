#!/usr/bin/env python3
"""Search features by state, assignee, priority, epic, dependency, etc.

Reads docs/features/*/idea.md from the given project root, applies filters,
and prints a table.

Usage:
    python3 search.py <project_root> [filters...] [--archive] [--format text|json]

Filters:
    --state <active|paused|replaced|abandoned>
    --assignee <name>
    --priority <P0|P1|P2>
    --type <Feature|Enhancement|Bug Fix|Tech Debt|Epic>
    --category <name>
    --epic <id>
    --depends-on <id>
    --archive            (include replaced + abandoned; default excludes them)
"""

import argparse
import json
import sys
from pathlib import Path

# Resolve shared lib import
SHARED_LIB = Path(__file__).parent.parent.parent / "shared" / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from models import FeatureContext, FeatureState  # noqa: E402


def search_features(project_root: Path, filters: dict) -> list[FeatureContext]:
    """Apply filters to features under project_root.

    Returns matching FeatureContexts. Excludes tombstones unless filters['archive'] is True.
    """
    features_dir = project_root / "docs" / "features"
    if not features_dir.is_dir():
        return []

    include_archive = bool(filters.get("archive"))

    results: list[FeatureContext] = []
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        ctx = FeatureContext.from_directory(feature_dir)
        if ctx is None:
            continue

        if ctx.is_tombstone() and not include_archive:
            continue

        if "state" in filters:
            if ctx.state.value != filters["state"]:
                continue

        if "assignee" in filters:
            if filters["assignee"] not in ctx.assignees:
                continue

        if "priority" in filters:
            if ctx.priority != filters["priority"]:
                continue

        if "type" in filters:
            if ctx.type.lower() != str(filters["type"]).lower():
                continue

        if "category" in filters:
            if ctx.category.lower() != str(filters["category"]).lower():
                continue

        if "epic" in filters:
            if ctx.epic != filters["epic"]:
                continue

        if "depends_on" in filters:
            if filters["depends_on"] not in ctx.depends_on:
                continue

        results.append(ctx)
    return results


def format_text(results: list[FeatureContext]) -> str:
    if not results:
        return "(no matches)"
    lines = ["| ID | Name | State | Type | Priority | Assignee | Epic |",
             "|----|------|-------|------|----------|----------|------|"]
    for ctx in results:
        assignee = ", ".join(ctx.assignees)
        lines.append(
            f"| {ctx.feature_id} | {ctx.name} | {ctx.state.value} | "
            f"{ctx.type} | {ctx.priority} | {assignee} | {ctx.epic} |"
        )
    return "\n".join(lines)


def format_json(results: list[FeatureContext]) -> str:
    return json.dumps([
        {
            "id": r.feature_id,
            "name": r.name,
            "state": r.state.value,
            "type": r.type,
            "priority": r.priority,
            "assignee": r.assignees,
            "epic": r.epic,
            "depends_on": r.depends_on,
            "lifecycle": r.status.value,
        }
        for r in results
    ], indent=2)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("project_root", type=Path)
    p.add_argument("--state")
    p.add_argument("--assignee")
    p.add_argument("--priority")
    p.add_argument("--type")
    p.add_argument("--category")
    p.add_argument("--epic")
    p.add_argument("--depends-on", dest="depends_on")
    p.add_argument("--archive", action="store_true")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    filters = {}
    for k in ("state", "assignee", "priority", "type", "category", "epic", "depends_on"):
        v = getattr(args, k)
        if v:
            filters[k] = v
    if args.archive:
        filters["archive"] = True

    results = search_features(args.project_root, filters)
    print(format_json(results) if args.format == "json" else format_text(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
