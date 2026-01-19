# Phase 4: Git Staging (Optional)

Ask user:
```
Would you like to stage this change with git?
```

If yes, run:
```bash
git add docs/planning/*.json
```

This stages all modified backlog files (backlog.json, and in-progress.json/completed.json if they exist and were updated).

---

# Phase 5: Confirmation

Display a summary:

```markdown
# Backlog Item Added

**ID**: [id]
**Name**: [name]
**Type**: [type]
**Priority**: [priority] | **Effort**: [effort] | **Impact**: [impact]

## Problem Statement
[problemStatement]

## Affected Areas
[affectedAreas as bullet list, or "None specified"]

## Dependencies
[dependsOn as bullet list with status, or "None - ready to start anytime"]
Example: "- analytics-api (in-progress)" or "- user-auth (completed)"

---

## Backlog Summary
- Total Items: [total]
- P0: [P0 count] | P1: [P1 count] | P2: [P2 count]
- Backlog: [backlog count] | In Progress: [in-progress count] | Completed: [completed count]

## Next Steps
- Run `/feature-plan [id]` when ready to start
- View backlog: `docs/planning/backlog.json`
```
