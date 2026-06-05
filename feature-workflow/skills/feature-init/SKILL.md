---
name: feature-init
description: Initialize feature-workflow for a project, or refresh CI files with --update. Creates docs/features/, .feature-workflow.yml, and optional GitHub Actions review setup.
user-invocable: true
---

# Initialize Feature Workflow

You are executing the **FEATURE INIT** workflow — either a one-time setup for a new project, or an update that refreshes CI files in an existing project.

## Two Modes

- **Init** — first time setup. Creates `docs/features/`, `.feature-workflow.yml`, and (if chosen) the GitHub Actions review workflow + prompts + API key secret.
- **Update** — existing project. Refreshes `.github/workflows/feature-review.yml` and `.github/review-prompt-*.md` from the current plugin templates. Does **not** touch `.feature-workflow.yml`, the API key secret, or `docs/features/`. Use this after upgrading the plugin to pull in improved workflow/prompt logic.

If the user said `/feature-init --update` or asked to "update" / "refresh" the CI files, jump to **Step 3: Run Init Script** with `--update` and skip the config gathering.

## Step 1: Check for Existing Setup

Check if `.feature-workflow.yml` exists in the project root. If it does, read it and show the current config:

**"Feature workflow is already configured:**
```
Branch prefix: <prefix>
Target branch: <target>
Reviewer:      <reviewer>
```
**Would you like to (a) change settings, (b) refresh CI files from the latest templates (`--update`), or (c) do nothing?"**

- **(a)** → continue to Step 2 to gather new config.
- **(b)** → run with `--update` (skip Step 2).
- **(c)** → stop.

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
   - `oci` — calls OCI Generative AI's OpenAI-compatible `chat/completions` endpoint directly (no agentic CLI). Use when the reviewer must run on an OCI-served model (e.g. `openai.gpt-4.1`) with an OCI GenAI API key.
   - `none` — skip CI review setup (can be added later by re-running init)
   - Default: `none`

4. **API key** (only if reviewer is gemini, codex, or oci) — the API key for the chosen reviewer.
   - For Gemini: a Google API key from https://aistudio.google.com/apikey
   - For Codex: an OpenAI API key from https://platform.openai.com/api-keys
   - For OCI: an OCI Generative AI API key (`sk-…`) from OCI Console → Analytics & AI → Generative AI → API keys.
   - The key is uploaded as a GitHub repo secret (`GOOGLE_API_KEY` / `OPENAI_API_KEY` / `OCI_GENAI_API_KEY`) via `gh secret set` — it is never stored locally.
   - OCI also reads two optional repo **variables**: `OCI_GENAI_BASE_URL` (default `…us-ashburn-1…/openai/v1`) and `OCI_GENAI_MODEL` (default `openai.gpt-4.1`). Set with `gh variable set` if your region/model differs.

## Step 3: Run Init Script

### Init mode

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/feature-init/scripts/init.py" . \
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
  - Enables the repo-level "Allow GitHub Actions to approve pull requests" setting so bot approvals actually land

### Update mode

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/feature-init/scripts/init.py" . --update
```

The script reads the existing reviewer from `.feature-workflow.yml` and refreshes only:
- `.github/workflows/feature-review.yml`
- `.github/review-prompt-plan.md`
- `.github/review-prompt-impl.md`
- Re-applies the bot-approval repo setting (idempotent)

It does **not** touch `.feature-workflow.yml`, the API key secret, `docs/features/`, or any feature documents. After it finishes, commit and push the refreshed files to the default branch so the new workflow is live.

> **`--update` overwrites the workflow YAML unconditionally.** If you've customized `.github/workflows/feature-review.yml` locally, those edits will be replaced by the current template. Diff before committing if you have local customizations.

> **When to run `--update`:** any time you upgrade the feature-workflow plugin. The workflow template carries bug fixes (e.g., v9.7.3 added a `concurrency:` block that prevents duplicate review comments) that only reach your project via this refresh. Plugin upgrade alone does NOT propagate to your `.github/`.

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
