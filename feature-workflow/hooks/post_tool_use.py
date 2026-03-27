#!/usr/bin/env python3
"""PostToolUse hook: Regenerate DASHBOARD.md when feature files change.

Called by Claude Code's PostToolUse hook when Write or Edit tools are used.
Returns additionalContext via hookSpecificOutput to inform Claude of updates.

Status detection by file presence:
- idea.md only → backlog
- idea.md + plan.md → in-progress
- idea.md + plan.md + shipped.md → completed
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# Pattern to match feature file writes
FEATURE_FILE_PATTERN = re.compile(r"docs/features/([^/]+)/(idea|plan|shipped)\.md$")

# Pattern to match review status file writes
REVIEW_STATUS_PATTERN = re.compile(r"docs/features/([^/]+)/reviews/review-status\.md$")


def main() -> int:
    """Check if dashboard needs regeneration after a tool call."""
    # Read hook input from stdin
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    # Only process Write or Edit tool calls
    tool_name = hook_data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return 0

    # Extract file path from tool input
    tool_input = hook_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return 0

    # Check if this is a review status file write
    review_match = REVIEW_STATUS_PATTERN.search(file_path)
    if review_match:
        feature_id = review_match.group(1)
        # Parse verdict from the file to provide context
        try:
            status_file = Path(file_path)
            if status_file.exists():
                content = status_file.read_text(encoding="utf-8")
                # Extract verdict from frontmatter
                verdict = ""
                phase = ""
                for line in content.split("\n"):
                    if line.startswith("verdict:"):
                        verdict = line.split(":", 1)[1].strip()
                    elif line.startswith("phase:"):
                        phase = line.split(":", 1)[1].strip()
                if verdict:
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PostToolUse",
                            "additionalContext": (
                                f"External review verdict for feature '{feature_id}' "
                                f"({phase} phase): {verdict.upper()}. "
                                f"See docs/features/{feature_id}/reviews/ for details."
                            ),
                        }
                    }
                    json.dump(output, sys.stdout)
        except Exception:
            pass  # Non-critical, don't block on review status parsing
        return 0

    # Check if this is a feature file write
    match = FEATURE_FILE_PATTERN.search(file_path)
    if not match:
        return 0

    feature_id = match.group(1)
    file_type = match.group(2)

    # Get project root (everything before docs/features/)
    project_root = file_path.split("/docs/features/")[0]
    if not project_root:
        project_root = "."

    # Find the dashboard generation script
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        # Try to find it relative to this script
        script_dir = Path(__file__).parent
        plugin_root = str(script_dir.parent)

    dashboard_script = Path(plugin_root) / "skills" / "shared" / "lib" / "run_dashboard.py"

    if not dashboard_script.exists():
        print(f"[hook] Warning: Dashboard script not found at {dashboard_script}", file=sys.stderr)
        return 0

    # Run the dashboard generation script
    dashboard_updated = False
    try:
        result = subprocess.run(
            [sys.executable, str(dashboard_script), project_root],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"[hook] Warning: Dashboard regeneration failed", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        else:
            dashboard_updated = True
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    except subprocess.TimeoutExpired:
        print("[hook] Warning: Dashboard regeneration timed out", file=sys.stderr)
    except Exception as e:
        print(f"[hook] Warning: Dashboard regeneration error: {e}", file=sys.stderr)

    # Return context to Claude about what happened
    if dashboard_updated:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"Feature file {feature_id}/{file_type}.md was written. "
                    f"DASHBOARD.md has been automatically regenerated."
                ),
            }
        }
        json.dump(output, sys.stdout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
