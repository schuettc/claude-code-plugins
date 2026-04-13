#!/usr/bin/env bash
# Parse a reviewer LLM's structured output and post it to the PR.
#
# Expected env vars:
#   PR_NUMBER      — PR to post the review on
#   REVIEW_KIND    — "Plan" or "Implementation" (used in fallback body)
#   GEMINI_SUMMARY — the raw LLM response (may also come from a different reviewer;
#                    the var name is historical)
#
# The LLM response must contain a line of the form:
#   VERDICT: PASS | CONDITIONAL_PASS | FAIL
# anywhere in the output. Any preamble before that line is discarded; the
# clean body posted to the PR is everything *after* the verdict line. An
# optional inline comments block may appear anywhere in the body:
#   <!-- INLINE_COMMENTS_JSON -->
#   [ {"path": "...", "line": N, "body": "..."}, ... ]
#   <!-- END_INLINE_COMMENTS_JSON -->
#
# Verdict mapping:
#   PASS             → gh pr review --approve
#   CONDITIONAL_PASS → gh pr review --comment
#   FAIL             → gh pr review --request-changes
#   (missing/unparseable) → gh pr review --comment with the raw output

set -euo pipefail

if [[ -z "${GEMINI_SUMMARY:-}" ]]; then
  echo "::warning::No reviewer output to post — skipping."
  exit 0
fi

SUMMARY_FILE="$(mktemp)"
printf '%s' "$GEMINI_SUMMARY" > "$SUMMARY_FILE"

# Find the verdict line anywhere in the output (LLMs often emit a reasoning
# preamble before the structured review). Take the first match.
VERDICT_LINE="$(grep -m1 -E '^VERDICT: (PASS|CONDITIONAL_PASS|FAIL)$' "$SUMMARY_FILE" || true)"
VERDICT=""
case "$VERDICT_LINE" in
  "VERDICT: PASS")             VERDICT="PASS" ;;
  "VERDICT: CONDITIONAL_PASS") VERDICT="CONDITIONAL_PASS" ;;
  "VERDICT: FAIL")             VERDICT="FAIL" ;;
esac

# Extract the inline comments JSON block (if present) and strip it from the
# main body so the body posted as the top-level review is clean. When a
# verdict was found, also drop everything up to and including the verdict
# line so any reasoning preamble doesn't leak into the posted review.
BODY_FILE="$(mktemp)"
INLINE_JSON_FILE="$(mktemp)"
awk -v verdict="$VERDICT_LINE" '
  BEGIN { inblock = 0; past_verdict = (verdict == "") ? 1 : 0 }
  /<!-- INLINE_COMMENTS_JSON -->/ { inblock = 1; next }
  /<!-- END_INLINE_COMMENTS_JSON -->/ { inblock = 0; next }
  {
    if (inblock) { print > "'"$INLINE_JSON_FILE"'"; next }
    if (!past_verdict) {
      if ($0 == verdict) { past_verdict = 1 }
      next
    }
    print > "'"$BODY_FILE"'"
  }
' "$SUMMARY_FILE"

# Trim leading blank lines from the body.
if [[ -n "$VERDICT" && -s "$BODY_FILE" ]]; then
  sed '/./,$!d' "$BODY_FILE" > "${BODY_FILE}.tmp"
  mv "${BODY_FILE}.tmp" "$BODY_FILE"
fi

# Fallback if no verdict was detected: post as a comment with the raw output.
if [[ -z "$VERDICT" ]]; then
  echo "::warning::Could not parse verdict line from reviewer output. Posting as comment."
  {
    echo "## ${REVIEW_KIND} Review (unparsed)"
    echo ""
    echo "The reviewer did not emit a recognizable \`VERDICT:\` line. Raw output:"
    echo ""
    echo '```'
    cat "$SUMMARY_FILE"
    echo '```'
  } > "$BODY_FILE"
  VERDICT="CONDITIONAL_PASS"
fi

case "$VERDICT" in
  PASS)             FLAG="--approve" ;;
  CONDITIONAL_PASS) FLAG="--comment" ;;
  FAIL)             FLAG="--request-changes" ;;
esac

echo "Posting ${REVIEW_KIND} review with verdict ${VERDICT} (${FLAG})."
gh pr review "$PR_NUMBER" $FLAG --body-file "$BODY_FILE"

# Post inline comments if the JSON parses.
if [[ -s "$INLINE_JSON_FILE" ]] && jq -e 'type == "array"' "$INLINE_JSON_FILE" >/dev/null 2>&1; then
  COUNT="$(jq 'length' "$INLINE_JSON_FILE")"
  if [[ "$COUNT" -gt 0 ]]; then
    REPO_FULL_NAME="${GITHUB_REPOSITORY:-}"
    HEAD_SHA="$(gh pr view "$PR_NUMBER" --json headRefOid --jq '.headRefOid')"
    echo "Posting ${COUNT} inline comment(s)."
    jq -c '.[]' "$INLINE_JSON_FILE" | while IFS= read -r obj; do
      P="$(jq -r '.path' <<<"$obj")"
      L="$(jq -r '.line' <<<"$obj")"
      B="$(jq -r '.body' <<<"$obj")"
      if [[ -z "$P" || -z "$L" || "$L" == "null" || -z "$B" ]]; then
        echo "::warning::Skipping malformed inline comment: $obj"
        continue
      fi
      gh api "repos/${REPO_FULL_NAME}/pulls/${PR_NUMBER}/comments" \
        --method POST \
        -f "body=$B" \
        -f "commit_id=$HEAD_SHA" \
        -f "path=$P" \
        -F "line=$L" \
        -f "side=RIGHT" \
        >/dev/null || echo "::warning::Failed to post inline comment at ${P}:${L}"
    done
  fi
elif [[ -s "$INLINE_JSON_FILE" ]]; then
  echo "::warning::Inline comments block present but not valid JSON — skipping inline posting."
fi

echo "Review posted."
