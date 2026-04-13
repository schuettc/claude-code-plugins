---
name: sprint-assign
description: Generate a structured team assignment message from the current sprint plan. Produces a copy-pasteable message for Slack, email, or team chat with per-person assignments, context blocks, and key ground rules. Use after sprint-plan to share assignments.
allowed-tools: Read, Glob, Grep
user-invocable: true
---

# Sprint Assign

Generate a shareable team assignment message from the current sprint plan.

## When to Use

- "Write up the assignments for the team"
- "Create a message I can share"
- "Send the sprint plan to the team"
- After `/sprint-plan` has created or updated the plan

## Arguments

`$ARGUMENTS` can be:
- Empty — auto-detect the most recent plan file
- A path to a specific plan file

## Workflow

### Step 1: Find the Plan

Look for the sprint plan in:
1. `.claude/plans/` — plan mode files (most recent by modification time)
2. Project docs directory (e.g., `docs/sprint-plan.md`, `maxwell/docs/next-steps.md`)
3. If no plan found: "No sprint plan found. Run `/sprint-plan` first."

### Step 2: Read Feature Specs

For each assigned feature in the plan, read its `docs/features/{id}/idea.md` to pull:
- Priority and effort
- One-line summary
- Key context the developer needs

### Step 3: Generate Message

Format a message with this structure:

```markdown
**[Project Name] Sprint — [Date Range]**

[1-2 sentence context: what's the driving event, what does success look like]

All features tracked in `docs/features/DASHBOARD.md`. Use `/feature-plan <id>` to generate your implementation plan before starting. Branch off `[branch-name]`, PR back into `[branch-name]`.

---

**[Senior Dev Name] — [Lane]**
- `feature-id` (Priority, Effort) — what to do
- `feature-id` (Priority, Effort) — what to do

**[Junior Dev Name] — [Lane]**
- `feature-id` (Priority, Effort) — what to do
- Feeds into: [which senior dev's work this supports]

[repeat for each team member]

---

**Key context for everyone:**
- [Branch strategy — which branch to work from]
- [Architecture context — key decisions they should know]
- [What's already done — don't re-do this]
- [Where to find docs — entry point for onboarding]
- [Questions → who to ask]
```

### Message Quality Rules

1. **Per-person sections** — every developer should be able to read just their section and know what to do
2. **Priority + effort on every item** — so devs can self-organize within their lane
3. **"Feeds into" links** — junior devs need to know who depends on their output
4. **Ground rules section** — branch strategy, architecture decisions, what's off-limits
5. **No jargon without context** — if you reference a technical term (IRR, NAPI, IPC), link to where they can learn about it or add a parenthetical
6. **Keep it scannable** — bullet points, not paragraphs. Bold the names. Use code formatting for feature IDs

### Step 4: Present to User

Show the message and ask:
- "Want me to adjust the tone, add/remove anything, or tailor it for a specific channel?"
- Offer to create domain-specific reference blocks if any features reference unfamiliar concepts

## Anti-Patterns

- Don't include tasks the user has explicitly removed from the sprint
- Don't assign the same feature to multiple people without flagging it as a pair/collaboration
- Don't list post-deadline items in the assignment message — they're noise
- Don't assume the message format (Slack vs email vs wiki) — keep it markdown-compatible for all
