---
name: feature-init
description: Initialize feature-workflow for a project. Creates docs/features/ directory and .feature-workflow.yml config with branch settings. Run once per project.
user-invocable: true
---

# Initialize Feature Workflow

You are executing the **FEATURE INIT** workflow — a one-time setup that configures the feature workflow for this project.

## Step 1: Check for Existing Setup

Check if `.feature-workflow.yml` exists in the project root. If it does, read it and show the current config:

**"Feature workflow is already configured:**
```
Branch prefix: <prefix>
Target branch: <target>
```
**Would you like to update these settings?"**

If the user says no, stop.

## Step 2: Gather Configuration

$ARGUMENTS

If arguments were provided, parse them as `<branch-prefix> <target-branch>` (e.g., `/feature-init feat/ main`).

If no arguments, ask the user:

1. **Branch prefix** — what prefix do feature branches use?
   - Examples: `feature/`, `feat/`, `fix/`, `topic/`
   - Default: `feature/`

2. **Target branch** — what branch do feature PRs merge into?
   - Examples: `dev`, `develop`, `main`, `staging`
   - Default: `dev`

3. **External reviewer** — which AI reviewer should review PRs via GitHub Actions?
   - `gemini` — uses Google's Gemini CLI via `google-github-actions/run-gemini-cli`
   - `codex` — uses OpenAI's Codex CLI via `openai/codex-action`
   - `none` — skip CI review setup (can be added later by re-running init)
   - Default: `none`

4. **API key** (only if reviewer is gemini or codex) — the API key for the chosen reviewer.
   - For Gemini: a Google API key from https://aistudio.google.com/apikey
   - For Codex: an OpenAI API key from https://platform.openai.com/api-keys
   - The key is uploaded as a GitHub repo secret via `gh secret set` — it is never stored locally.

## Step 3: Run Init Script

Pass the configuration to the init script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/feature-init/scripts/init.py" "$(pwd)" \
  --prefix "<prefix>" \
  --target "<target>" \
  --reviewer "<reviewer>" \
  --api-key "<api-key>"
```

The script creates:
- `docs/features/` directory with initial `DASHBOARD.md`
- `.feature-workflow.yml` config file (includes `reviewer:` setting)
- If reviewer configured:
  - `.github/workflows/feature-review.yml` — GitHub Actions workflow
  - `.github/review-prompt-plan.md` — plan review prompt
  - `.github/review-prompt-impl.md` — implementation review prompt
  - Uploads the API key as a GitHub repo secret

## Step 4: Confirm

```
## Feature Workflow Initialized

Config: .feature-workflow.yml
  Branch prefix: <prefix>
  Target branch: <target>
  Reviewer:      <reviewer>

Feature branches will be named: <prefix><feature-id>
PRs will target: <target>

### CI Review Setup (if reviewer configured)
- Workflow: .github/workflows/feature-review.yml
- API secret: GOOGLE_API_KEY or OPENAI_API_KEY (uploaded)
- IMPORTANT: Commit and push the .github/ files to your default branch
  before creating your first feature PR.

### Next Steps
- `/feature-capture` to create your first feature
- Edit .feature-workflow.yml anytime to change settings
```
