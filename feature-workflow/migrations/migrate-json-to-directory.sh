#!/bin/bash
# Migration Script: JSON-based backlog → Directory-based architecture
#
# Migrates from feature-workflow v2.x (JSON files) to v3.x (directory structure)
#
# Source structure (v2.x):
#   docs/planning/backlog.json
#   docs/planning/in-progress.json
#   docs/planning/completed.json
#   docs/planning/features/[id]/{plan.md, requirements.md, design.md}
#
# Target structure (v3.x):
#   docs/features/DASHBOARD.md (auto-generated)
#   docs/features/[id]/idea.md (required - contains metadata)
#   docs/features/[id]/plan.md (optional - indicates in-progress)
#   docs/features/[id]/shipped.md (optional - indicates completed)
#
# Usage: migrate-json-to-directory.sh <project_root> [--dry-run]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
PROJECT_ROOT="${1:-}"
DRY_RUN=false

if [[ "$PROJECT_ROOT" == "--dry-run" ]]; then
  echo -e "${RED}Error: Project root is required as first argument${NC}"
  echo "Usage: migrate-json-to-directory.sh <project_root> [--dry-run]"
  exit 1
fi

if [[ -z "$PROJECT_ROOT" ]]; then
  echo -e "${RED}Error: Project root is required${NC}"
  echo "Usage: migrate-json-to-directory.sh <project_root> [--dry-run]"
  exit 1
fi

if [[ "${2:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
fi

# Validate project root
if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo -e "${RED}Error: Project root does not exist: $PROJECT_ROOT${NC}"
  exit 1
fi

# Paths
OLD_PLANNING_DIR="$PROJECT_ROOT/docs/planning"
OLD_FEATURES_DIR="$OLD_PLANNING_DIR/features"
NEW_FEATURES_DIR="$PROJECT_ROOT/docs/features"

BACKLOG_JSON="$OLD_PLANNING_DIR/backlog.json"
INPROGRESS_JSON="$OLD_PLANNING_DIR/in-progress.json"
COMPLETED_JSON="$OLD_PLANNING_DIR/completed.json"

# Counters
MIGRATED_BACKLOG=0
MIGRATED_INPROGRESS=0
MIGRATED_COMPLETED=0
SKIPPED=0

# Check if jq is available
if ! command -v jq &> /dev/null; then
  echo -e "${RED}Error: jq is required but not installed${NC}"
  echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
  exit 1
fi

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create idea.md from JSON item
create_idea_md() {
  local feature_id="$1"
  local name="$2"
  local type="$3"
  local priority="$4"
  local effort="$5"
  local impact="$6"
  local created="$7"
  local problem_statement="$8"
  local proposed_solution="${9:-}"
  local affected_areas="${10:-}"
  local target_dir="$NEW_FEATURES_DIR/$feature_id"

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Would create: $target_dir/idea.md"
    return
  fi

  mkdir -p "$target_dir"

  cat > "$target_dir/idea.md" << EOF
---
id: $feature_id
name: $name
type: $type
priority: $priority
effort: $effort
impact: $impact
created: $created
---

# $name

## Problem Statement
$problem_statement
EOF

  if [[ -n "$proposed_solution" && "$proposed_solution" != "null" ]]; then
    cat >> "$target_dir/idea.md" << EOF

## Proposed Solution
$proposed_solution
EOF
  fi

  if [[ -n "$affected_areas" && "$affected_areas" != "null" && "$affected_areas" != "[]" ]]; then
    echo "" >> "$target_dir/idea.md"
    echo "## Affected Areas" >> "$target_dir/idea.md"
    # Parse JSON array of affected areas
    echo "$affected_areas" | jq -r '.[]?' 2>/dev/null | while read -r area; do
      if [[ -n "$area" ]]; then
        echo "- $area" >> "$target_dir/idea.md"
      fi
    done
  fi
}

# Add frontmatter to existing plan.md
add_plan_frontmatter() {
  local feature_id="$1"
  local started_date="$2"
  local target_dir="$NEW_FEATURES_DIR/$feature_id"
  local plan_file="$target_dir/plan.md"

  if [[ ! -f "$plan_file" ]]; then
    return
  fi

  # Check if plan.md already has frontmatter
  if head -1 "$plan_file" | grep -q "^---$"; then
    log_warning "Plan already has frontmatter: $plan_file (skipping frontmatter addition)"
    return
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Would add frontmatter to: $plan_file"
    return
  fi

  # Create temp file with frontmatter
  local temp_file=$(mktemp)
  cat > "$temp_file" << EOF
---
started: $started_date
---

EOF
  cat "$plan_file" >> "$temp_file"
  mv "$temp_file" "$plan_file"
}

# Create shipped.md from JSON completed item
create_shipped_md() {
  local feature_id="$1"
  local shipped_date="$2"
  local shipping_notes="$3"
  local key_changes="${4:-}"
  local testing_notes="${5:-}"
  local name="$6"
  local target_dir="$NEW_FEATURES_DIR/$feature_id"

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Would create: $target_dir/shipped.md"
    return
  fi

  mkdir -p "$target_dir"

  cat > "$target_dir/shipped.md" << EOF
---
shipped: $shipped_date
---

# Shipped: $name

## Summary
$shipping_notes
EOF

  if [[ -n "$key_changes" && "$key_changes" != "null" && "$key_changes" != "[]" ]]; then
    echo "" >> "$target_dir/shipped.md"
    echo "## Key Changes" >> "$target_dir/shipped.md"
    echo "$key_changes" | jq -r '.[]?' 2>/dev/null | while read -r change; do
      if [[ -n "$change" ]]; then
        echo "- $change" >> "$target_dir/shipped.md"
      fi
    done
  fi

  if [[ -n "$testing_notes" && "$testing_notes" != "null" ]]; then
    cat >> "$target_dir/shipped.md" << EOF

## Testing
$testing_notes
EOF
  fi
}

# Copy existing feature files (plan.md, requirements.md, design.md, etc.)
copy_existing_files() {
  local feature_id="$1"
  local old_dir="$OLD_FEATURES_DIR/$feature_id"
  local new_dir="$NEW_FEATURES_DIR/$feature_id"

  if [[ ! -d "$old_dir" ]]; then
    return
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Would copy files from: $old_dir to $new_dir"
    return
  fi

  mkdir -p "$new_dir"

  # Copy all markdown files except idea.md and shipped.md (we create those)
  for file in "$old_dir"/*.md; do
    if [[ -f "$file" ]]; then
      local filename=$(basename "$file")
      # Don't overwrite files we're generating
      if [[ "$filename" != "idea.md" && "$filename" != "shipped.md" ]]; then
        cp "$file" "$new_dir/"
        log_info "Copied: $filename"
      fi
    fi
  done
}

# Main migration logic
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Feature Workflow Migration (v2 → v3) ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Project: $PROJECT_ROOT"
echo ""

# Validate source files exist
if [[ ! -f "$BACKLOG_JSON" && ! -f "$INPROGRESS_JSON" && ! -f "$COMPLETED_JSON" ]]; then
  log_error "No JSON files found in $OLD_PLANNING_DIR"
  echo "Expected files:"
  echo "  - backlog.json"
  echo "  - in-progress.json"
  echo "  - completed.json"
  exit 1
fi

# Create target directory
if [[ "$DRY_RUN" != "true" ]]; then
  mkdir -p "$NEW_FEATURES_DIR"
fi

# Migrate backlog items
if [[ -f "$BACKLOG_JSON" ]]; then
  log_info "Processing backlog.json..."

  item_count=$(jq '.items | length' "$BACKLOG_JSON" 2>/dev/null || echo "0")
  log_info "Found $item_count backlog items"

  jq -c '.items[]?' "$BACKLOG_JSON" 2>/dev/null | while read -r item; do
    if [[ -z "$item" ]]; then continue; fi

    id=$(echo "$item" | jq -r '.id // empty')
    if [[ -z "$id" ]]; then continue; fi

    name=$(echo "$item" | jq -r '.name // .id')
    type=$(echo "$item" | jq -r '.type // "Feature"')
    priority=$(echo "$item" | jq -r '.priority // "P2"')
    effort=$(echo "$item" | jq -r '.effort // "Medium"')
    impact=$(echo "$item" | jq -r '.impact // "Medium"')
    created=$(echo "$item" | jq -r '.createdAt // .created // empty' | cut -d'T' -f1)
    problem=$(echo "$item" | jq -r '.problemStatement // .description // "No problem statement provided"')
    solution=$(echo "$item" | jq -r '.proposedSolution // empty')
    areas=$(echo "$item" | jq -c '.affectedAreas // []')

    log_info "Migrating backlog: $id"
    create_idea_md "$id" "$name" "$type" "$priority" "$effort" "$impact" "$created" "$problem" "$solution" "$areas"
    copy_existing_files "$id"

    MIGRATED_BACKLOG=$((MIGRATED_BACKLOG + 1))
  done
fi

# Migrate in-progress items
if [[ -f "$INPROGRESS_JSON" ]]; then
  log_info "Processing in-progress.json..."

  item_count=$(jq '.items | length' "$INPROGRESS_JSON" 2>/dev/null || echo "0")
  log_info "Found $item_count in-progress items"

  jq -c '.items[]?' "$INPROGRESS_JSON" 2>/dev/null | while read -r item; do
    if [[ -z "$item" ]]; then continue; fi

    id=$(echo "$item" | jq -r '.id // empty')
    if [[ -z "$id" ]]; then continue; fi

    name=$(echo "$item" | jq -r '.name // .id')
    type=$(echo "$item" | jq -r '.type // "Feature"')
    priority=$(echo "$item" | jq -r '.priority // "P2"')
    effort=$(echo "$item" | jq -r '.effort // "Medium"')
    impact=$(echo "$item" | jq -r '.impact // "Medium"')
    created=$(echo "$item" | jq -r '.createdAt // .created // empty' | cut -d'T' -f1)
    started=$(echo "$item" | jq -r '.startedAt // empty' | cut -d'T' -f1)
    problem=$(echo "$item" | jq -r '.problemStatement // .description // "No problem statement provided"')
    solution=$(echo "$item" | jq -r '.proposedSolution // empty')
    areas=$(echo "$item" | jq -c '.affectedAreas // []')

    log_info "Migrating in-progress: $id"
    create_idea_md "$id" "$name" "$type" "$priority" "$effort" "$impact" "$created" "$problem" "$solution" "$areas"
    copy_existing_files "$id"

    # Add frontmatter to plan.md if it exists
    if [[ -n "$started" ]]; then
      add_plan_frontmatter "$id" "$started"
    fi

    MIGRATED_INPROGRESS=$((MIGRATED_INPROGRESS + 1))
  done
fi

# Migrate completed items
if [[ -f "$COMPLETED_JSON" ]]; then
  log_info "Processing completed.json..."

  item_count=$(jq '.items | length' "$COMPLETED_JSON" 2>/dev/null || echo "0")
  log_info "Found $item_count completed items"

  jq -c '.items[]?' "$COMPLETED_JSON" 2>/dev/null | while read -r item; do
    if [[ -z "$item" ]]; then continue; fi

    id=$(echo "$item" | jq -r '.id // empty')
    if [[ -z "$id" ]]; then continue; fi

    name=$(echo "$item" | jq -r '.name // .id')
    type=$(echo "$item" | jq -r '.type // "Feature"')
    priority=$(echo "$item" | jq -r '.priority // "P2"')
    effort=$(echo "$item" | jq -r '.effort // "Medium"')
    impact=$(echo "$item" | jq -r '.impact // "Medium"')
    created=$(echo "$item" | jq -r '.createdAt // .created // empty' | cut -d'T' -f1)
    started=$(echo "$item" | jq -r '.startedAt // empty' | cut -d'T' -f1)
    completed=$(echo "$item" | jq -r '.completedAt // empty' | cut -d'T' -f1)
    problem=$(echo "$item" | jq -r '.problemStatement // .description // "No problem statement provided"')
    solution=$(echo "$item" | jq -r '.proposedSolution // empty')
    areas=$(echo "$item" | jq -c '.affectedAreas // []')
    shipping_notes=$(echo "$item" | jq -r '.shippingNotes // "Feature completed"')
    key_changes=$(echo "$item" | jq -c '.keyChanges // []')
    testing=$(echo "$item" | jq -r '.testingNotes // empty')

    log_info "Migrating completed: $id"
    create_idea_md "$id" "$name" "$type" "$priority" "$effort" "$impact" "$created" "$problem" "$solution" "$areas"
    copy_existing_files "$id"

    # Add frontmatter to plan.md if it exists
    if [[ -n "$started" ]]; then
      add_plan_frontmatter "$id" "$started"
    fi

    # Create shipped.md
    create_shipped_md "$id" "$completed" "$shipping_notes" "$key_changes" "$testing" "$name"

    MIGRATED_COMPLETED=$((MIGRATED_COMPLETED + 1))
  done
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Migration Summary                    ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Backlog items migrated: $MIGRATED_BACKLOG"
echo "In-progress items migrated: $MIGRATED_INPROGRESS"
echo "Completed items migrated: $MIGRATED_COMPLETED"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
  echo -e "${YELLOW}This was a dry run. No files were modified.${NC}"
  echo "Run without --dry-run to perform actual migration."
else
  log_success "Migration complete!"
  echo ""
  echo "Next steps:"
  echo "  1. Review generated files in: $NEW_FEATURES_DIR"
  echo "  2. Run the dashboard generator:"
  echo "     ./feature-workflow/hooks/generate-dashboard.sh $PROJECT_ROOT"
  echo "  3. Optionally archive old JSON files:"
  echo "     mkdir -p $OLD_PLANNING_DIR/archive"
  echo "     mv $OLD_PLANNING_DIR/*.json $OLD_PLANNING_DIR/archive/"
fi
