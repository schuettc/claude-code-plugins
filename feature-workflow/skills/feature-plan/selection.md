# Phase 1: Feature Selection

## Workflow Steps

1. Read backlog and identify/select feature
2. Check dependencies
3. Proceed to Phase 2

> **Note**: The terminal statusline is automatically updated when you write to the feature directory (e.g., `docs/planning/features/[id]/plan.md`). No manual action needed.

---

## Step 1: Read Backlog and Select Feature

Read `docs/planning/backlog.json` to get the current backlog.

**If Feature ID Provided** ($ARGUMENTS not empty):
- Find item in `items` array where `id` matches
- If not found, list available items and ask user to select

**If No Feature ID Provided**:
- Filter items where `status === "backlog"`
- Display organized by priority
- Ask user to select by ID

---

## Step 2: Dependency Check

Before proceeding with planning, check if this feature has unmet dependencies.

1. Get the `dependsOn` array for the selected feature
2. If empty or missing, skip to Phase 2 (no dependencies)
3. If dependencies exist, check each one:
   - Find the dependency item in the backlog
   - Check its `status` field
   - **Met**: status === "completed"
   - **Unmet**: status === "backlog" or "in-progress"

**If blocked**, display warning and ask user to proceed, show alternatives, or cancel.

---

## Step 3: Proceed to Phase 2

Once feature is selected and dependencies are checked, continue to Phase 2 (Requirements).
