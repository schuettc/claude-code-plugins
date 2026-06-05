---
name: checking-backlog
description: Check project backlog when discussing feature ideas or priorities. Use when user mentions adding features, asks what's planned, discusses priorities, or proposes new functionality. Silently reads DASHBOARD.md to show relevant items and suggest /feature-capture for untracked ideas.
allowed-tools: Read, Glob, Bash
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

Scan the feature directories to generate a live dashboard:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/run_dashboard.py <project_root> --stdout
```

If the script fails or `docs/features/` doesn't exist: "No backlog found. Use `/feature-capture` to start tracking."

### Archive Exclusion

When checking for an existing feature, the dashboard's Archive section (collapsed `<details>`) contains replaced and abandoned features. By default, **do not** suggest these in match results — the user is looking for things they can work on. Exception: if the user's prompt explicitly mentions a tombstoned ID by name, surface it with a note like "This was replaced by X" so they know its history.

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

- **Feature exists**: Show status, priority, and category from DASHBOARD.md. Suggest `/feature-plan [id]` if in backlog.
- **Related items found**: List them with their category, ask if user's idea is an extension or new feature.
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
