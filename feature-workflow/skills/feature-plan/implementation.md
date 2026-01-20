# Phase 4: Implementation Plan

## Contents

- [Phase 4: Implementation Plan](#phase-4-implementation-plan-1)
- [Phase 5: Backlog Status Update](#phase-5-backlog-status-update-hook-based)
- [Phase 6: Kickoff Summary](#phase-6-kickoff-summary--todo-creation)

---

Create file: `docs/planning/features/[feature-id]/plan.md`

Use this template:

```markdown
# [Feature Name]

**Status**: In Progress
**Priority**: [priority]
**Effort**: [effort]
**Started**: [YYYY-MM-DD]
**Backlog ID**: [id]

## Problem Statement
[From requirements.md - why we're building this]

## Requirements
[Summary from requirements.md - key acceptance criteria]

## System Design
[Summary from design.md, or "No architecture changes required"]

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

## Dependencies
- [Any prerequisite work]
- [Any external dependencies]

## Risks/Unknowns
- **Risk**: [Description]
  - **Mitigation**: [How to address]

## Progress Log
### [Today's Date]
- Created implementation plan
- Next: [First implementation step]
```

Write this file using the Write tool.

**Output**: Implementation plan file created at `docs/planning/features/[feature-id]/plan.md`

---

# Phase 5: Backlog Status Update (Hook-Based)

Trigger the atomic transition by writing an intent file. The hook handles all file manipulation reliably.

## Step 1: Create Transition Directory

```bash
mkdir -p docs/planning/.transition
```

## Step 2: Write Transition Intent File

Write the following to `docs/planning/.transition/intent.json`:

```json
{
  "type": "backlog-to-inprogress",
  "itemId": "[feature-id]",
  "planPath": "docs/planning/features/[feature-id]/plan.md",
  "projectRoot": "[absolute path to project root]"
}
```

**Important**: The `projectRoot` must be an absolute path (e.g., `/Users/username/project`).

## Step 3: Verify Result

**IMPORTANT**: Writing the intent file automatically triggers the PostToolUse hook. You do NOT need to run any script manually. The hook runs immediately after your Write tool completes.

The hook automatically:
1. Validates the item exists in backlog.json
2. Updates item status and timestamps
3. Writes to in-progress.json FIRST (atomic pattern)
4. Verifies write success
5. Removes from backlog.json
6. Syncs global summary across all files

Read the result from `docs/planning/.transition/result.json`:

```json
{
  "success": true,
  "transition": "backlog-to-inprogress",
  "itemId": "[id]",
  "timestamp": "[ISO timestamp]",
  "filesModified": ["docs/planning/backlog.json", "docs/planning/in-progress.json"]
}
```

If there's an error, display it and stop the workflow.

## Step 4: Stage Changes

```bash
git add docs/planning/*.json
git add docs/planning/features/[feature-id]/
```

**Output**: Item moved from backlog.json to in-progress.json, feature files staged

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

## Feature Files Created:
- `docs/planning/features/[feature-id]/requirements.md` - Detailed requirements
- `docs/planning/features/[feature-id]/design.md` - System design [if applicable]
- `docs/planning/features/[feature-id]/plan.md` - Implementation plan

---

## What's Ready:
- Requirements analyzed with detailed acceptance criteria
- System design completed [or "No architecture changes needed"]
- Implementation plan created with [N] actionable steps
- Backlog status updated to "in-progress"

---

## Next Steps:

### 1. Review Your Plan
Read: docs/planning/features/[feature-id]/plan.md

### 2. Start First Implementation Step
Task: [First step description]
Files: [Affected files]

### 3. Development Workflow
- Update progress in plan.md as you work
- Run tests frequently
- Before committing: ensure tests pass

---

Ready to start coding!
```

**Output**: Complete kickoff summary with clear next steps
