"""Auto-sync helper for the `replaces:` forward field.

When feature X has `replaces: [a, b]` in its idea.md, ensure features a and b
are marked `state: replaced` with `replacedBy: X`. This lets users write the
relationship in one place (the new feature) and get tombstones+backlinks for free.

Idempotent: only writes when the target needs changing. Skipped if a target
doesn't exist on disk (the dashboard's Validation Warnings will surface the
missing reference instead).
"""

import sys
from pathlib import Path
from typing import Iterable

# Handle both package and standalone imports
try:
    from .frontmatter import parse_frontmatter
except ImportError:
    from frontmatter import parse_frontmatter


def sync_replaces(project_root: Path) -> int:
    """Walk every feature's idea.md, apply `replaces:` forward-direction sync.

    Returns the number of target files modified.
    """
    features_dir = project_root / "docs" / "features"
    if not features_dir.is_dir():
        return 0

    # First pass: collect every (referrer, target) pair from `replaces:` fields.
    sync_pairs: list[tuple[str, str]] = []
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        idea = feature_dir / "idea.md"
        if not idea.exists():
            continue
        fm = parse_frontmatter(idea)
        replaces_raw = fm.get("replaces", [])
        if isinstance(replaces_raw, str):
            replaces = [replaces_raw] if replaces_raw else []
        elif isinstance(replaces_raw, list):
            replaces = [str(r).strip() for r in replaces_raw if str(r).strip()]
        else:
            continue
        for target_id in replaces:
            sync_pairs.append((feature_dir.name, target_id))

    if not sync_pairs:
        return 0

    # Second pass: for each target, ensure state=replaced and replacedBy=referrer.
    modified = 0
    for referrer_id, target_id in sync_pairs:
        target_dir = features_dir / target_id
        target_idea = target_dir / "idea.md"
        if not target_idea.exists():
            # Missing reference — dashboard validation will warn. Skip.
            continue
        if _ensure_replaced(target_idea, referrer_id):
            print(
                f"[sync_replaces] {target_id}: state=replaced replacedBy={referrer_id}",
                file=sys.stderr,
            )
            modified += 1
    return modified


def _ensure_replaced(idea_path: Path, referrer_id: str) -> bool:
    """Set `state: replaced` and `replacedBy: <referrer_id>` on the target file.

    Returns True if the file was modified, False if it was already in the right state.
    """
    content = idea_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Find frontmatter boundaries
    if not lines or lines[0].strip() != "---":
        return False
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return False

    fm_lines = lines[1:end_idx]
    body_lines = lines[end_idx:]  # Keep the closing --- and everything after

    # Parse existing key positions so we can update in place rather than reorder
    state_line_idx = None
    replaced_by_idx = None
    for i, line in enumerate(fm_lines):
        stripped = line.lstrip()
        if stripped.startswith("state:"):
            state_line_idx = i
        elif stripped.startswith("replacedBy:"):
            replaced_by_idx = i

    desired_state = "state: replaced"
    desired_replaced_by = f"replacedBy: {referrer_id}"

    # Check if already in desired state
    current_state = fm_lines[state_line_idx].strip() if state_line_idx is not None else ""
    current_replaced_by = fm_lines[replaced_by_idx].strip() if replaced_by_idx is not None else ""
    if current_state == desired_state and current_replaced_by == desired_replaced_by:
        return False

    # Apply updates
    if state_line_idx is not None:
        fm_lines[state_line_idx] = desired_state
    else:
        fm_lines.append(desired_state)

    if replaced_by_idx is not None:
        fm_lines[replaced_by_idx] = desired_replaced_by
    else:
        fm_lines.append(desired_replaced_by)

    new_content = "\n".join(["---"] + fm_lines + body_lines)
    idea_path.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    """CLI entry point: sync_replaces.py <project_root>"""
    if len(sys.argv) < 2:
        print("Usage: sync_replaces.py <project_root>", file=sys.stderr)
        return 1
    project_root = Path(sys.argv[1])
    if not project_root.is_dir():
        print(f"Not a directory: {project_root}", file=sys.stderr)
        return 1
    modified = sync_replaces(project_root)
    print(f"[sync_replaces] {modified} target(s) updated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
