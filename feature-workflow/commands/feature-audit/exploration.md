---
name: feature-audit:exploration
description: "Phase 2: Code Exploration"
user-invocable: false
---

# Phase 2: Code Exploration

## Load Audit Context

Read `docs/audits/[audit-id]/session.json` to get:
- Entry points to start from
- Questions we're trying to answer
- Target process description

## Trace Execution Paths

Starting from each entry point:

### 1. Follow the Call Graph
```
Entry Point: handleLogin()
  → calls validateCredentials()
    → calls hashPassword()
    → calls database.query()
  → calls createSession()
    → calls generateToken()
  → calls sendResponse()
```

### 2. Identify Key Decision Points
Look for:
- Conditionals that change flow (`if/else`, `switch`)
- Error handling (`try/catch`, error callbacks)
- Async operations (promises, callbacks, goroutines)
- External calls (APIs, databases, services)

### 3. Map Data Transformations
Track how data changes:
```
Input: { email, password }
  → validated: { email: normalized, passwordHash }
  → stored: { userId, sessionToken, expiresAt }
  → output: { token, user: { id, email } }
```

## Identify Strategic Log Points

For each question we're verifying, identify WHERE to inject logs:

### Categories of Log Points

| Category | Purpose | Example Location |
|----------|---------|------------------|
| **Entry** | Capture inputs | Function entry, request handler |
| **Decision** | Which branch taken | After conditionals |
| **Transform** | Data before/after | Before and after processing |
| **External** | Call parameters/responses | Database queries, API calls |
| **Exit** | Final outputs | Return statements, responses |

### Log Point Selection Criteria

Good log points:
- Reveal actual data values
- Show which code path was taken
- Capture timing (for performance questions)
- Don't interrupt control flow

Avoid:
- Inside tight loops (too much output)
- Sensitive data without sanitization
- Locations that would change behavior

## Document Findings

Create exploration notes in session:

```json
{
  "exploration": {
    "completedAt": "[timestamp]",
    "callGraph": {
      "[entry-point]": {
        "calls": ["function1", "function2"],
        "decisions": ["line 42: auth check", "line 67: role validation"],
        "externals": ["database.users.findOne", "jwt.sign"]
      }
    },
    "dataFlow": {
      "input": "[description]",
      "transformations": ["[step 1]", "[step 2]"],
      "output": "[description]"
    },
    "proposedLogPoints": [
      {
        "file": "[file]",
        "line": "[line]",
        "category": "[entry|decision|transform|external|exit]",
        "purpose": "[what this reveals]",
        "dataToLog": "[variables/expressions]"
      }
    ]
  }
}
```

## Leverage Code-Archaeologist Patterns

Use these exploration techniques:

### Dependency Mapping
```
Component A
  -> imports Component B
  -> calls Component C
  -> uses Database D
```

### Data Flow Analysis
```
user_input
  -> validated in validate_input()
  -> transformed in process_data()
  -> stored in save_to_db()
  -> returned in api_response()
```

## Present Exploration Results

Display to user:

```
## Code Exploration Complete

### Execution Flow
[ASCII diagram or description of call graph]

### Key Decision Points
1. [file:line] - [what decision is made]
2. [file:line] - [what decision is made]

### Data Transformations
- Input: [description]
- Processing: [key steps]
- Output: [description]

### Proposed Log Points: [N] locations
| # | File | Line | Purpose |
|---|------|------|---------|
| 1 | [file] | [line] | [purpose] |
| 2 | [file] | [line] | [purpose] |

**Next**: We'll create a detailed injection strategy for your approval.

Proceed to injection strategy?
```

**Output**: Code paths mapped, log points identified
