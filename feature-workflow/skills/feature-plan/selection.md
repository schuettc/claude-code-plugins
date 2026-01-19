# Phase 1: Feature Selection

## Contents

- [Read Backlog](#read-backlog)
- [If Feature ID Provided](#if-feature-id-provided-arguments-not-empty)
- [If No Feature ID Provided](#if-no-feature-id-provided)
- [Dependency Check](#dependency-check)

---

## Read Backlog

Read `docs/planning/backlog.json` to get the current backlog.

## If Feature ID Provided ($ARGUMENTS not empty)

1. Find item in `items` array where `id` matches the argument
2. If not found:
   - List available items with status "backlog"
   - Ask user to select one
3. If found, confirm:
   ```
   Ready to start: [name]
   Priority: [priority] | Effort: [effort] | Impact: [impact]

   Problem: [problemStatement]

   Proceed? (yes/no)
   ```

## If No Feature ID Provided

1. Filter items where `status === "backlog"`
2. Display organized by priority:
   ```
   ## Available Backlog Items

   ### P0 (High Priority)
   - [id]: [name] - [effort] effort, [impact] impact

   ### P1 (Medium Priority)
   - [id]: [name] - [effort] effort, [impact] impact

   ### P2 (Low Priority)
   - [id]: [name] - [effort] effort, [impact] impact
   ```
3. Ask user to select by ID

**Output**: Selected feature with full details

4. **REQUIRED - Set Terminal Context**: Immediately after the user selects a feature, you MUST run this command:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/hooks/set-feature-context.sh "[feature-id]"
   ```
   This updates the statusline to show which feature is being worked on.

5. Display tip: `Tip: Run /rename [feature-id] to name this session for easy resume later.`

---

# Dependency Check

Before proceeding with planning, check if this feature has unmet dependencies.

## Step 1: Check Dependencies

1. Get the `dependsOn` array for the selected feature
2. If empty or missing, skip to Phase 2 (no dependencies)
3. If dependencies exist, check each one:
   - Find the dependency item in the backlog
   - Check its `status` field
   - Categorize as:
     - **Met**: status === "completed"
     - **Unmet**: status === "backlog" or "in-progress"

## Step 2: Calculate Dependency Status

```
dependencyStatus:
  - "ready": No dependencies OR all dependencies completed
  - "blocked": One or more dependencies not completed
  - "partial": Some dependencies completed, others pending
```

## Step 3: Display Warning (If Blocked)

If any dependencies are unmet, display:

```markdown
## Dependency Warning

This feature has unmet dependencies:

| Dependency | Status | Notes |
|------------|--------|-------|
| [dep-id] | [status] | [Started X days ago / Not started] |
| [dep-id] | completed | Ready |

[N] of [M] dependencies unmet.

### Options:
1. **Proceed anyway** - Work may be blocked until dependencies complete
2. **Show alternatives** - See features with no blockers
3. **Cancel** - Work on prerequisites first
```

Use AskUserQuestion to get the user's choice.

## Step 4: Handle User Choice

**Option 1 - Proceed Anyway**:
- Log acknowledgment: "User chose to proceed with unmet dependencies"
- Continue to Phase 2

**Option 2 - Show Alternatives**:
- Filter backlog for items where:
  - `status === "backlog"` AND
  - (`dependsOn` is empty OR all items in `dependsOn` have status "completed")
- Display as "Ready to Start" list
- Ask user to select one or cancel

**Option 3 - Cancel**:
- Display: "Cancelled. Consider working on: [list unmet dependency IDs]"
- Exit workflow
