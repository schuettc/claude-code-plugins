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

**Note**: Dependencies create bidirectional relationships:
- The new item's `dependsOn` array will include the specified IDs
- Each dependency target's `blockedBy` array will include this new item's ID
