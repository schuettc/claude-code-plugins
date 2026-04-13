---
name: sprint-triage
description: Focused backlog triage — categorize features into deadline-critical, this-sprint, and post-deadline buckets. Removes stale items, verifies PR/merge status, and produces a clean prioritized list. Use when the backlog needs cleanup before planning.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
user-invocable: true
---

# Sprint Triage

Clean up and categorize the backlog for sprint planning.

## When to Use

- "Triage the backlog"
- "What's stale? What should we cut?"
- "Clean up the feature list"
- Before `/sprint-plan` when the backlog is messy or outdated
- When coming back from a break and need to re-orient

## Arguments

`$ARGUMENTS` can be:
- Empty — triage the full backlog
- A deadline — e.g., "for April 27 demo" — used as the categorization anchor

## Triage Process

### Phase 1: Load Current State

1. Read `docs/features/DASHBOARD.md` for the full backlog
2. Run `gh pr list --state all --limit 20` to see recent PR activity
3. Run `git log --oneline -30` to see recent commits
4. Check for stale items: anything with a `blocked-by` referencing a completed feature

### Phase 2: Identify Stale Items

An item is stale if:
- Its `blocked-by` feature has already shipped (check `shipped.md` existence)
- The work was already done in a different PR or commit (search git log)
- The feature was organically resolved (e.g., "compiler warnings" that are now zero)
- It's been in backlog for 4+ weeks with no activity and no deadline relevance

**For each stale item, present to the user:**
```
**[feature-id]** — [reason it's stale]
Recommend: [close / update / keep]
```

Do NOT auto-close anything. Present findings and let the user decide.

### Phase 3: Verify PR/Branch State

For features that reference PRs or branches:
- Check if the PR is merged, open, or closed: `gh pr view <number> --json state`
- Check if the branch exists: `git branch -r --list '*feature-name*'`
- Flag mismatches: "Plan says to merge PR #97, but it was merged 3 days ago"

### Phase 4: Categorize

Given a deadline, sort every non-stale backlog item:

| Bucket | Criteria |
|--------|----------|
| **Deadline-Critical** | Without this, the demo/release fundamentally fails. Not "nice to have" — MUST have |
| **This Sprint** | Important, achievable, and relevant to the deadline context, but the deadline doesn't fail without it |
| **Post-Deadline** | Too large, not relevant, blocked, or lower priority. Explicitly say WHY it's deferred |

**Categorization rules:**
- Ask "if this isn't done, does the deadline event fail?" — if no, it's not critical
- Items with effort "Large" that haven't started are almost never deadline-critical this week
- Design spikes are "this sprint" at most — scope to design doc, not implementation
- Items blocked by external teams/infrastructure go to post-deadline unless the blocker resolves this sprint

### Phase 5: Present Results

```markdown
## Triage Results

### Stale Items (recommend closing)
| ID | Reason | Action |
|----|--------|--------|

### Deadline-Critical (must ship by [date])
| ID | Priority | Effort | Rationale |
|----|----------|--------|-----------|

### This Sprint
| ID | Priority | Effort | Rationale |
|----|----------|--------|-----------|

### Post-Deadline (deferred)
| ID | Priority | Rationale for deferring |
|----|----------|------------------------|
```

### Phase 6: Get Confirmation

Ask the user to confirm:
- Which stale items to close (offer to create `shipped.md` files)
- Whether the categorization is correct
- Any items they want to move between buckets

## Anti-Patterns

- **Don't assume priority = criticality.** A P1 item might not be deadline-critical if the deadline is a demo and the feature isn't demo-relevant
- **Don't keep zombie items alive.** If something's been in backlog for 6 weeks with no progress and no deadline, recommend closing it
- **Don't create new items during triage.** Triage is about cleaning and categorizing, not adding. Use `/feature-capture` for new items
- **Don't re-add removed items.** If the user closes something during triage, it stays closed. Period.

## Integration Notes

Works with:
- `/feature-status` — quick overview before deep triage
- `/sprint-plan` — takes triage output as input for planning
- `/feature-ship` — use to close stale items the user confirms
