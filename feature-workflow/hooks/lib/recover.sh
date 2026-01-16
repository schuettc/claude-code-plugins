#!/bin/bash
# Recovery script for interrupted transitions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/summary.sh"

# Usage: recover.sh <project_root>
PROJECT_ROOT="${1:-$(pwd)}"

BACKLOG="$PROJECT_ROOT/docs/planning/backlog.json"
INPROGRESS="$PROJECT_ROOT/docs/planning/in-progress.json"
COMPLETED="$PROJECT_ROOT/docs/planning/completed.json"

log_info "Running recovery on $PROJECT_ROOT"

# Collect all item IDs across all files
declare -A item_locations

for file in "$BACKLOG" "$INPROGRESS" "$COMPLETED"; do
  if [[ -f "$file" ]]; then
    while IFS= read -r id; do
      if [[ -n "$id" ]]; then
        if [[ -v item_locations["$id"] ]]; then
          item_locations["$id"]="${item_locations[$id]},$file"
        else
          item_locations["$id"]="$file"
        fi
      fi
    done < <(jq -r '.items[].id // empty' "$file" 2>/dev/null)
  fi
done

# Find and fix duplicates
duplicates_found=0
for id in "${!item_locations[@]}"; do
  locations="${item_locations[$id]}"
  if [[ "$locations" == *","* ]]; then
    duplicates_found=1
    log_info "Duplicate found: $id in multiple files"

    # Determine which file to keep item in (furthest along status wins)
    # Priority: completed > in-progress > backlog
    keep_in=""
    if [[ "$locations" == *"$COMPLETED"* ]]; then
      keep_in="$COMPLETED"
    elif [[ "$locations" == *"$INPROGRESS"* ]]; then
      keep_in="$INPROGRESS"
    else
      keep_in="$BACKLOG"
    fi

    log_info "  Keeping in: $keep_in"

    # Remove from other files
    for file in "$BACKLOG" "$INPROGRESS" "$COMPLETED"; do
      if [[ -f "$file" ]] && [[ "$file" != "$keep_in" ]]; then
        if jq -e --arg id "$id" '.items[] | select(.id == $id)' "$file" >/dev/null 2>&1; then
          log_info "  Removing from: $file"
          temp=$(mktemp)
          jq --arg id "$id" '.items = [.items[] | select(.id != $id)]' "$file" > "$temp"
          mv "$temp" "$file"
        fi
      fi
    done
  fi
done

if [[ $duplicates_found -eq 0 ]]; then
  log_info "No duplicates found"
fi

# Recalculate and sync summaries
timestamp=$(get_timestamp)
sync_global_summary "$BACKLOG" "$INPROGRESS" "$COMPLETED" "$timestamp"

log_info "Recovery complete"
