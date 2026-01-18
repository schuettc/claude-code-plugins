# Phase 1: Problem Definition

## Gather Problem Details

If `$ARGUMENTS` was provided, parse it for problem context.

If more information is needed, ask the user:

```
## Define the Problem

Let's clearly understand what's happening.

### 1. What's the symptom?
What are you observing? (e.g., "error message appears", "page doesn't load", "data is wrong")

### 2. What should happen instead?
What's the expected behavior?

### 3. When did it start?
- Always been this way
- After a specific change
- Started randomly
- Don't know

### 4. Can you reproduce it?
- Every time
- Sometimes
- Only in specific conditions
- Can't reproduce reliably

### 5. Any error messages?
Please share exact error messages, stack traces, or logs if available.
```

## Document Problem Statement

Create structured problem definition:

```json
{
  "problemId": "[auto-generated]",
  "createdAt": "[timestamp]",
  "status": "investigating",
  "problem": {
    "symptom": "[what's happening]",
    "expected": "[what should happen]",
    "started": "[when it started]",
    "reproducible": "[always/sometimes/rarely/unknown]",
    "errorMessages": ["[error 1]", "[error 2]"],
    "stepsToReproduce": [
      "Step 1: ...",
      "Step 2: ...",
      "Step 3: ..."
    ]
  }
}
```

## Reproduction Steps

If user can reproduce:

```
## Reproduction Steps

Please provide the exact steps to reproduce:

1. Start from: [clean state / specific page / etc.]
2. Do: [action]
3. Then: [action]
4. Observe: [symptom]

Is this consistent every time?
```

## Scope the Problem

Determine boundaries:

```
### Problem Scope

- **Affected users**: All / Some / Just me
- **Affected environments**: Production / Staging / Dev / All
- **Affected features**: [specific feature] / Multiple features
- **Frequency**: Always / Sometimes / Rarely
```

## Gather Context

Search for relevant information:

### 1. Recent Changes

```bash
git log --oneline -20  # Recent commits
git diff HEAD~10       # What changed recently
```

### 2. Error Logs

Ask user for:
- Browser console errors
- Server logs
- Application error tracking (Sentry, etc.)

### 3. Environment Details

- OS / Browser version
- Node / Python / etc. version
- Relevant configuration

## Check for Known Issues

Search codebase for related issues:

```
Search for:
- TODO/FIXME comments related to area
- Previous bug fixes in same area
- Related test failures
```

## Create Problem Summary

Present to user:

```
## Problem Summary

### Symptom
[Clear description of what's happening]

### Expected Behavior
[What should happen instead]

### Reproduction
[Steps or "cannot reliably reproduce"]

### Scope
- Environment: [env]
- Frequency: [frequency]
- Users affected: [scope]

### Context
- Recent changes: [yes/no - relevant commits]
- Error messages: [summary]
- Related code areas: [file paths]

---

**Next**: Form hypotheses about possible causes.

Does this accurately capture the problem?
```

## Handle Unclear Problems

If problem is too vague:

```
## Need More Information

The problem description is too general to investigate effectively.

Can you help me understand:

1. **Specific error**: What exact message do you see?
2. **Specific action**: What were you doing when it happened?
3. **Comparison**: Did this work before? What changed?

Even small details can help narrow down the cause.
```

## Store Session (for complex issues)

For complex issues, create troubleshooting session:

```
docs/troubleshooting/[session-id]/
├── session.json      # Problem definition and investigation status
└── evidence/         # Collected logs, screenshots, etc.
```

**Output**: Problem clearly defined with scope and reproduction steps
