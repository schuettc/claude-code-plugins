# Phase 6: Analysis & Report

## Load Audit Context

Read from audit directory:
- `session.json` - Questions to answer, injection purposes
- `injections.json` - What each log was meant to capture
- `logs/*.log` - Captured runtime data

## Analyze Captured Data

### 1. Map Logs to Questions

For each original question, gather evidence:

```
Question: "Are credentials validated before database query?"

Evidence:
- Log #1 (Entry): credentials received with email and password
- Log #2 (Validation): validation function returned true
- Log #3 (Database): query executed AFTER validation

Conclusion: VERIFIED - credentials are validated before database query
```

### 2. Compare Expected vs Actual

| Expected Behavior | Actual Behavior | Status |
|-------------------|-----------------|--------|
| Validation runs first | Validation ran at log #2 | Verified |
| Error returns early | Error logged at #4, no #5 | Verified |
| Token includes userId | Token data: `{userId: 123}` | Verified |
| Session saved to DB | No database log captured | Unexpected |

### 3. Identify Unexpected Findings

Look for:
- Unexpected code paths taken
- Data values outside expected ranges
- Missing expected log entries
- Order different than expected
- Performance anomalies (if timing captured)

### 4. Analyze by Scenario

If multiple capture rounds:

```
Scenario: Successful Login
  - All expected paths taken
  - Data transformations correct
  - Session created properly

Scenario: Invalid Password
  - Validation correctly failed
  - Error path taken
  - No session created (correct)

Scenario: User Not Found
  - Unexpected: validation ran before user lookup
  - Issue: Should check user exists first
```

## Generate Audit Report

Create `docs/audits/[audit-id]/report.md`:

```markdown
# Audit Report: [Audit Name]

**Audit ID**: [audit-id]
**Generated**: [timestamp]
**Status**: [Completed with findings / All verified / Issues found]

---

## Executive Summary

[2-3 sentence overview of what was audited and key findings]

**Key Result**: [VERIFIED / ISSUES FOUND / PARTIAL]

---

## Audit Scope

### Target Process
[Description of what was audited]

### Files Analyzed
| File | Lines Instrumented |
|------|-------------------|
| [file1] | [N] |
| [file2] | [N] |

### Questions Investigated
1. [Question 1]
2. [Question 2]
3. [Question 3]

---

## Log Injection Points

| ID | File:Line | Purpose | Captured |
|----|-----------|---------|----------|
| 1 | src/auth/login.ts:16 | Entry point | Yes |
| 2 | src/auth/login.ts:29 | Validation result | Yes |
| 3 | src/auth/login.ts:45 | Error handling | No |
| 4 | src/auth/session.ts:12 | Session creation | Yes |

---

## Findings

### Finding 1: [Title]

**Status**: Verified / Issue Found / Unexpected Behavior

**Question**: [What we were trying to verify]

**Evidence**:
```
[AUDIT:id:1] Entry - credentials: { email: "test@example.com", hasPassword: true }
[AUDIT:id:2] Validation result: true
[AUDIT:id:4] Session created: { userId: 123, token: "..." }
```

**Analysis**: [What this evidence tells us]

**Recommendation**: [If applicable]

---

### Finding 2: [Title]

[Continue for each finding...]

---

## Verification Results

### Questions Answered

| Question | Status | Evidence |
|----------|--------|----------|
| Are credentials validated? | Verified | Logs #1, #2 |
| Is session created after auth? | Verified | Logs #2, #4 |
| Are errors handled properly? | Not Captured | Error path not triggered |

### Unexpected Discoveries

1. [Any unexpected behavior observed]
2. [Performance issues if timing captured]
3. [Edge cases revealed]

---

## Scenarios Tested

### Scenario 1: Successful Login
- **Result**: All expected behaviors verified
- **Logs**: #1, #2, #4
- **Notes**: [Any observations]

### Scenario 2: Invalid Password
- **Result**: Error handling works correctly
- **Logs**: #1, #2, #3
- **Notes**: [Any observations]

---

## Recommendations

1. [Recommendation based on findings]
2. [Suggested improvements]
3. [Areas for further investigation]

---

## Cleanup Status

- [ ] Injected logs removed
- [ ] Code restored to pre-audit state

**Note**: Run cleanup phase to remove all audit instrumentation.

---

## Appendix

### Raw Log Data

See: `docs/audits/[audit-id]/logs/`

### Injection Manifest

See: `docs/audits/[audit-id]/injections.json`
```

## Update Session Status

```json
{
  "phases": {
    "analysis": "completed"
  },
  "report": {
    "generatedAt": "[timestamp]",
    "path": "docs/audits/[audit-id]/report.md",
    "findingsCount": 5,
    "verifiedCount": 4,
    "issuesCount": 1
  }
}
```

## Present Analysis Summary

```
## Audit Analysis Complete

**Audit**: [audit-id]
**Report**: `docs/audits/[audit-id]/report.md`

### Summary

| Metric | Count |
|--------|-------|
| Questions investigated | 5 |
| Behaviors verified | 4 |
| Issues found | 1 |
| Unexpected discoveries | 0 |

### Key Findings

1. **Verified**: Credentials are validated before database query
2. **Verified**: Sessions expire correctly
3. **Issue**: Error logging missing stack trace
4. **Verified**: Tokens include correct claims

### Recommendations

1. Add stack trace to error logging at `auth/errors.ts:34`

---

**Next**: Clean up injected logs and restore code to original state.

Proceed to cleanup?
```

**Output**: Audit report generated with findings and recommendations
