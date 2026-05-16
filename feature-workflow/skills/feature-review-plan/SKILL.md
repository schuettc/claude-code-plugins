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
| `<id>` (effective: external) | Submit plan for external CI review | [submit.md](submit.md) |
| `<id>` (effective: internal) | Submit plan for internal review | [submit.md](submit.md) (branches internally) |
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
| `external_gemini` / `external_codex` / `external_default` | Original flow — open PR, apply `plan-review` label, let CI run |
| `internal` | Open PR, then dispatch the internal-review subagent (see `../shared/internal-review.md`) |
| `skip` | Don't run any review; just open the PR if not present, and surface to the user that they've opted out of review |

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
