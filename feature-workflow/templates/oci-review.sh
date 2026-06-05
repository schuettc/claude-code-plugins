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
jq -n --rawfile u "$INPUT" '{
  model: env.MODEL,
  max_tokens: 2000,
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
