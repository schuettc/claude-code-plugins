# Phase 4: Final Verification

## Contents

- [Phase 4: Final Verification](#phase-4-final-verification-1)
- [Phase 5: Write shipped.md](#phase-5-write-shippedmd)
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

Check that all items in `docs/features/[id]/plan.md` are marked complete:
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
- Create shipped.md with completion notes
- Update DASHBOARD.md (move to Completed section)
- Clear terminal statusline
- Feature files will remain in docs/features/[id]/ as a record

Proceed? (yes/no)
```

**Output**: Final verification complete, user confirmation received

---

# Phase 5: Write shipped.md

Create the shipped.md file to mark the feature as completed.

## Write shipped.md

Write `docs/features/[id]/shipped.md` with the following format:

```markdown
---
shipped: YYYY-MM-DD
---

# Shipped: [Feature Name]

## Summary
Brief summary of what was delivered...

## Key Changes
- Change 1
- Change 2
- Change 3

## Testing
- Tests: [N] passing
- Coverage: [X]% (if available)
- Manual testing completed

## Quality Gates Passed
- Security Review: Passed
- QA Validation: Passed
- Build: Successful

## Notes
Any follow-up items, known limitations, or context for future maintainers...
```

**IMPORTANT**: Writing shipped.md automatically triggers the PostToolUse hook. You do NOT need to run any script manually or update DASHBOARD.md directly.

The hook automatically:
1. Detects the new shipped.md file
2. Clears the terminal statusline
3. Regenerates DASHBOARD.md (feature moves to Completed section)

## Stage Changes

```bash
git add docs/features/[id]/ docs/features/DASHBOARD.md
```

**Output**: Feature marked as completed, statusline cleared

---

# Phase 6: Completion Summary

Display comprehensive completion report:

```markdown
# Feature Completed: [Name]

**ID**: [id]
**Completed**: [YYYY-MM-DD]

---

## Timeline
- Created: [from idea.md frontmatter]
- Started: [from plan.md frontmatter]
- Completed: [today]
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
- `docs/features/[id]/idea.md` - Original problem statement
- `docs/features/[id]/plan.md` - Implementation plan
- `docs/features/[id]/shipped.md` - Completion notes

---

## Next Steps
1. Consider creating a commit for this completion:
   `git commit -m "Complete feature: [feature-name]"`
2. Review backlog for next feature:
   `/feature-plan`

---

Congratulations on completing this feature!
```

> **Note**: The terminal statusline is automatically cleared when shipped.md is written.

**Output**: Complete summary displayed
