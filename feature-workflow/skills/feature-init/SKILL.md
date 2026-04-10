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

## Step 3: Run Init Script

Pass the configuration to the init script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/feature-init/scripts/init.py" "$(pwd)" --prefix "<prefix>" --target "<target>"
```

The script creates:
- `docs/features/` directory with initial `DASHBOARD.md`
- `.feature-workflow.yml` config file

## Step 4: Confirm

```
## Feature Workflow Initialized

Config: .feature-workflow.yml
  Branch prefix: <prefix>
  Target branch: <target>

Feature branches will be named: <prefix><feature-id>
PRs will target: <target>

### Next Steps
- `/feature-capture` to create your first feature
- Edit .feature-workflow.yml anytime to change settings
```
