# Submit Implementation for Review

Submit the implementation for external review. Pushes code to the existing feature branch and updates (or creates) the draft PR.

## Step 1: Branch Management

Check the current branch:

```bash
git branch --show-current
```

Check if a PR already exists for this feature:

```bash
gh pr list --head feature/<id> --json number,url,state --jq '.[0]'
```

**If feature branch already exists (expected — created during plan review):**
1. Verify you're on `feature/<id>` — if not, switch to it
2. Continue on the existing branch

**If no feature branch exists (plan review was skipped):**
1. Ensure you're on `dev` and up to date:
   ```bash
   git checkout dev && git pull
   ```
2. Create and switch to the feature branch from `dev`:
   ```bash
   git checkout -b feature/<id>
   ```

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
   git commit -m "feat(<id>): submit implementation for review"
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
## Implementation Review

This PR contains the **implementation** for feature `<id>`. Requesting review of the code before shipping.

## What Was Done
- [Auto-generated from commit messages and plan.md checked items]

## Why
- [From idea.md problem statement and plan.md rationale]

## How
- [From git diff summary — key files and areas changed]

## Areas of Concern
- [Leave blank for user to fill in]

---
*Feature: <id> | Phase: Implementation Review | Plan: docs/features/<id>/plan.md*
```

#### 4c: Present Draft to User

Show the draft to the user and ask:
- **"Here's the auto-generated PR description. Please review and edit — especially the 'Areas of Concern' section. What should reviewers focus on?"**

Incorporate the user's edits into the final version.

#### 4d: Create the Draft PR

The PR should target `dev`:

```bash
gh pr create --draft --title "feat(<id>): [feature name]" --base dev --body "<PR body>"
```

### If PR already exists — update it:

1. Push is already done (Step 3), PR auto-updates with new commits
2. Update the PR body to reflect the implementation phase:
   ```bash
   gh pr comment <pr-number> --body "## Implementation Submitted

### Phase: Implementation Review

This PR now includes the implementation. Previous plan review comments are preserved above.

### Changes Since Plan Review
- [Summary of implementation changes]

### Implementation Highlights
- [Key technical details]

### Areas of Concern
- [What reviewers should focus on]"
   ```

## Step 5: Swap Review Labels (if CI reviewer configured)

Read `.feature-workflow.yml` and check the `reviewer:` setting.

**If reviewer is `gemini` or `codex`:**

Remove the plan-review label (if present) and add impl-review:

```bash
gh pr edit <pr-number> --remove-label plan-review --add-label impl-review
```

This automatically triggers the GitHub Actions workflow to run the implementation review.

**If reviewer is `none`:** Skip this step.

## Step 6: Display Next Steps and STOP

Display the following to the user, then **STOP**. Do NOT launch any code review agents, do NOT run any review skills, do NOT analyze the code further. Your job is done.

**If CI reviewer is configured:**

```
## Implementation Submitted for Review

PR: <pr-url>
Branch: feature/<id>
Status: Draft
Phase: Implementation Review
Label: impl-review (added — CI review will start automatically)

### What happens next:
The external reviewer will analyze the implementation and post findings directly on the PR.
Watch the PR for comments.

### When reviews are complete:
Run `/feature-review-impl <id> --respond` to read feedback and iterate.

### If reviews are satisfactory:
Run `/feature-ship <id>` to merge and complete the feature.
```

**If no CI reviewer (reviewer: none):**

```
## Implementation Ready for Review

PR: <pr-url>
Branch: feature/<id>
Status: Draft
Phase: Implementation Review

### To trigger reviewers:
- **Gemini**: "Review the implementation at <pr-url> for feature <id>"
- **Codex**: "Review the implementation at <pr-url> for feature <id>"

### When reviews are complete:
Run `/feature-review-impl <id> --respond` to read feedback and iterate.

### If reviews are satisfactory:
Run `/feature-ship <id>` to merge and complete the feature.
```

**IMPORTANT: After displaying the above, your turn is COMPLETE. Do not take any further action.**
