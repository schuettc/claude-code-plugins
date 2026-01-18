# Phase 4: Log Injection (Active)

## Prerequisites

- User has approved the injection strategy
- Strategy is stored in session.json
- injections.json is initialized

## Execute Injections

For each approved injection:

### 1. Read Current File State

```
Read the target file to get exact current content
Store original line content in injections.json
```

### 2. Inject Log Statement

Use Edit tool to add the log statement:

| Position | Action |
|----------|--------|
| `before` | Insert new line before target line |
| `after` | Insert new line after target line |
| `replace` | Replace target line (rare - only for adding to existing logs) |

### 3. Track in Manifest

Update `injections.json`:

```json
{
  "auditId": "auth-flow-001",
  "injectedAt": "[timestamp]",
  "injections": [
    {
      "id": 1,
      "file": "src/auth/login.ts",
      "line": 15,
      "position": "after",
      "injectedLine": 16,
      "originalContent": "",
      "injectedContent": "console.log('[AUDIT:auth-flow-001:1] Entry - credentials:', { email: credentials.email, hasPassword: !!credentials.password }); // AUDIT-INJECTED",
      "purpose": "Capture login entry with sanitized credentials",
      "status": "injected"
    }
  ]
}
```

## Injection Order

Process injections in reverse line order within each file:
- This prevents line number shifts from affecting subsequent injections
- Start with highest line number, work backwards

Example for a file with injections at lines 15, 28, 45:
1. Inject at line 45
2. Inject at line 28
3. Inject at line 15

## Verify Code Integrity

After all injections:

### 1. Syntax Check (if applicable)

| Language | Check Command |
|----------|---------------|
| TypeScript | `npx tsc --noEmit` |
| Python | `python -m py_compile [file]` |
| Go | `go build ./...` |
| Rust | `cargo check` |
| Java | Compile with javac |

### 2. If Check Fails

- Identify which injection caused the issue
- Rollback that specific injection
- Update injections.json with `status: "failed"`
- Report to user and ask how to proceed

### 3. If Check Passes

- Update session phase status
- Proceed to runtime capture

## Handle Multi-File Injections

When injecting across multiple files:

1. Group injections by file
2. Process one file at a time
3. Verify each file individually
4. Track all in single injections.json

## Present Injection Summary

Display to user:

```
## Log Injection Complete

**Audit**: [audit-id]
**Injections**: [N] successful, [M] failed

### Files Modified

| File | Injections | Status |
|------|------------|--------|
| src/auth/login.ts | 3 | Verified |
| src/auth/session.ts | 2 | Verified |

### All Injections Tracked

All changes are recorded in `docs/audits/[audit-id]/injections.json`
Complete cleanup available at any time.

### Code Verification

[Type check/compile passed]

---

**Next**: Execute your process to capture the audit logs.

How would you like to capture the logs?

1. **Paste output** - You'll run the process and paste the output here
2. **Direct execution** - I'll run a command and capture the output
```

## Error Handling

| Error | Resolution |
|-------|------------|
| File not found | Report error, skip this injection, continue with others |
| Edit fails | Try alternative edit approach, or mark as failed |
| Syntax error after injection | Rollback that injection, report issue |
| Permission denied | Report to user, may need to run with different permissions |

**Output**: All approved logs injected and tracked in manifest
