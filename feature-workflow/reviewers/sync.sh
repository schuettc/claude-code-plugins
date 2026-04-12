#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GEMINI_REPO="${GEMINI_REPO:-$REPO_ROOT/../gemini-reviewer}"
CODEX_REPO="${CODEX_REPO:-$REPO_ROOT/../codex-reviewer}"

CLI_APPROVAL_MANDATE='3. **APPROVAL BEFORE POSTING:** You MUST NOT post anything to GitHub without explicit user approval. Always present the full review draft (top-level body + every inline comment) in the chat first and wait for the user to say "post it", "approved", or equivalent. If the user asks for edits, revise and present again. No `gh pr review`, no `gh pr comment`, no `gh api .../comments` until approved.'

CLI_APPROVAL_STEP='## Step 4: Present the draft for approval

Before calling any `gh` command that writes to GitHub, output the full proposed review in the chat:

1. The top-level review body (verdict, critical findings, recommendations, residual risks, areas-of-concern response).
2. Every inline comment you intend to post, each with its `path`, `line`, and full body.

Then stop and ask: **"Post this review to PR #<n>? (yes / edit / cancel)"**

- **yes / approved / post it** → proceed to the posting step.
- **edit** → revise based on the feedback and present the updated draft again.
- **cancel** → do not post anything. Done.

Never skip this step. Never post a "preview" comment, a single inline, or a top-level body without approval covering the whole review.

'

generate_cli_skill() {
  local skill_name="$1"
  local source_file="$SKILLS_DIR/$skill_name.md"
  local description

  description=$(head -1 "$source_file" | sed 's/^# //')

  {
    echo "---"
    echo "name: $skill_name"
    echo "description: $description"
    echo "---"
    echo ""

    sed \
      -e "s/^3\. \*\*POST DIRECTLY:.*/$(echo "$CLI_APPROVAL_MANDATE" | sed 's/[&/\]/\\&/g')/" \
      -e '/^## Step 4: Post the PR Review$/i\
'"$(echo "$CLI_APPROVAL_STEP" | sed 's/[&/\]/\\&/g')" \
      -e 's/^## Step 4: Post the PR Review$/## Step 5: Post the PR Review (only after approval)/' \
      "$source_file"
  }
}

generate_cli_skill_simple() {
  local skill_name="$1"
  local source_file="$SKILLS_DIR/$skill_name.md"
  local description
  local content

  description=$(head -1 "$source_file" | sed 's/^# //')
  content=$(cat "$source_file")

  content=$(echo "$content" | sed "s|^3\. \*\*POST DIRECTLY:\*\*.*|$CLI_APPROVAL_MANDATE|")

  local step4_header
  if echo "$content" | grep -q "^## Step 4: Post the PR Review"; then
    step4_header="## Step 4: Post the PR Review"
    local new_header="## Step 5: Post the PR Review (only after approval)"
    content=$(echo "$content" | sed "s|^$step4_header|${CLI_APPROVAL_STEP}${new_header}|")
  fi

  echo "---"
  echo "name: $skill_name"
  echo "description: $description"
  echo "---"
  echo ""
  echo "$content"
}

echo "=== Syncing reviewer skills ==="
echo "Source: $SKILLS_DIR"
echo "Gemini: $GEMINI_REPO"
echo "Codex:  $CODEX_REPO"
echo ""

for repo in "$GEMINI_REPO" "$CODEX_REPO"; do
  if [ ! -d "$repo" ]; then
    echo "ERROR: $repo does not exist. Clone it first."
    exit 1
  fi
done

for skill in feature-review-plan feature-review-impl; do
  source_file="$SKILLS_DIR/$skill.md"
  if [ ! -f "$source_file" ]; then
    echo "ERROR: $source_file not found"
    exit 1
  fi

  description=$(head -1 "$source_file" | sed 's/^# //')

  # --- Gemini: flat root-level */SKILL.md ---
  gemini_dir="$GEMINI_REPO/$skill"
  mkdir -p "$gemini_dir"

  {
    echo "---"
    echo "name: $skill"
    echo "description: $description"
    echo "---"
    echo ""
    cat "$source_file"
  } > "$gemini_dir/SKILL.md"

  echo "  Wrote $gemini_dir/SKILL.md"

  # --- Codex: skills/*/SKILL.md ---
  codex_dir="$CODEX_REPO/skills/$skill"
  mkdir -p "$codex_dir"

  {
    echo "---"
    echo "name: $skill"
    echo "description: $description"
    echo "---"
    echo ""
    cat "$source_file"
  } > "$codex_dir/SKILL.md"

  echo "  Wrote $codex_dir/SKILL.md"
done

echo ""
echo "=== Sync complete ==="
echo ""
echo "Review diffs:"
echo "  cd $GEMINI_REPO && git diff"
echo "  cd $CODEX_REPO && git diff"
echo ""
echo "Then commit and push each repo."
