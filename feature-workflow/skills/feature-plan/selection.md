# Phase 1: Feature Selection

## Workflow Steps

1. Read DASHBOARD.md and identify/select feature
2. Read feature's idea.md for details
3. Verify feature is in backlog status
4. Proceed to Phase 2

> **Note**: The terminal statusline is automatically updated when you write plan.md. No manual action needed.

---

## Step 1: Read Dashboard and Select Feature

Read `docs/features/DASHBOARD.md` to see the current backlog.

**If Feature ID Provided** ($ARGUMENTS not empty):
- Look for the ID in the Backlog table
- If not in Backlog table, check In Progress table (may already be started)
- If not found anywhere, list available items and ask user to select

**If No Feature ID Provided**:
- Display features from the Backlog section
- Organize by priority (P0 first)
- Ask user to select by ID

---

## Step 2: Read Feature Details

Once a feature is selected, read its idea.md:

```
docs/features/[id]/idea.md
```

This contains:
- Full problem statement
- Priority, effort, impact
- Affected areas
- Any proposed solution hints

---

## Step 3: Verify Feature Status

Check the feature's current status by file presence:

```
docs/features/[id]/
├── idea.md    ← Must exist
├── plan.md    ← Should NOT exist (otherwise already in-progress)
└── shipped.md ← Should NOT exist (otherwise already completed)
```

**If plan.md exists**:
- Feature is already in-progress
- Ask user: "Continue working on this feature?" or "Start a different feature?"

**If shipped.md exists**:
- Feature is already completed
- Ask user to select a different feature

---

## Step 4: Proceed to Phase 2

Once feature is selected and verified to be in backlog status, continue to Phase 2 (Requirements).

Store the feature details for later phases:
- Feature ID
- Feature name (from idea.md frontmatter)
- Priority, effort, impact
- Problem statement
