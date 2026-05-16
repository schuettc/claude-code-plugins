---
name: feature-search
description: Search and filter features by state, assignee, priority, epic, dependency, type, or category. Use when the user wants to find features matching criteria — "what's paused", "what's court working on", "what's in the auth-overhaul epic", "what depends on X".
user-invocable: true
allowed-tools: Bash, Read
---

# Search Features

You are executing the **SEARCH FEATURES** workflow — querying the backlog by filters and presenting a table.

## Arguments

`$ARGUMENTS` is a series of flags. Pass them through to the search script.

Supported filters:
- `--state <active|paused|replaced|abandoned>`
- `--assignee <name>`
- `--priority <P0|P1|P2>`
- `--type <Feature|Enhancement|Bug Fix|Tech Debt|Epic>`
- `--category <name>`
- `--epic <id>` (children of an epic)
- `--depends-on <id>` (features that depend on the given ID)
- `--archive` (include replaced + abandoned)
- `--format text|json` (default text)

If no filters: show all active features (excludes archive by default).

## Step 1: Run the Search

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/feature-search/scripts/search.py <project-root> $ARGUMENTS
```

Capture stdout.

## Step 2: Format Response

For text output, render the markdown table as-is, plus a one-line summary above:
> "**N matching features:**"

For JSON output (passed `--format json`), echo the JSON.

## Step 3: Suggest Follow-Ups

If results contain features in specific states, suggest:
- Paused → `/feature-state <id> active` to resume
- Active backlog → `/feature-plan <id>` or `/feature-autopilot <id>`
- In progress → `/feature-implement <id>`

If zero results:
- If user gave a specific filter, suggest broader filters or `--archive` to include tombstones.
- If user is looking for an unknown feature, suggest `/feature-capture` to add it.

## Examples

| User request | Command |
|---|---|
| "what's paused?" | `/feature-search --state paused` |
| "what is court working on?" | `/feature-search --assignee court` |
| "show all P0s" | `/feature-search --priority P0` |
| "what's in the auth-overhaul epic?" | `/feature-search --epic auth-overhaul` |
| "what depends on user-roles?" | `/feature-search --depends-on user-roles` |
| "show abandoned features" | `/feature-search --state abandoned --archive` |
