#!/usr/bin/env python3
"""CLI entry point for dashboard generation.

This script can be called directly from skills or hooks:
    python3 run_dashboard.py <project_root>            # write to disk
    python3 run_dashboard.py <project_root> --stdout    # print to stdout

It handles the import path setup needed to use the shared library.
"""

import sys
from pathlib import Path

# Add the lib directory to the Python path for imports
LIB_DIR = Path(__file__).parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

# Now we can import the modules directly
from frontmatter import parse_frontmatter, parse_frontmatter_string
from models import FeatureStatus, FeatureState, FeatureContext
from deps import detect_cycles, find_unknown_refs


# Known frontmatter keys on idea.md. Anything else is flagged as an unknown-key
# warning so users catch typos like `supersedes:` vs `replaces:`.
KNOWN_IDEA_KEYS: frozenset[str] = frozenset({
    "id", "name", "type", "priority", "effort", "impact", "category", "created",
    "dependsOn", "blockedBy", "relatedTo", "parallelSafe",
    "assignee",
    "epic", "children",
    "state", "pausedReason", "replacedBy", "abandonedReason", "replaces",
    "review",
})


def find_unknown_keys(features_dir: Path) -> list[tuple[str, str]]:
    """Walk idea.md files and report frontmatter keys outside the known schema.

    Returns a list of (feature_id, unknown_key) tuples.
    """
    if not features_dir.is_dir():
        return []
    unknown: list[tuple[str, str]] = []
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        idea = feature_dir / "idea.md"
        if not idea.exists():
            continue
        fm = parse_frontmatter(idea)
        for key in fm.keys():
            if key not in KNOWN_IDEA_KEYS:
                unknown.append((feature_dir.name, key))
    return unknown


def partition_features(features: list[FeatureContext]) -> dict[str, list[FeatureContext]]:
    """Split a feature list into dashboard buckets.

    Returns a dict with keys: in_progress, paused, backlog, completed, archive, epics.
    A single feature may appear in multiple buckets (e.g., an Epic in backlog also lands in 'epics').
    """
    buckets: dict[str, list[FeatureContext]] = {
        "in_progress": [],
        "paused": [],
        "backlog": [],
        "completed": [],
        "archive": [],
        "epics": [],
    }
    for ctx in features:
        if ctx.is_tombstone():
            buckets["archive"].append(ctx)
            continue
        if ctx.is_paused():
            buckets["paused"].append(ctx)
            continue
        # Active features
        if ctx.status == FeatureStatus.COMPLETED:
            buckets["completed"].append(ctx)
        elif ctx.status == FeatureStatus.IN_PROGRESS:
            buckets["in_progress"].append(ctx)
        else:
            buckets["backlog"].append(ctx)
        # Epics also surface in their own bucket
        if ctx.is_epic():
            buckets["epics"].append(ctx)
    return buckets


def _render_in_progress(items: list[FeatureContext]) -> list[str]:
    lines = ["## In Progress"]
    if not items:
        lines.append("*No features in progress*")
        lines.append("")
        return lines
    lines.append("")
    lines.append("| ID | Name | Epic | Assignee | Category | Priority | Started |")
    lines.append("|----|------|------|----------|----------|----------|---------|")
    for ctx in items:
        started = str(ctx.started) if ctx.started else ""
        assignee = ", ".join(ctx.assignees)
        lines.append(f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | {ctx.epic} | {assignee} | {ctx.category} | {ctx.priority} | {started} |")
    lines.append("")
    return lines


def _render_backlog(items: list[FeatureContext], by_id: dict[str, FeatureContext]) -> list[str]:
    lines = ["## Backlog"]
    if not items:
        lines.append("*No features in backlog*")
        lines.append("")
        return lines
    lines.append("")
    lines.append("| ID | Name | Epic | Category | Priority | Effort | Added | Blocked By |")
    lines.append("|----|------|------|----------|----------|--------|-------|------------|")
    for ctx in items:
        created = str(ctx.created) if ctx.created else ""
        unmet = ctx.has_unmet_dependencies(by_id)
        blocked_by = ", ".join(unmet)
        lines.append(f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | {ctx.epic} | {ctx.category} | {ctx.priority} | {ctx.effort} | {created} | {blocked_by} |")
    lines.append("")
    return lines


def _render_completed(items: list[FeatureContext]) -> list[str]:
    lines = ["## Completed"]
    if not items:
        lines.append("*No completed features*")
        lines.append("")
        return lines
    lines.append("")
    lines.append("| ID | Name | Assignee | Shipped |")
    lines.append("|----|------|----------|---------|")
    for ctx in items:
        assignee = ", ".join(ctx.assignees)
        shipped = str(ctx.shipped) if ctx.shipped else ""
        lines.append(f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | {assignee} | {shipped} |")
    lines.append("")
    return lines


def _render_paused(items: list[FeatureContext]) -> list[str]:
    if not items:
        return []
    lifecycle_label = {
        FeatureStatus.BACKLOG: "Backlog",
        FeatureStatus.IN_PROGRESS: "In Progress",
        FeatureStatus.COMPLETED: "Completed",
    }
    lines = ["## Paused", ""]
    lines.append("| ID | Name | Lifecycle | Waiting On | Assignee |")
    lines.append("|----|------|-----------|------------|----------|")
    for ctx in items:
        assignee = ", ".join(ctx.assignees)
        lines.append(
            f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | "
            f"{lifecycle_label.get(ctx.status, '')} | {ctx.paused_reason} | {assignee} |"
        )
    lines.append("")
    return lines


def _render_archive(items: list[FeatureContext], by_id: dict[str, FeatureContext]) -> list[str]:
    if not items:
        return []
    replaced = [c for c in items if c.state == FeatureState.REPLACED]
    abandoned = [c for c in items if c.state == FeatureState.ABANDONED]
    lines = ["## Archive", ""]
    lines.append("<details>")
    lines.append(f"<summary>{len(replaced)} replaced, {len(abandoned)} abandoned</summary>")
    lines.append("")
    lines.append("| ID | Name | State | Reason / Replaced By |")
    lines.append("|----|------|-------|----------------------|")
    for ctx in items:
        if ctx.state == FeatureState.REPLACED:
            detail = f"→ {ctx.replaced_by}" if ctx.replaced_by else ""
        else:
            detail = ctx.abandoned_reason
        lines.append(f"| [{ctx.feature_id}](./{ctx.feature_id}/) | {ctx.name} | {ctx.state.value} | {detail} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    return lines


def _render_warnings(by_id: dict[str, FeatureContext], features_dir: Path) -> list[str]:
    cycles = detect_cycles(by_id)
    unknown = find_unknown_refs(by_id)
    unknown_keys = find_unknown_keys(features_dir)
    empty_epics = [fid for fid, ctx in by_id.items() if ctx.is_epic() and not ctx.children]
    if not cycles and not unknown and not unknown_keys and not empty_epics:
        return []
    lines = ["## Validation Warnings", ""]
    for cycle in cycles:
        lines.append(f"- ⚠️ Cycle detected: {' → '.join(cycle)} → {cycle[0]}")
    for fid, field_name, ref in unknown:
        label = "Unknown dependency" if field_name == "dependsOn" else f"Unknown {field_name} reference"
        lines.append(f"- ⚠️ {label}: `{fid}` → `{ref}`")
    for fid, key in unknown_keys:
        lines.append(f"- ⚠️ Unknown frontmatter key in `{fid}/idea.md`: `{key}:` (typo or unsupported field)")
    for fid in empty_epics:
        lines.append(f"- ⚠️ Epic `{fid}` has no children — set `children: [...]` in its frontmatter, or change `type:` away from Epic")
    lines.append("")
    return lines


def _render_epics(items: list[FeatureContext], by_id: dict[str, FeatureContext]) -> list[str]:
    if not items:
        return []
    lines = ["## Epics", ""]
    lines.append("| ID | Name | Children | Done | In Progress | Backlog |")
    lines.append("|----|------|----------|------|-------------|---------|")
    for epic in items:
        done = inprog = backlog = 0
        for child_id in epic.children:
            child = by_id.get(child_id)
            if child is None:
                continue
            if child.is_tombstone():
                continue  # tombstoned children don't count toward epic progress
            if child.status == FeatureStatus.COMPLETED:
                done += 1
            elif child.status == FeatureStatus.IN_PROGRESS:
                inprog += 1
            else:
                backlog += 1
        lines.append(
            f"| [{epic.feature_id}](./{epic.feature_id}/) | {epic.name} | "
            f"{len(epic.children)} | {done} | {inprog} | {backlog} |"
        )
    lines.append("")
    return lines


def _scan_features(root: Path) -> list[FeatureContext]:
    """Load every FeatureContext under ``root/docs/features``."""
    features_dir = Path(root) / "docs" / "features"
    out: list[FeatureContext] = []
    if features_dir.exists():
        for feature_dir in sorted(features_dir.iterdir()):
            if not feature_dir.is_dir():
                continue
            ctx = FeatureContext.from_directory(feature_dir)
            if ctx is not None:
                out.append(ctx)
    return out


def generate_dashboard_content(project_root: Path) -> str:
    """Scan feature directories and return dashboard markdown content."""
    features_dir = project_root / "docs" / "features"
    all_features = _scan_features(project_root)

    by_id = {f.feature_id: f for f in all_features}
    parts = partition_features(all_features)

    lines: list[str] = ["# Feature Dashboard", "", "*Auto-generated by hooks. Do not edit directly.*", ""]
    lines += _render_in_progress(parts["in_progress"])
    lines += _render_paused(parts["paused"])
    lines += _render_backlog(parts["backlog"], by_id)
    lines += _render_epics(parts["epics"], by_id)
    lines += _render_completed(parts["completed"])
    lines += _render_archive(parts["archive"], by_id)
    lines += _render_warnings(by_id, features_dir)
    return "\n".join(lines) + "\n"


def generate_dashboard(project_root: Path) -> None:
    """Generate DASHBOARD.md from feature directories and write to disk."""
    features_dir = project_root / "docs" / "features"
    dashboard_path = features_dir / "DASHBOARD.md"

    features_dir.mkdir(parents=True, exist_ok=True)

    content = generate_dashboard_content(project_root)
    dashboard_path.write_text(content, encoding="utf-8")

    print(f"[dashboard] Generated DASHBOARD.md", file=sys.stderr)


def generate_workspace_dashboard_content(workspace_root: Path) -> str:
    """Aggregate this workspace's own features plus every member repo's.

    One roll-up table of per-repo counts, then combined In Progress / Backlog /
    Epics tables tagged with the originating repo. Each member's path comes from
    the ``.feature-workspace.yml`` manifest.
    """
    from workspace import load_members

    workspace_root = Path(workspace_root)
    repos: list[tuple[str, Path]] = [("(workspace)", workspace_root)]
    repos += [(m["dir"], workspace_root / m["dir"]) for m in load_members(workspace_root)]

    summary: list[tuple[str, int, int, int]] = []
    in_progress: list[tuple[str, FeatureContext]] = []
    backlog: list[tuple[str, FeatureContext]] = []
    epics: list[tuple[str, FeatureContext]] = []
    for label, root in repos:
        parts = partition_features(_scan_features(root))
        summary.append((label, len(parts["in_progress"]), len(parts["backlog"]), len(parts["completed"])))
        in_progress += [(label, f) for f in parts["in_progress"]]
        backlog += [(label, f) for f in parts["backlog"]]
        epics += [(label, f) for f in parts["epics"]]

    lines: list[str] = [
        "# Workspace Dashboard",
        "",
        "*Auto-generated by hooks. Aggregates this workspace repo and its members. Do not edit directly.*",
        "",
        "## Repos",
        "",
        "| Repo | In Progress | Backlog | Completed |",
        "|------|-------------|---------|-----------|",
    ]
    for label, ip, bl, cp in summary:
        lines.append(f"| {label} | {ip} | {bl} | {cp} |")

    lines += ["", "## In Progress", ""]
    if in_progress:
        lines += ["| Repo | ID | Name | Priority |", "|------|----|------|----------|"]
        lines += [f"| {label} | {f.feature_id} | {f.name} | {f.priority} |" for label, f in in_progress]
    else:
        lines.append("*Nothing in progress.*")

    lines += ["", "## Backlog", ""]
    if backlog:
        lines += ["| Repo | ID | Name | Priority |", "|------|----|------|----------|"]
        lines += [f"| {label} | {f.feature_id} | {f.name} | {f.priority} |" for label, f in backlog]
    else:
        lines.append("*Backlog empty.*")

    lines += ["", "## Epics (cross-repo coordinators)", ""]
    if epics:
        lines += ["| Repo | Epic | Children |", "|------|------|----------|"]
        lines += [f"| {label} | {f.feature_id} | {len(f.children)} |" for label, f in epics]
    else:
        lines.append("*No epics.*")

    return "\n".join(lines) + "\n"


def generate_workspace_dashboard(workspace_root: Path) -> None:
    """Write the aggregated workspace DASHBOARD.md to disk."""
    workspace_root = Path(workspace_root)
    features_dir = workspace_root / "docs" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    content = generate_workspace_dashboard_content(workspace_root)
    (features_dir / "DASHBOARD.md").write_text(content, encoding="utf-8")
    print("[dashboard] Generated workspace DASHBOARD.md", file=sys.stderr)


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 run_dashboard.py <project_root> [--stdout]", file=sys.stderr)
        return 1

    project_root = Path(sys.argv[1])
    stdout_mode = "--stdout" in sys.argv

    if not project_root.is_dir():
        print(f"Error: {project_root} is not a directory", file=sys.stderr)
        return 1

    from workspace import is_workspace

    write = generate_workspace_dashboard if is_workspace(project_root) else generate_dashboard
    render = generate_workspace_dashboard_content if is_workspace(project_root) else generate_dashboard_content

    try:
        if stdout_mode:
            # Always write to disk too, so the local file stays accurate
            write(project_root)
            print(render(project_root))
        else:
            write(project_root)
        return 0
    except Exception as e:
        print(f"Error generating dashboard: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
