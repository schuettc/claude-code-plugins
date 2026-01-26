#!/usr/bin/env python3
"""Manual feature ship script.

Use this to manually mark a feature as shipped if the automatic workflow didn't complete.
This will:
1. Create a minimal shipped.md file
2. Clear the statusline
3. Regenerate DASHBOARD.md

Usage:
    python3 ship_feature.py <project_root> <feature_id> [summary]

Example:
    python3 ship_feature.py /path/to/project my-feature "Implemented the feature"
"""

import sys
from datetime import date
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: ship_feature.py <project_root> <feature_id> [summary]")
        print("")
        print("Example:")
        print('  python3 ship_feature.py /path/to/project my-feature "Implemented the feature"')
        return 1

    project_root = Path(sys.argv[1])
    feature_id = sys.argv[2]
    summary = sys.argv[3] if len(sys.argv) > 3 else "Feature completed"

    feature_dir = project_root / "docs" / "features" / feature_id
    shipped_file = feature_dir / "shipped.md"
    idea_file = feature_dir / "idea.md"

    # Validate feature exists
    if not feature_dir.is_dir():
        print(f"Error: Feature directory not found: {feature_dir}")
        return 1

    if not idea_file.exists():
        print("Error: idea.md not found - this doesn't appear to be a valid feature")
        return 1

    # Check if already shipped
    if shipped_file.exists():
        print("Feature already has shipped.md")
        print(f"If you want to re-ship, delete {shipped_file} first")
        return 1

    # Get feature name from idea.md frontmatter
    feature_name = feature_id
    try:
        idea_content = idea_file.read_text()
        for line in idea_content.split("\n"):
            if line.startswith("name:"):
                feature_name = line.split(":", 1)[1].strip()
                break
    except Exception:
        pass

    today = date.today().isoformat()

    print(f"[ship] Creating shipped.md for: {feature_id}")

    # Create shipped.md
    shipped_content = f"""---
shipped: {today}
---

# Shipped: {feature_name}

## Summary
{summary}

## Notes
Marked as shipped via manual script.
"""
    shipped_file.write_text(shipped_content)
    print(f"[ship] Created: {shipped_file}")

    # Clear statusline
    print("[ship] Clearing statusline...")
    try:
        # Add lib directory to path
        script_dir = Path(__file__).parent
        lib_dir = script_dir.parent.parent / "shared" / "lib"
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))

        from statusline import clear_context
        clear_context()
    except Exception as e:
        print(f"[ship] Warning: Could not clear statusline: {e}")

    # Regenerate dashboard
    print("[ship] Regenerating DASHBOARD.md...")
    try:
        from run_dashboard import generate_dashboard
        generate_dashboard(project_root)
    except Exception as e:
        print(f"[ship] Warning: Dashboard regeneration failed: {e}")

    print(f"[ship] Feature shipped successfully: {feature_id}")
    print("")
    print("Next steps:")
    print(f"  1. Review {shipped_file} and add more details if needed")
    print(f'  2. Commit the changes: git add docs/features/ && git commit -m "Ship: {feature_name}"')

    return 0


if __name__ == "__main__":
    sys.exit(main())
