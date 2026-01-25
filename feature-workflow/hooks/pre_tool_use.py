#!/usr/bin/env python3
"""PreToolUse hook to block direct writes to auto-generated files.

Exit codes:
- 0: Allow the tool call
- 2: Block the tool call (only stderr is shown to Claude)

Blocks:
- docs/features/DASHBOARD.md (auto-generated from feature directories)

Allows:
- All writes to docs/features/[id]/*.md (feature directories)
"""

import json
import sys


def main() -> int:
    """Check if the tool call should be blocked."""
    # Read hook input from stdin
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Can't parse input, allow the operation
        return 0

    # Extract file path from tool input
    tool_input = hook_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return 0

    # Block direct writes to DASHBOARD.md
    if file_path.endswith("docs/features/DASHBOARD.md") or "/docs/features/DASHBOARD.md" in file_path:
        print("", file=sys.stderr)
        print("=" * 67, file=sys.stderr)
        print("  BLOCKED: Direct write to DASHBOARD.md is not allowed", file=sys.stderr)
        print("=" * 67, file=sys.stderr)
        print("", file=sys.stderr)
        print("  DASHBOARD.md is auto-generated from feature directories.", file=sys.stderr)
        print("", file=sys.stderr)
        print("  To update the dashboard, write to feature directories instead:", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Add to backlog:    Write docs/features/[id]/idea.md", file=sys.stderr)
        print("  Start work:        Write docs/features/[id]/plan.md", file=sys.stderr)
        print("  Complete feature:  Write docs/features/[id]/shipped.md", file=sys.stderr)
        print("", file=sys.stderr)
        print("  The hook will automatically regenerate DASHBOARD.md.", file=sys.stderr)
        print("", file=sys.stderr)
        print("=" * 67, file=sys.stderr)
        return 2

    # Allow all other writes
    return 0


if __name__ == "__main__":
    sys.exit(main())
