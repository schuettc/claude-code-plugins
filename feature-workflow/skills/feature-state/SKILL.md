---
name: feature-state
description: Change a feature's state (active/paused/superseded/abandoned). Use when a feature needs to be paused while waiting on something, marked obsolete because another feature replaces it, or abandoned because it won't be pursued. Requires companion fields for non-active states.
user-invocable: true
allowed-tools: Read, Edit, Bash
---

# Change Feature State

You are executing the **CHANGE STATE** workflow — flipping the `state:` field in a feature's `idea.md` frontmatter and validating the required companion fields.

## Arguments

`$ARGUMENTS`: `<feature-id> <state> [--reason "..."] [--superseded-by <id>]`

Examples:
- `/feature-state user-roles paused --reason "Waiting on auth team"`
- `/feature-state old-feature superseded --superseded-by new-feature`
- `/feature-state nice-to-have abandoned --reason "Out of scope"`
- `/feature-state stuck-feature active` (resume from paused/tombstone)

## Step 1: Parse Arguments

Extract:
- `<feature-id>` — required
- `<state>` — one of `active`, `paused`, `superseded`, `abandoned`
- `--reason "..."` — used for `paused` (writes `pausedReason`) or `abandoned` (writes `abandonedReason`)
- `--superseded-by <id>` — used for `superseded` (writes `supersededBy`)

If arguments are missing or malformed, show usage and stop.

## Step 2: Load Feature

Read `docs/features/<feature-id>/idea.md`. If it doesn't exist, error:
> "No feature `<feature-id>`. Check `docs/features/` or run `/feature-search`."

If `shipped.md` exists AND the requested new state is `superseded` or `abandoned`, refuse:
> "`<feature-id>` is already shipped — tombstoning it makes no sense. If it needs to be reverted, revert the PR and remove `shipped.md` first."

## Step 3: Validate Required Companions

| Target state | Required argument |
|---|---|
| `paused` | `--reason "..."` |
| `superseded` | `--superseded-by <id>` |
| `abandoned` | `--reason "..."` |
| `active` | none |

If the required companion is missing, ask the user for it via AskUserQuestion before proceeding.

For `superseded`: also check that the referenced ID has an `idea.md` on disk. If not, warn but allow (forward reference).

## Step 4: Update Frontmatter

Use the Edit tool to update `docs/features/<feature-id>/idea.md`:

1. **Set `state:`** — replace any existing `state:` line, or insert one after `id:`.
2. **Set companion field** — same insertion pattern.
3. **Clean up obsolete companions** when state changes:
   - Resuming to `active` from `paused`: remove `pausedReason:`
   - Resuming to `active` from `superseded`: remove `supersededBy:`
   - Resuming to `active` from `abandoned`: remove `abandonedReason:`

Do NOT touch any other frontmatter or content.

## Step 5: Confirm + Regen Dashboard

The PostToolUse hook will regenerate `DASHBOARD.md` automatically when you edit `idea.md`.

Print a one-line confirmation:
> "✓ `<feature-id>` is now `<state>`. <Companion field summary>"

## Step 6: Suggest Follow-Up

| New state | Suggest |
|---|---|
| paused | "When the blocker clears, run `/feature-state <id> active` to resume." |
| superseded | "If `<superseded-by-id>` doesn't exist yet, run `/feature-capture` to create it." |
| abandoned | (none — terminal state for now) |
| active (from paused) | "Resume with `/feature-implement <id>` or `/feature-autopilot <id>`." |

## Notes

- This is the only correct way to tombstone a feature. Do NOT delete the directory — the history is the whole point.
- The dashboard hook regenerates on edit; no manual regen needed.
- State changes are reversible. Going `paused → active → paused` is fine.
