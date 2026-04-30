---
name: feature-ship
description: Complete a feature by writing shipped.md, committing to the feature branch, and merging the PR. Use when external reviews are done and the feature is ready to ship.
user-invocable: true
---

# Ship Feature

You are executing the **SHIP FEATURE** workflow — writing the completion record, committing it to the feature branch, and merging the PR.

## Branch Configuration

**Before doing anything else**, read `.feature-workflow.yml` in the project root for branch settings. See [../shared/config.md](../shared/config.md) for details.

| Setting | Default | Used for |
|---------|---------|----------|
| `branch.prefix` | `feature/` | Branch naming: `<prefix><id>` |
| `branch.target` | `dev` | Merge target, checkout after merge |

Throughout this skill, replace `feature/<id>` with `<prefix><id>` and `dev` with `<target>` based on the config.

## First Step (Do This Now)

**Read the file at path: `docs/features/DASHBOARD.md`**

This file shows in-progress features. Look at the "In Progress" section to find features ready to ship.

## Feature Target

$ARGUMENTS

If no specific feature ID was provided above, you will help the user select from in-progress items.

---

## Workflow Overview

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Pre-flight | Verify feature is in-progress and has a PR |
| 2 | Write shipped.md | Create completion record on the feature branch |
| 3 | Prepare PR | Remove review labels + commit and push shipped.md |
| 4 | Merge PR | Mark PR ready, merge into dev, clean up branches |
| 5 | Update Dashboard | Regenerate dashboard and clear statusline |

---

## Phase 1: Pre-flight

1. Read the feature's `idea.md` and `plan.md` for context
2. Verify feature is in-progress (has plan.md, no shipped.md)
3. Check for the PR:
   ```bash
   gh api "repos/{owner}/{repo}/pulls?state=open&per_page=100" \
     --jq '[.[] | select(.head.ref == "feature/<id>")] | .[0] | {number, url: .html_url, state, draft, base_ref: .base.ref}'
   ```
4. Verify you're on the `feature/<id>` branch — if not, switch to it:
   ```bash
   git checkout feature/<id>
   ```

If there's no PR, warn the user — they may want to run `/feature-review-impl` first, or proceed with a local merge.

---

## Phase 2: Write shipped.md

Write `docs/features/<id>/shipped.md` with the following format:

```markdown
---
shipped: YYYY-MM-DD
---

# Shipped: [Feature Name]

## Summary
Brief summary of what was delivered...

## Key Changes
- Change 1
- Change 2
- Change 3

## Files Changed
- `path/to/file1.ts`
- `path/to/file2.ts`

## Testing
How the feature was tested and verified...

## Notes
Any follow-up items, known limitations, or context for future maintainers...
```

Populate this from the plan.md, commit messages, and git diff.

---

## Phase 3: Prepare PR (labels first, then commit + push)

**Order matters here.** The review workflow (`feature-review.yml`)
triggers on `pull_request: types: [labeled, synchronize]`. If review
labels (`plan-review`, `impl-review`) are still on the PR when the
shipped.md push fires a `synchronize` event, the workflow runs a
pointless extra review on a docs-only commit, spending API quota and
posting irrelevant review comments on a PR that's about to merge.

Remove the labels **before** pushing shipped.md:

1. Remove review labels (must be first — prevents the
   push-triggered re-review):
   ```bash
   gh pr edit <pr-number> --remove-label plan-review --remove-label impl-review 2>/dev/null || true
   ```

2. Commit shipped.md to the feature branch and push:
   ```bash
   git add docs/features/<id>/shipped.md
   git commit -m "docs(<id>): mark feature as shipped"
   git push
   ```

**After writing shipped.md, regenerate the dashboard** by running:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/run_dashboard.py <project_root>
```

DASHBOARD.md is auto-resolved on merge via CI — no need to commit it from feature branches.

---

## Phase 4: Merge PR

PRs are opened as non-draft (since v9.5.2), so no draft → ready conversion is needed. Merge directly via REST.

1. Confirm with user: **"Merge PR #<number> for feature/<id> into dev?"**
2. **If you encounter a draft PR (legacy / opened externally):** convert with `gh pr ready <pr-number>` once. This is a GraphQL mutation, used at most once per stuck PR. Don't retry on rate-limit failure — wait for the GraphQL window to reset (`gh api rate_limit --jq '.resources.graphql.reset'`).
3. Merge the PR via REST and delete the branch:
   ```bash
   gh api "repos/{owner}/{repo}/pulls/<pr-number>/merge" \
     --method PUT \
     --field merge_method=merge

   # Delete the remote branch (REST):
   gh api "repos/{owner}/{repo}/git/refs/heads/feature/<id>" --method DELETE
   ```

   > **Why REST merge:** `gh pr merge` uses GraphQL `mergePullRequest`. The REST endpoint `PUT /pulls/{n}/merge` is functionally equivalent, doesn't count against the GraphQL points budget, and isn't subject to the secondary mutation rate limit. The 405 "still a draft" failure mode no longer applies because we never open as draft.

4. Switch to dev, pull, and delete the local feature branch:
   ```bash
   git checkout dev && git pull && git branch -d feature/<id>
   ```

---

## Phase 5: Update Dashboard and Cleanup

1. Regenerate the dashboard on dev (shipped.md is now merged):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/run_dashboard.py <project_root>
   ```
2. Clear the statusline:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/statusline.py clear
   ```
3. Display completion summary:

```
## Feature Shipped

**Feature**: [name]
**ID**: <id>
**PR**: <pr-url> (merged)
**Shipped**: YYYY-MM-DD

The feature is now in dev. Dashboard updated.
```

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Feature not in-progress | Direct user to correct command or status |
| No PR exists | Suggest `/feature-review-impl` first, or offer local merge |
| Not on feature branch | Switch to `feature/<id>` |
| Already completed | Feature has shipped.md — nothing to do |

---

## Fallback: Manual Ship

If shipped.md wasn't created, you can use the ship script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/feature-ship/scripts/ship_feature.py <project_root> <feature-id> "Summary message"
```

After creating shipped.md, regenerate the dashboard:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/run_dashboard.py <project_root>
```
