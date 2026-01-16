#!/bin/bash
# Main hook dispatcher for feature-workflow transitions
#
# This script is called by Claude Code's PostToolUse hook when the Write tool is used.
# It detects when Claude writes to the transition intent file and dispatches to
# the appropriate transition script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read hook JSON from stdin
HOOK_DATA=$(cat)

# Extract tool input
TOOL_NAME=$(echo "$HOOK_DATA" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$HOOK_DATA" | jq -r '.tool_input.file_path // empty')

# Only process Write tool calls
if [[ "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

# Only process if this is our transition intent file
if [[ "$FILE_PATH" != *"docs/planning/.transition/intent.json" ]]; then
  exit 0
fi

log_info "Detected transition intent file write"

# Read the intent file
if [[ ! -f "$FILE_PATH" ]]; then
  echo "Intent file not found: $FILE_PATH" >&2
  exit 2
fi

INTENT=$(cat "$FILE_PATH")
TRANSITION_TYPE=$(echo "$INTENT" | jq -r '.type // empty')
PROJECT_ROOT=$(echo "$INTENT" | jq -r '.projectRoot // empty')

if [[ -z "$TRANSITION_TYPE" ]]; then
  echo "No transition type specified in intent file" >&2
  exit 2
fi

if [[ -z "$PROJECT_ROOT" ]]; then
  echo "No projectRoot specified in intent file" >&2
  exit 2
fi

# Create result directory if needed
mkdir -p "$PROJECT_ROOT/docs/planning/.transition"

# Check for stale lock (recovery)
LOCKFILE="$PROJECT_ROOT/docs/planning/.transition/.lock"
if [[ -f "$LOCKFILE" ]]; then
  # Check lock age (macOS stat syntax)
  if [[ "$(uname)" == "Darwin" ]]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCKFILE") ))
  else
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCKFILE") ))
  fi

  if [[ $LOCK_AGE -gt 300 ]]; then  # 5 minute timeout
    log_info "Stale lock detected, running recovery"
    "$SCRIPT_DIR/lib/recover.sh" "$PROJECT_ROOT"
    rm -f "$LOCKFILE"
  else
    echo "Transition in progress (locked). Wait or manually remove .transition/.lock" >&2
    exit 2
  fi
fi

# Create lock
touch "$LOCKFILE"
trap "rm -f '$LOCKFILE'" EXIT

# Dispatch to appropriate transition script
log_info "Dispatching transition: $TRANSITION_TYPE"

case "$TRANSITION_TYPE" in
  "backlog-to-inprogress")
    "$SCRIPT_DIR/transitions/backlog-to-inprogress.sh" <<< "$INTENT"
    ;;
  "inprogress-to-completed")
    "$SCRIPT_DIR/transitions/inprogress-to-completed.sh" <<< "$INTENT"
    ;;
  "add-to-backlog")
    "$SCRIPT_DIR/transitions/add-to-backlog.sh" <<< "$INTENT"
    ;;
  *)
    echo "Unknown transition type: $TRANSITION_TYPE" >&2
    echo "{\"success\":false,\"error\":\"Unknown transition type: $TRANSITION_TYPE\"}" > "$PROJECT_ROOT/docs/planning/.transition/result.json"
    exit 2
    ;;
esac
