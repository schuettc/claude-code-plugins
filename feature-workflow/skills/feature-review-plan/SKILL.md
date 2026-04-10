---
name: feature-review-plan
description: Submit a feature plan for external review via draft PR, or respond to reviewer feedback on the plan. Creates a feature branch, opens a draft PR containing the plan, and manages the review cycle.
user-invocable: true
---

# Review Plan

You are executing the **REVIEW PLAN** workflow — submitting your feature plan for external review by Gemini and/or Codex reviewers via a GitHub draft PR, or responding to their feedback.

## Target Feature

$ARGUMENTS

Parse the arguments for:
- **Feature ID** (required): The feature directory name
- **`--respond`** flag: If present, enter respond mode to read and address PR review feedback

## Mode Detection

| Arguments | Mode | Skill File |
|-----------|------|------------|
| `<id>` | Submit plan for review | [submit.md](submit.md) |
| `<id> --respond` | Respond to feedback | [../shared/respond.md](../shared/respond.md) |

## Step 1: Load Feature Context

1. Read `docs/features/<id>/plan.md` — confirm the plan exists
2. Read `docs/features/<id>/idea.md` — original problem statement

If the feature doesn't exist or has no plan.md, stop and suggest `/feature-plan` first.

## Step 2: Route to Mode

Based on arguments, follow the appropriate mode:

- **No `--respond` flag** → [submit.md](submit.md) (create branch, open draft PR, push plan)
- **`--respond` flag** → [../shared/respond.md](../shared/respond.md) (read PR reviews, address feedback, push updates)

## Branch Configuration

**Before doing anything else**, read `.feature-workflow.yml` in the project root for branch settings. See [../shared/config.md](../shared/config.md) for details.

| Setting | Default | Used for |
|---------|---------|----------|
| `branch.prefix` | `feature/` | Branch naming: `<prefix><id>` |
| `branch.target` | `dev` | Base branch for checkout, PR `--base`, merge target |

```
<prefix><id>  →  <target>  →  main
```

- Feature branches are created from `<target>` during plan review
- Draft PRs target `<target>`
- The same branch and PR are reused for `/feature-review-impl` later
- `/feature-ship` merges the PR into `<target>`

## Guidelines

- **Stay on the feature branch** — all review work happens on `feature/<id>`
- **Commit frequently** — each round of changes gets its own commit
- **The PR is the review artifact** — all review context, feedback, and discussion lives on the PR
- **Validate before dismissing** — if a reviewer flags something, investigate before disagreeing
- **Do NOT self-review** — after submitting, STOP. Do not launch code review agents, run review skills, or analyze the plan. External reviewers handle reviews in separate sessions.
- **No review files** — do not create `reviews/` directories or write review markdown files. All feedback lives on the GitHub PR.
