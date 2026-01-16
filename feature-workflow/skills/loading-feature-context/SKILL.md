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

Read `docs/planning/in-progress.json` to find current work.

If multiple features are in-progress:
1. Check if user mentioned a specific feature name/ID
2. Look at recent file edits to infer which feature
3. If unclear, ask which feature they're working on

### Step 2: Load Feature Context

For the relevant feature, read these files (if they exist):
```
docs/planning/features/[feature-id]/
├── requirements.md    # Acceptance criteria, user stories
├── design.md          # Architecture, component design
└── plan.md            # Implementation steps, progress
```

### Step 3: Use Context Naturally

Reference context when responding - don't dump it all at once:
- Reference **requirements** when discussing what to build
- Reference **design** when discussing how to build
- Reference **plan** when discussing what's next

Also note dependency relationships (`dependsOn`, `blockedBy`) when relevant.

## Example

**User**: "What's the next step for the auth feature?"

**Response** (after silently loading context):
```
Looking at your implementation plan for **User Authentication**:

You've completed 3 of 7 steps. The next step is:
- [ ] Implement JWT token refresh logic in `auth/tokens.ts`

Key requirement for this step: Tokens must refresh 5 minutes before expiry.

The design specifies using the existing `TokenManager` class.
```

## Integration Notes

This skill works with:
- `tracking-progress` skill - Updates the plan.md this skill reads
- `guarding-scope` skill - Uses requirements.md to check scope
- `/feature-ship` - Uses these files for completion review
