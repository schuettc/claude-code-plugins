# Submit Mode

Submit the current implementation for external review. Creates a feature branch (if needed), commits changes, generates review context, and pushes.

## Step 1: Determine Round

Count existing `context-round-*.md` files in `docs/features/<id>/reviews/`:
- If none exist: this is **Round 1**
- Otherwise: round = count + 1

## Step 2: Branch Management

Check the current branch:

```bash
git branch --show-current
```

**Round 1 (first submission):**
1. Create and switch to the feature branch:
   ```bash
   git checkout -b feature/<id>
   ```
2. If the branch already exists, switch to it:
   ```bash
   git checkout feature/<id>
   ```

**Round N > 1 (subsequent submissions):**
1. Verify you're on `feature/<id>` — if not, switch to it
2. Continue on the existing branch

## Step 3: Stage and Commit

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
   git commit -m "feat(<id>): submit for review round N"
   ```

## Step 4: Generate Review Context (Hybrid)

Auto-generate a draft context file, then present it to the user for editing.

### 4a: Gather Raw Data

Collect information for the context draft:

1. **Git diff summary** — what files changed:
   ```bash
   git diff main --stat
   ```
2. **Commit messages** since branching (or since last round):
   ```bash
   git log main..HEAD --oneline
   ```
3. **Plan.md progress** — read `docs/features/<id>/plan.md` and extract:
   - Which implementation steps are checked off `[x]`
   - Which are still pending `[ ]`
4. **If Round > 1**: Read the previous `context-round-(N-1).md` and the review files from round N-1 to understand what was addressed

### 4b: Draft the Context File

Generate a draft with the following structure:

```markdown
---
round: N
branch: feature/<id>
commit: <HEAD sha>
submitted: YYYY-MM-DD HH:MM:SS
---

# Review Context: Round N

## What Was Done
- [Auto-generated from commit messages and plan.md checked items]

## Why
- [Auto-generated from idea.md problem statement and plan.md rationale]

## How
- [Auto-generated from git diff summary — key files and areas changed]

## Changes Since Last Round
- [If round > 1: summarize what changed based on review feedback addressed]
- [If round 1: "Initial submission"]

## Areas of Concern
- [Leave blank for user to fill in]
```

### 4c: Present Draft to User

Show the draft to the user and ask:
- **"Here's the auto-generated review context. Please review and edit — especially the 'Areas of Concern' section. What should reviewers focus on?"**

Incorporate the user's edits into the final version.

## Step 5: Write Context File

Write the final context to `docs/features/<id>/reviews/context-round-N.md`.

Create the `reviews/` directory if it doesn't exist.

## Step 6: Commit and Push

1. Stage the context file:
   ```bash
   git add docs/features/<id>/reviews/context-round-N.md
   ```
2. Commit:
   ```bash
   git commit -m "docs(<id>): add review context for round N"
   ```
3. Push the branch:
   ```bash
   git push -u origin feature/<id>
   ```

## Step 7: Display Next Steps

```
## Ready for Review (Round N)

Branch `feature/<id>` pushed to origin.
Review context: docs/features/<id>/reviews/context-round-N.md

### To trigger reviewers:
- **Gemini**: `activate_skill feature-reviewer` then review <id>
- **Codex**: `/implementation-review <id>`

### When reviews are complete:
Run `/feature-submit <id> --respond` to read feedback and iterate.

### If reviews are satisfactory:
Run `/feature-ship <id>` to merge and complete the feature.
```
