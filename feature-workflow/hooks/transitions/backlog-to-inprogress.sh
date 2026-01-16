#!/bin/bash
# Atomic transition: backlog.json -> in-progress.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/validate.sh"
source "$SCRIPT_DIR/../lib/summary.sh"

init_transition

# Read intent from stdin
INTENT=$(cat)

# Extract parameters
ITEM_ID=$(echo "$INTENT" | jq -r '.itemId')
PLAN_PATH=$(echo "$INTENT" | jq -r '.planPath // ""')
PROJECT_ROOT=$(echo "$INTENT" | jq -r '.projectRoot')

# Define file paths
BACKLOG="$PROJECT_ROOT/docs/planning/backlog.json"
INPROGRESS="$PROJECT_ROOT/docs/planning/in-progress.json"
COMPLETED="$PROJECT_ROOT/docs/planning/completed.json"
export RESULT_FILE="$PROJECT_ROOT/docs/planning/.transition/result.json"

TIMESTAMP=$(get_timestamp)

log_info "Moving '$ITEM_ID' from backlog to in-progress"

# Step 1: Validate backlog.json exists and has the item
if ! validate_json_file "$BACKLOG"; then
  exit_error "Invalid or missing backlog.json"
fi

ITEM=$(jq --arg id "$ITEM_ID" '.items[] | select(.id == $id)' "$BACKLOG")
if [[ -z "$ITEM" || "$ITEM" == "null" ]]; then
  exit_error "Item '$ITEM_ID' not found in backlog.json"
fi

# Step 2: Prepare updated item
UPDATED_ITEM=$(echo "$ITEM" | jq \
  --arg ts "$TIMESTAMP" \
  --arg plan "$PLAN_PATH" \
  '
  .status = "in-progress" |
  .updatedAt = $ts |
  .startedAt = $ts |
  .implementationPlan = $plan
')

# Step 3: Initialize in-progress.json if needed
if [[ ! -f "$INPROGRESS" ]]; then
  log_info "Creating in-progress.json"
  init_status_file "$INPROGRESS" "$TIMESTAMP"
fi

# Step 4: ATOMIC SEQUENCE - Write to destination FIRST

# 4a: Add item to in-progress.json
log_info "Adding item to in-progress.json"
TEMP_INPROG=$(mktemp)
jq --argjson item "$UPDATED_ITEM" --arg ts "$TIMESTAMP" '
  .items += [$item] |
  .lastUpdated = $ts
' "$INPROGRESS" > "$TEMP_INPROG"

# Validate before overwriting
if ! validate_json_file "$TEMP_INPROG"; then
  rm "$TEMP_INPROG"
  exit_error "Generated invalid in-progress.json"
fi
mv "$TEMP_INPROG" "$INPROGRESS"

# 4b: Verify item exists in destination
log_info "Verifying write success"
if ! item_exists_in_file "$INPROGRESS" "$ITEM_ID"; then
  exit_error "Verification failed: item not in in-progress.json after write"
fi

# 4c: Remove from backlog.json (safe now - item exists in destination)
log_info "Removing item from backlog.json"
TEMP_BACKLOG=$(mktemp)
jq --arg id "$ITEM_ID" --arg ts "$TIMESTAMP" '
  .items = [.items[] | select(.id != $id)] |
  .lastUpdated = $ts
' "$BACKLOG" > "$TEMP_BACKLOG"

if ! validate_json_file "$TEMP_BACKLOG"; then
  rm "$TEMP_BACKLOG"
  exit_error "Generated invalid backlog.json"
fi
mv "$TEMP_BACKLOG" "$BACKLOG"

# Step 5: Sync global summary across all files
log_info "Syncing global summary"
sync_global_summary "$BACKLOG" "$INPROGRESS" "$COMPLETED" "$TIMESTAMP"

# Step 6: Write success result
RESULT=$(cat <<EOF
{
  "success": true,
  "transition": "backlog-to-inprogress",
  "itemId": "$ITEM_ID",
  "timestamp": "$TIMESTAMP",
  "filesModified": [
    "docs/planning/backlog.json",
    "docs/planning/in-progress.json"
  ]
}
EOF
)

exit_success "$RESULT"
