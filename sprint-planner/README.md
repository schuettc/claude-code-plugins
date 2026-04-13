# Sprint Planner

Sprint planning and team coordination plugin for Claude Code. Designed for small teams (2-6 devs) with mixed experience levels preparing for demos, releases, or time-boxed sprints.

## What It Does

Turns a messy backlog into an actionable, well-documented sprint plan with team assignments that developers can work from independently.

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **Sprint Plan** | `/sprint-plan` | Create a weekly sprint plan — triage backlog, assign owners, identify critical path |
| **Sprint Triage** | `/sprint-triage` | Clean up the backlog — close stale items, verify PR status, categorize by deadline |
| **Sprint Audit Specs** | `/sprint-audit-specs` | Audit feature specs for completeness — ensure devs can work independently |
| **Sprint Assign** | `/sprint-assign` | Generate a shareable team assignment message for Slack/email |
| **Sprint Retro** | `/sprint-retro` | End-of-sprint review — planned vs. actual, lessons learned |

## Typical Workflow

```
/sprint-triage          # Clean up backlog, close stale items
/sprint-plan            # Create the sprint plan with assignments
/sprint-audit-specs     # Verify specs are complete for all assignees
/sprint-assign          # Generate team message
... [sprint happens] ...
/sprint-retro           # Review outcomes, capture lessons
```

## Design Principles

These principles are encoded from real sprint planning sessions:

1. **Verify state before planning.** Always check PR status, branch state, and recent merges before assuming work needs to be done. Don't plan to "land" already-merged PRs.

2. **Single source of truth.** One backlog, one dashboard, one status page. If duplicates exist, consolidate immediately.

3. **Respect removals.** When someone says "remove this," remove it completely. Don't re-add it under a different name.

4. **Self-service specs for junior devs.** Every assigned task needs enough context for independent work: domain definitions, file paths, code maps, realistic examples, and clear deliverables.

5. **Critical path first.** Assign blocking work to senior devs. Assign parallelizable leaf work to junior devs that feeds into senior work streams.

6. **Triage by deadline, not by priority.** A P1 item isn't deadline-critical if the deadline is a demo and the feature isn't demo-relevant.

7. **Don't create tracking artifacts.** Use what exists (feature-workflow's DASHBOARD.md, existing docs). Adding more tracking systems creates confusion, not clarity.

## Works With

- **feature-workflow plugin** — reads `docs/features/DASHBOARD.md` and feature idea files. Use `/feature-capture` to add new items, `/feature-plan` to start work, `/feature-ship` to close items.

## Requirements

- Git repository with feature tracking (e.g., `docs/features/DASHBOARD.md` from feature-workflow plugin)
- GitHub CLI (`gh`) for PR status checks
- A backlog with feature idea files to triage and assign

## License

MIT
