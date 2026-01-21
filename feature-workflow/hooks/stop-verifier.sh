#!/bin/bash
# Stop hook - Verify state and sync dashboard after Claude finishes responding
#
# This hook runs after every Claude response completes.
# It ensures dashboard stays in sync and statusline reflects reality.
#
# Behavior:
# 1. Check stop_hook_active flag to prevent infinite loops
# 2. Get current feature from session file
# 3. If shipped.md exists, clear statusline
# 4. Always regenerate DASHBOARD.md
# 5. Exit 0 (never block)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Prevent infinite loops - check if we're already running
mkdir -p "$HOME/.claude"
LOCK_FILE="$HOME/.claude/feature-workflow-stop-hook.lock"
if [[ -f "$LOCK_FILE" ]]; then
  # Check if lock is stale (older than 30 seconds)
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo "0") ))
  if [[ "$LOCK_AGE" -lt 30 ]]; then
    exit 0
  fi
  rm -f "$LOCK_FILE"
fi

# Set lock
echo "$$" > "$LOCK_FILE"
trap "rm -f '$LOCK_FILE'" EXIT

# Read hook JSON from stdin
HOOK_DATA=$(cat)

# Extract session ID and working directory
SESSION_ID=$(echo "$HOOK_DATA" | jq -r '.session_id // empty')
CWD=$(echo "$HOOK_DATA" | jq -r '.cwd // empty')

# Default to current directory if not provided
if [[ -z "$CWD" ]]; then
  CWD="$PWD"
fi

FEATURES_DIR="$CWD/docs/features"

# Check if this project uses feature-workflow
if [[ ! -d "$FEATURES_DIR" ]]; then
  exit 0
fi

# Get current feature from session file
CURRENT_FEATURE=""
if [[ -n "$SESSION_ID" && -f "$HOME/.claude/sessions/${SESSION_ID}.feature" ]]; then
  CURRENT_FEATURE=$(cat "$HOME/.claude/sessions/${SESSION_ID}.feature" 2>/dev/null || true)
fi

# If no session file, try iTerm mapping
if [[ -z "$CURRENT_FEATURE" && -n "${ITERM_SESSION_ID:-}" ]]; then
  SESSION_FILE="$HOME/.claude/sessions/iterm-${ITERM_SESSION_ID}.session"
  if [[ -f "$SESSION_FILE" ]]; then
    MAPPED_SESSION_ID=$(cat "$SESSION_FILE")
    if [[ -n "$MAPPED_SESSION_ID" && -f "$HOME/.claude/sessions/${MAPPED_SESSION_ID}.feature" ]]; then
      CURRENT_FEATURE=$(cat "$HOME/.claude/sessions/${MAPPED_SESSION_ID}.feature" 2>/dev/null || true)
      SESSION_ID="$MAPPED_SESSION_ID"
    fi
  fi
fi

# Sync statusline with reality
if [[ -n "$CURRENT_FEATURE" ]]; then
  SHIPPED_FILE="$FEATURES_DIR/$CURRENT_FEATURE/shipped.md"

  if [[ -f "$SHIPPED_FILE" ]]; then
    # Feature is shipped but statusline still shows it - clear it
    "$SCRIPT_DIR/clear-feature-context.sh" 2>/dev/null || true
    log_info "Statusline auto-cleared: $CURRENT_FEATURE is shipped"
  fi
fi

# Always regenerate dashboard to keep it in sync
# Run in background to not slow down response
(
  "$SCRIPT_DIR/generate-dashboard.sh" "$CWD" 2>/dev/null || true
) &

# Allow stop (never block)
exit 0
