---
name: scope-guard
description: Check if requested changes are within current feature scope. Use when user requests new functionality or changes during implementation that might be scope creep. Compares requests against feature requirements and suggests adding out-of-scope items to backlog.
allowed-tools: Read
---

# Scope Guard

Prevent scope creep by checking if requested changes align with the current feature's requirements.

## When to Use

Invoke this skill when the user:
- Requests new functionality while implementing a feature
- Asks to add something that seems tangential
- Proposes changes that weren't in the original requirements
- Says "while we're at it, let's also..."

**Do NOT invoke for:**
- Bug fixes in the feature code
- Refactoring within scope
- Clarifying existing requirements
- Implementation details of planned features

## Instructions

### Step 1: Identify Current Feature

```
Read: docs/planning/backlog.json
```

Find the in-progress feature. If none or multiple:
- Check context for which feature is active
- If unclear, skip scope check (don't block the user)

### Step 2: Load Feature Requirements

```
Read: docs/planning/features/[feature-id]/requirements.md
```

Extract:
- User stories
- Acceptance criteria
- Defined scope boundaries (if documented)
- Out-of-scope items (if documented)

### Step 3: Analyze the Request

Compare the user's request against the requirements:

**In Scope** if the request:
- Directly implements an acceptance criterion
- Is a reasonable interpretation of a user story
- Fixes a bug in feature code
- Is implementation detail of a planned component

**Potential Scope Creep** if the request:
- Adds new user-facing functionality not in requirements
- Affects areas outside the feature's `affectedAreas`
- Would require updating the requirements document
- Is "nice to have" but not "must have"

**Clearly Out of Scope** if the request:
- Is unrelated to the feature's problem statement
- Would better serve as its own feature
- Is explicitly listed as out-of-scope

### Step 4: Respond Appropriately

**If clearly in scope:**
Proceed without comment. Don't slow down valid work.

**If potential scope creep:**
```
This seems outside the current feature scope.

**Current Feature**: [name]
**Original Scope**: [brief summary from requirements]
**Your Request**: [what they asked for]

Options:
1. **Include it** - Add to current feature (may increase effort)
2. **Add to backlog** - Track as separate item: `/feature-capture`
3. **Skip for now** - Focus on original scope first

What would you like to do?
```

**If clearly out of scope:**
```
This is outside the scope of [feature name].

Consider adding it as a separate backlog item:
`/feature-capture`

This keeps the current feature focused and trackable.
```

## Output Format

Be helpful, not obstructive:
- Don't block legitimate work
- Offer clear options
- Make it easy to add to backlog
- Respect user's decision

### When User Chooses to Include

If user decides to expand scope:
```
Got it. Consider updating the requirements:
docs/planning/features/[id]/requirements.md

This helps track what the feature actually delivers.
```

## Integration Notes

This skill works with:
- `feature-context` skill - Uses same requirements.md
- `backlog-awareness` skill - For checking if idea is already tracked
- `/feature-capture` - For adding out-of-scope items
