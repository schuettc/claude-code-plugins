#!/usr/bin/env bash
# Check that the local base branch is in sync with origin/<base>.
#
# Exit codes:
#   0 — in sync (safe to proceed)
#   1 — local is ahead of origin (unpushed work — branching here would carry those commits into the PR)
#   2 — local is behind origin (needs pull)
#   3 — local diverged from origin (manual resolution required)
#   4 — usage error
#
# Usage: check-base-sync.sh <base-branch>

set -euo pipefail

BASE="${1:-}"
if [[ -z "$BASE" ]]; then
  echo "Usage: check-base-sync.sh <base-branch>" >&2
  exit 4
fi

# Fetch quietly; the script returns useful exit codes even if fetch fails
# (e.g., no network) — we just compare what we have.
if ! git fetch origin "$BASE" --quiet 2>/dev/null; then
  echo "check-base-sync: warning — could not fetch origin/$BASE; comparing against last-known remote ref" >&2
fi

if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
  echo "check-base-sync: local branch '$BASE' does not exist" >&2
  exit 4
fi

if ! git rev-parse --verify "origin/$BASE" >/dev/null 2>&1; then
  echo "check-base-sync: origin/$BASE does not exist (push the base branch first?)" >&2
  exit 4
fi

LOCAL=$(git rev-parse "$BASE")
REMOTE=$(git rev-parse "origin/$BASE")

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "check-base-sync: local $BASE matches origin/$BASE ($LOCAL)" >&2
  exit 0
fi

AHEAD=$(git rev-list --count "origin/$BASE..$BASE")
BEHIND=$(git rev-list --count "$BASE..origin/$BASE")

if [[ "$AHEAD" -gt 0 && "$BEHIND" -eq 0 ]]; then
  echo "check-base-sync: local $BASE is $AHEAD commit(s) ahead of origin — UNPUSHED WORK" >&2
  echo "" >&2
  echo "Branching off this state means the upcoming PR will include those unpushed commits." >&2
  echo "Options:" >&2
  echo "  - git push origin $BASE  (if those commits belong on the base)" >&2
  echo "  - git log origin/$BASE..$BASE --oneline  (to see what's pending)" >&2
  exit 1
elif [[ "$AHEAD" -eq 0 && "$BEHIND" -gt 0 ]]; then
  echo "check-base-sync: local $BASE is $BEHIND commit(s) behind origin/$BASE" >&2
  echo "Run: git pull origin $BASE" >&2
  exit 2
else
  echo "check-base-sync: local $BASE has DIVERGED from origin ($AHEAD ahead, $BEHIND behind)" >&2
  echo "Resolution is manual — investigate before branching off." >&2
  exit 3
fi
