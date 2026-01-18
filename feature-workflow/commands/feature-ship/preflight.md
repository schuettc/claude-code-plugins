---
name: feature-ship:preflight
description: "Phase 1: Pre-flight Check"
user-invocable: false
---

# Phase 1: Pre-flight Check

## Read In-Progress Items

Read `docs/planning/in-progress.json` to get current in-progress items.

**Note**: In multi-file format (v2.0), in-progress items are in their own file. If file doesn't exist, there are no in-progress items.

## If Feature ID Provided ($ARGUMENTS not empty)

1. Find item in `items` array where `id` matches the argument
2. If not found in `in-progress.json`:
   - Check `docs/planning/backlog.json` - if found there with status "backlog": Ask user to run `/feature-plan` first
   - Check `docs/planning/completed.json` - if found there: Inform user feature is already completed
3. Verify implementation artifacts exist:
   - `docs/planning/features/[feature-id]/plan.md`
   - `docs/planning/features/[feature-id]/requirements.md`

## If No Feature ID Provided

1. Read `docs/planning/in-progress.json`
2. If file doesn't exist or items array is empty:
   ```
   ## No In-Progress Features

   No features are currently in-progress.
   Run `/feature-plan` to start a feature from the backlog.
   ```
3. Otherwise display available items:
   ```
   ## In-Progress Features Ready for Completion

   - [id]: [name] - Started [startedAt]
   ```
4. Ask user to select by ID

## Pre-flight Checklist

Display and verify:
```
## Pre-flight Check: [feature-name]

Feature status: in-progress
Implementation plan exists
Requirements documented

Ready to proceed with quality gates.
```

**Output**: Feature validated and ready for quality review

---

# Effort-Based Workflow Selection

The ship workflow scales based on effort level from backlog.json:

## Low Effort (< 8 hours)

Skip agent-based reviews. Run quick verification instead:
- **Skip Phase 2**: Run `npm audit --audit-level=high` instead of security-reviewer agent
- **Skip Phase 3**: Run `npm test` instead of qa-engineer agent
- **Continue to Phase 4**: Standard final verification

## Medium or Large Effort

Run full workflow with all quality gates:
- **Phase 2**: Full security-reviewer agent scan
- **Phase 3**: Full qa-engineer agent validation
- **Phase 4-6**: Standard completion workflow
