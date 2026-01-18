---
name: feature-troubleshoot:verification
description: "Phase 5: Verification"
user-invocable: false
---

# Phase 5: Verification

## Verify Fix Works

Confirm the fix resolves the original problem.

### Verification Methods

#### 1. Reproduction Test

```
## Verification: Reproduction Test

Please try to reproduce the original problem:

1. [Original step 1]
2. [Original step 2]
3. [Original step 3]

**Expected**: The problem should no longer occur.

Does the issue still happen?
```

#### 2. Automated Tests

Run relevant tests:

```bash
npm test              # Full suite
npm test -- [pattern] # Specific tests
```

#### 3. Targeted Testing

Create specific test for the fix:

```
## Targeted Verification

Testing specific scenario:
- Input: [test input]
- Expected: [expected result]
- Actual: [what happened]

Status: [PASS/FAIL]
```

## Check for Regressions

Ensure fix didn't break other things:

### 1. Run Full Test Suite

```bash
npm test
```

### 2. Check Related Functionality

```
## Regression Check

Testing related functionality that might be affected:

| Feature | Status |
|---------|--------|
| User login | Verified working |
| User registration | Verified working |
| Password reset | Verified working |
| Session management | Verified working |
```

### 3. Type/Lint Checks

```bash
npm run typecheck
npm run lint
```

## Verification Results

### If Fix Works

```
## Verification Complete

### Original Problem
[Description of the problem]

### Resolution
[What was fixed]

### Verification Results

- [x] Original problem no longer occurs
- [x] Automated tests pass
- [x] No regressions detected
- [x] Type check passed
- [x] Lint check passed

---

**The issue has been resolved!**

### Summary

| Phase | Result |
|-------|--------|
| Problem Definition | Identified |
| Hypothesis Formation | 5 hypotheses generated |
| Investigation | H2 confirmed as root cause |
| Resolution | Fix applied |
| Verification | Confirmed working |

### What Was Fixed
[Brief description]

### Files Changed
| File | Change |
|------|--------|
| [file1] | [change] |
| [file2] | [change] |

---

Would you like me to commit these changes?
```

### If Fix Doesn't Work

```
## Verification Failed

The original problem still occurs after the fix.

### What We Observed
[Description of what happened during verification]

### Options

1. **Re-investigate** - Return to Phase 2 with new information
2. **Adjust fix** - Modify the current fix approach
3. **Rollback** - Undo changes and try different hypothesis

What would you like to do?
```

### If Regressions Found

```
## Regression Detected

The fix introduced a new issue:

### Regression
[Description of new problem]

### Test Failures
- [test1]: [reason]
- [test2]: [reason]

### Options

1. **Adjust fix** - Modify to avoid regression
2. **Rollback** - Undo and try different approach
3. **Accept trade-off** - If regression is acceptable (rare)

How should we proceed?
```

## Document Resolution

Create final resolution document:

```markdown
# Troubleshooting Resolution: [Problem Title]

**Session ID**: [id]
**Resolved**: [timestamp]

## Problem Summary
[Brief description of the issue]

## Root Cause
[What caused the problem]

## Solution
[What was done to fix it]

## Files Changed
| File | Change |
|------|--------|
| [file1] | [description] |

## Verification
- Original problem: Resolved
- Test suite: Passed
- Regressions: None detected

## Lessons Learned
[Optional: What can prevent this in the future]

## Related
- [Links to related issues, PRs, etc.]
```

## Update Session Status

```json
{
  "status": "resolved",
  "resolvedAt": "[timestamp]",
  "verification": {
    "originalProblemResolved": true,
    "testsPassed": true,
    "regressionsFound": false
  }
}
```

## Offer Follow-Up Actions

```
## Issue Resolved

### Follow-Up Options

1. **Commit changes** - Create a commit with the fix
2. **Add test** - Write a test to prevent regression
3. **Update docs** - Document the fix for future reference
4. **Create PR** - Open a pull request for review

What would you like to do next?
```

## Handle Partial Success

If fix partially works:

```
## Partial Resolution

The fix addressed part of the problem:

### Resolved
- [x] [Symptom 1] - Fixed
- [x] [Symptom 2] - Fixed

### Still Occurring
- [ ] [Symptom 3] - Still present

### Next Steps

This may be multiple issues. Options:
1. **Continue** - Investigate remaining symptoms
2. **Accept partial** - Mark main issue as resolved, create new issue for remainder
3. **Rollback** - This fix isn't the complete solution
```

**Output**: Fix verified working, resolution documented
