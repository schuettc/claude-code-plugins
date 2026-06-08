#!/usr/bin/env bash
# Generate a feature-workflow review via OCI Generative AI's OpenAI-compatible
# chat/completions endpoint. A single chat call can't explore the repo the way
# an agentic reviewer (codex/gemini) does, so this gathers the context the
# review prompt references — the PR diff plus the feature's idea.md/plan.md —
# and sends it inline. Prints the review markdown to stdout; exits non-zero on
# failure so the workflow falls back to an "unavailable" note.
#
# Env (set by feature-review.yml): OPENAI_API_KEY, BASE_URL, MODEL, PR_NUMBER,
#   HEAD_REF, BASE_REF, PROMPT_FILE, GH_TOKEN.
set -uo pipefail

: "${OPENAI_API_KEY:?OCI_GENAI_API_KEY secret is not set}"
: "${BASE_URL:?BASE_URL not set}"
: "${MODEL:?MODEL not set}"
: "${PR_NUMBER:?PR_NUMBER not set}"
: "${PROMPT_FILE:?PROMPT_FILE not set}"
# Optional under set -u (always present on pull_request events; default for safety).
HEAD_REF="${HEAD_REF:-}"
BASE_REF="${BASE_REF:-main}"

DIFF="$(gh pr diff "$PR_NUMBER" --patch 2>/dev/null | head -c 250000)"

# feature-workflow branches are "<prefix>/<id>"; use the last segment to find the
# feature's spec so impl review can compare against idea.md / plan.md.
FID="${HEAD_REF##*/}"
CONTEXT=""
for f in "docs/features/$FID/idea.md" "docs/features/$FID/plan.md"; do
  if [ -f "$f" ]; then
    CONTEXT+="

===== $f =====
$(cat "$f")"
  fi
done

INPUT="$(mktemp)"
{
  cat "$PROMPT_FILE"
  printf '\n\n## PR #%s (%s -> %s)\n' "$PR_NUMBER" "${HEAD_REF:-?}" "${BASE_REF:-main}"
  [ -n "$CONTEXT" ] && printf '\n## Feature context\n%s\n' "$CONTEXT"
  printf '\n## Diff under review\n```diff\n%s\n```\n' "$DIFF"
} > "$INPUT"

BODY="$(mktemp)"
# Use max_completion_tokens, not max_tokens: gpt-5.x models (e.g. the configured
# OCI_GENAI_MODEL openai.gpt-5.5) reject max_tokens with HTTP 400 ("Unsupported
# parameter ... Use 'max_completion_tokens' instead"). The budget must also cover
# reasoning: gpt-5.5 spends ~1.5-2k reasoning tokens on a real review prompt, so a
# 2000 budget is fully consumed by reasoning (finish_reason=length, empty content)
# and the workflow only ever posts the "unavailable" placeholder. 16000 leaves
# room for the review markdown after reasoning (verified against the live endpoint).
jq -n --rawfile u "$INPUT" '{
  model: env.MODEL,
  max_completion_tokens: 16000,
  messages: [
    {role: "system", content: "You are a senior reviewer. Follow the reviewer instructions in the user message exactly. Output only the review markdown — do not run commands and do not attempt to post anything."},
    {role: "user", content: $u}
  ]
}' > "$BODY"

RESP="$(mktemp)"
code=$(curl -sS -m 180 -o "$RESP" -w '%{http_code}' -X POST \
  "$BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @"$BODY") || { echo "curl to OCI GenAI failed" >&2; exit 1; }

if [ "$code" != "200" ]; then
  echo "OCI GenAI returned HTTP $code" >&2
  head -c 400 "$RESP" >&2
  exit 1
fi

content="$(jq -r '.choices[0].message.content // empty' "$RESP")"
[ -n "$content" ] || { echo "empty content from model" >&2; exit 1; }
printf '%s\n' "$content"
