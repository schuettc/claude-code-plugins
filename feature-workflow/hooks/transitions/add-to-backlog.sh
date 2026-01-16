#!/bin/bash
# Add new item to backlog.json with dependency handling

set -eo pipefail  # Removed -u to handle empty arrays gracefully

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/validate.sh"
source "$SCRIPT_DIR/../lib/summary.sh"

init_transition

# Read intent from stdin
INTENT=$(cat)

# Extract parameters
ITEM=$(echo "$INTENT" | jq '.item')
PROJECT_ROOT=$(echo "$INTENT" | jq -r '.projectRoot')

# Define file paths
BACKLOG="$PROJECT_ROOT/docs/planning/backlog.json"
INPROGRESS="$PROJECT_ROOT/docs/planning/in-progress.json"
COMPLETED="$PROJECT_ROOT/docs/planning/completed.json"
export RESULT_FILE="$PROJECT_ROOT/docs/planning/.transition/result.json"

TIMESTAMP=$(get_timestamp)
ITEM_ID=$(echo "$ITEM" | jq -r '.id')

log_info "Adding '$ITEM_ID' to backlog"

# Step 1: Validate item structure
if ! validate_item_structure "$ITEM"; then
  exit_error "Invalid item structure - missing required fields"
fi

# Step 2: Initialize backlog.json if needed
if [[ ! -f "$BACKLOG" ]]; then
  log_info "Creating backlog.json"
  mkdir -p "$(dirname "$BACKLOG")"
  init_status_file "$BACKLOG" "$TIMESTAMP"
fi

if ! validate_json_file "$BACKLOG"; then
  exit_error "Invalid backlog.json"
fi

# Step 3: Check for duplicate ID
if item_exists_in_file "$BACKLOG" "$ITEM_ID"; then
  exit_error "Item with ID '$ITEM_ID' already exists in backlog"
fi

# Also check in-progress and completed
if [[ -f "$INPROGRESS" ]] && item_exists_in_file "$INPROGRESS" "$ITEM_ID"; then
  exit_error "Item with ID '$ITEM_ID' already exists in in-progress"
fi
if [[ -f "$COMPLETED" ]] && item_exists_in_file "$COMPLETED" "$ITEM_ID"; then
  exit_error "Item with ID '$ITEM_ID' already exists in completed"
fi

# Step 4: Validate dependencies
DEPENDS_ON=$(echo "$ITEM" | jq -r '.dependsOn // [] | .[]' 2>/dev/null || true)
UPDATED_DEPS=()

if [[ -n "$DEPENDS_ON" ]]; then
  # Collect all items for circular dependency check
  ALL_ITEMS="[]"
  if [[ -f "$BACKLOG" ]]; then
    ALL_ITEMS=$(jq -s '.[0] + .[1]' <(echo "$ALL_ITEMS") <(jq '.items // []' "$BACKLOG"))
  fi
  if [[ -f "$INPROGRESS" ]]; then
    ALL_ITEMS=$(jq -s '.[0] + .[1]' <(echo "$ALL_ITEMS") <(jq '.items // []' "$INPROGRESS"))
  fi
  if [[ -f "$COMPLETED" ]]; then
    ALL_ITEMS=$(jq -s '.[0] + .[1]' <(echo "$ALL_ITEMS") <(jq '.items // []' "$COMPLETED"))
  fi

  while IFS= read -r dep_id; do
    if [[ -n "$dep_id" ]]; then
      # Check dependency exists
      DEP_EXISTS=false
      for file in "$BACKLOG" "$INPROGRESS" "$COMPLETED"; do
        if [[ -f "$file" ]] && item_exists_in_file "$file" "$dep_id"; then
          DEP_EXISTS=true
          break
        fi
      done

      if [[ "$DEP_EXISTS" == "false" ]]; then
        exit_error "Dependency '$dep_id' not found in any backlog file"
      fi

      # Check for circular dependency
      if ! check_circular_dependency "$ITEM_ID" "$dep_id" "$ALL_ITEMS"; then
        exit_error "Circular dependency detected: $ITEM_ID -> $dep_id -> ... -> $ITEM_ID"
      fi

      UPDATED_DEPS+=("$dep_id")
    fi
  done <<< "$DEPENDS_ON"
fi

# Step 5: Add item to backlog
log_info "Adding item to backlog.json"

# Ensure item has required timestamps
ITEM=$(echo "$ITEM" | jq \
  --arg ts "$TIMESTAMP" \
  '
  .createdAt = (.createdAt // $ts) |
  .updatedAt = $ts |
  .startedAt = null |
  .completedAt = null |
  .implementationPlan = null |
  .blockedBy = (.blockedBy // [])
')

TEMP_BACKLOG=$(mktemp)
jq --argjson item "$ITEM" --arg ts "$TIMESTAMP" '
  .items += [$item] |
  .lastUpdated = $ts
' "$BACKLOG" > "$TEMP_BACKLOG"

if ! validate_json_file "$TEMP_BACKLOG"; then
  rm "$TEMP_BACKLOG"
  exit_error "Generated invalid backlog.json"
fi
mv "$TEMP_BACKLOG" "$BACKLOG"

# Step 6: Update blockedBy arrays on dependency targets
if [[ ${#UPDATED_DEPS[@]} -gt 0 ]]; then
  for dep_id in "${UPDATED_DEPS[@]}"; do
    log_info "Updating blockedBy for '$dep_id'"

    for file in "$BACKLOG" "$INPROGRESS" "$COMPLETED"; do
      if [[ -f "$file" ]] && item_exists_in_file "$file" "$dep_id"; then
        TEMP_FILE=$(mktemp)
        jq --arg dep_id "$dep_id" --arg new_id "$ITEM_ID" --arg ts "$TIMESTAMP" '
          .items = [.items[] | if .id == $dep_id then
            .blockedBy = ((.blockedBy // []) + [$new_id] | unique) |
            .updatedAt = $ts
          else . end] |
          .lastUpdated = $ts
        ' "$file" > "$TEMP_FILE"
        mv "$TEMP_FILE" "$file"
        break
      fi
    done
  done
fi

# Step 7: Sync global summary
log_info "Syncing global summary"
sync_global_summary "$BACKLOG" "$INPROGRESS" "$COMPLETED" "$TIMESTAMP"

# Step 8: Write success result
RESULT=$(jq -n \
  --arg itemId "$ITEM_ID" \
  --arg timestamp "$TIMESTAMP" \
  '{
    success: true,
    transition: "add-to-backlog",
    itemId: $itemId,
    timestamp: $timestamp,
    filesModified: ["docs/planning/backlog.json"]
  }')

exit_success "$RESULT"
