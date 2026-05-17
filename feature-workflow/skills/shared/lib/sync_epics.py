"""Auto-sync helper for `epic:` ↔ `children:` relationships.

Mirrors sync_replaces. Walks every feature, builds the desired graph from
BOTH directions (each child's `epic:` field + each epic's `children:` array),
and writes back the missing direction on each target file. Idempotent;
removals are NOT mirrored (user-driven).

Nested epics are rejected: a feature with `type: Epic` cannot be marked as
another epic's child. This sync silently skips such pairings (the dashboard's
validation surfaces the conflict separately if needed).
"""

import sys
from pathlib import Path

# Handle both package and standalone imports
try:
    from .frontmatter import parse_frontmatter
except ImportError:
    from frontmatter import parse_frontmatter


def sync_epics(project_root: Path) -> int:
    """Walk features and reconcile `epic:` ↔ `children:` relationships.

    Returns the number of files modified.
    """
    features_dir = project_root / "docs" / "features"
    if not features_dir.is_dir():
        return 0

    # First pass: read everyone's frontmatter
    fm_by_id: dict[str, dict] = {}
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        idea = feature_dir / "idea.md"
        if not idea.exists():
            continue
        fm_by_id[feature_dir.name] = parse_frontmatter(idea)

    # Build desired epic → children mapping from BOTH directions
    desired_children: dict[str, list[str]] = {}  # epic_id -> ordered child list
    desired_epic: dict[str, str] = {}  # child_id -> epic_id

    for fid, fm in fm_by_id.items():
        # Direction 1: this feature's `epic:` field
        epic_ref = str(fm.get("epic", "") or "").strip()
        if epic_ref and epic_ref in fm_by_id:
            target_type = str(fm_by_id[epic_ref].get("type", "") or "").strip().lower()
            self_type = str(fm.get("type", "") or "").strip().lower()
            if target_type == "epic" and self_type != "epic":
                # Valid epic→child reference
                desired_epic[fid] = epic_ref
                desired_children.setdefault(epic_ref, [])
                if fid not in desired_children[epic_ref]:
                    desired_children[epic_ref].append(fid)

        # Direction 2: this feature's `children:` array (only if this feature is an Epic)
        self_type = str(fm.get("type", "") or "").strip().lower()
        if self_type == "epic":
            children_raw = fm.get("children", [])
            if isinstance(children_raw, str):
                children = [children_raw] if children_raw else []
            elif isinstance(children_raw, list):
                children = [str(c).strip() for c in children_raw if str(c).strip()]
            else:
                children = []
            desired_children.setdefault(fid, [])
            for child_id in children:
                if child_id not in fm_by_id:
                    continue  # unknown ref — validation surfaces it
                child_type = str(fm_by_id[child_id].get("type", "") or "").strip().lower()
                if child_type == "epic":
                    continue  # nested epics not allowed
                desired_epic[child_id] = fid
                if child_id not in desired_children[fid]:
                    desired_children[fid].append(child_id)

    # Second pass: write back the missing direction on each affected feature
    modified = 0

    for child_id, epic_id in desired_epic.items():
        idea = features_dir / child_id / "idea.md"
        if not idea.exists():
            continue
        current_epic = str(fm_by_id[child_id].get("epic", "") or "").strip()
        if current_epic == epic_id:
            continue  # already correct
        if _ensure_epic_field(idea, epic_id):
            print(f"[sync_epics] {child_id}: epic={epic_id}", file=sys.stderr)
            modified += 1

    for epic_id, children_list in desired_children.items():
        idea = features_dir / epic_id / "idea.md"
        if not idea.exists():
            continue
        current_children_raw = fm_by_id[epic_id].get("children", [])
        if isinstance(current_children_raw, str):
            current_children = [current_children_raw] if current_children_raw else []
        elif isinstance(current_children_raw, list):
            current_children = [str(c).strip() for c in current_children_raw if str(c).strip()]
        else:
            current_children = []
        # Append any missing children (preserve existing order)
        to_append = [c for c in children_list if c not in current_children]
        if not to_append:
            continue
        new_children = current_children + to_append
        if _ensure_children_field(idea, new_children):
            print(f"[sync_epics] {epic_id}: children={new_children}", file=sys.stderr)
            modified += 1

    return modified


def _ensure_epic_field(idea_path: Path, epic_id: str) -> bool:
    """Set `epic: <epic_id>` on the target file. Returns True if modified."""
    content = idea_path.read_text(encoding="utf-8")
    lines = content.split("\n")

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
    body_lines = lines[end_idx:]

    epic_line_idx = None
    for i, line in enumerate(fm_lines):
        if line.lstrip().startswith("epic:"):
            epic_line_idx = i
            break

    desired = f"epic: {epic_id}"
    if epic_line_idx is not None:
        if fm_lines[epic_line_idx].strip() == desired:
            return False
        fm_lines[epic_line_idx] = desired
    else:
        fm_lines.append(desired)

    new_content = "\n".join(["---"] + fm_lines + body_lines)
    idea_path.write_text(new_content, encoding="utf-8")
    return True


def _ensure_children_field(idea_path: Path, children: list[str]) -> bool:
    """Set `children: [a, b, c]` on the target file. Returns True if modified."""
    content = idea_path.read_text(encoding="utf-8")
    lines = content.split("\n")

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
    body_lines = lines[end_idx:]

    children_line_idx = None
    for i, line in enumerate(fm_lines):
        if line.lstrip().startswith("children:"):
            children_line_idx = i
            break

    desired = f"children: [{', '.join(children)}]"
    if children_line_idx is not None:
        if fm_lines[children_line_idx].strip() == desired:
            return False
        fm_lines[children_line_idx] = desired
    else:
        fm_lines.append(desired)

    new_content = "\n".join(["---"] + fm_lines + body_lines)
    idea_path.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: sync_epics.py <project_root>", file=sys.stderr)
        return 1
    project_root = Path(sys.argv[1])
    if not project_root.is_dir():
        print(f"Not a directory: {project_root}", file=sys.stderr)
        return 1
    modified = sync_epics(project_root)
    print(f"[sync_epics] {modified} file(s) updated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
