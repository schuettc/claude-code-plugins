#!/usr/bin/env bash
# Wait for an external review on a PR, classify the verdict, exit accordingly.
#
# Usage: wait-for-review.sh <PR#> [plan|impl]
#
# Blocks on `gh pr checks --watch` until the review workflow resolves,
# then reads the newest review comment on the PR (prefixed with
# "## Plan Review" or "## Implementation Review" by post-review.sh)
# and classifies the verdict from the `### Verdict:` line.
#
# Exit codes:
#   0 — Verdict PASS or CONDITIONAL PASS (safe to auto-advance)
#   1 — Verdict FAIL (changes requested; pause and run `--respond`)
#   2 — Workflow failed, timed out, or no review comment present
#   3 — Usage error (bad args, mismatched review kind)
#
# Stdout: full review body (for the invoker to read and summarize)
# Stderr: progress notes + verdict

set -euo pipefail

PR="${1:-}"
KIND="${2:-plan}"

if [[ -z "$PR" ]]; then
  echo "Usage: wait-for-review.sh <PR#> [plan|impl]" >&2
  exit 3
fi

case "$KIND" in
  plan) EXPECTED_HEADER="## Plan Review" ;;
  impl) EXPECTED_HEADER="## Implementation Review" ;;
  *) echo "wait-for-review: unknown kind '$KIND' (want plan|impl)" >&2; exit 3 ;;
esac

echo "wait-for-review: PR #$PR (kind=$KIND)" >&2
echo "wait-for-review: letting GitHub Actions register the label event..." >&2
sleep 10

echo "wait-for-review: blocking on 'gh pr checks --watch'..." >&2
if ! gh pr checks "$PR" --watch >/dev/null; then
  # --watch exits non-zero if ANY check fails. Could be a workflow
  # error, or an unrelated required check. Fetch the review comment
  # anyway — if the reviewer posted one, it may still be classifiable.
  echo "wait-for-review: some checks failed; fetching review comment to classify..." >&2
fi

echo "wait-for-review: fetching latest review comment..." >&2

# REST endpoint — issue comments include PR comments (PRs are issues).
BODY=$(
  gh api "repos/{owner}/{repo}/issues/$PR/comments" --paginate \
    --jq '[.[] | select(.body | startswith("## Plan Review") or startswith("## Implementation Review"))] | last.body' \
    2>/dev/null || echo ""
)

if [[ -z "$BODY" || "$BODY" == "null" ]]; then
  echo "wait-for-review: no review comment found on PR #$PR." >&2
  HEAD_REF=$(gh api "repos/{owner}/{repo}/pulls/$PR" --jq '.head.ref' 2>/dev/null || echo "")
  if [[ -n "$HEAD_REF" ]]; then
    echo "wait-for-review: diagnose with 'gh run list --branch $HEAD_REF'." >&2
  fi
  exit 2
fi

FIRST_LINE=$(printf '%s\n' "$BODY" | head -n 1)
if [[ "$FIRST_LINE" != "$EXPECTED_HEADER" ]]; then
  echo "wait-for-review: latest review is '$FIRST_LINE' but expected '$EXPECTED_HEADER' (wrong phase?)." >&2
  exit 3
fi

# Emit the full review body to stdout for the invoker to read.
printf '%s\n' "$BODY"

VERDICT=$(
  printf '%s\n' "$BODY" \
    | grep -oE '^### Verdict: (PASS|CONDITIONAL PASS|FAIL)' \
    | head -n 1 \
    | sed 's/^### Verdict: //'
)

case "$VERDICT" in
  PASS|"CONDITIONAL PASS")
    echo "wait-for-review: verdict=$VERDICT — auto-advance" >&2
    exit 0
    ;;
  FAIL)
    echo "wait-for-review: verdict=FAIL — changes requested; invoke --respond" >&2
    exit 1
    ;;
  *)
    echo "wait-for-review: verdict line not found or unparseable; manual inspection needed" >&2
    exit 2
    ;;
esac
