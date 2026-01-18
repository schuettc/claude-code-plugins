---
name: feature-troubleshoot:resolution
description: "Phase 4: Resolution"
user-invocable: false
---

# Phase 4: Resolution

## Propose Fix

Based on the confirmed root cause, propose a solution.

### Fix Proposal Format

```
## Proposed Fix

### Root Cause
[Summary of confirmed issue]

### Solution
[Clear description of what we'll change]

### Files to Modify

| File | Change |
|------|--------|
| [file1] | [what changes] |
| [file2] | [what changes] |

### Code Changes

#### File: [path]

**Before**:
```[language]
[current code]
```

**After**:
```[language]
[proposed code]
```

### Risk Assessment

- **Scope**: [How much code changes]
- **Risk level**: Low / Medium / High
- **Potential side effects**: [Any concerns]
- **Rollback difficulty**: Easy / Medium / Hard

---

**Do you approve this fix?**
```

## Get User Approval

Wait for explicit approval before making changes.

### If user approves:
- Proceed with implementation
- Track all changes made

### If user has concerns:
- Address concerns
- Propose alternative if needed
- Get approval for revised approach

### If user suggests different fix:
- Evaluate their suggestion
- Discuss trade-offs
- Implement their preferred approach

## Apply the Fix

### 1. Make Changes

Use Edit tool to apply approved changes:

```
Applying changes to [file]...
```

### 2. Track Changes

Document all modifications:

```json
{
  "resolution": {
    "appliedAt": "[timestamp]",
    "changes": [
      {
        "file": "[path]",
        "description": "[what was changed]",
        "linesModified": [42, 43, 44]
      }
    ]
  }
}
```

### 3. Verify Syntax

After changes:

| Language | Check |
|----------|-------|
| TypeScript | `npx tsc --noEmit` |
| Python | `python -m py_compile [file]` |
| Go | `go build ./...` |

## Handle Complex Fixes

### Multiple Changes Required

```
## Multi-Step Fix

This fix requires changes in multiple places:

### Step 1 of 3: Update validation
[change description]

### Step 2 of 3: Add migration
[change description]

### Step 3 of 3: Update tests
[change description]

Proceeding with Step 1...
```

### Data Fixes Required

If the issue is data, not code:

```
## Data Fix Required

The root cause is data-related, not code-related.

### Data Issue
[Description of data problem]

### Recommended Fix
```sql
-- Or appropriate command for your data store
UPDATE users SET emailVerified = false WHERE emailVerified IS NULL;
```

### Before Running

- [ ] Backup affected data
- [ ] Test in staging first
- [ ] Have rollback plan

Would you like to proceed with the data fix?
```

### Configuration Fixes

If the issue is configuration:

```
## Configuration Fix

The root cause is a configuration issue.

### Current Configuration
```
KEY=wrong_value
```

### Correct Configuration
```
KEY=correct_value
```

### Where to Change
- File: [path] or
- Environment: [where to set env var] or
- Service: [where to update]

Apply this configuration change?
```

## Document Resolution

Create or update resolution record:

```json
{
  "resolution": {
    "type": "code|data|config",
    "description": "[What was fixed]",
    "rootCause": "[Reference to confirmed hypothesis]",
    "changes": [
      {
        "file": "[path]",
        "before": "[old code/value]",
        "after": "[new code/value]"
      }
    ],
    "appliedAt": "[timestamp]",
    "appliedBy": "claude-troubleshoot"
  }
}
```

## Present Fix Summary

```
## Fix Applied

### Changes Made

| File | Change |
|------|--------|
| src/auth/login.ts | Added null check for emailVerified |
| src/db/migrations/003.ts | Backfill migration for existing users |

### Code Verification
- [x] Syntax check passed
- [x] No type errors

---

**Next**: Verify the fix resolves the original problem.

Proceed to verification?
```

## Handle Fix Failures

### If fix causes new errors:

```
## Fix Issue Detected

The applied fix caused a new error:

```
[error message]
```

Options:
1. **Rollback** - Undo the change
2. **Adjust** - Modify the fix to address new error
3. **Investigate** - This reveals a deeper issue
```

### If fix doesn't compile:

```
## Compilation Error

The fix introduced a compilation error:

```
[error message]
```

Adjusting the fix...
```

**Output**: Fix applied and documented, ready for verification
