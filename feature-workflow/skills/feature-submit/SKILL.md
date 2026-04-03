---
name: feature-submit
description: Submit feature implementation for external review or respond to review feedback. Creates a feature branch, commits, pushes, and writes review context. Use when implementation is ready for review by Gemini or Codex reviewers.
user-invocable: true
---

# Submit for Review

You are executing the **SUBMIT FOR REVIEW** workflow — preparing your implementation for external review by Gemini and/or Codex reviewers, or responding to their feedback.

## Target Feature

$ARGUMENTS

Parse the arguments for:
- **Feature ID** (required): The feature directory name
- **`--respond`** flag: If present, enter respond mode to read and address review feedback

## Mode Detection

| Arguments | Mode | Skill File |
|-----------|------|------------|
| `<id>` | Submit for review | [submit.md](submit.md) |
| `<id> --respond` | Respond to feedback | [respond.md](respond.md) |

## Step 1: Load Feature Context

1. Read `docs/features/<id>/plan.md` — confirm feature is in-progress
2. Read `docs/features/<id>/idea.md` — original problem statement
3. Count existing `docs/features/<id>/reviews/context-round-*.md` files to determine current round

If the feature doesn't exist or has no plan.md, stop and suggest `/feature-plan` first.

## Step 2: Route to Mode

Based on arguments, follow the appropriate mode:

- **No `--respond` flag** → [submit.md](submit.md) (create/update branch, write context, push)
- **`--respond` flag** → [respond.md](respond.md) (read reviews, address feedback, re-commit)

## Guidelines

- **Stay on the feature branch** — all review work happens on `feature/<id>`
- **Commit frequently** — each round of changes gets its own commit
- **Write clear context** — reviewers depend on your explanation to focus their review
- **Validate before dismissing** — if a reviewer flags something, investigate before disagreeing
