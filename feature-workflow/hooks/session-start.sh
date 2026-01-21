#!/bin/bash
# SessionStart hook - Brief project summary on session start
#
# Shows a quick summary of feature status. Detailed context loading
# is handled by prompt-handler.sh when /feature-* commands are used.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Read hook JSON from stdin
HOOK_DATA=$(cat)

CWD=$(echo "$HOOK_DATA" | jq -r '.cwd // empty')
if [[ -z "$CWD" ]]; then
  CWD="$PWD"
fi

FEATURES_DIR="$CWD/docs/features"

# Check if this project uses feature-workflow
if [[ ! -d "$FEATURES_DIR" ]]; then
  exit 0
fi

# Count features by status
BACKLOG=0
INPROGRESS=0
COMPLETED=0

for feature_dir in "$FEATURES_DIR"/*/; do
  [[ -d "$feature_dir" ]] || continue
  feature_id=$(basename "$feature_dir")
  [[ "$feature_id" == "DASHBOARD.md" ]] && continue
  [[ -f "$feature_dir/idea.md" ]] || continue

  if [[ -f "$feature_dir/shipped.md" ]]; then
    ((COMPLETED++)) || true
  elif [[ -f "$feature_dir/plan.md" ]]; then
    ((INPROGRESS++)) || true
  else
    ((BACKLOG++)) || true
  fi
done

# Brief output
echo "Feature Workflow: $INPROGRESS in-progress, $BACKLOG in backlog, $COMPLETED shipped"
echo "Commands: /feature-plan, /feature-ship, /feature-capture"

exit 0
