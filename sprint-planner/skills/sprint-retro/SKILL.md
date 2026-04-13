---
name: sprint-retro
description: Sprint retrospective — review what was planned vs. accomplished, capture lessons learned, identify what worked and what didn't. Use at the end of a sprint or after a deadline event (demo, release). Produces actionable takeaways for the next sprint.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
---

# Sprint Retro

Review the sprint outcome and capture lessons for next time.

## When to Use

- "How did the sprint go?"
- "Let's do a retro"
- "What did we miss?"
- End of sprint or after the driving deadline event
- When something went wrong and you want to capture the lesson

## Arguments

`$ARGUMENTS` can be:
- Empty — review the most recent sprint plan
- A path to a specific plan file

## Workflow

### Phase 1: Gather Evidence

1. **Read the sprint plan** — what was planned, who was assigned what
2. **Read the dashboard** — `docs/features/DASHBOARD.md` — what actually shipped
3. **Check git history** — `git log --oneline --since="[sprint start]"` — what actually landed
4. **Check PR history** — `gh pr list --state all --limit 30` — what was opened, merged, closed

### Phase 2: Planned vs. Actual

Build a comparison table:

```markdown
| Feature | Planned | Actual | Notes |
|---------|---------|--------|-------|
| `feature-a` | Deadline-Critical | Shipped | On track |
| `feature-b` | This Sprint | In Progress | Took longer than expected — effort was Medium, needed Large |
| `feature-c` | This Sprint | Not Started | Blocked by AIDP cluster access |
| `feature-d` | Not Planned | Shipped | Emerged mid-sprint as a dependency |
```

### Phase 3: Identify Patterns

Look for recurring themes:

**Estimation accuracy:**
- Were effort estimates (Small/Medium/Large) accurate?
- Which items took longer than expected? Why?
- Were any items easier than expected?

**Blocking patterns:**
- What blocked progress? (external teams, infrastructure, unclear specs, missing context)
- Could the blocks have been identified earlier?
- Did the dependency graph hold up, or were there surprise dependencies?

**Spec quality:**
- Did developers have to ask questions that should have been in the spec?
- Were any specs missing critical information?
- Did the spec audit (`/sprint-audit-specs`) catch the gaps?

**Assignment quality:**
- Were tasks assigned to the right people?
- Did junior devs get stuck? On what?
- Were senior devs bottlenecked on too many critical-path items?

### Phase 4: Capture Lessons

Format lessons as actionable rules:

```markdown
## Lessons Learned

### What Worked
- [Specific thing that worked well and WHY]
- [Pattern to repeat next sprint]

### What Didn't Work
- [Specific problem and root cause]
- [What we'd do differently]

### Process Improvements
- [Concrete change to make next sprint]
- [E.g., "Add realistic data ranges to all data-generation specs"]
- [E.g., "Verify PR status with `gh pr view` before planning around it"]

### Estimation Calibration
- [Feature X was estimated Small, took Medium — reason: ...]
- [Adjust future estimates for similar work]
```

### Phase 5: Update Plugin Memory

If lessons are broadly applicable (not project-specific), suggest adding them to the sprint-planner plugin itself:
- New checklist items for `/sprint-audit-specs`
- New anti-patterns for `/sprint-triage`
- New rules for `/sprint-plan`

Present these as suggestions — don't auto-modify the plugin.

## Output

Present the retro summary and ask:
- "Anything I missed?"
- "Should we capture any of these lessons in the plugin for next time?"
- "Ready to start planning the next sprint?"

## Integration Notes

Works with:
- `/sprint-plan` — lessons feed into the next sprint's planning
- `/sprint-audit-specs` — retro findings improve the audit checklist
- feature-workflow plugin — reads DASHBOARD.md for shipped status
