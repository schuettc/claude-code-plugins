# Phase 4: Git Staging (Optional)

Ask user:
```
Would you like to stage this change with git?
```

If yes, run:
```bash
git add docs/features/[id]/idea.md docs/features/DASHBOARD.md
```

This stages the new idea.md and the regenerated DASHBOARD.md.

---

# Phase 5: Confirmation

Display a summary:

```markdown
# Feature Added to Backlog

**ID**: [id]
**Name**: [name]
**Type**: [type]
**Priority**: [priority] | **Effort**: [effort] | **Impact**: [impact]

## Problem Statement
[problemStatement]

## Affected Areas
[affectedAreas as bullet list, or "None specified"]

---

## Files Created
- `docs/features/[id]/idea.md` - Feature details
- `docs/features/DASHBOARD.md` - Updated automatically

## Next Steps
- Run `/feature-plan [id]` when ready to start implementation
- View all features: `docs/features/DASHBOARD.md`
- View this feature: `docs/features/[id]/idea.md`
```

## Dashboard Summary

If DASHBOARD.md was successfully regenerated, briefly mention the counts:
- "You now have X features in backlog, Y in progress, Z completed"
