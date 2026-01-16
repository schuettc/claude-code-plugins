#!/bin/bash
# Atomic transition: in-progress.json -> completed.json

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
PROJECT_ROOT=$(echo "$INTENT" | jq -r '.projectRoot')

# Define file paths
BACKLOG="$PROJECT_ROOT/docs/planning/backlog.json"
INPROGRESS="$PROJECT_ROOT/docs/planning/in-progress.json"
COMPLETED="$PROJECT_ROOT/docs/planning/completed.json"
export RESULT_FILE="$PROJECT_ROOT/docs/planning/.transition/result.json"

TIMESTAMP=$(get_timestamp)

log_info "Moving '$ITEM_ID' from in-progress to completed"

# Step 1: Validate in-progress.json exists and has the item
if ! validate_json_file "$INPROGRESS"; then
  exit_error "Invalid or missing in-progress.json"
fi

ITEM=$(jq --arg id "$ITEM_ID" '.items[] | select(.id == $id)' "$INPROGRESS")
if [[ -z "$ITEM" || "$ITEM" == "null" ]]; then
  exit_error "Item '$ITEM_ID' not found in in-progress.json"
fi

# Step 2: Prepare updated item
UPDATED_ITEM=$(echo "$ITEM" | jq \
  --arg ts "$TIMESTAMP" \
  '
  .status = "completed" |
  .updatedAt = $ts |
  .completedAt = $ts
')

# Step 3: Check for blocked features (for unblock notification)
BLOCKED_BY=$(echo "$ITEM" | jq -r '.blockedBy // [] | .[]' 2>/dev/null || true)
UNBLOCKED_FEATURES="[]"

if [[ -n "$BLOCKED_BY" ]] && [[ -f "$BACKLOG" ]]; then
  # For each feature blocked by this one, check if it's now fully unblocked
  while IFS= read -r blocked_id; do
    if [[ -n "$blocked_id" ]]; then
      # Get the blocked feature's dependsOn array
      BLOCKED_ITEM=$(jq --arg id "$blocked_id" '.items[] | select(.id == $id)' "$BACKLOG" 2>/dev/null || true)
      if [[ -n "$BLOCKED_ITEM" ]]; then
        DEPS=$(echo "$BLOCKED_ITEM" | jq -r '.dependsOn // [] | .[]')
        ALL_MET=true

        while IFS= read -r dep; do
          if [[ -n "$dep" ]] && [[ "$dep" != "$ITEM_ID" ]]; then
            # Check if this dependency is completed
            if [[ -f "$COMPLETED" ]]; then
              DEP_STATUS=$(jq -r --arg id "$dep" '.items[] | select(.id == $id) | .status // "not-found"' "$COMPLETED")
            else
              DEP_STATUS="not-found"
            fi
            if [[ "$DEP_STATUS" != "completed" ]]; then
              ALL_MET=false
              break
            fi
          fi
        done <<< "$DEPS"

        if [[ "$ALL_MET" == "true" ]]; then
          UNBLOCKED_FEATURES=$(echo "$UNBLOCKED_FEATURES" | jq --arg id "$blocked_id" '. += [$id]')
        fi
      fi
    fi
  done <<< "$BLOCKED_BY"
fi

# Step 4: Initialize completed.json if needed
if [[ ! -f "$COMPLETED" ]]; then
  log_info "Creating completed.json"
  init_status_file "$COMPLETED" "$TIMESTAMP"
fi

# Step 5: ATOMIC SEQUENCE - Write to destination FIRST

# 5a: Add item to completed.json
log_info "Adding item to completed.json"
TEMP_COMPLETED=$(mktemp)
jq --argjson item "$UPDATED_ITEM" --arg ts "$TIMESTAMP" '
  .items += [$item] |
  .lastUpdated = $ts
' "$COMPLETED" > "$TEMP_COMPLETED"

if ! validate_json_file "$TEMP_COMPLETED"; then
  rm "$TEMP_COMPLETED"
  exit_error "Generated invalid completed.json"
fi
mv "$TEMP_COMPLETED" "$COMPLETED"

# 5b: Verify item exists in destination
log_info "Verifying write success"
if ! item_exists_in_file "$COMPLETED" "$ITEM_ID"; then
  exit_error "Verification failed: item not in completed.json after write"
fi

# 5c: Remove from in-progress.json (safe now - item exists in destination)
log_info "Removing item from in-progress.json"
TEMP_INPROG=$(mktemp)
jq --arg id "$ITEM_ID" --arg ts "$TIMESTAMP" '
  .items = [.items[] | select(.id != $id)] |
  .lastUpdated = $ts
' "$INPROGRESS" > "$TEMP_INPROG"

if ! validate_json_file "$TEMP_INPROG"; then
  rm "$TEMP_INPROG"
  exit_error "Generated invalid in-progress.json"
fi
mv "$TEMP_INPROG" "$INPROGRESS"

# Step 6: Sync global summary across all files
log_info "Syncing global summary"
sync_global_summary "$BACKLOG" "$INPROGRESS" "$COMPLETED" "$TIMESTAMP"

# Step 7: Write success result with unblocked features
RESULT=$(jq -n \
  --arg itemId "$ITEM_ID" \
  --arg timestamp "$TIMESTAMP" \
  --argjson unblockedFeatures "$UNBLOCKED_FEATURES" \
  '{
    success: true,
    transition: "inprogress-to-completed",
    itemId: $itemId,
    timestamp: $timestamp,
    filesModified: [
      "docs/planning/in-progress.json",
      "docs/planning/completed.json"
    ],
    unblockedFeatures: $unblockedFeatures
  }')

exit_success "$RESULT"
