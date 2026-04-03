---
name: feature-submit
description: Submit feature implementation for external review via draft PR, or respond to PR review feedback. Creates a feature branch, opens a draft PR, and manages the review cycle with Gemini and Codex reviewers.
user-invocable: true
---

# Submit for Review

You are executing the **SUBMIT FOR REVIEW** workflow — preparing your implementation for external review by Gemini and/or Codex reviewers via a GitHub draft PR, or responding to their PR feedback.

## Target Feature

$ARGUMENTS

Parse the arguments for:
- **Feature ID** (required): The feature directory name
- **`--respond`** flag: If present, enter respond mode to read and address PR review feedback

## Mode Detection

| Arguments | Mode | Skill File |
|-----------|------|------------|
| `<id>` | Submit for review | [submit.md](submit.md) |
| `<id> --respond` | Respond to feedback | [respond.md](respond.md) |

## Step 1: Load Feature Context

1. Read `docs/features/<id>/plan.md` — confirm feature is in-progress
2. Read `docs/features/<id>/idea.md` — original problem statement

If the feature doesn't exist or has no plan.md, stop and suggest `/feature-plan` first.

## Step 2: Route to Mode

Based on arguments, follow the appropriate mode:

- **No `--respond` flag** → [submit.md](submit.md) (create branch, open draft PR, push)
- **`--respond` flag** → [respond.md](respond.md) (read PR reviews, address feedback, push updates)

## Branching Strategy

```
feature/<id>  →  dev  →  main
```

- Feature branches are created from `dev`
- Draft PRs target `dev`
- `/feature-ship` merges the PR into `dev`
- `dev` → `main` promotion is handled separately (releases, etc.)

## Guidelines

- **Stay on the feature branch** — all review work happens on `feature/<id>`
- **Commit frequently** — each round of changes gets its own commit
- **The PR is the review artifact** — all review context, feedback, and discussion lives on the PR
- **Validate before dismissing** — if a reviewer flags something, investigate before disagreeing
- **Do NOT self-review** — after submitting, STOP. Do not launch code review agents, run review skills, or analyze the code. External reviewers (Gemini/Codex) handle reviews in separate sessions.
- **No review files** — do not create `reviews/` directories or write review markdown files. All feedback lives on the GitHub PR.
