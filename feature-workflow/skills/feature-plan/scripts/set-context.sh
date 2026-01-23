#!/bin/bash
# Set feature context for statusline display
# Usage: set-feature-context.sh <feature-id>
#
# Writes the feature ID to ~/.claude/sessions/${SESSION_ID}.feature
# The statusline script reads this to show current feature

FEATURE_ID="$1"

if [[ -z "$FEATURE_ID" ]]; then
  echo "Usage: set-feature-context.sh <feature-id>" >&2
  exit 1
fi

mkdir -p "$HOME/.claude/sessions"

# Primary: Check for SESSION_ID environment variable (set by hooks)
if [[ -n "${SESSION_ID:-}" ]]; then
  echo "$FEATURE_ID" > "$HOME/.claude/sessions/${SESSION_ID}.feature"
  echo "Feature context set: $FEATURE_ID"
  exit 0
fi

# Fallback: iTerm session mapping
if [[ -n "$ITERM_SESSION_ID" ]]; then
  SESSION_FILE="$HOME/.claude/sessions/iterm-${ITERM_SESSION_ID}.session"
  if [[ -f "$SESSION_FILE" ]]; then
    SESSION_ID=$(cat "$SESSION_FILE")
    if [[ -n "$SESSION_ID" ]]; then
      echo "$FEATURE_ID" > "$HOME/.claude/sessions/${SESSION_ID}.feature"
      echo "Feature context set: $FEATURE_ID"
      exit 0
    fi
  fi
fi

echo "Warning: Could not determine session ID (ITERM_SESSION_ID not set or session file not found)" >&2
exit 0
