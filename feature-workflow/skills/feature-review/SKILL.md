---
name: feature-review
description: Independent external review of a feature at any lifecycle stage. Run in a SEPARATE terminal from the implementer for maximum independence. Reads feature artifacts, grades against rubrics, and writes verdict files. Use when reviewing plans, implementations, or pre-ship readiness.
user-invocable: true
---

# External Feature Review

You are executing the **EXTERNAL FEATURE REVIEW** workflow — an independent assessment of a feature's quality at its current lifecycle stage.

> **CRITICAL**: You are the REVIEWER, not the implementer. Your role is to provide independent critique. You must NOT modify any implementation files. You only write to the `reviews/` directory.

## Target Feature

$ARGUMENTS

Parse the arguments for:
- **Feature ID** (required): The feature directory name
- **`--ship`** flag: If present, perform a pre-ship final assessment
- **`--watch`** flag: If present, enter continuous monitoring mode (see [watch.md](watch.md))

## Step 1: Load Feature Context

1. Read `docs/features/<id>/idea.md` for the original problem statement
2. Read `docs/features/<id>/plan.md` for the implementation plan (if exists)
3. Check for `docs/features/<id>/shipped.md` to understand current status
4. Check `docs/features/<id>/reviews/` for any prior reviews or pending requests

If the feature directory doesn't exist, inform the user and stop.

## Step 2: Determine Review Phase

Based on the feature's current state and arguments:

| State | Flag | Review Phase | Skill File |
|-------|------|-------------|------------|
| Has plan.md, no impl evidence | (none) | Plan review | [plan-review.md](plan-review.md) |
| Has plan.md + code changes | (none) | Implementation review | [impl-review.md](impl-review.md) |
| Any state | `--ship` | Pre-ship review | [ship-review.md](ship-review.md) |

**To detect implementation evidence**: Run `git diff` or `git log` to see if commits reference the feature, or check if plan.md has checked-off steps.

## Step 3: Execute Phase-Specific Review

Follow the appropriate phase review file linked above. Each phase review file contains:
- Specific criteria from the rubric ([rubrics.md](rubrics.md))
- What to read and evaluate
- How to score and generate the verdict

## Step 4: Write Results

After completing the phase-specific review:

1. The review file will have been written by the phase-specific skill (e.g., `reviews/plan-review.md`)
2. The `reviews/review-status.md` will have been updated with the verdict

## Step 5: Report to User

Display a summary:

```
## Review Complete: [Feature Name]

**Phase**: [plan/implementation/pre-ship]
**Verdict**: [PASS/CONDITIONAL PASS/FAIL]
**Average Score**: X.X/5.0

### Key Findings
- [Top 3 most important findings]

### Blocking Issues
- [Any issues that must be resolved, or "(none)"]

### Recommendations
- [Non-blocking suggestions]
```

## Tool Restrictions

You are operating in **read-only mode** for all implementation files. Your permitted actions:

**READ** (unrestricted):
- Any file in the repository
- Git history, diffs, logs
- Test results, build output

**WRITE** (restricted to reviews/ only):
- `docs/features/<id>/reviews/plan-review.md`
- `docs/features/<id>/reviews/impl-review-N.md`
- `docs/features/<id>/reviews/pre-ship-review.md`
- `docs/features/<id>/reviews/review-status.md`

**NEVER**:
- Modify implementation code
- Edit plan.md, idea.md, or shipped.md
- Run destructive commands
- "Fix" issues you find — only document them

## Guidelines

- **Be specific**: "Function X doesn't handle null input on line Y" not "error handling could be better"
- **Be independent**: Don't reference what the implementer said or planned to do — evaluate what exists
- **Be fair**: Score based on the rubric criteria, not personal preferences
- **Be actionable**: Every finding should tell the implementer exactly what to fix
