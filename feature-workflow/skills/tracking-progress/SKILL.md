---
name: tracking-progress
description: Update feature progress log and check off completed tasks. Use when user completes implementation tasks, makes commits, or indicates work is done. ASKS BEFORE MODIFYING files. Updates plan.md progress log section and implementation step checkboxes.
allowed-tools: Read, Edit
---

# Progress Tracker

Track feature implementation progress by updating plan.md when tasks are completed.

## When to Use

Invoke this skill when the user:
- Completes a task: "Done with X", "Finished the Y"
- Makes a commit related to the feature
- Says they've implemented something
- Explicitly asks to update progress

## Important: Ask Before Writing

This skill modifies files. **Always ask before making changes.**

## Instructions

### Step 1: Identify the Feature

Read `docs/features/DASHBOARD.md` and look at the **In Progress** section to find current features.

If multiple exist, check context or ask which one.

### Step 2: Load the Plan

Read `docs/features/[id]/plan.md`

Locate:
- **Progress Log** section (usually at the end)
- **Implementation Steps** section (checkbox list)

### Step 3: Prepare Update

From the user's statement, identify what was completed and match it to implementation steps.

Prepare:
1. Progress log entry with date and description
2. Checkbox update: `- [ ]` → `- [x]`

### Step 4: Confirm and Apply

Show proposed changes, get confirmation, then use Edit tool to apply.

## Example

**User**: "Done with the JWT token refresh logic"

**Response**:
```
Update progress in plan.md?

1. Add progress log entry:
   ### 2026-01-15
   - Completed JWT token refresh logic in auth/tokens.ts
   - Next: Implement session timeout handling

2. Mark complete:
   - [x] Implement JWT token refresh logic

Proceed? (yes/no)
```

**After confirmation**:
```
Progress updated in plan.md:
- Added log entry for 2026-01-15
- Marked complete: Implement JWT token refresh logic

Remaining steps: 4 of 7
```

## Error Handling

- **No plan.md**: "No implementation plan found. Run /feature-plan first."
- **No matching step**: "Couldn't find a matching step. Add to progress log only?"
- **Multiple matches**: List options and ask which to check off

## Integration Notes

This skill works with:
- `loading-feature-context` skill - Reads the same plan.md
- `/feature-ship` - Relies on accurate progress tracking
