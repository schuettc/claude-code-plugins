---
name: loading-feature-context
description: Load feature requirements, design, and implementation plan when working on in-progress features. Use when user is implementing code, debugging, asking about requirements, or making changes related to a tracked feature. Silently loads context files to inform responses.
allowed-tools: Read, Glob
---

# Feature Context

Automatically load feature documentation when the user is working on an in-progress feature.

## When to Use

Invoke this skill when the user:
- Is implementing code for a feature
- Asks about requirements or acceptance criteria
- Asks about design decisions
- Debugs or troubleshoots feature-related code
- References "the current feature" or a specific feature name

## Instructions

### Step 1: Identify In-Progress Features

Read `docs/features/DASHBOARD.md` and look at the **In Progress** section to find current work.

If multiple features are in-progress:
1. Check if user mentioned a specific feature name/ID
2. Look at recent file edits to infer which feature
3. If unclear, ask which feature they're working on

### Step 2: Load Feature Context

For the relevant feature, read these files:
```
docs/features/[id]/
├── idea.md    # Problem statement, priority, context
└── plan.md    # Implementation steps, progress, technical decisions
```

The `idea.md` contains:
- Problem statement (what and why)
- Priority, effort, impact
- Affected areas

The `plan.md` contains:
- Implementation steps (with checkboxes)
- Technical decisions
- Testing strategy
- Progress log

### Step 3: Use Context Naturally

Reference context when responding - don't dump it all at once:
- Reference **idea.md** when discussing what to build or why
- Reference **plan.md** when discussing how to build or what's next

Also check the implementation steps in plan.md to see what's completed vs remaining.

## Example

**User**: "What's the next step for the auth feature?"

**Response** (after silently loading context):
```
Looking at your implementation plan for **User Authentication**:

You've completed 3 of 7 steps. The next step is:
- [ ] Implement JWT token refresh logic in `auth/tokens.ts`

Key requirement from idea.md: Tokens must refresh 5 minutes before expiry.

The plan specifies using the existing `TokenManager` class.
```

## Integration Notes

This skill works with:
- `tracking-progress` skill - Updates the plan.md this skill reads
- `guarding-scope` skill - Uses idea.md to check scope
- `/feature-ship` - Uses these files for completion review
