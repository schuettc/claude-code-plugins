#!/bin/bash
# Common utilities for feature-workflow hooks

set -euo pipefail

# Colors for output (disabled if not a terminal)
if [[ -t 2 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  NC='\033[0m' # No Color
else
  RED=''
  GREEN=''
  YELLOW=''
  NC=''
fi

# Global result file path (set by transition scripts)
RESULT_FILE="${RESULT_FILE:-}"

# Exit with error and write result
exit_error() {
  local msg="$1"
  if [[ -n "$RESULT_FILE" ]]; then
    echo "{\"success\":false,\"error\":\"$msg\"}" > "$RESULT_FILE"
  fi
  echo -e "${RED}ERROR: $msg${NC}" >&2
  exit 2  # Exit code 2 signals error to Claude Code
}

# Exit with success and write result
exit_success() {
  local result="$1"
  if [[ -n "$RESULT_FILE" ]]; then
    echo "$result" > "$RESULT_FILE"
  fi
  echo -e "${GREEN}SUCCESS${NC}" >&2
  exit 0
}

# Log info message
log_info() {
  echo -e "${YELLOW}[transition]${NC} $1" >&2
}

# Get current ISO timestamp
get_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%S.000Z"
}

# Check if jq is available
check_jq() {
  if ! command -v jq &> /dev/null; then
    exit_error "jq is required but not installed. Install with: brew install jq"
  fi
}

# Initialize - call at start of each transition script
init_transition() {
  check_jq
}
