# Phase 7: Cleanup

## Load Injection Manifest

Read `docs/audits/[audit-id]/injections.json` to get all injected logs.

## Remove All Injected Logs

For each injection in the manifest:

### 1. Verify Injection Still Present

Read the file and confirm the injected line exists:
- Check for `AUDIT-INJECTED` marker
- Match the expected injected content

### 2. Remove the Injection

Use Edit tool to remove the injected line:
- Delete the entire line containing `// AUDIT-INJECTED` or `# AUDIT-INJECTED`
- Preserve original formatting and indentation

### 3. Update Manifest Status

```json
{
  "id": 1,
  "file": "src/auth/login.ts",
  "status": "removed",
  "removedAt": "[timestamp]"
}
```

## Cleanup Order

Process removals in forward order (lowest line first):
- This is opposite of injection order
- Prevents line number shifts from causing issues
- Track actual line numbers as they shift

Alternative approach:
- Use marker-based removal (grep for `AUDIT-INJECTED`)
- More reliable for complex injection patterns

## Verify Code Integrity

After all removals:

### 1. Syntax Check

Run same checks as after injection:

| Language | Check Command |
|----------|---------------|
| TypeScript | `npx tsc --noEmit` |
| Python | `python -m py_compile [file]` |
| Go | `go build ./...` |
| Rust | `cargo check` |

### 2. Diff Check

Verify no audit artifacts remain:
```bash
grep -r "AUDIT-INJECTED" src/
grep -r "\[AUDIT:" src/
```

Should return no results.

### 3. Compare to Pre-Audit State

If git is available:
```bash
git diff --stat  # Should show no changes in audited files
```

## Handle Cleanup Issues

### Partial Cleanup

If some injections can't be removed:

```
## Cleanup Issue

Some injections could not be automatically removed:

| File | Line | Issue |
|------|------|-------|
| src/auth/login.ts | 16 | File modified since injection |
| src/auth/session.ts | 28 | Line not found |

### Manual Cleanup Required

Search for and remove lines containing:
- `// AUDIT-INJECTED`
- `# AUDIT-INJECTED`
- `[AUDIT:[audit-id]`

Would you like me to:
1. **Show remaining lines** - Display exact content to remove
2. **Force remove** - Attempt alternative removal approach
3. **Skip cleanup** - Leave injections in place (not recommended)
```

### File Modified Since Injection

If the file was modified during audit:

1. Search for marker comment: `AUDIT-INJECTED`
2. Remove lines containing the marker
3. Verify audit log pattern is removed
4. Report to user

## Update Session

Mark audit as complete:

```json
{
  "status": "completed",
  "completedAt": "[timestamp]",
  "phases": {
    "cleanup": "completed"
  },
  "cleanup": {
    "completedAt": "[timestamp]",
    "injectionsRemoved": 7,
    "failedRemovals": 0,
    "codeVerified": true
  }
}
```

## Update Registry

Update `docs/audits/registry.json`:

```json
{
  "id": "[audit-id]",
  "name": "[name]",
  "createdAt": "[timestamp]",
  "completedAt": "[timestamp]",
  "status": "completed",
  "findingsCount": 5
}
```

## Present Final Summary

```
## Audit Complete

**Audit**: [audit-id]
**Status**: Completed

---

### Cleanup Summary

| Metric | Count |
|--------|-------|
| Injections removed | 7 |
| Files restored | 3 |
| Failed removals | 0 |

### Code Verification

- [x] All AUDIT-INJECTED markers removed
- [x] Syntax check passed
- [x] No audit artifacts remaining

---

### Audit Report

Your audit report is saved at:
`docs/audits/[audit-id]/report.md`

### Key Findings Recap

1. **Verified**: [finding 1]
2. **Issue Found**: [finding 2]
3. **Verified**: [finding 3]

---

### What's Next?

- Review the full report for detailed analysis
- Address any issues found
- Consider running `/feature-audit` again after fixes

---

Thank you for using the Runtime Audit workflow!
```

## Archive Option

Optionally offer to archive the audit:

```
### Archive Audit?

Would you like to:
1. **Keep full audit data** - Report, logs, and session data remain
2. **Archive** - Compress to `docs/audits/[audit-id].tar.gz`
3. **Keep report only** - Delete logs and session, keep report.md
```

**Output**: Code restored to pre-audit state, audit session marked complete
