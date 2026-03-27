---
name: feature-implement
description: Execute a feature implementation plan from a clean context. Use when starting implementation after planning, or when resuming work on an in-progress feature. Reads plan.md and executes implementation steps.
user-invocable: true
---

# Implement Feature

You are executing the **IMPLEMENT FEATURE** workflow — picking up a plan and executing it with a clean context.

## Target Feature

$ARGUMENTS

## Step 1: Load the Plan

1. If a feature ID was provided above, read `docs/features/<id>/plan.md`
2. If no ID was provided, read `docs/features/DASHBOARD.md` and show the **In Progress** features. Ask the user which one to implement.
3. Also read `docs/features/<id>/idea.md` for the original problem statement and context.

If the plan doesn't exist, suggest running `/feature-workflow:feature-plan` first.

## Step 2: Set Context

Set the statusline so the user can see which feature is active:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/statusline.py set <feature-id>
```

## Step 2.5: Check External Review Status

Check if an external reviewer has provided feedback on the plan:

1. Read `docs/features/<id>/reviews/review-status.md` (if it exists)
2. Based on the verdict:

| Verdict | Action |
|---------|--------|
| `fail` | Display all blocking issues from the review. Ask the user: **"The external reviewer flagged blocking issues. Address these before implementing, or proceed anyway?"** |
| `conditional-pass` | Display recommendations. Inform the user: **"External review passed with recommendations — see below."** Then proceed. |
| `pass` | Inform the user: **"External plan review passed."** Proceed. |
| File absent | Proceed silently. External review is optional. |

If the review file exists, also read the full `reviews/plan-review.md` for detailed findings to share with the user.

## Step 3: Review and Confirm

Present a brief summary:
- Feature name and ID
- Number of implementation steps
- Which steps are already checked off (if resuming)
- First uncompleted step
- External review status (if available)

Ask the user: **"Ready to start? Any changes to the plan before we begin?"**

## Step 4: Execute Implementation Steps

Work through the implementation steps from plan.md sequentially:

1. For each step:
   - State what you're about to do
   - Implement it
   - Run relevant tests
   - Mark the step complete in plan.md using `/feature-workflow:tracking-progress`

2. After completing each step, briefly summarize what was done and what's next.

3. If you hit a blocker:
   - Explain the issue clearly
   - Suggest alternatives
   - Ask the user how to proceed
   - Consider if this is scope creep — use `/feature-workflow:guarding-scope` if needed

## Step 5: Completion

When all steps are done:

1. Run the full test suite
2. Summarize what was implemented
3. Suggest running `/feature-workflow:feature-ship <id>` to complete the feature

## Guidelines

- **Stay focused on the plan** — don't add unplanned features
- **Test as you go** — don't defer all testing to the end
- **Update progress** — keep plan.md checkboxes current
- **Ask when uncertain** — the plan may not cover every edge case
