---
name: feature-review-impl
description: Submit a feature implementation for external review via the existing draft PR, or respond to reviewer feedback on the code. Pushes implementation to the feature branch and updates the PR.
user-invocable: true
---

# Review Implementation

You are executing the **REVIEW IMPLEMENTATION** workflow — submitting your code for external review by Gemini and/or Codex reviewers via the existing GitHub draft PR, or responding to their feedback.

## Target Feature

$ARGUMENTS

Parse the arguments for:
- **Feature ID** (required): The feature directory name
- **`--respond`** flag: If present, enter respond mode to read and address PR review feedback

## Mode Detection

| Arguments | Mode | Skill File |
|-----------|------|------------|
| `<id>` (effective: external) | Submit implementation for external CI review | [submit.md](submit.md) |
| `<id>` (effective: internal) | Submit implementation for internal review | [submit.md](submit.md) (branches internally) |
| `<id>` (effective: skip) | Refuse — review opted out | (stop, surface to user) |
| `<id> --respond` | Respond to feedback (works for any mode) | [../shared/respond.md](../shared/respond.md) |

## Step 0: Determine Effective Review Mode

Before routing, compute the effective review mode for this feature:

1. Read `.feature-workflow.yml` for `reviewer:` (defaults to none if absent).
2. Read `docs/features/<id>/idea.md` frontmatter for `review:`.
3. Compute the mode using `feature-workflow/skills/shared/lib/effective_review.py`:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/skills/shared/lib')
from effective_review import resolve_review
# parse project_reviewer from .feature-workflow.yml
# parse feature_review from idea.md frontmatter
mode = resolve_review(feature_review='<value>', project_reviewer='<value>')
print(mode.value)
"
```

Or simpler: read both values yourself and apply the precedence rule (feature override wins, else project default, else skip).

| Mode | Behavior |
|---|---|
| `external_gemini` / `external_codex` / `external_default` | Original flow — push changes, swap `plan-review` for `impl-review` label, let CI run |
| `internal` | Push changes, remove `plan-review` if present, dispatch internal-review subagent for impl phase |
| `skip` | Push changes, remove any review label, no review will be performed |

## Step 1: Load Feature Context

1. Read `docs/features/<id>/plan.md` — confirm feature is in-progress
2. Read `docs/features/<id>/idea.md` — original problem statement

If the feature doesn't exist or has no plan.md, stop and suggest `/feature-plan` first.

## Step 2: Route to Mode

Based on arguments, follow the appropriate mode:

- **No `--respond` flag** → [submit.md](submit.md) (push code to branch/PR, trigger reviewers)
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

- The feature branch should already exist from `/feature-review-plan`
- If not, this skill creates it from `<target>`
- Draft PRs target `<target>`
- `/feature-ship` merges the PR into `<target>`

## Guidelines

- **Stay on the feature branch** — all review work happens on `feature/<id>`
- **Commit frequently** — each round of changes gets its own commit
- **The PR is the review artifact** — all review context, feedback, and discussion lives on the PR
- **Validate before dismissing** — if a reviewer flags something, investigate before disagreeing
- **Do NOT self-review** — after submitting, STOP. Do not launch code review agents, run review skills, or analyze the code. External reviewers handle reviews in separate sessions.
- **No review files** — do not create `reviews/` directories or write review markdown files. All feedback lives on the GitHub PR.
