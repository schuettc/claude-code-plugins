#!/bin/bash
# Clear feature context from statusline display
# Usage: clear-feature-context.sh
#
# Removes the ~/.claude/sessions/${SESSION_ID}.feature file
# Called when feature is shipped/completed

# Get session ID from iTerm session mapping
if [[ -n "$ITERM_SESSION_ID" ]]; then
  SESSION_FILE="$HOME/.claude/sessions/iterm-${ITERM_SESSION_ID}.session"
  if [[ -f "$SESSION_FILE" ]]; then
    SESSION_ID=$(cat "$SESSION_FILE")
    if [[ -n "$SESSION_ID" ]]; then
      FEATURE_FILE="$HOME/.claude/sessions/${SESSION_ID}.feature"
      if [[ -f "$FEATURE_FILE" ]]; then
        FEATURE_ID=$(cat "$FEATURE_FILE")
        rm -f "$FEATURE_FILE"
        echo "Feature context cleared: $FEATURE_ID"
      else
        echo "No feature context to clear"
      fi
      exit 0
    fi
  fi
fi

echo "Warning: Could not determine session ID" >&2
exit 0
