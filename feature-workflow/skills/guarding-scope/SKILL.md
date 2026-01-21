---
name: guarding-scope
description: Check if requested changes are within current feature scope. Use when user requests new functionality or changes during implementation that might be scope creep. Compares requests against feature requirements and suggests adding out-of-scope items to backlog.
allowed-tools: Read
---

# Scope Guard

Prevent scope creep by checking if requested changes align with the current feature's requirements.

## When to Use

Invoke this skill when the user:
- Requests new functionality while implementing a feature
- Asks to add something that seems tangential
- Proposes changes not in the original requirements
- Says "while we're at it, let's also..."

**Do NOT invoke for:**
- Bug fixes in feature code
- Refactoring within scope
- Clarifying existing requirements
- Implementation details of planned features

## Instructions

### Step 1: Identify Current Feature

Read `docs/features/DASHBOARD.md` and look at the **In Progress** section to find the active feature.

If none or unclear, skip scope check - don't block the user.

### Step 2: Load Requirements

Read `docs/features/[id]/idea.md`

Extract: problem statement, affected areas, proposed solution hints.

Also read `docs/features/[id]/plan.md` for:
- Implementation steps (what was planned)
- Technical decisions made

### Step 3: Analyze the Request

**In Scope** - Implements the problem statement, reasonable extension of the feature, bug fix, or implementation detail.

**Potential Scope Creep** - New functionality not related to problem statement, affects other areas beyond what's listed, would require updating the plan significantly.

**Clearly Out of Scope** - Unrelated to problem statement, better as its own feature.

### Step 4: Respond

- **In scope**: Proceed without comment
- **Potential creep**: Flag it, offer options (include, add to backlog, skip)
- **Out of scope**: Suggest `/feature-capture`

Be helpful, not obstructive. Respect user's decision.

## Example

**User**: "While we're adding dark mode, let's also add notification preferences"

**Response**:
```
This seems outside the current feature scope.

**Current Feature**: Dark Mode Toggle
**Original Scope**: Theme switching with light/dark modes
**Your Request**: Notification preferences

Options:
1. **Include it** - Add to current feature (increases scope)
2. **Add to backlog** - Track separately: `/feature-capture`
3. **Skip for now** - Focus on dark mode first

What would you like to do?
```

## Integration Notes

This skill works with:
- `checking-backlog` skill - For checking if idea is already tracked
- `/feature-capture` - For adding out-of-scope items
