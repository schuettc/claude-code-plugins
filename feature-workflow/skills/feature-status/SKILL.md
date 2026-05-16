---
name: feature-status
description: Display project status and backlog overview. Use when user asks about current status, what's in progress, what to work on next, or wants a summary of the backlog. Read-only skill that formats DASHBOARD.md into a clear dashboard view.
allowed-tools: Read, Bash
user-invocable: true
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

## Arguments

`$ARGUMENTS` can be:
- Empty — show full dashboard (active sections only)
- `cat:<category>` — filter all tables to that category (case-insensitive)
- `state:<state>` — filter to features with that state (e.g., `state:paused`)
- `assignee:<name>` — filter to features owned by that name
- `--archive` — include superseded and abandoned features
- A feature ID — show details for that specific feature

Filters can stack: `state:active assignee:court` shows court's active features.

For filter combinations beyond what the dashboard table supports, fall back to invoking `/feature-search` with equivalent flags.

## Instructions

### Step 1: Load Dashboard

Scan the feature directories to generate a live dashboard:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/run_dashboard.py <project_root> --stdout
```

If the script fails or `docs/features/` doesn't exist: "No backlog found. Use `/feature-capture` to start tracking."

### Step 1.5: Apply Filters

Parse `$ARGUMENTS` for filter tokens before rendering:

- `cat:<value>` — keep only rows whose Category column matches (case-insensitive). Display header: **"Filtered by category: [value]"**
- `state:<value>` — keep only rows whose State/Status column matches (case-insensitive). Display header: **"Filtered by state: [value]"**
- `assignee:<value>` — keep only rows whose Assignee column matches (case-insensitive). Display header: **"Filtered by assignee: [value]"**
- `--archive` — include the Archive section (superseded/abandoned features) in the output; omit it by default
- Multiple filter tokens stack (AND logic); apply all before rendering.

### Step 2: Parse Dashboard Sections

The DASHBOARD.md may contain the following sections (render each that is present):
- **In Progress** - Features currently being worked on
- **Paused** - Features that were started but are temporarily on hold
- **Backlog** - Features waiting to start
- **Epics** - Multi-feature initiatives grouping related work
- **Completed** - Finished features
- **Archive** - Superseded or abandoned features (omit unless `--archive` flag is present)

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

**Summary**: 1 in progress, 1 paused, 4 in backlog, 3 completed

## In Progress
- **Dark Mode Toggle** (P1) - Started 2024-01-18

## Paused
- **Offline Mode** (P2) - Paused 2024-01-12 (blocked: waiting on design)

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
- `/feature-implement` - Suggest for writing code for in-progress items
- `/feature-review-plan` - Suggest for submitting plan for external review
- `/feature-review-impl` - Suggest for submitting implementation for external review
- `/feature-ship` - Suggest for merging the PR after external reviews pass
