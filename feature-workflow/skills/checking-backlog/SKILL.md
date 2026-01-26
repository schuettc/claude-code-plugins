---
name: checking-backlog
description: Check project backlog when discussing feature ideas or priorities. Use when user mentions adding features, asks what's planned, discusses priorities, or proposes new functionality. Silently reads DASHBOARD.md to show relevant items and suggest /feature-capture for untracked ideas.
allowed-tools: Read, Glob
---

# Backlog Awareness

Automatically check the project backlog when the user discusses feature ideas, priorities, or planned work.

## When to Use

Invoke this skill when the user:
- Proposes new functionality: "We should add...", "It would be nice if...", "What if we..."
- Asks about planned work: "What features are planned?", "Is X in the backlog?"
- Discusses priorities: "What should we work on next?", "What's most important?"
- Mentions a specific feature by name that might be tracked

## Instructions

### Step 1: Load Dashboard

Read `docs/features/DASHBOARD.md` to see all features by status.

If it doesn't exist: "No backlog found. Use `/feature-capture` to start tracking."

### Step 2: Search for Matches

Parse the DASHBOARD.md tables to find:
- Feature IDs and names in each section (In Progress, Backlog, Completed)
- Priority and effort information

For deeper context on a specific feature, read its files:
```
docs/features/[id]/
├── idea.md      # Problem statement, priority, effort, impact
├── plan.md      # Implementation details (if in-progress)
└── shipped.md   # Completion notes (if completed)
```

Search `idea.md` for:
- `name` in frontmatter (partial match, case-insensitive)
- Problem statement content (keyword match)
- `affectedAreas` (if user mentions specific areas)

### Step 3: Respond Based on Results

- **Feature exists**: Show status, priority from DASHBOARD.md. Suggest `/feature-plan [id]` if in backlog.
- **Related items found**: List them, ask if user's idea is an extension or new feature.
- **Not tracked**: Suggest `/feature-capture` to add it.

## Example

**User**: "We should add dark mode support"

**Response**:
```
This feature is already tracked:

**Dark Mode Toggle** (ID: dark-mode-toggle)
- Status: backlog
- Priority: P1

Ready to start! Use `/feature-plan dark-mode-toggle`
```

## Integration Notes

This skill works with:
- `/feature-capture` - Suggest when idea isn't tracked
- `/feature-plan` - Suggest when item is in backlog
- `/feature-status` - For broader status queries
