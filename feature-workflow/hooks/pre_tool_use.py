#!/usr/bin/env python3
"""PreToolUse hook to block direct writes to auto-generated and protected files.

Uses hookSpecificOutput JSON format for decisions:
- permissionDecision: "allow" to permit, "deny" to block
- permissionDecisionReason: explanation shown to Claude (deny) or user (allow)

Blocks:
- docs/features/DASHBOARD.md (auto-generated from feature directories)
- docs/features/*/reviews/review-status.md (reviewer-only, unless in reviewer mode)
- docs/features/*/reviews/*-review.md (reviewer-only, unless in reviewer mode)

Allows:
- All writes to docs/features/[id]/*.md (feature directories)
- docs/features/[id]/reviews/request-*.md (implementer review requests)
"""

import json
import os
import re
import sys

# Pattern to match review verdict/status files (reviewer-only)
REVIEW_VERDICT_PATTERN = re.compile(
    r"docs/features/[^/]+/reviews/(review-status\.md|.*-review(-\d+)?\.md)$"
)

# Pattern to match review request files (implementer-allowed)
REVIEW_REQUEST_PATTERN = re.compile(
    r"docs/features/[^/]+/reviews/request-.*\.md$"
)


def _is_reviewer_mode() -> bool:
    """Check if the current terminal is running in reviewer mode.

    Reviewer mode is indicated by:
    - FEATURE_REVIEW_MODE=reviewer environment variable
    - ~/.claude/reviewer-mode marker file exists
    """
    if os.environ.get("FEATURE_REVIEW_MODE") == "reviewer":
        return True

    marker = os.path.expanduser("~/.claude/reviewer-mode")
    if os.path.exists(marker):
        return True

    return False


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

    # Check review file protection (only when NOT in reviewer mode)
    if not _is_reviewer_mode():
        # Allow review request files from implementer
        if REVIEW_REQUEST_PATTERN.search(file_path):
            return 0

        # Block review verdict/status files from implementer
        if REVIEW_VERDICT_PATTERN.search(file_path):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Review verdict and status files can only be written by the external reviewer terminal. "
                        "To write review files, run Claude Code with FEATURE_REVIEW_MODE=reviewer environment variable. "
                        "The implementer can write review request files (reviews/request-*.md) to signal the reviewer."
                    ),
                }
            }
            json.dump(output, sys.stdout)
            return 0

    # Allow all other writes
    return 0


if __name__ == "__main__":
    sys.exit(main())
