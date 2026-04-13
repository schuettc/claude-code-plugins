---
name: sprint-audit-specs
description: Audit all assigned feature specs for completeness. Checks that every developer has enough information to work independently — domain context, file paths, code maps, realistic examples, and clear deliverables. Flags gaps and offers to fix them. Use after sprint-plan, before sharing assignments.
allowed-tools: Read, Write, Edit, Glob, Grep, Agent
user-invocable: true
---

# Sprint Audit Specs

Audit every assigned feature spec to ensure developers can work independently.

## When to Use

- "Does everyone have enough information?"
- "Check the specs before we share"
- "Audit the feature specs"
- After `/sprint-plan`, before `/sprint-assign`
- When onboarding new team members to existing work

## Arguments

`$ARGUMENTS` can be:
- Empty — audit all features assigned in the current sprint plan
- A feature ID — audit just that one feature
- `junior` — audit only features assigned to junior developers (higher bar)

## Why This Matters

The #1 cause of sprint delays for small teams is blocked time — a developer waiting for answers instead of writing code. Self-service specs eliminate most of this. The cost of enriching a spec for 15 minutes is far less than the cost of a junior dev blocked for 2 hours.

## Audit Checklist

For every assigned feature, read its `docs/features/{id}/idea.md` and score against this checklist:

### Minimum Bar (all developers)

| Check | Question | How to Verify |
|-------|----------|---------------|
| Problem statement | Does the developer understand WHY this work matters? | Has a "Problem Statement" section that explains the motivation, not just the task |
| Deliverables | Does the developer know what DONE looks like? | Has explicit deliverables or acceptance criteria |
| Affected areas | Does the developer know WHERE to start? | Lists specific file paths (not just directories) |
| Dependencies | Does the developer know what they're BLOCKED BY? | `blocked-by` frontmatter or explicit dependency notes |

### Elevated Bar (junior developers)

| Check | Question | How to Verify |
|-------|----------|---------------|
| Domain definitions | Are unfamiliar terms defined? | Technical/business terms have definitions with realistic ranges/examples |
| Code map | Are starting-point files identified with context? | Specific file paths + line numbers + what the code does |
| Examples | Are there concrete examples of expected input/output? | JSON snippets, query examples, expected shapes |
| Existing patterns | Is there a pattern to follow? | Points to existing similar code: "follow the pattern in X" |
| Test guidance | Does the developer know how to verify their work? | Test commands, expected output, or test file locations |

### Red Flags

Watch for these spec problems:
- **Vague scope**: "improve the UX" without listing specific issues → needs concrete bug list
- **Missing domain context**: References business terms (IRR, TVPI, NAPI, federation) without definition → needs glossary or reference section
- **Orphan references**: Points to files or functions that might not exist → verify with Glob/Grep
- **No code map for audit/fix tasks**: "audit the pipeline" without listing which files comprise the pipeline → needs a starting-point file list with roles
- **Stale blocked-by**: References a feature that's already shipped → remove the blocker

## Workflow

### Phase 1: Collect Assignments

1. Read the sprint plan to get: `{feature_id, assigned_to, developer_level}`
2. If no plan exists, read `docs/features/DASHBOARD.md` for in-progress and backlog items

### Phase 2: Audit Each Spec

For each assigned feature:

1. Read `docs/features/{id}/idea.md`
2. Score against the checklist above
3. For junior dev assignments, apply the elevated bar
4. If file paths are referenced, spot-check that they exist (`Glob` or `Grep`)
5. If `blocked-by` references another feature, check if that feature is already shipped

### Phase 3: Report

Present findings in a table:

```markdown
## Spec Audit Results

| Feature | Assigned To | Level | Score | Gaps |
|---------|-------------|-------|-------|------|
| `feature-a` | Junior Dev A | Junior | 7/10 | Missing domain definitions, no test guidance |
| `feature-b` | Senior Dev | Senior | 9/10 | Good — all checks pass |
| `feature-c` | Junior Dev B | Junior | 5/10 | No code map, vague deliverables, stale blocked-by |
```

### Phase 4: Fix Gaps

For each feature with gaps, offer to fix them:
- **Domain definitions**: Research the domain (read related code, docs, or web search) and add a reference section
- **Code map**: Use Explore agents to trace the relevant code paths and add file/function references
- **Examples**: Generate realistic examples based on existing test fixtures or data patterns
- **Stale references**: Remove or update

When fixing, edit the `idea.md` directly — don't create separate docs.

## Output

End with a summary:
- How many specs are ready vs. need work
- Which gaps were fixed
- Any remaining gaps that need user input (e.g., "I don't know which AIDP cluster to use — you'll need to add that")

## Integration Notes

Works with:
- `/sprint-plan` — produces the assignment list this skill audits
- `/sprint-assign` — generates team message after specs are validated
- feature-workflow plugin — reads/writes feature idea files
