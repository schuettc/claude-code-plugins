#!/bin/bash
# PreToolUse hook to block direct writes to backlog JSON files
# Exit code 2 = block the tool call (only stderr is shown to Claude)

# Read the tool input from stdin
INPUT=$(cat)

# Extract the file path from the input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, allow the operation
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Check if this is a direct write to backlog files
if [[ "$FILE_PATH" == *"docs/planning/backlog.json" ]] || \
   [[ "$FILE_PATH" == *"docs/planning/in-progress.json" ]] || \
   [[ "$FILE_PATH" == *"docs/planning/completed.json" ]]; then

  FILENAME=$(basename "$FILE_PATH")
  PROJECT_ROOT=$(echo "$FILE_PATH" | sed 's|/docs/planning/.*||')

  # Output to stderr (this is what Claude sees when blocked)
  echo "" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2
  echo "  BLOCKED: Direct write to $FILENAME is not allowed" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2
  echo "" >&2
  echo "  To update backlog status, write to: docs/planning/.transition/intent.json" >&2
  echo "" >&2
  echo "  Example for moving backlog → in-progress:" >&2
  echo "    {" >&2
  echo "      \"type\": \"backlog-to-inprogress\"," >&2
  echo "      \"itemId\": \"your-feature-id\"," >&2
  echo "      \"planPath\": \"docs/planning/features/[id]/plan.md\"," >&2
  echo "      \"projectRoot\": \"$PROJECT_ROOT\"" >&2
  echo "    }" >&2
  echo "" >&2
  echo "  Example for moving in-progress → completed:" >&2
  echo "    {" >&2
  echo "      \"type\": \"inprogress-to-completed\"," >&2
  echo "      \"itemId\": \"your-feature-id\"," >&2
  echo "      \"projectRoot\": \"$PROJECT_ROOT\"" >&2
  echo "    }" >&2
  echo "" >&2
  echo "═══════════════════════════════════════════════════════════════════" >&2

  # Exit code 2 blocks the tool call
  exit 2
fi

# Allow all other writes
exit 0
