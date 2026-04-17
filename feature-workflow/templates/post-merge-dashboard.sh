#!/usr/bin/env bash
# Post-merge hook: regenerate DASHBOARD.md from the merged working tree.
# Installed by /feature-init into .git/hooks/post-merge.
#
# The merge driver (via .gitattributes) prevents DASHBOARD.md conflicts
# by keeping "ours" and exiting 0.  This hook then regenerates from the
# full merged tree so the local copy is accurate.  CI handles the commit
# on main/dev.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
REGEN="$REPO_ROOT/.github/scripts/dashboard-regen.py"

if [[ ! -f "$REGEN" ]]; then
    exit 0
fi

python3 "$REGEN" "$REPO_ROOT"
