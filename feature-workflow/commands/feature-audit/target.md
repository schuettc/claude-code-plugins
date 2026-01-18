---
name: feature-audit:target
description: "Phase 1: Target Identification"
user-invocable: false
---

# Phase 1: Target Identification

## Understand the Audit Request

If `$ARGUMENTS` was provided, parse it to understand what process to audit.

If no arguments provided, ask the user:
```
## What Would You Like to Audit?

Please describe the process, feature, or behavior you want to verify:

1. **What process?** (e.g., "user login flow", "payment processing", "data sync")
2. **What questions?** (e.g., "Does user data get validated before save?")
3. **What's the entry point?** (e.g., "The login button click", "The API endpoint /auth/login")

The more specific you are, the more targeted our audit can be.
```

## Identify Entry Points

Based on user description:

1. Search for relevant files using Glob/Grep
2. Identify the entry point function/handler
3. Map initial code paths to explore
4. Document what we're trying to verify

## Generate Audit ID

Create a unique audit ID based on:
- Process name (slugified)
- Timestamp or sequence number

Example: `auth-flow-001`, `payment-validation-002`

## Initialize Audit Session

Create audit directory structure:

```
docs/audits/[audit-id]/
├── session.json
├── injections.json
└── logs/
```

### session.json

```json
{
  "auditId": "[audit-id]",
  "name": "[descriptive name]",
  "createdAt": "[timestamp]",
  "status": "in-progress",
  "target": {
    "description": "[user's description]",
    "entryPoints": ["[file:line]", "..."],
    "questions": ["[what we're verifying]", "..."]
  },
  "phases": {
    "target": "completed",
    "exploration": "pending",
    "strategy": "pending",
    "injection": "pending",
    "capture": "pending",
    "analysis": "pending",
    "cleanup": "pending"
  }
}
```

### injections.json

```json
{
  "auditId": "[audit-id]",
  "injections": []
}
```

## Update Registry

Create or update `docs/audits/registry.json`:

```json
{
  "audits": [
    {
      "id": "[audit-id]",
      "name": "[name]",
      "createdAt": "[timestamp]",
      "status": "in-progress"
    }
  ]
}
```

## Present Summary

Display to user:

```
## Audit Session Created

**ID**: [audit-id]
**Target**: [description]

### Entry Points Identified
- [file:line]: [description]

### Questions to Verify
1. [question 1]
2. [question 2]

**Next**: We'll explore the code paths to identify strategic log injection points.

Proceed to code exploration?
```

**Output**: Audit session initialized, entry points identified
