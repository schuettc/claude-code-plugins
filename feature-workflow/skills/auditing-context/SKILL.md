---
name: auditing-context
description: Auto-load active audit context when working with audited code. Use when user is working on code that has an active audit session, discussing audit findings, or making changes related to a runtime audit. Silently loads audit session data to inform responses.
allowed-tools: Read, Glob
---

# Auditing Context

Automatically load active audit session data when the user is working in the context of a runtime audit.

## When to Use

Invoke this skill when the user:
- Is working on code that has pending audit injections
- Asks about audit findings or captured data
- Discusses runtime behavior verification
- References "the audit" or a specific audit ID
- Is making changes to audited code paths
- Asks about injected logs or cleanup status

## Instructions

### Step 1: Check for Active Audits

Read `docs/audits/registry.json` to find active audit sessions.

```json
{
  "audits": [
    {
      "id": "auth-flow-001",
      "status": "in-progress",
      "name": "Login Flow Verification"
    }
  ]
}
```

Filter for audits with `status: "in-progress"`.

### Step 2: Load Active Audit Context

For relevant audits, read:

```
docs/audits/[audit-id]/
├── session.json      # Current phase, target description, questions
├── injections.json   # Active injections in code
└── report.md         # Findings (if analysis complete)
```

### Step 3: Check for Injected Code

If there are active injections:

1. Read `injections.json` to understand what's currently injected
2. Be aware of which files have audit instrumentation
3. Warn user if they're editing files with active injections

### Step 4: Use Context Naturally

Reference context when responding:

- **If injections are active**: Remind user of cleanup requirements
- **If discussing audited code**: Reference what was verified
- **If editing audited files**: Note any pending injections in that file
- **If asking about findings**: Reference the audit report

## Context Awareness Scenarios

### User Editing Injected File

```
Note: This file has active audit injections at lines 42, 67.
Consider running cleanup before making significant changes,
or be careful not to modify the AUDIT-INJECTED lines.
```

### User Asking About Behavior

```
The audit "auth-flow-001" verified this behavior:
- Credentials ARE validated before database query (confirmed)
- Session IS created after successful auth (confirmed)

Evidence captured in the audit report.
```

### User Forgot About Active Audit

```
Reminder: There's an active audit "auth-flow-001" with injections
in src/auth/login.ts. Status: awaiting runtime capture.

Would you like to:
1. Continue the audit capture
2. Run cleanup to remove injections
```

## Integration Notes

This skill works with:
- `/feature-audit` command - Provides context during audit workflow
- `/feature-troubleshoot` command - Can reference audit findings
- `runtime-auditor` agent - Shares context with audit operations

## Example

**User**: "Why is there a console.log in the login function?"

**Response** (after silently loading context):
```
That's an audit injection from the active "auth-flow-001" audit.

It was added to capture the user object at login entry. The audit
is currently in the "runtime-capture" phase, waiting for you to
trigger the login flow and capture the output.

You can:
1. Run the process to capture the logs
2. Run `/feature-audit` to continue the workflow
3. Jump to cleanup if you want to remove the injections
```

## Warning Triggers

Alert the user when:

1. **Editing injected files**: "This file has active audit injections"
2. **Long-running audit**: "Audit started [X hours ago], injections still active"
3. **Incomplete cleanup**: "Audit marked complete but injections may remain"
4. **Multiple active audits**: "Multiple audits active - specify which one"

## Status Interpretation

| Session Status | Meaning |
|----------------|---------|
| `in-progress` | Audit active, may have injections |
| `awaiting-capture` | Injections present, waiting for runtime |
| `analyzing` | Captured data being processed |
| `completed` | Audit finished, should be cleaned up |

Always check `injections.json` for actual injection state regardless of session status.
