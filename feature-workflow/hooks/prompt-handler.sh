#!/bin/bash
# UserPromptSubmit hook - Detect /feature-* commands and load context
#
# Fires BEFORE Claude processes the prompt. Detects feature workflow commands
# and injects relevant context.
#
# Commands handled:
#   /feature-plan   → Load backlog summary, prepare for selection
#   /feature-ship   → Load current feature for completion review
#   /feature-capture → Light context (just dashboard location)
#   /feature-audit  → Load current feature context
#   /feature-troubleshoot → Load current feature context

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read hook JSON from stdin
HOOK_DATA=$(cat)

# Extract prompt and working directory
PROMPT=$(echo "$HOOK_DATA" | jq -r '.prompt // empty')
SESSION_ID=$(echo "$HOOK_DATA" | jq -r '.session_id // empty')
CWD=$(echo "$HOOK_DATA" | jq -r '.cwd // empty')

if [[ -z "$CWD" ]]; then
  CWD="$PWD"
fi

FEATURES_DIR="$CWD/docs/features"

# Check if this project uses feature-workflow
if [[ ! -d "$FEATURES_DIR" ]]; then
  exit 0
fi

# Get current feature from session (if any)
get_current_feature() {
  local feature=""

  # Try session file
  if [[ -n "$SESSION_ID" && -f "$HOME/.claude/sessions/${SESSION_ID}.feature" ]]; then
    feature=$(cat "$HOME/.claude/sessions/${SESSION_ID}.feature" 2>/dev/null || true)
  fi

  # Try iTerm mapping
  if [[ -z "$feature" && -n "${ITERM_SESSION_ID:-}" ]]; then
    local session_file="$HOME/.claude/sessions/iterm-${ITERM_SESSION_ID}.session"
    if [[ -f "$session_file" ]]; then
      local mapped_id=$(cat "$session_file")
      if [[ -n "$mapped_id" && -f "$HOME/.claude/sessions/${mapped_id}.feature" ]]; then
        feature=$(cat "$HOME/.claude/sessions/${mapped_id}.feature" 2>/dev/null || true)
      fi
    fi
  fi

  echo "$feature"
}

# Find first in-progress feature
find_in_progress_feature() {
  for feature_dir in "$FEATURES_DIR"/*/; do
    [[ -d "$feature_dir" ]] || continue
    local feature_id=$(basename "$feature_dir")

    if [[ -f "$feature_dir/plan.md" && ! -f "$feature_dir/shipped.md" ]]; then
      echo "$feature_id"
      return
    fi
  done
}

# Load feature context (idea.md + plan.md summary)
load_feature_context() {
  local feature_id="$1"
  local feature_dir="$FEATURES_DIR/$feature_id"

  if [[ ! -d "$feature_dir" ]]; then
    return
  fi

  echo "Active Feature: $feature_id"
  echo ""

  # Get name from idea.md
  if [[ -f "$feature_dir/idea.md" ]]; then
    local name=$(grep -E '^name:' "$feature_dir/idea.md" | head -1 | sed 's/name:[[:space:]]*//' || true)
    [[ -n "$name" ]] && echo "Name: $name"
  fi

  # Progress from plan.md
  if [[ -f "$feature_dir/plan.md" ]]; then
    local total=$(grep -c '^\s*- \[.\]' "$feature_dir/plan.md" 2>/dev/null || echo "0")
    local done=$(grep -c '^\s*- \[x\]' "$feature_dir/plan.md" 2>/dev/null || echo "0")

    if [[ "$total" -gt 0 ]]; then
      echo "Progress: $done/$total steps"
    fi

    # Next step
    local next=$(grep -m1 '^\s*- \[ \]' "$feature_dir/plan.md" 2>/dev/null | sed 's/^\s*- \[ \]//' || true)
    [[ -n "$next" ]] && echo "Next:$next"
  fi

  echo ""
  echo "Files: docs/features/$feature_id/"
}

# Load backlog summary for /feature-plan
load_backlog_summary() {
  local backlog_count=0
  local inprogress_count=0

  echo "Backlog Summary:"
  echo ""

  for feature_dir in "$FEATURES_DIR"/*/; do
    [[ -d "$feature_dir" ]] || continue
    local feature_id=$(basename "$feature_dir")
    [[ "$feature_id" == "DASHBOARD.md" ]] && continue

    local idea_file="$feature_dir/idea.md"
    [[ -f "$idea_file" ]] || continue

    if [[ -f "$feature_dir/shipped.md" ]]; then
      continue  # Skip completed
    elif [[ -f "$feature_dir/plan.md" ]]; then
      ((inprogress_count++)) || true
      local name=$(grep -E '^name:' "$idea_file" | head -1 | sed 's/name:[[:space:]]*//' || echo "$feature_id")
      echo "  [IN PROGRESS] $feature_id: $name"
    else
      ((backlog_count++)) || true
      local name=$(grep -E '^name:' "$idea_file" | head -1 | sed 's/name:[[:space:]]*//' || echo "$feature_id")
      local priority=$(grep -E '^priority:' "$idea_file" | head -1 | sed 's/priority:[[:space:]]*//' || echo "P2")
      echo "  [$priority] $feature_id: $name"
    fi
  done

  echo ""
  echo "Total: $backlog_count in backlog, $inprogress_count in progress"
  echo "Dashboard: docs/features/DASHBOARD.md"
}

# Handle /feature-plan
handle_feature_plan() {
  echo "---"
  echo "Feature Plan Context"
  echo ""

  # Check for in-progress features first
  local current=$(get_current_feature)
  if [[ -z "$current" ]]; then
    current=$(find_in_progress_feature)
  fi

  if [[ -n "$current" ]]; then
    echo "Note: Feature '$current' is already in progress"
    echo ""
    load_feature_context "$current"
  else
    load_backlog_summary
  fi

  echo "---"
}

# Handle /feature-ship
handle_feature_ship() {
  echo "---"
  echo "Feature Ship Context"
  echo ""

  local current=$(get_current_feature)
  if [[ -z "$current" ]]; then
    current=$(find_in_progress_feature)
  fi

  if [[ -n "$current" ]]; then
    load_feature_context "$current"
  else
    echo "No active feature found."
    echo "Check docs/features/DASHBOARD.md for feature status."
  fi

  echo "---"
}

# Handle /feature-capture
handle_feature_capture() {
  echo "---"
  echo "Feature Capture"
  echo "New features go to: docs/features/<id>/idea.md"
  echo "Dashboard: docs/features/DASHBOARD.md"
  echo "---"
}

# Handle /feature-audit or /feature-troubleshoot
handle_feature_context() {
  local current=$(get_current_feature)
  if [[ -z "$current" ]]; then
    current=$(find_in_progress_feature)
  fi

  if [[ -n "$current" ]]; then
    echo "---"
    load_feature_context "$current"
    echo "---"
  fi
}

# Match commands (case-insensitive, handles leading whitespace)
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//')

case "$PROMPT_LOWER" in
  /feature-plan*)
    handle_feature_plan
    ;;
  /feature-ship*)
    handle_feature_ship
    ;;
  /feature-capture*)
    handle_feature_capture
    ;;
  /feature-audit*|/feature-troubleshoot*)
    handle_feature_context
    ;;
  *)
    # Not a feature command - check if prompt mentions a feature ID
    # Look for feature IDs in the prompt
    for feature_dir in "$FEATURES_DIR"/*/; do
      [[ -d "$feature_dir" ]] || continue
      feature_id=$(basename "$feature_dir")
      [[ "$feature_id" == "DASHBOARD.md" ]] && continue

      # Check if feature ID is mentioned in prompt
      if [[ "$PROMPT_LOWER" == *"$feature_id"* ]]; then
        # Set this as the current feature context
        if [[ -n "$SESSION_ID" ]]; then
          mkdir -p "$HOME/.claude/sessions"
          echo "$feature_id" > "$HOME/.claude/sessions/${SESSION_ID}.feature"
        fi

        echo "---"
        echo "Detected feature reference: $feature_id"
        load_feature_context "$feature_id"
        echo "---"
        break
      fi
    done
    ;;
esac

exit 0
