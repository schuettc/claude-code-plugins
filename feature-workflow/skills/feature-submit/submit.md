# Submit Mode

Submit the current implementation for external review. Creates a feature branch (if needed), commits changes, pushes, and opens a draft PR.

## Step 1: Branch Management

Check the current branch:

```bash
git branch --show-current
```

Check if a PR already exists for this feature:

```bash
gh pr list --head feature/<id> --json number,url,state --jq '.[0]'
```

**If no feature branch exists (first submission):**
1. Ensure you're on `dev` and up to date:
   ```bash
   git checkout dev && git pull
   ```
2. Create and switch to the feature branch from `dev`:
   ```bash
   git checkout -b feature/<id>
   ```
3. If the branch already exists locally, switch to it:
   ```bash
   git checkout feature/<id>
   ```

**If feature branch already exists (subsequent submissions):**
1. Verify you're on `feature/<id>` — if not, switch to it
2. Continue on the existing branch

## Step 2: Stage and Commit

1. Stage all implementation changes:
   ```bash
   git add -A
   ```
2. Check if there are changes to commit:
   ```bash
   git status --porcelain
   ```
3. If there are changes, commit:
   ```bash
   git commit -m "feat(<id>): submit for review"
   ```

## Step 3: Push Branch

```bash
git push -u origin feature/<id>
```

## Step 4: Open or Update Draft PR

### If no PR exists — create one:

Generate the PR body using a hybrid approach:

#### 4a: Gather Raw Data

1. **Git diff summary** — what files changed:
   ```bash
   git diff dev --stat
   ```
2. **Commit messages** since branching:
   ```bash
   git log dev..HEAD --oneline
   ```
3. **Plan.md progress** — read `docs/features/<id>/plan.md` and extract:
   - Which implementation steps are checked off `[x]`
   - Which are still pending `[ ]`
4. **idea.md** — the original problem statement

#### 4b: Draft the PR Body

Generate a draft PR body with this structure:

```markdown
## What Was Done
- [Auto-generated from commit messages and plan.md checked items]

## Why
- [From idea.md problem statement and plan.md rationale]

## How
- [From git diff summary — key files and areas changed]

## Areas of Concern
- [Leave blank for user to fill in]

---
*Feature: <id> | Plan: docs/features/<id>/plan.md*
```

#### 4c: Present Draft to User

Show the draft to the user and ask:
- **"Here's the auto-generated PR description. Please review and edit — especially the 'Areas of Concern' section. What should reviewers focus on?"**

Incorporate the user's edits into the final version.

#### 4d: Create the Draft PR

The PR should target `dev` (feature branches merge to `dev`, then `dev` merges to `main`):

```bash
gh pr create --draft --title "feat(<id>): [feature name]" --base dev --body "<PR body>"
```

### If PR already exists — update it:

1. Push is already done (Step 3), PR auto-updates with new commits
2. Add a comment summarizing what changed in this round:
   ```bash
   gh pr comment <pr-number> --body "## Round N Update\n\n### Changes Made\n- [summary of changes]\n\n### Feedback Addressed\n- [which review items were fixed]"
   ```

## Step 5: Display Next Steps

```
## Ready for Review

PR: <pr-url>
Branch: feature/<id>
Status: Draft

### To trigger reviewers:
- **Gemini**: "Review the PR at <pr-url> for feature <id>"
- **Codex**: "Review the PR at <pr-url> for feature <id>"

### When reviews are complete:
Run `/feature-submit <id> --respond` to read feedback and iterate.

### If reviews are satisfactory:
Run `/feature-ship <id>` to merge and complete the feature.
```
