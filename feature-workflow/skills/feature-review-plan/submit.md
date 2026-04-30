# Submit Plan for Review

Submit the feature plan for external review. Creates a feature branch (if needed), commits the plan, pushes, and opens a draft PR.

## Step 1: Branch Management

Check the current branch:

```bash
git branch --show-current
```

Check if a PR already exists for this feature:

```bash
gh api "repos/{owner}/{repo}/pulls?state=open&per_page=100" \
  --jq '[.[] | select(.head.ref == "feature/<id>")] | .[0] | {number, url: .html_url, state}'
```

**If no feature branch exists (first submission):**
1. Ensure you're on the target branch, synced with remote, and local commits are pushed:
   ```bash
   git checkout dev && git pull && git push
   ```
   The `git push` is critical — if local has unpushed commits, the remote base
   branch will be stale and GitHub Actions `labeled` triggers may silently fail
   because the workflow file on the remote base doesn't match expectations.
2. Create and switch to the feature branch from the target branch:
   ```bash
   git checkout -b feature/<id>
   ```

**If feature branch already exists (subsequent submissions):**
1. Verify you're on `feature/<id>` — if not, switch to it
2. Continue on the existing branch

## Step 2: Stage and Commit

1. Stage plan and idea files:
   ```bash
   git add docs/features/<id>/idea.md docs/features/<id>/plan.md
   ```
2. Check if there are changes to commit:
   ```bash
   git status --porcelain
   ```
3. If there are changes, commit:
   ```bash
   git commit -m "docs(<id>): submit plan for review"
   ```

## Step 3: Push Branch

```bash
git push -u origin feature/<id>
```

## Step 4: Open or Update Draft PR

### If no PR exists — create one:

Generate the PR body:

#### 4a: Gather Raw Data

1. Read `docs/features/<id>/plan.md` and extract:
   - Feature name and summary
   - Implementation steps
   - Testing strategy
   - Risks and mitigations
2. Read `docs/features/<id>/idea.md` — the original problem statement

#### 4b: Draft the PR Body

Generate a draft PR body with this structure:

```markdown
## Plan Review

This PR contains the **plan** for feature `<id>`. No implementation yet — requesting review of the approach before coding begins.

## Problem Statement
- [From idea.md]

## Proposed Approach
- [Key design decisions from plan.md]

## Implementation Steps
- [Numbered steps from plan.md]

## Testing Strategy
- [From plan.md]

## Risks & Mitigations
- [From plan.md]

## Areas of Concern
- [Leave blank for user to fill in — what should reviewers focus on?]

---
*Feature: <id> | Phase: Plan Review | Plan: docs/features/<id>/plan.md*
```

#### 4c: Present Draft to User

Show the draft to the user and ask:
- **"Here's the auto-generated PR description. Please review and edit — especially the 'Areas of Concern' section. What should reviewers focus on?"**

Incorporate the user's edits into the final version.

#### 4d: Create the PR (non-draft)

```bash
gh pr create --title "plan(<id>): [feature name]" --base dev --body "<PR body>"
```

> **Why non-draft:** review gating is driven by the `plan-review` / `impl-review` labels and the `feature-review.yml` workflow, not by draft state. Opening as draft would force a `gh pr ready` (GraphQL-only mutation) at ship time, which has hit secondary rate limits during multi-feature sweeps. The label is the gate; the merge is blocked by branch protection or human approval, not by draft state.

### If PR already exists — update it:

1. Push is already done (Step 3), PR auto-updates with new commits
2. Add a comment summarizing what changed:
   ```bash
   gh pr comment <pr-number> --body "## Plan Update\n\n### Changes Made\n- [summary of plan changes]\n\n### Feedback Addressed\n- [which review items were fixed]"
   ```

## Step 5: Add Review Label (if CI reviewer configured)

Read `.feature-workflow.yml` and check the `reviewer:` setting.

**If reviewer is `gemini` or `codex`:**

```bash
gh pr edit <pr-number> --add-label plan-review
```

This automatically triggers the GitHub Actions workflow to run the external review.

**If reviewer is `none`:** Skip this step.

## Step 6: Display Next Steps and STOP

Display the following to the user, then **STOP**. Do NOT launch any code review agents, do NOT run any review skills, do NOT analyze the plan further. Your job is done.

**If CI reviewer is configured:**

```
## Plan Submitted for Review

PR: <pr-url>
Branch: feature/<id>
Status: Draft
Phase: Plan Review
Label: plan-review (added — CI review will start automatically)

### What happens next:
The external reviewer will analyze the plan and post findings directly on the PR.
Watch the PR for comments.

### When reviews are complete:
Run `/feature-review-plan <id> --respond` to read feedback and iterate.

### When plan is approved:
Run `/feature-implement <id>` to start coding.
```

**If no CI reviewer (reviewer: none):**

```
## Plan Ready for Review

PR: <pr-url>
Branch: feature/<id>
Status: Draft
Phase: Plan Review

### To trigger reviewers:
- **Gemini**: "Review the plan at <pr-url> for feature <id>"
- **Codex**: "Review the plan at <pr-url> for feature <id>"

### When reviews are complete:
Run `/feature-review-plan <id> --respond` to read feedback and iterate.

### When plan is approved:
Run `/feature-implement <id>` to start coding.
```

**IMPORTANT: After displaying the above, your turn is COMPLETE. Do not take any further action.**
