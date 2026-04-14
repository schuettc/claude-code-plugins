#!/usr/bin/env bash
# Post a reviewer LLM's output to a PR as a comment.
#
# Expected env vars:
#   PR_NUMBER      — PR to post the review on
#   REVIEW_KIND    — "Plan" or "Implementation" (used in the comment header)
#   GEMINI_SUMMARY — the raw LLM response (var name is historical; any reviewer works)
#
# This intentionally does not parse the reviewer output. LLM free-text output
# is too unreliable to map to gh pr review --approve/--request-changes, and
# inline line-anchored comments frequently fail with HTTP 422 when the
# reviewer cites lines outside the diff. We post a single PR comment with
# whatever the reviewer emitted and let humans read it.

set -euo pipefail

if [[ -z "${GEMINI_SUMMARY:-}" ]]; then
  echo "::warning::No reviewer output to post — skipping."
  exit 0
fi

BODY_FILE="$(mktemp)"
{
  echo "## ${REVIEW_KIND} Review"
  echo ""
  printf '%s\n' "$GEMINI_SUMMARY"
} > "$BODY_FILE"

echo "Posting ${REVIEW_KIND} review as PR comment."
gh pr comment "$PR_NUMBER" --body-file "$BODY_FILE"
echo "Review posted."
