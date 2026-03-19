#!/usr/bin/env python3
"""PreToolUse hook to block direct writes to auto-generated files.

Uses hookSpecificOutput JSON format for decisions:
- permissionDecision: "allow" to permit, "deny" to block
- permissionDecisionReason: explanation shown to Claude (deny) or user (allow)

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
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "DASHBOARD.md is auto-generated from feature directories. "
                    "Write to docs/features/[id]/idea.md, plan.md, or shipped.md instead. "
                    "The PostToolUse hook will automatically regenerate DASHBOARD.md."
                ),
            }
        }
        json.dump(output, sys.stdout)
        return 0

    # Allow all other writes
    return 0


if __name__ == "__main__":
    sys.exit(main())
