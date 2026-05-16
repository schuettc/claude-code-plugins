# Phase 1: Interactive Questions

Use the AskUserQuestion tool to ask these 8 questions. You may ask multiple questions at once where appropriate.

## Question 1: Item Type

```
What type of item is this?
- Feature - New capability
- Enhancement - Improvement to existing feature
- Tech Debt - Code/infrastructure improvement
- Bug Fix - Defect correction
```

## Question 2: Feature Name

```
Enter a short descriptive name (will be converted to kebab-case for ID):
Example: "Dark Mode Toggle" -> id: "dark-mode-toggle"
```

## Question 3: Problem Statement

```
What problem does this solve? (1-3 sentences)
```

## Question 4: Priority

```
What is the priority?
- P0 (High) - Critical, blocks other work
- P1 (Medium) - Important, should be done soon
- P2 (Low) - Nice to have, can wait
```

## Question 5: Effort Estimate

```
Estimated effort?
- Low (< 8 hours)
- Medium (1-2 weeks)
- Large (2+ weeks)
```

## Question 6: Impact Level

```
Expected impact?
- Low - Minor improvement
- Medium - Noticeable improvement
- High - Significant value or risk reduction
```

## Question 7: Affected Areas (Optional)

```
Which parts of the system will this affect?
(comma-separated list, or leave blank)
Example: frontend/settings, backend/api, database
```

## Question 8: Dependencies (Optional)

```
Does this feature depend on any other backlog items being completed first?
(comma-separated feature IDs, or leave blank)
Example: analytics-api, user-auth
```

## Question 9a: Assignee (Optional)

```
Who is responsible for this? (free-form name, list, or leave blank)
Examples: court | [court, alex]
```

## Question 9b: Related Features (Optional)

```
Are there features this is related to (but not blocked by)? (comma-separated IDs, or leave blank)
Soft links — useful for "see also" / shared context. Use Dependencies (Q8) for hard blockers.
```

## Question 9c: Parallel-Safety (Optional, default Yes)

```
Can this feature run in parallel with other in-flight work, or does it touch files
that are likely to conflict?
- Yes (default) — safe to dispatch alongside siblings
- No — touches files other features touch; must run alone within its wave
```

## Question 9d: Initial State (Optional, default Active)

```
Is this feature actively pursuable now, or do we need to mark it differently?
- Active (default)
- Paused (work known, but blocked on something external)
- Superseded (replaced by another feature)
- Abandoned (decided not to pursue)

If Paused: ask "What are we waiting on?" → pausedReason
If Superseded: ask "Which feature replaces this?" → supersededBy
If Abandoned: ask "Why dropped?" → abandonedReason
```

## Question 9e: Epic (Optional)

```
Is this part of a larger initiative (epic)? (epic ID, or leave blank)
Example: auth-overhaul

If the epic doesn't exist yet, suggest the user create it first with /feature-capture
choosing type=Epic.
```

## Question 9: Category (Optional)

```
What category does this belong to? (e.g., coding, business, infrastructure, design)
Leave blank for "general".
```
