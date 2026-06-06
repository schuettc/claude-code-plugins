# Submit Implementation for Review

Submit the implementation for external review. Pushes code to the existing feature branch and updates (or creates) the draft PR.

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

**If feature branch already exists (expected — created during plan review):**
1. Verify you're on `feature/<id>` — if not, switch to it
2. Continue on the existing branch

**If no feature branch exists (plan review was skipped):**
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

## Step 2: Stage and Commit

1. Stage all implementation changes:
   ```bash
   git add -A
   ```
2. Check if there are changes to commit:
   ```bash
   git status --porcelain
   ```
3. If there are changes, commit with a Conventional Commits message (`feat`/`fix`
   for code, `docs` for doc-only changes) — do NOT use `implement(...)` or any
   other non-conventional verb; the `commit-msg` hook will reject it. See
   [../shared/commit-conventions.md](../shared/commit-conventions.md).
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

#### 4d: Create the PR (non-draft)

The PR should target `dev`:

```bash
gh pr create --title "feat(<id>): [feature name]" --base dev --body "<PR body>"
```

> **Why non-draft:** review gating is driven by the `plan-review` / `impl-review` labels, not by draft state. Opening as draft forces a `gh pr ready` (GraphQL-only mutation) at ship time, which has hit secondary rate limits during multi-feature sweeps. The label is the gate.

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

## Step 4.5: Branch by Effective Review Mode

You have the effective review mode from Step 0 of SKILL.md, and the implementation is now pushed to the feature branch. Branch:

**external_gemini / external_codex / external_default:**
Continue to Step 5 (swap `plan-review` for `impl-review`).

**internal:**
Skip the label swap. If `plan-review` is still on the PR, remove it without replacement:
```
gh pr edit <pr-number> --remove-label plan-review
```
Then follow `${CLAUDE_PLUGIN_ROOT}/skills/shared/internal-review.md` to dispatch the subagent (phase: `impl`) and post the impl review comment. Then continue to the success message step.

**skip:**
Skip the label swap. Remove any review label still on the PR:
```
gh pr edit <pr-number> --remove-label plan-review --remove-label impl-review
```
Print: "`<id>` is configured for `review: skip`. Implementation review will not be performed." Continue to the success message step with a "review skipped" note.

## Step 5: Swap Review Labels (if CI reviewer configured)

Read `.feature-workflow.yml` and check the `reviewer:` setting.

**If reviewer is `gemini` or `codex`:**

Swap labels as TWO separate operations with a short wait between, so the GitHub Actions workflow sees a clean state at each step. The previous combined `--remove --add` pattern occasionally let both labels appear briefly, which caused the workflow's job conditionals to fire against an ambiguous label set.

```bash
# 5a. Remove plan-review. The workflow listens for `labeled` (not `unlabeled`),
#     so this unlabeled event doesn't fire any job — it just clears the state.
gh pr edit <pr-number> --remove-label plan-review
sleep 3

# 5b. Add impl-review. This is the labeled event we want.
gh pr edit <pr-number> --add-label impl-review
```

The 3-second wait gives GitHub Actions time to register the unlabeled event before the labeled event arrives. Without it, the two events can coalesce in the workflow's event queue.

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
