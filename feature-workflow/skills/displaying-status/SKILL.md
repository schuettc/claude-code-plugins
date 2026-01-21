---
name: displaying-status
description: Display project status and backlog overview. Use when user asks about current status, what's in progress, what to work on next, or wants a summary of the backlog. Read-only skill that formats backlog.json into a clear dashboard view.
allowed-tools: Read
---

# Status Dashboard

Provide a quick overview of project status and backlog.

## When to Use

Invoke this skill when the user asks:
- "What's in progress?"
- "What's the status?"
- "What should I work on next?"
- "Show me the backlog"
- "What have we completed recently?"

## Instructions

### Step 1: Load Dashboard

Read `docs/features/DASHBOARD.md` - this is the auto-generated dashboard that shows all features organized by status.

If it doesn't exist: "No backlog found. Use `/feature-capture` to start tracking."

### Step 2: Parse Dashboard Sections

The DASHBOARD.md contains three tables:
- **In Progress** - Features currently being worked on
- **Backlog** - Features waiting to start
- **Completed** - Finished features

### Step 3: Format Response

Display a scannable summary with:
1. **Summary counts** - In progress, backlog (by priority), completed
2. **In Progress** - Name, priority, when started
3. **Ready to Start** - Backlog items sorted by priority
4. **Recently Completed** - Last 3-5 items

Use tables for lists. Highlight P0 items.

For additional context on any feature, read its files:
```
docs/features/[id]/
├── idea.md      # Full problem statement
├── plan.md      # Implementation details (if in-progress)
└── shipped.md   # Completion notes (if completed)
```

## Example

**User**: "What's the status?"

**Response**:
```
# Project Status

**Summary**: 1 in progress, 4 in backlog, 3 completed

## In Progress
- **Dark Mode Toggle** (P1) - Started 2024-01-18

## Backlog (Ready to Start)
| Priority | Name | Effort |
|----------|------|--------|
| P0 | User Authentication | Medium |
| P1 | API Rate Limiting | Small |

## Recently Completed
- Export Feature (2024-01-15)
- Search Improvements (2024-01-10)
```

## Integration Notes

This skill works with:
- `checking-backlog` skill - For deeper dives into specific items
- `/feature-plan` - Suggest for starting backlog items
- `/feature-ship` - Suggest for finishing in-progress items
