---
name: feature-capture
description: Interactive workflow for adding items to the JSON backlog
version: 1.3.0
argument-hint: ""
---

# Add Item to Backlog Command

You are executing the **ADD TO BACKLOG** workflow - an interactive process to capture new features, enhancements, tech debt, or bug fixes in the JSON-based backlog.

## Target File
`docs/planning/backlog.json`

## Workflow Overview

1. **Interactive Questions** - Capture essential information through 7 focused questions
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

## Phase 2: Validation

1. **Check if backlog.json exists**: If not, create initial structure:
```json
{
  "version": "1.0.0",
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

## Phase 3: JSON Update

1. **Create new item object**:
```json
{
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
  "createdAt": "[ISO 8601 timestamp]",
  "updatedAt": "[ISO 8601 timestamp]",
  "startedAt": null,
  "completedAt": null,
  "implementationPlan": null,
  "metadata": {}
}
```

2. **Add to items array** in backlog.json

3. **Recalculate summary**:
   - Increment `total`
   - Increment `byStatus.backlog`
   - Increment `byPriority.[priority]`
   - Update `lastUpdated` to current timestamp

4. **Write updated JSON** back to `docs/planning/backlog.json`

## Phase 4: Git Staging (Optional)

Ask user:
```
Would you like to stage this change with git?
```

If yes, run:
```bash
git add docs/planning/backlog.json
```

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
├── backlog.json                    # Single source of truth (all items, all statuses)
└── features/
    └── [feature-id]/               # Created when implementing (not when adding)
        ├── plan.md
        ├── requirements.md
        └── design.md
```

**Key Principles**:
- `backlog.json` is the only file created/updated by `/feature-capture`
- Feature directories are created by `/feature-plan` when work starts
- Status is tracked in JSON, not by file location

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
