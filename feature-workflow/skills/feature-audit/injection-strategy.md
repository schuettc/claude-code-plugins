# Phase 3: Injection Strategy

## Load Exploration Results

Read `docs/audits/[audit-id]/session.json` to get:
- Proposed log points from exploration
- Questions we're verifying
- Target description

## Design Specific Log Statements

For each proposed log point, create the exact code to inject.

### Detect Language

Determine language from file extension:

| Extension | Language | Pattern |
|-----------|----------|---------|
| `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs` | TypeScript/JavaScript | `console.log('[AUDIT:id:N]', data);` |
| `.py` | Python | `print(f'[AUDIT:id:N] {data}')` |
| `.go` | Go | `fmt.Printf("[AUDIT:id:N] %v\n", data)` |
| `.rs` | Rust | `println!("[AUDIT:id:N] {:?}", data);` |
| `.java` | Java | `System.out.println("[AUDIT:id:N] " + data);` |
| `.rb` | Ruby | `puts "[AUDIT:id:N] #{data}"` |
| `.php` | PHP | `error_log("[AUDIT:id:N] " . json_encode($data));` |

### Log Statement Format

Each log statement includes:
- Audit ID for filtering
- Sequence number for ordering
- Descriptive label
- Data to capture

Example (TypeScript):
```typescript
console.log('[AUDIT:auth-flow-001:1] Entry - user:', JSON.stringify(user)); // AUDIT-INJECTED
```

Example (Python):
```python
print(f'[AUDIT:auth-flow-001:1] Entry - user: {user}')  # AUDIT-INJECTED
```

### Data Safety Considerations

For sensitive data:
```typescript
// Instead of logging password:
console.log('[AUDIT:id:N] password received:', password ? '[PRESENT]' : '[MISSING]'); // AUDIT-INJECTED

// Instead of full credit card:
console.log('[AUDIT:id:N] card:', `****${card.slice(-4)}`); // AUDIT-INJECTED
```

## Create Injection Plan

Build detailed plan for each log:

```json
{
  "strategy": {
    "createdAt": "[timestamp]",
    "language": "[detected language]",
    "injections": [
      {
        "id": 1,
        "file": "src/auth/login.ts",
        "line": 15,
        "position": "after",
        "code": "console.log('[AUDIT:auth-flow-001:1] Entry - credentials:', { email: credentials.email, hasPassword: !!credentials.password }); // AUDIT-INJECTED",
        "purpose": "Capture login entry with sanitized credentials",
        "answersQuestion": "Are credentials validated before use?"
      },
      {
        "id": 2,
        "file": "src/auth/login.ts",
        "line": 28,
        "position": "after",
        "code": "console.log('[AUDIT:auth-flow-001:2] Validation result:', isValid); // AUDIT-INJECTED",
        "purpose": "Capture validation outcome",
        "answersQuestion": "Are credentials validated before use?"
      }
    ]
  }
}
```

## Present Strategy for Approval

Display to user:

```
## Injection Strategy

**Audit**: [audit-id]
**Language**: [detected language]
**Total Injections**: [N]

### Proposed Log Injections

Each injection is marked with `// AUDIT-INJECTED` for cleanup.

---

#### Injection #1
**File**: `src/auth/login.ts:15`
**Purpose**: Capture login entry with sanitized credentials
**Answers**: "Are credentials validated before use?"

```typescript
console.log('[AUDIT:auth-flow-001:1] Entry - credentials:', { email: credentials.email, hasPassword: !!credentials.password }); // AUDIT-INJECTED
```

---

#### Injection #2
**File**: `src/auth/login.ts:28`
**Purpose**: Capture validation outcome
**Answers**: "Are credentials validated before use?"

```typescript
console.log('[AUDIT:auth-flow-001:2] Validation result:', isValid); // AUDIT-INJECTED
```

---

[Continue for all injections...]

### Safety Summary

- All injections are observational only (no behavior changes)
- All injections marked with `// AUDIT-INJECTED`
- Complete rollback available via cleanup phase
- No sensitive data logged in plain text

---

**Do you approve these injections?**

Options:
1. **Approve all** - Proceed with injection
2. **Modify** - Adjust specific injections
3. **Add more** - Identify additional log points
4. **Cancel** - Abort audit
```

## Handle User Feedback

### If user requests modifications:
- Adjust specific injections as requested
- Re-present updated strategy
- Get approval before proceeding

### If user wants additional logs:
- Return to exploration phase for those areas
- Add new log points to strategy
- Re-present complete strategy

### If user approves:
- Update session status
- Proceed to injection phase

**Output**: Detailed injection plan approved by user
