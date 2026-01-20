---
name: feature-capture
description: Interactive workflow for adding items to the JSON backlog. Use when user wants to add a new feature, track an idea, capture requirements, or mentions something that should be in the backlog.
user-invocable: true
---

# Add Item to Backlog Command

You are executing the **ADD TO BACKLOG** workflow - an interactive process to capture new features, enhancements, tech debt, or bug fixes in the JSON-based backlog.

**First step**: Read existing backlog from `docs/planning/backlog.json` (to check for duplicates and understand context)

> **Note**: To add items to the backlog, write to `docs/planning/.transition/intent.json`. Direct writes to backlog JSON files are blocked by the hook system.

## Target File

`docs/planning/backlog.json`

## Workflow Overview

| Phase | Description | Details |
|-------|-------------|---------|
| 1 | Interactive Questions | Capture essential information through 8 focused questions |
| 2 | Validation | Check for duplicate IDs, validate dependencies |
| 3 | JSON Update | Add entry via hook-based transition |
| 4 | Git Staging | Optionally stage changes |
| 5 | Confirmation | Display summary and next steps |

---

### Phase 1: Interactive Questions
**See**: [interview.md](interview.md)
- Ask 8 questions using AskUserQuestion tool
- Capture type, name, problem, priority, effort, impact, areas, dependencies

### Phase 2: Validation
**See**: [validation.md](validation.md)
- Detect single-file vs multi-file format
- Initialize or load backlog.json
- Generate kebab-case ID
- Check for duplicates and circular dependencies

### Phase 3: Add to Backlog
**See**: [capture.md](capture.md)
- Create transition intent file
- Hook handles atomic JSON update
- Verify result from hook

### Phase 4-5: Git Staging & Confirmation
**See**: [confirmation.md](confirmation.md)
- Optionally stage with git
- Display summary and next steps

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
