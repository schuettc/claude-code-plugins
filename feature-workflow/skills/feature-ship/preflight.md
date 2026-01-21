# Phase 1: Pre-flight Check

## Read In-Progress Items

Read `docs/features/DASHBOARD.md` to see current in-progress items.

Look for the **In Progress** section table.

## If Feature ID Provided ($ARGUMENTS not empty)

1. Look for the ID in the In Progress table
2. If not found in In Progress:
   - Check Backlog table - if there: Ask user to run `/feature-plan` first
   - Check Completed table - if there: Inform user feature is already completed
3. Read the feature's files and verify artifacts exist:
   - `docs/features/[id]/idea.md` (must exist)
   - `docs/features/[id]/plan.md` (must exist for in-progress)
   - No `docs/features/[id]/shipped.md` (should not exist yet)

## If No Feature ID Provided

1. Read `docs/features/DASHBOARD.md`
2. If In Progress section is empty:
   ```
   ## No In-Progress Features

   No features are currently in-progress.
   Run `/feature-plan` to start a feature from the backlog.
   ```
3. Otherwise display available items from the In Progress table:
   ```
   ## In-Progress Features Ready for Completion

   - [id]: [name] - Started [started date]
   ```
4. Ask user to select by ID

## Pre-flight Checklist

Display and verify:
```
## Pre-flight Check: [feature-name]

Feature status: in-progress (plan.md exists, no shipped.md)
Implementation plan exists
Problem statement documented (idea.md)

Ready to proceed with quality gates.
```

**Output**: Feature validated and ready for quality review

---

# Effort-Based Workflow Selection

The ship workflow scales based on effort level from idea.md frontmatter:

## Small Effort (< 8 hours)

Skip agent-based reviews. Run quick verification instead:
- **Skip Phase 2**: Run `npm audit --audit-level=high` instead of security-reviewer agent
- **Skip Phase 3**: Run `npm test` instead of qa-engineer agent
- **Continue to Phase 4**: Standard final verification

## Medium or Large Effort

Run full workflow with all quality gates:
- **Phase 2**: Full security-reviewer agent scan
- **Phase 3**: Full qa-engineer agent validation
- **Phase 4-6**: Standard completion workflow
