#!/bin/bash
# JSON validation utilities for feature-workflow hooks

# Validate a JSON file exists and is valid JSON
validate_json_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 1
  fi
  jq empty "$file" 2>/dev/null
}

# Validate item has required fields
validate_item_structure() {
  local item="$1"
  local required_fields=("id" "name" "type" "priority" "status")

  for field in "${required_fields[@]}"; do
    local value
    value=$(echo "$item" | jq -r ".$field // empty")
    if [[ -z "$value" ]]; then
      echo "Missing required field: $field" >&2
      return 1
    fi
  done
  return 0
}

# Check if item exists in a file
item_exists_in_file() {
  local file="$1"
  local item_id="$2"

  if [[ ! -f "$file" ]]; then
    return 1
  fi

  local found
  found=$(jq -r --arg id "$item_id" '.items[] | select(.id == $id) | .id' "$file" 2>/dev/null)
  [[ -n "$found" ]]
}

# Check for circular dependencies using BFS
# Returns 0 if no cycle, 1 if cycle detected
check_circular_dependency() {
  local new_item_id="$1"
  local target_dep_id="$2"
  local all_items_json="$3"  # JSON array of all items

  # BFS to check if target_dep_id already depends on new_item_id
  local visited=()
  local queue=("$target_dep_id")

  while [[ ${#queue[@]} -gt 0 ]]; do
    local current="${queue[0]}"
    queue=("${queue[@]:1}")  # Pop first element

    # Check if we've reached the new item (cycle!)
    if [[ "$current" == "$new_item_id" ]]; then
      return 1  # Cycle detected
    fi

    # Skip if already visited
    if [[ " ${visited[*]} " =~ " ${current} " ]]; then
      continue
    fi
    visited+=("$current")

    # Get dependencies of current item
    local deps
    deps=$(echo "$all_items_json" | jq -r --arg id "$current" '
      .[] | select(.id == $id) | .dependsOn // [] | .[]
    ')

    # Add to queue
    while IFS= read -r dep; do
      if [[ -n "$dep" ]] && [[ ! " ${visited[*]} " =~ " ${dep} " ]]; then
        queue+=("$dep")
      fi
    done <<< "$deps"
  done

  return 0  # No cycle
}
