---
name: checking-backlog
description: Check project backlog when discussing feature ideas or priorities. Use when user mentions adding features, asks what's planned, discusses priorities, or proposes new functionality. Silently reads backlog.json to show relevant items and suggest /feature-capture for untracked ideas.
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

### Step 1: Load Backlog Files

Read these files (some may not exist):
- `docs/planning/backlog.json` - Items waiting to start
- `docs/planning/in-progress.json` - Items being worked on
- `docs/planning/completed.json` - Finished items

Combine all `items` arrays to search across all statuses.

If no files exist: "No backlog found. Use `/feature-capture` to start tracking."

### Step 2: Search for Matches

Search `items` for:
- `name` (partial match, case-insensitive)
- `problemStatement` (keyword match)
- `affectedAreas` (if user mentions specific areas)
- `dependsOn` / `blockedBy` (if discussing dependencies)

### Step 3: Respond Based on Results

- **Feature exists**: Show status, priority, dependencies. Suggest `/feature-plan [id]` if ready.
- **Related items found**: List them, ask if user's idea is an extension or new feature.
- **Not tracked**: Suggest `/feature-capture` to add it.

Include dependency status (blocked/ready) when relevant.

## Example

**User**: "We should add dark mode support"

**Response**:
```
This feature is already tracked:

**Dark Mode Toggle** (ID: dark-mode-toggle)
- Status: backlog
- Priority: P1
- Dependencies: None

Ready to start! Use `/feature-plan dark-mode-toggle`
```

## Integration Notes

This skill works with:
- `/feature-capture` - Suggest when idea isn't tracked
- `/feature-plan` - Suggest when item is ready to start
- `displaying-status` skill - For broader status queries
