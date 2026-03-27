# Phase 4: Implementation Plan

## Contents

- [Phase 4: Implementation Plan](#phase-4-implementation-plan-1)
- [Phase 5: Write plan.md](#phase-5-write-planmd)
- [Phase 6: Kickoff Summary](#phase-6-kickoff-summary--todo-creation)

---

## Phase 4: Implementation Plan

Create the implementation plan document to write to `docs/features/[id]/plan.md`.

Use this template:

```markdown
---
started: YYYY-MM-DD
---

# Implementation Plan: [Feature Name]

## Overview
[Brief summary of what will be implemented and why]

## Requirements Summary
[Key requirements from idea.md and requirements analysis]

## System Design
[Summary from design phase, or "No architecture changes required"]

## Implementation Steps
- [ ] Step 1: [Specific, actionable task with file references]
- [ ] Step 2: [Specific, actionable task with file references]
- [ ] Step 3: [Continue with all steps...]

Each step should:
- Be concrete and testable
- Reference specific files or components
- Be completable in 1-4 hours ideally

## Testing Strategy

### Unit Tests
- [What needs unit testing]
- [Coverage targets]

### Integration Tests
- [What needs integration testing]
- [Test scenarios]

### Manual Testing Checklist
- [ ] Test scenario 1
- [ ] Test scenario 2
- [ ] Test scenario 3

## Documentation Updates Needed
- [ ] Update [doc file 1] - [what needs updating]
- [ ] Update [doc file 2] - [what needs updating]

## Risks & Mitigations
- **Risk**: [Description]
  - **Mitigation**: [How to address]

## Progress Log
### [Today's Date]
- Created implementation plan
- Next: [First implementation step]
```

---

# Phase 5: Write plan.md

Write the plan document to `docs/features/[id]/plan.md`.

**IMPORTANT**: Writing plan.md automatically triggers the PostToolUse hook which regenerates DASHBOARD.md. You do NOT need to update DASHBOARD.md directly.

The hook automatically:
1. Detects the new plan.md file
2. Regenerates DASHBOARD.md (feature moves to In Progress section)

**Set statusline** (after writing plan.md):
```bash
${CLAUDE_PLUGIN_ROOT}/skills/feature-plan/scripts/set-context.sh [feature-id]
```

## Verification

After writing plan.md:
1. Check that the file was created successfully
2. Read DASHBOARD.md to verify the feature appears in the In Progress table

## Signal External Reviewer

After writing plan.md, create a review request file to signal the reviewer terminal (if one is running). This is **non-blocking** — the implementer proceeds regardless of whether a reviewer is active.

Write the file `docs/features/[id]/reviews/request-plan.md`:

```markdown
---
phase: plan
requested: YYYY-MM-DD HH:MM:SS
---

# Review Requested: Plan

External review requested for the **plan** phase.
```

> **Note**: This simply creates a signal file. If a reviewer terminal is running `/feature-review <id> --watch`, it will automatically pick up this request and begin a plan review. If no reviewer is active, the file has no effect.

## Stage Changes

```bash
git add docs/features/[id]/ docs/features/DASHBOARD.md
```

**Output**: Feature transitioned to in-progress, statusline set, review requested

---

# Phase 6: Kickoff Summary & Implementation Handoff

1. **Create TodoWrite list** with implementation steps from the plan

2. **Display comprehensive summary**:

```markdown
# Feature Development Kickoff Complete

## Feature: [Name]
**ID**: [id]
**Priority**: [priority]

---

## Feature Files:
- `docs/features/[id]/idea.md` - Problem statement & context
- `docs/features/[id]/plan.md` - Implementation plan (just created)

---

## What's Ready:
- Requirements analyzed with detailed acceptance criteria
- System design completed [or "No architecture changes needed"]
- Implementation plan created with [N] actionable steps
- Feature status: in-progress (shown in DASHBOARD.md)
```

3. **Launch implementation in a clean context**

Ask the user: **"Plan is ready. Want to start implementation with a fresh context?"**

If yes, check if cmux is available and launch accordingly:

```bash
# Check for cmux
if command -v cmux &> /dev/null; then
  cmux new-workspace --cwd "$PWD" --command "claude --prompt '/feature-workflow:feature-implement [id]'"
else
  echo "NO_CMUX"
fi
```

- **If cmux is available**: The command above opens a new workspace with a fresh Claude session that auto-starts implementation. Tell the user: *"Opened a new workspace to start implementation."*
- **If cmux is not available**: Tell the user to start a new session:
  ```
  To start implementation with a clean context, run /clear and then:
  /feature-workflow:feature-implement [id]
  ```

**Output**: Complete kickoff summary with implementation handoff
