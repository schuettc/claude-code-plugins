---
name: sprint-plan
description: Create a weekly sprint plan from backlog and deadline. Triages features into deadline buckets, assigns owners by expertise lane, identifies critical path, and produces a shareable plan file. Use when starting a new sprint or preparing for a demo/release.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
user-invocable: true
---

# Sprint Plan

Create a weekly sprint plan from the current backlog, team roster, and driving deadline.

## When to Use

- "Let's plan the week"
- "What should the team work on?"
- "We have a demo on [date], let's plan"
- "Create a sprint plan"
- Start of a new sprint or work cycle

## Arguments

`$ARGUMENTS` can be:
- Empty — interactive mode, will ask for deadline and team info
- A deadline description — e.g., "demo April 27" or "release Friday"

## Critical Principles

These are hard-won lessons from real sprint planning. Follow them strictly:

### 1. Verify State Before Planning
**Never plan work around assumed state.** Before assigning any task:
- Check PR status (`gh pr list`) — don't plan to "land" already-merged PRs
- Check branch state (`git log`, `git branch -r`) — know what's already integrated
- Check what's changed since last sprint — `git log main..HEAD --oneline` or similar

### 2. Single Source of Truth
If you find duplicate tracking systems (multiple dashboards, overlapping docs, parallel backlogs):
- Flag it immediately
- Recommend consolidation — one backlog, one dashboard, one status page
- Never create a new tracking artifact without checking for existing ones first

### 3. Respect Removals
When the user removes a task or says "we don't want this":
- Remove it completely — from the plan, from assignments, from all references
- Do NOT re-add it under a different name or as a subtask of something else
- Do NOT suggest it again unless the user explicitly asks

### 4. Junior Devs Need Self-Service Specs
Tasks assigned to junior developers MUST include enough context for independent work:
- Domain definitions (don't assume they know what IRR or TVPI means)
- Realistic data ranges and examples
- File paths and code starting points
- Clear deliverables, not vague goals

### 5. Critical Path First
Identify which tasks block other tasks. Assign blockers to senior devs. Assign parallelizable leaf work to junior devs that feeds into senior work streams.

## Workflow

### Phase 1: Gather Context

1. **Read the backlog**: Look for `docs/features/DASHBOARD.md` (feature-workflow plugin) or equivalent backlog
2. **Check branch state**: Run `git status`, `git log --oneline -20`, `gh pr list --state all --limit 10`
3. **Check for existing plans**: Look for plan files, sprint docs, or next-steps docs in the repo
4. **Ask the user** (if not provided):
   - What is the driving deadline? (demo date, release date, review date)
   - Who is on the team? Names + roles (senior/junior, frontend/backend/fullstack)
   - Any known blockers or dependencies? (waiting on infrastructure, external teams, etc.)

### Phase 2: Triage Backlog

Categorize every backlog item into exactly one bucket:

| Bucket | Criteria | Action |
|--------|----------|--------|
| **Deadline-Critical** | Must be done for the deadline to succeed. Failure = demo/release fails | Assign to senior devs, track daily |
| **This Sprint** | Important and achievable this week, but not a blocker for the deadline | Assign based on skill match |
| **Post-Deadline** | Nice to have, too large, blocked, or not relevant to deadline | Explicitly defer with rationale |

**Triage rules:**
- P0 items are deadline-critical unless the user says otherwise
- Large items (effort: Large) should be scoped down — what's the minimum viable slice for the deadline?
- Items blocked by external dependencies go to post-deadline unless the blocker can be resolved this sprint
- Architecture/design spikes are "this sprint" but scoped to design doc only, no implementation

### Phase 3: Assign Work

Create ownership lanes based on team structure:

**Senior devs** get:
- Critical path / blocking work
- Architecture decisions
- Tasks that require cross-cutting knowledge
- PR triage and review coordination

**Junior devs** get:
- Leaf tasks that feed into senior work (test fixtures, sample data, UX polish)
- Well-defined scope with clear deliverables
- Tasks where mistakes are recoverable (not deployment, not auth, not data migration)

**Assignment format per person:**
```
### [Name]: [Lane Description]
- `feature-id` (Priority, Effort) — one-line context on what to do
- `feature-id` (Priority, Effort) — one-line context
- Dependencies: what they need from others, what others need from them
```

### Phase 4: Identify Dependencies

Draw the dependency graph:
- Which tasks block which other tasks?
- Which tasks feed into which (e.g., "chart fixtures" feeds into "viz audit")
- Are there any circular dependencies? (fix them)
- What's the critical path? (longest chain of dependent tasks)

### Phase 5: Write the Plan

Create or update a plan file. Recommended location: `.claude/plans/` or a project-specific docs directory.

**Plan structure:**
```markdown
# Sprint Plan: [Week/Date Range]

## Context
[Driving event, deadline, what success looks like]

## Team
[Names, roles, availability notes]

## Branch State
[Current branch, what's merged, open PRs, stale PRs]

## Triage Summary
| Bucket | Count | Key Items |
|--------|-------|-----------|

## Deadline-Critical Items
[Table with ID, owner, effort, dependencies]

## This Sprint Items
[Table with ID, owner, effort, dependencies]

## Deferred (Post-Deadline)
[Table with ID and rationale for deferring]

## Team Assignments
[Per-person sections with assigned features]

## Dependencies & Critical Path
[Dependency chain, blocking relationships]

## Verification (before deadline)
[Checklist of what "done" looks like]

## Open Questions
[Things that need answers from stakeholders]
```

### Phase 6: Validate Specs

Before finalizing, run the equivalent of `/sprint-audit-specs`:
- For each assigned feature, read its `idea.md`
- Check: does it have enough detail for the assigned developer?
- If junior dev: does it have domain definitions, file paths, code maps, examples?
- If not: flag the gap and offer to enrich it

## Output

Present the plan to the user for review. Highlight:
- Deadline-critical items and their owners
- Any gaps in feature specs that need enrichment
- Open questions that need stakeholder input
- Suggested order of work (what to start Monday morning)

## Integration Notes

Works with:
- `/feature-status` — quick view of backlog state before planning
- `/sprint-audit-specs` — deep check on spec completeness
- `/sprint-assign` — generate team communication message
- `/sprint-triage` — focused backlog categorization
- feature-workflow plugin — reads `docs/features/DASHBOARD.md` and feature idea files
