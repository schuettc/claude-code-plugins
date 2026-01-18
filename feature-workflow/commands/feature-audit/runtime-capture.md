---
name: feature-audit:runtime-capture
description: "Phase 5: Runtime Capture"
user-invocable: false
---

# Phase 5: Runtime Capture

## Capture Method Selection

User chooses how to capture log output:

### Option 1: Paste Output

For complex environments (CI/CD, remote systems, containerized apps):

```
## Paste Capture Mode

1. Run your process that triggers the audited code path
2. Copy all output that contains `[AUDIT:` prefixed lines
3. Paste the output here

Example of what to look for:
```
[AUDIT:auth-flow-001:1] Entry - credentials: { email: "test@example.com", hasPassword: true }
[AUDIT:auth-flow-001:2] Validation result: true
[AUDIT:auth-flow-001:3] Session created: { token: "eyJ...", expiresAt: "..." }
```

**Tip**: You can paste multiple times if you want to capture different scenarios.

Paste your output when ready:
```

### Option 2: Direct Execution

For local development with simple commands:

```
## Direct Execution Mode

What command should I run to trigger the audited code path?

Examples:
- `npm test -- --grep "login"`
- `curl -X POST localhost:3000/api/login -d '{"email":"test@example.com","password":"test"}'`
- `python manage.py test auth.tests.LoginTest`

Enter command:
```

## Process Captured Output

### Parse Log Lines

Extract all lines matching the audit pattern:
```
[AUDIT:audit-id:sequence] message
```

Create structured capture data:

```json
{
  "captureId": "capture-001",
  "capturedAt": "[timestamp]",
  "method": "paste|direct",
  "command": "[if direct execution]",
  "logs": [
    {
      "sequence": 1,
      "raw": "[AUDIT:auth-flow-001:1] Entry - credentials: { email: \"test@example.com\", hasPassword: true }",
      "timestamp": "[if present]",
      "data": { "email": "test@example.com", "hasPassword": true }
    },
    {
      "sequence": 2,
      "raw": "[AUDIT:auth-flow-001:2] Validation result: true",
      "timestamp": "[if present]",
      "data": true
    }
  ],
  "missingSequences": [],
  "unexpectedLogs": []
}
```

### Store Captured Data

Save to audit directory:
```
docs/audits/[audit-id]/logs/captured-[timestamp].log
```

Also save raw output for reference.

### Validate Capture

Check for:

1. **Missing sequences**: Expected logs that didn't appear
   - May indicate code path wasn't hit
   - May indicate conditional branch taken

2. **Unexpected order**: Logs out of expected sequence
   - May reveal async behavior
   - May indicate parallel execution

3. **Gaps**: Large sequence jumps
   - May indicate error occurred
   - May indicate early return

## Support Multiple Capture Rounds

User may want to capture multiple scenarios:

```
## Capture Round [N] Complete

**Logs captured**: [count]
**Sequences covered**: [1, 2, 3, 5, 6]
**Missing**: [4, 7]

Would you like to:
1. **Capture another round** - Test a different scenario
2. **Proceed to analysis** - Analyze what we have
3. **Investigate missing** - Understand why some logs didn't appear
```

### Scenario Tagging

When capturing multiple rounds:

```json
{
  "captures": [
    {
      "captureId": "capture-001",
      "scenario": "successful login",
      "logs": [...]
    },
    {
      "captureId": "capture-002",
      "scenario": "invalid password",
      "logs": [...]
    },
    {
      "captureId": "capture-003",
      "scenario": "user not found",
      "logs": [...]
    }
  ]
}
```

## Direct Execution Handling

When using direct execution:

### 1. Run Command

```bash
[user-provided command] 2>&1 | tee docs/audits/[audit-id]/logs/raw-[timestamp].log
```

### 2. Filter Audit Logs

Extract only audit-related lines:
```bash
grep '\[AUDIT:' docs/audits/[audit-id]/logs/raw-[timestamp].log
```

### 3. Handle Long-Running Processes

For servers or watch processes:
```
## Long-Running Process Detected

The process appears to be long-running. Options:

1. **Trigger and stop** - I'll start the process, you trigger the code path, then tell me to stop
2. **Timeout** - Run for [N] seconds then capture output
3. **Switch to paste** - Run the process yourself and paste relevant output
```

## Update Session

Update `session.json` with capture status:

```json
{
  "phases": {
    "capture": "completed"
  },
  "captures": [
    {
      "captureId": "capture-001",
      "scenario": "[description]",
      "logsCount": 7,
      "complete": true
    }
  ]
}
```

## Present Capture Summary

```
## Capture Complete

**Audit**: [audit-id]
**Capture rounds**: [N]
**Total logs captured**: [count]

### Coverage Summary

| Injection | Purpose | Captured |
|-----------|---------|----------|
| #1 | Entry point | Captured |
| #2 | Validation | Captured |
| #3 | Error path | Not captured |
| #4 | Success path | Captured |

### Scenarios Captured
1. **Successful login** - [7 logs]
2. **Invalid password** - [4 logs]

**Next**: We'll analyze the captured data and generate the audit report.

Proceed to analysis?
```

**Output**: Log output captured and stored for analysis
