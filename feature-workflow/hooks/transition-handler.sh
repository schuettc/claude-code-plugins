#!/bin/bash
# Hook dispatcher for feature-workflow
#
# This script is called by Claude Code's PostToolUse hook when Write, Edit, or Bash tools are used.
# It detects when Claude writes to feature directories or commits with shipping patterns and:
# 1. Regenerates DASHBOARD.md from feature directory state
# 2. Sets statusline when plan.md is created
# 3. Clears statusline when shipped.md is created OR when a shipping commit is detected
#
# Status detection by file presence:
# - idea.md only → backlog
# - idea.md + plan.md → in-progress
# - idea.md + plan.md + shipped.md → completed
#
# Git commit detection patterns (case-insensitive):
# - "complete feature", "feature complete", "ship", "shipped", "finish", "done"
# - Combined with feature ID from current session

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read hook JSON from stdin
HOOK_DATA=$(cat)

# Extract tool input
TOOL_NAME=$(echo "$HOOK_DATA" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$HOOK_DATA" | jq -r '.tool_input.file_path // empty')
COMMAND=$(echo "$HOOK_DATA" | jq -r '.tool_input.command // empty')
SESSION_ID=$(echo "$HOOK_DATA" | jq -r '.session_id // empty')

# Handle Bash tool - detect git commits that indicate shipping
if [[ "$TOOL_NAME" == "Bash" && -n "$COMMAND" ]]; then
  # Check if this is a git commit command
  if [[ "$COMMAND" =~ git\ commit ]]; then
    # Extract commit message (handle various formats)
    COMMIT_MSG=""
    if [[ "$COMMAND" =~ -m\ \"([^\"]+)\" ]]; then
      COMMIT_MSG="${BASH_REMATCH[1]}"
    elif [[ "$COMMAND" =~ -m\ \'([^\']+)\' ]]; then
      COMMIT_MSG="${BASH_REMATCH[1]}"
    elif [[ "$COMMAND" =~ -m\ ([^\ ]+) ]]; then
      COMMIT_MSG="${BASH_REMATCH[1]}"
    fi

    # Convert to lowercase for matching
    COMMIT_MSG_LOWER=$(echo "$COMMIT_MSG" | tr '[:upper:]' '[:lower:]')

    # Shipping patterns (flexible matching)
    SHIP_PATTERNS="complete|completed|ship|shipped|shipping|finish|finished|done|close|closes|closed|final|finalize"

    if [[ "$COMMIT_MSG_LOWER" =~ ($SHIP_PATTERNS) ]]; then
      log_info "Detected potential shipping commit: $COMMIT_MSG"

      # Get current feature from session
      CURRENT_FEATURE=""
      if [[ -n "$SESSION_ID" && -f "$HOME/.claude/sessions/${SESSION_ID}.feature" ]]; then
        CURRENT_FEATURE=$(cat "$HOME/.claude/sessions/${SESSION_ID}.feature" 2>/dev/null || true)
      fi

      if [[ -n "$CURRENT_FEATURE" ]]; then
        log_info "Current feature context: $CURRENT_FEATURE"

        # Try to find the project root by looking for docs/features directory
        # Start from current working directory
        PROJECT_ROOT=$(echo "$HOOK_DATA" | jq -r '.cwd // empty')
        if [[ -z "$PROJECT_ROOT" ]]; then
          PROJECT_ROOT="$PWD"
        fi

        # Check if shipped.md already exists
        SHIPPED_FILE="$PROJECT_ROOT/docs/features/$CURRENT_FEATURE/shipped.md"
        if [[ ! -f "$SHIPPED_FILE" ]]; then
          log_info "shipped.md not found - clearing statusline anyway (commit indicates completion)"

          # Clear the statusline
          "$SCRIPT_DIR/clear-feature-context.sh" 2>/dev/null || true
          log_info "Statusline cleared via commit detection"

          # Note: We don't create shipped.md here as we don't have the content
          # The DASHBOARD.md won't update until shipped.md is created
          # But at least the statusline is cleared
        fi
      fi
    fi
  fi

  exit 0
fi

# Only process Write or Edit tool calls for file-based triggers
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
