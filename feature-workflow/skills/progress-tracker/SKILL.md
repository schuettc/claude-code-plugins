---
name: progress-tracker
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

This skill modifies files. **Always ask before making changes:**

```
Update progress in plan.md?
- Add progress log entry: "[description of what was done]"
- Check off: "[ ] [matching task]" → "[x] [matching task]"

Proceed? (yes/no)
```

## Instructions

### Step 1: Identify the Feature

```
Read: docs/planning/backlog.json
```

Find the in-progress feature. If multiple exist:
- Check if user mentioned a specific feature
- Look at what files were just modified
- Ask if unclear

### Step 2: Load the Plan

```
Read: docs/planning/features/[feature-id]/plan.md
```

Identify:
- The **Progress Log** section (usually at the end)
- The **Implementation Steps** section (checkbox list)

### Step 3: Determine What Was Completed

From the user's statement, identify:
- What task was finished
- Which implementation step(s) it corresponds to

### Step 4: Prepare the Update

**Progress Log Entry:**
```markdown
### [Today's Date - YYYY-MM-DD]
- [Description of what was accomplished]
- Next: [What comes next, if known]
```

**Implementation Step Checkbox:**
Find matching unchecked item and mark complete:
```
- [ ] Step description  →  - [x] Step description
```

### Step 5: Confirm with User

Show the proposed changes:
```
Proposed updates to docs/planning/features/[id]/plan.md:

1. Progress Log entry:
   ### 2026-01-01
   - Completed [task description]

2. Mark complete:
   - [x] [matching implementation step]

Apply these updates? (yes/no)
```

### Step 6: Apply Updates (if confirmed)

Use the Edit tool to:
1. Add the progress log entry
2. Check off the implementation step

## Output Format

After successful update:
```
Progress updated in plan.md:
- Added log entry for [date]
- Marked complete: [step description]

Remaining steps: [N] of [total]
```

## Error Handling

- **No plan.md**: "No implementation plan found. Run /feature-workflow:implement first."
- **No matching step**: "Couldn't find a matching implementation step. Add to progress log only?"
- **Multiple matches**: List options and ask which to check off

## Integration Notes

This skill works with:
- `feature-context` skill - Reads the same plan.md
- `/feature-workflow:complete` - Relies on accurate progress tracking
