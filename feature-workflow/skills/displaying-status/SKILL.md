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

### Step 1: Load Backlog Files

Read these files (some may not exist):
- `docs/planning/backlog.json` - Items waiting to start
- `docs/planning/in-progress.json` - Items being worked on
- `docs/planning/completed.json` - Finished items

Any file contains the global `summary` with counts across all statuses.

### Step 2: Calculate Status

For each backlog item, check dependency status:
- **Ready**: `dependsOn` empty OR all dependencies completed
- **Blocked**: One or more dependencies not completed

For in-progress items, note what features they block via `blockedBy`.

### Step 3: Format Response

Display a scannable dashboard with:
1. **Summary counts** - In progress, backlog (by priority), completed
2. **In Progress** - Name, duration, what it blocks
3. **Ready to Start** - Backlog items with no blockers, sorted by priority
4. **Blocked** - Items waiting on dependencies
5. **Recently Completed** - Last 3-5 items

Use tables for lists. Highlight P0 items and long-running work.

## Example

**User**: "What's the status?"

**Response**:
```
# Project Status

**Summary**: 1 in progress, 4 in backlog (2 ready, 2 blocked), 3 completed

## In Progress
- **Dark Mode Toggle** (P1) - Started 3 days ago
  Blocks: dashboard-theme, settings-page

## Ready to Start
| Priority | Name | Effort |
|----------|------|--------|
| P0 | User Authentication | Medium |
| P1 | API Rate Limiting | Low |

## Blocked
- **Analytics Dashboard** - Needs: analytics-api (in-progress)

## Recently Completed
- Export Feature (2 days ago)
- Search Improvements (5 days ago)
```

## Integration Notes

This skill works with:
- `checking-backlog` skill - For deeper dives into specific items
- `/feature-plan` - Suggest for starting backlog items
- `/feature-ship` - Suggest for finishing in-progress items
