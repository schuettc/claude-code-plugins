---
name: feature-capture
description: Interactive workflow for adding items to the JSON backlog
version: 2.0.0
argument-hint: ""
---

# Add Item to Backlog Command

You are executing the **ADD TO BACKLOG** workflow - an interactive process to capture new features, enhancements, tech debt, or bug fixes in the JSON-based backlog.

## Contents

- [Target File](#target-file)
- [Workflow Overview](#workflow-overview)
- [Phase 1: Interactive Questions](#phase-1-interactive-questions)
- [Phase 2: Validation](#phase-2-validation)
- [Phase 3: Add to Backlog](#phase-3-add-to-backlog-hook-based)
- [Phase 4: Git Staging](#phase-4-git-staging-optional)
- [Phase 5: Confirmation](#phase-5-confirmation)
- [What Makes a Good Backlog Item](#what-makes-a-good-backlog-item)
- [Error Handling](#error-handling)

---

## Target File
`docs/planning/backlog.json`

## Workflow Overview

1. **Interactive Questions** - Capture essential information through 8 focused questions
2. **Validation** - Check for duplicate IDs and validate input
3. **JSON Update** - Add entry to backlog.json with proper structure
4. **Summary Recalculation** - Update counts and timestamps
5. **Confirmation** - Display what was added and next steps

## Phase 1: Interactive Questions

Use the AskUserQuestion tool to ask these 7 questions. You may ask multiple questions at once where appropriate.

### Question 1: Item Type
```
What type of item is this?
- Feature - New capability
- Enhancement - Improvement to existing feature
- Tech Debt - Code/infrastructure improvement
- Bug Fix - Defect correction
```

### Question 2: Feature Name
```
Enter a short descriptive name (will be converted to kebab-case for ID):
Example: "Dark Mode Toggle" -> id: "dark-mode-toggle"
```

### Question 3: Problem Statement
```
What problem does this solve? (1-3 sentences)
```

### Question 4: Priority
```
What is the priority?
- P0 (High) - Critical, blocks other work
- P1 (Medium) - Important, should be done soon
- P2 (Low) - Nice to have, can wait
```

### Question 5: Effort Estimate
```
Estimated effort?
- Low (< 8 hours)
- Medium (1-2 weeks)
- Large (2+ weeks)
```

### Question 6: Impact Level
```
Expected impact?
- Low - Minor improvement
- Medium - Noticeable improvement
- High - Significant value or risk reduction
```

### Question 7: Affected Areas (Optional)
```
Which parts of the system will this affect?
(comma-separated list, or leave blank)
Example: frontend/settings, backend/api, database
```

### Question 8: Dependencies (Optional)
```
Does this feature depend on any other backlog items being completed first?
(comma-separated feature IDs, or leave blank)
Example: analytics-api, user-auth
```

**Note**: Dependencies create bidirectional relationships:
- The new item's `dependsOn` array will include the specified IDs
- Each dependency target's `blockedBy` array will include this new item's ID

## Phase 2: Validation

### Step 1: Format Detection

Determine if using single-file (v1.x) or multi-file (v2.0) format:

1. **Check for multi-file indicators**:
   - If `docs/planning/in-progress.json` exists → multi-file format
   - If `docs/planning/completed.json` exists → multi-file format
   - If `docs/planning/backlog.json` exists with `version === "2.0.0"` → multi-file format
   - Otherwise → single-file format (or new backlog)

2. **Store format for later phases**:
   - `isMultiFile = true` if any multi-file indicator found
   - This determines whether to sync summaries to other files

### Step 2: Initialize or Load Backlog

1. **Check if backlog.json exists**: If not, create initial structure:
```json
{
  "version": "2.0.0",
  "lastUpdated": "[current ISO timestamp]",
  "summary": {
    "total": 0,
    "byStatus": { "backlog": 0, "in-progress": 0, "completed": 0 },
    "byPriority": { "P0": 0, "P1": 0, "P2": 0 }
  },
  "items": []
}
```

2. **Read existing backlog**: Load `docs/planning/backlog.json`

3. **Generate ID**: Convert feature name to kebab-case
   - "Dark Mode Toggle" -> "dark-mode-toggle"
   - Remove special characters, lowercase, replace spaces with hyphens

4. **Check for duplicate ID**: Search items array for matching id
   - If duplicate exists, ask user to choose a different name or cancel

5. **Validate required fields**: Ensure all required data is captured

6. **Validate dependencies (if provided)**:
   a. Parse comma-separated list, trim whitespace
   b. For each dependency ID:
      - Check it exists in the items array → If not found: "Feature '[id]' not found. Available IDs: [list]"
      - Check it's not the same as new item's ID → If same: "A feature cannot depend on itself"
   c. Check for circular dependencies using BFS algorithm (see below)
   d. If any validation fails, report error and ask for correction

### Circular Dependency Detection Algorithm

Before adding dependencies, verify no cycles would be created:

```
FUNCTION hasCircularDependency(newItemId, targetDepId, allItems):
    """
    Check if making newItemId depend on targetDepId would create a cycle.
    A cycle exists if targetDepId already depends (directly or transitively) on newItemId.
    """

    visited = Set()
    queue = [targetDepId]

    WHILE queue is not empty:
        current = queue.shift()

        IF current === newItemId:
            RETURN true  // Cycle detected!

        IF current in visited:
            CONTINUE

        visited.add(current)

        item = findItemById(current, allItems)
        IF item AND item.dependsOn:
            FOR EACH depId IN item.dependsOn:
                IF depId not in visited:
                    queue.push(depId)

    RETURN false  // No cycle
```

If a cycle is detected, reject with: "Circular dependency detected: [chain path]"

## Phase 3: Add to Backlog (Hook-Based)

Trigger the atomic addition by writing a transition intent file. The hook will handle all JSON manipulation reliably.

### Step 1: Create Transition Directory

```bash
mkdir -p docs/planning/.transition
```

### Step 2: Write Transition Intent File

Write the following to `docs/planning/.transition/intent.json`:

```json
{
  "type": "add-to-backlog",
  "projectRoot": "[absolute path to project root]",
  "item": {
    "id": "[kebab-case-name]",
    "name": "[Original Name]",
    "type": "[Feature|Enhancement|Tech Debt|Bug Fix]",
    "priority": "[P0|P1|P2]",
    "effort": "[Low|Medium|Large]",
    "impact": "[Low|Medium|High]",
    "problemStatement": "[User's problem description]",
    "proposedSolution": "",
    "affectedAreas": ["[parsed from user input]"],
    "status": "backlog",
    "dependsOn": ["[parsed dependency IDs, or empty array]"],
    "blockedBy": [],
    "metadata": {}
  }
}
```

**Important**: The `projectRoot` must be an absolute path (e.g., `/Users/username/project`).

### Step 3: Verify Result

After writing the intent file, the hook automatically:
1. Validates the item structure
2. Checks for duplicate IDs across all status files
3. Validates dependencies exist and no circular dependencies
4. Adds item to backlog.json
5. Updates blockedBy arrays on dependency targets
6. Syncs global summary across all files

Read the result from `docs/planning/.transition/result.json`:

```json
{
  "success": true,
  "transition": "add-to-backlog",
  "itemId": "[id]",
  "timestamp": "[ISO timestamp]",
  "filesModified": ["docs/planning/backlog.json"]
}
```

If there's an error, the result will contain:
```json
{
  "success": false,
  "error": "[error message]"
}
```

Display the error to the user and stop the workflow.

## Phase 4: Git Staging (Optional)

Ask user:
```
Would you like to stage this change with git?
```

If yes, run:
```bash
git add docs/planning/*.json
```

This stages all modified backlog files (backlog.json, and in-progress.json/completed.json if they exist and were updated).

## Phase 5: Confirmation

Display a summary:

```markdown
# Backlog Item Added

**ID**: [id]
**Name**: [name]
**Type**: [type]
**Priority**: [priority] | **Effort**: [effort] | **Impact**: [impact]

## Problem Statement
[problemStatement]

## Affected Areas
[affectedAreas as bullet list, or "None specified"]

## Dependencies
[dependsOn as bullet list with status, or "None - ready to start anytime"]
Example: "- analytics-api (in-progress)" or "- user-auth (completed ✓)"

---

## Backlog Summary
- Total Items: [total]
- P0: [P0 count] | P1: [P1 count] | P2: [P2 count]
- Backlog: [backlog count] | In Progress: [in-progress count] | Completed: [completed count]

## Next Steps
- Run `/feature-plan [id]` when ready to start
- View backlog: `docs/planning/backlog.json`
```

---

## File Organization

All planning files are organized cleanly:

```
docs/planning/
├── backlog.json                    # Items with status: "backlog"
├── in-progress.json                # Items with status: "in-progress" (created by /feature-plan)
├── completed.json                  # Items with status: "completed" (created by /feature-ship)
└── features/
    └── [feature-id]/               # Created when implementing (not when adding)
        ├── plan.md
        ├── requirements.md
        └── design.md
```

**Key Principles**:
- Items are split by status across three JSON files (multi-file format v2.0)
- Each file contains a global `summary` for quick dashboard access
- `/feature-capture` adds new items to `backlog.json` only
- `/feature-plan` moves items from `backlog.json` to `in-progress.json`
- `/feature-ship` moves items from `in-progress.json` to `completed.json`
- Feature directories are created by `/feature-plan` when work starts

---

## Integration Notes

This command works with `/feature-plan` to provide a complete feature lifecycle:

1. **`/feature-capture`** - Captures idea in backlog (YOU ARE HERE)
2. **`/feature-plan [id]`** - Creates feature directory and detailed planning

---

## What Makes a Good Backlog Item?

**IMPORTANT: Capture the WHAT and WHY, not the HOW.**

This phase is about documenting what you want and why it matters. The implementation details come later during `/feature-plan`.

### DO Capture:
- **What you need** - The feature, fix, or improvement
- **Why it matters** - The value, pain point, or opportunity
- **Who benefits** - Which users or systems are affected
- **Context** - Any relevant background information

### DO NOT Capture:
- **Implementation details** - Don't describe how to build it yet
- **Technical designs** - That's for `/feature-plan`
- **Architecture decisions** - That's for `/feature-plan`
- **Specific technologies** - That's for `/feature-plan`

### Examples

**Good (focuses on what/why):**
> "Users can't find their validation reports after running a scan. They have to search through multiple pages and often give up."

**Good (new feature):**
> "We need dark mode support. Many users work late and have requested reduced eye strain options."

**Bad (jumps to solution):**
> "We need to add a reports dashboard with filters and a search bar that queries the DynamoDB table."

Save the "how" for the planning phase where you'll have proper context and can make informed architectural decisions.

---

## Error Handling

- If `docs/planning/` directory doesn't exist, create it
- If JSON is malformed, report error and ask user to fix manually
- If duplicate ID found, offer to choose different name

---

**Let's capture your idea!**
