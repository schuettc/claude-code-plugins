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

**IMPORTANT**: Writing plan.md automatically triggers the PostToolUse hook. You do NOT need to run any script manually or update DASHBOARD.md directly.

The hook automatically:
1. Detects the new plan.md file
2. Sets the terminal statusline to the feature ID
3. Regenerates DASHBOARD.md (feature moves to In Progress section)

## Verification

After writing plan.md:
1. Check that the file was created successfully
2. Read DASHBOARD.md to verify the feature appears in the In Progress table

## Stage Changes

```bash
git add docs/features/[id]/ docs/features/DASHBOARD.md
```

**Output**: Feature transitioned to in-progress, statusline set

---

# Phase 6: Kickoff Summary & Todo Creation

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
- Terminal statusline set to feature ID

---

## Next Steps:

### 1. Review Your Plan
Read: docs/features/[id]/plan.md

### 2. Start First Implementation Step
Task: [First step description]
Files: [Affected files]

### 3. Development Workflow
- Update progress in plan.md as you work
- Run tests frequently
- Before committing: ensure tests pass

### 4. When Done
Run `/feature-ship [id]` to complete the feature

---

Ready to start coding!
```

**Output**: Complete kickoff summary with clear next steps
