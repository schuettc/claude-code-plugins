#!/bin/bash
# PostToolUse hook: Regenerate DASHBOARD.md when feature files change
#
# Called by Claude Code's PostToolUse hook when Write or Edit tools are used.
# Only regenerates DASHBOARD.md when docs/features/**/*.md files are modified.
#
# Status detection by file presence:
# - idea.md only → backlog
# - idea.md + plan.md → in-progress
# - idea.md + plan.md + shipped.md → completed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read hook JSON from stdin
HOOK_DATA=$(cat)

# Extract tool input
TOOL_NAME=$(echo "$HOOK_DATA" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$HOOK_DATA" | jq -r '.tool_input.file_path // empty')

# Only process Write or Edit tool calls
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  exit 0
fi

# Detect writes to docs/features/[id]/*.md
if [[ "$FILE_PATH" =~ docs/features/([^/]+)/(idea|plan|shipped)\.md$ ]]; then
  FEATURE_ID="${BASH_REMATCH[1]}"
  FILE_TYPE="${BASH_REMATCH[2]}"

  # Get project root (everything before docs/features/)
  PROJECT_ROOT=$(echo "$FILE_PATH" | sed 's|/docs/features/.*||')

  log_info "Detected feature file write: $FEATURE_ID/$FILE_TYPE.md"

  # Regenerate DASHBOARD.md
  log_info "Regenerating DASHBOARD.md"
  "$SCRIPT_DIR/generate-dashboard.sh" "$PROJECT_ROOT" || {
    log_info "Warning: Dashboard regeneration failed"
  }

  exit 0
fi

# No matching pattern - allow operation silently
exit 0
