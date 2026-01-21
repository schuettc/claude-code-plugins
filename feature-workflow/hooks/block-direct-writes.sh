#!/bin/bash
# PreToolUse hook to block direct writes to auto-generated files
# Exit code 2 = block the tool call (only stderr is shown to Claude)
#
# Blocks:
# - docs/features/DASHBOARD.md (auto-generated from feature directories)
#
# Allows:
# - All writes to docs/features/[id]/*.md (feature directories)

# Read the tool input from stdin
INPUT=$(cat)

# Extract the file path from the input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, allow the operation
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Block direct writes to DASHBOARD.md (it's auto-generated)
if [[ "$FILE_PATH" == *"docs/features/DASHBOARD.md" ]]; then
  echo "" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2
  echo "  BLOCKED: Direct write to DASHBOARD.md is not allowed" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  echo "  DASHBOARD.md is auto-generated from feature directories." >&2
  echo "" >&2
  echo "  To update the dashboard, write to feature directories instead:" >&2
  echo "" >&2
  echo "  Add to backlog:    Write docs/features/[id]/idea.md" >&2
  echo "  Start work:        Write docs/features/[id]/plan.md" >&2
  echo "  Complete feature:  Write docs/features/[id]/shipped.md" >&2
  echo "" >&2
  echo "  The hook will automatically regenerate DASHBOARD.md." >&2
  echo "" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2

  exit 2
fi

# Allow all other writes
exit 0
