#!/bin/bash
# Hook dispatcher for feature-workflow
#
# This script is called by Claude Code's PostToolUse hook when the Write or Edit tool is used.
# It detects when Claude writes to feature directories and:
# 1. Regenerates DASHBOARD.md from feature directory state
# 2. Sets statusline when plan.md is created
# 3. Clears statusline when shipped.md is created
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

  # STATUSLINE: Set context on plan.md, clear on shipped.md
  if [[ "$FILE_TYPE" == "plan" ]]; then
    "$SCRIPT_DIR/set-feature-context.sh" "$FEATURE_ID" 2>/dev/null || true
    log_info "Statusline set to: $FEATURE_ID"
  elif [[ "$FILE_TYPE" == "shipped" ]]; then
    "$SCRIPT_DIR/clear-feature-context.sh" 2>/dev/null || true
    log_info "Statusline cleared"
  fi

  # DASHBOARD: Regenerate from feature directories
  log_info "Regenerating DASHBOARD.md"
  "$SCRIPT_DIR/generate-dashboard.sh" "$PROJECT_ROOT" || {
    log_info "Warning: Dashboard regeneration failed"
  }

  exit 0
fi

# No matching pattern - allow operation silently
exit 0
