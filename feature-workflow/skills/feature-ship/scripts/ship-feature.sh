#!/bin/bash
# Manual feature ship script
#
# Use this to manually mark a feature as shipped if the automatic hook didn't trigger.
# This will:
# 1. Create a minimal shipped.md file
# 2. Clear the statusline
# 3. Regenerate DASHBOARD.md
#
# Usage: ship-feature.sh <project_root> <feature_id> [summary]
#
# Example:
#   ./skills/feature-ship/scripts/ship-feature.sh /path/to/project my-feature "Implemented the feature"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$PLUGIN_ROOT/hooks/lib/common.sh"

PROJECT_ROOT="${1:-}"
FEATURE_ID="${2:-}"
SUMMARY="${3:-Feature completed}"

if [[ -z "$PROJECT_ROOT" || -z "$FEATURE_ID" ]]; then
  echo "Usage: ship-feature.sh <project_root> <feature_id> [summary]"
  echo ""
  echo "Example:"
  echo "  ./skills/feature-ship/scripts/ship-feature.sh /path/to/project my-feature \"Implemented the feature\""
  exit 1
fi

FEATURE_DIR="$PROJECT_ROOT/docs/features/$FEATURE_ID"
SHIPPED_FILE="$FEATURE_DIR/shipped.md"
IDEA_FILE="$FEATURE_DIR/idea.md"

# Validate feature exists
if [[ ! -d "$FEATURE_DIR" ]]; then
  echo "Error: Feature directory not found: $FEATURE_DIR"
  exit 1
fi

if [[ ! -f "$IDEA_FILE" ]]; then
  echo "Error: idea.md not found - this doesn't appear to be a valid feature"
  exit 1
fi

# Check if already shipped
if [[ -f "$SHIPPED_FILE" ]]; then
  echo "Feature already has shipped.md"
  echo "If you want to re-ship, delete $SHIPPED_FILE first"
  exit 1
fi

# Get feature name from idea.md frontmatter
FEATURE_NAME=$(grep -E "^name:" "$IDEA_FILE" | head -1 | sed 's/^name:[[:space:]]*//' || echo "$FEATURE_ID")

# Get today's date
TODAY=$(date +"%Y-%m-%d")

log_info "Creating shipped.md for: $FEATURE_ID"

# Create shipped.md
cat > "$SHIPPED_FILE" << EOF
---
shipped: $TODAY
---

# Shipped: $FEATURE_NAME

## Summary
$SUMMARY

## Notes
Marked as shipped via manual script.
EOF

log_info "Created: $SHIPPED_FILE"

# Clear statusline
log_info "Clearing statusline..."
"$SCRIPT_DIR/clear-context.sh" 2>/dev/null || true

# Regenerate dashboard
log_info "Regenerating DASHBOARD.md..."
"$PLUGIN_ROOT/hooks/generate-dashboard.sh" "$PROJECT_ROOT" || {
  log_info "Warning: Dashboard regeneration failed"
}

log_info "Feature shipped successfully: $FEATURE_ID"
echo ""
echo "Next steps:"
echo "  1. Review $SHIPPED_FILE and add more details if needed"
echo "  2. Commit the changes: git add docs/features/ && git commit -m \"Ship: $FEATURE_NAME\""
