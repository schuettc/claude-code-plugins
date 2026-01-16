#!/bin/bash
# Summary synchronization for feature-workflow hooks

# Recalculate and sync global summary across all 3 files
sync_global_summary() {
  local backlog="$1"
  local inprogress="$2"
  local completed="$3"
  local timestamp="$4"

  # Count items in each file (handle missing files)
  local backlog_count=0
  local inprog_count=0
  local completed_count=0

  if [[ -f "$backlog" ]]; then
    backlog_count=$(jq '.items | length' "$backlog" 2>/dev/null || echo 0)
  fi
  if [[ -f "$inprogress" ]]; then
    inprog_count=$(jq '.items | length' "$inprogress" 2>/dev/null || echo 0)
  fi
  if [[ -f "$completed" ]]; then
    completed_count=$(jq '.items | length' "$completed" 2>/dev/null || echo 0)
  fi

  local total=$((backlog_count + inprog_count + completed_count))

  # Merge all items to count by priority
  local all_items="[]"
  if [[ -f "$backlog" ]]; then
    all_items=$(jq -s '.[0] + .[1]' <(echo "$all_items") <(jq '.items // []' "$backlog"))
  fi
  if [[ -f "$inprogress" ]]; then
    all_items=$(jq -s '.[0] + .[1]' <(echo "$all_items") <(jq '.items // []' "$inprogress"))
  fi
  if [[ -f "$completed" ]]; then
    all_items=$(jq -s '.[0] + .[1]' <(echo "$all_items") <(jq '.items // []' "$completed"))
  fi

  local p0 p1 p2
  p0=$(echo "$all_items" | jq '[.[] | select(.priority == "P0")] | length')
  p1=$(echo "$all_items" | jq '[.[] | select(.priority == "P1")] | length')
  p2=$(echo "$all_items" | jq '[.[] | select(.priority == "P2")] | length')

  # Build summary object
  local summary
  summary=$(cat <<EOF
{
  "total": $total,
  "byStatus": {
    "backlog": $backlog_count,
    "in-progress": $inprog_count,
    "completed": $completed_count
  },
  "byPriority": {
    "P0": $p0,
    "P1": $p1,
    "P2": $p2
  }
}
EOF
)

  # Update all existing files with the same summary
  for file in "$backlog" "$inprogress" "$completed"; do
    if [[ -f "$file" ]]; then
      local temp
      temp=$(mktemp)
      jq --argjson sum "$summary" --arg ts "$timestamp" '
        .summary = $sum |
        .lastUpdated = $ts
      ' "$file" > "$temp"
      mv "$temp" "$file"
    fi
  done
}

# Initialize a new status file with empty items array
init_status_file() {
  local file="$1"
  local timestamp="$2"

  cat > "$file" <<EOF
{
  "version": "2.0.0",
  "lastUpdated": "$timestamp",
  "summary": {
    "total": 0,
    "byStatus": { "backlog": 0, "in-progress": 0, "completed": 0 },
    "byPriority": { "P0": 0, "P1": 0, "P2": 0 }
  },
  "items": []
}
EOF
}
