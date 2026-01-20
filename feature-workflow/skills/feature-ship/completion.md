# Phase 4: Final Verification

## Contents

- [Phase 4: Final Verification](#phase-4-final-verification-1)
- [Phase 5: Status Update](#phase-5-status-update-hook-based)
- [Phase 6: Completion Summary](#phase-6-completion-summary)

---

## Run Full Test Suite

```bash
# Run all tests
npm test 2>/dev/null || echo "No test command found"

# Run type check if available
npm run type-check 2>/dev/null || npm run typecheck 2>/dev/null || echo "No type-check"

# Run lint if available
npm run lint 2>/dev/null || echo "No lint command"
```

## Verify Build

```bash
# Verify build succeeds
npm run build 2>/dev/null || echo "No build command"
```

## Review Implementation Checklist

Check that all items in `docs/planning/features/[feature-id]/plan.md` are marked complete:
- Read the plan file
- Count checked `- [x]` vs unchecked `- [ ]` items
- If unchecked items remain, ask user:
  ```
  ## Incomplete Tasks Found

  The following tasks in plan.md are not marked complete:
  - [ ] [Task 1]
  - [ ] [Task 2]

  Options:
  1. Mark these as complete (if actually done)
  2. Remove from scope (if not needed)
  3. Cancel completion (finish tasks first)
  ```

## User Confirmation

```
## Final Verification Summary

Security Review: Passed
QA Validation: Passed
Tests: [N] passing
Build: Successful
Plan Tasks: [N/N] complete

Ready to mark feature as completed?

This will:
- Update status to "completed"
- Set completedAt timestamp
- Feature files will remain in docs/planning/features/[id]/ as a record

Proceed? (yes/no)
```

**Output**: Final verification complete, user confirmation received

---

# Phase 5: Status Update (Hook-Based)

Trigger the atomic transition by writing an intent file. The hook handles all file manipulation reliably.

## Step 1: Create Transition Directory

```bash
mkdir -p docs/planning/.transition
```

## Step 2: Write Transition Intent File

Write the following to `docs/planning/.transition/intent.json`:

```json
{
  "type": "inprogress-to-completed",
  "itemId": "[feature-id]",
  "projectRoot": "[absolute path to project root]"
}
```

**Important**: The `projectRoot` must be an absolute path (e.g., `/Users/username/project`).

## Step 3: Verify Result

After writing the intent file, the hook automatically:
1. Validates the item exists in in-progress.json
2. Updates item status and completedAt timestamp
3. Writes to completed.json FIRST (atomic pattern)
4. Verifies write success
5. Removes from in-progress.json
6. Syncs global summary across all files
7. Calculates unblocked features

Read the result from `docs/planning/.transition/result.json`:

```json
{
  "success": true,
  "transition": "inprogress-to-completed",
  "itemId": "[id]",
  "timestamp": "[ISO timestamp]",
  "filesModified": ["docs/planning/in-progress.json", "docs/planning/completed.json"],
  "unblockedFeatures": ["feature-id-1", "feature-id-2"]
}
```

The `unblockedFeatures` array contains IDs of features that are now fully unblocked.

## Step 4: Stage Changes

```bash
git add docs/planning/*.json
```

**Output**: Item moved from in-progress.json to completed.json

---

# Phase 6: Completion Summary

Display comprehensive completion report:

```markdown
# Feature Completed: [Name]

**ID**: [id]
**Completed**: [YYYY-MM-DD]

---

## Timeline
- Created: [createdAt]
- Started: [startedAt]
- Completed: [completedAt]
- Duration: [days] days

---

## Quality Gates Passed

### Security Review
- No Critical/High vulnerabilities
- [N] Medium/Low recommendations noted

### QA Validation
- Tests: [N] passing
- Coverage: [X]%
- Acceptance Criteria: [N/N] verified

### Final Verification
- Build: Successful
- Type Check: Passed
- Lint: Passed

---

## Artifacts (preserved as record)
- `docs/planning/features/[feature-id]/requirements.md`
- `docs/planning/features/[feature-id]/design.md` (if applicable)
- `docs/planning/features/[feature-id]/plan.md`

---

## Features Now Unblocked

[If unblockedFeatures array is not empty:]

### Fully Unblocked (ready to start)
- **[name]** ([id]): All dependencies now met - ready for `/feature-plan`

[If no dependents existed:]
No features were waiting on this one.

---

## Next Steps
1. Consider creating a commit for this completion:
   `git commit -m "Complete feature: [feature-name]"`
2. Review backlog for next feature:
   `/feature-plan`

---

Congratulations on completing this feature!
```

> **Note**: The terminal statusline is automatically cleared when the completion transition runs.

**Output**: Complete summary displayed
