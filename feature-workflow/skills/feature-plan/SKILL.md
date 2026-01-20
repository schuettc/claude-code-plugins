---
name: feature-plan
description: Start implementing a feature from the JSON backlog with adaptive agent dispatch. Use when user wants to begin work on a backlog item, start implementation, or mentions a specific feature ID to work on.
user-invocable: true
---

# Implement Feature Command

You are executing the **IMPLEMENT FEATURE** workflow - a comprehensive feature kickoff process that ensures proper planning before any implementation begins.

> **CRITICAL: Never write directly to backlog.json, in-progress.json, or completed.json!**
>
> To move a feature to in-progress, you MUST write to `docs/planning/.transition/intent.json` with the transition type. The hook will handle moving items between files atomically. Direct writes will cause data inconsistency and break statusline tracking.

## Contents

- [Feature Target](#feature-target)
- [File Organization](#file-organization)
- [Workflow Overview](#workflow-overview)
- [Phase Details](#phase-details)
- [Completing a Feature](#completing-a-feature)
- [Error Handling](#error-handling)

---

## Feature Target

$ARGUMENTS

If no specific feature ID was provided above, you will help the user select from the backlog.

---

## File Organization

All feature artifacts are stored in a single location:

```
docs/planning/
├── backlog.json                    # Items with status: "backlog"
├── in-progress.json                # Items with status: "in-progress"
├── completed.json                  # Items with status: "completed"
└── features/
    └── [feature-id]/               # One directory per feature
        ├── plan.md                 # Implementation plan
        ├── requirements.md         # Detailed requirements
        └── design.md               # System design (if applicable)
```

**Key Principles**:
- Items are split by status across three JSON files (multi-file format v2.0)
- Each file contains a global `summary` for quick dashboard access
- Status transitions move items between files atomically via hooks
- Files are created once in `features/[id]/` and never move

---

## Workflow Overview

This command orchestrates a 6-phase workflow:

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Feature Selection | Choose from backlog or validate provided ID |
| 2 | Requirements Analysis | Deep dive with project-manager agent |
| 3 | System Design | Architecture planning (adaptive based on feature type) |
| 4 | Implementation Plan | Create detailed plan document |
| 5 | Backlog Status Update | Update status to "in-progress" via hook |
| 6 | Kickoff Summary | Create todos and provide clear next steps |

---

## Phase Details

### Phase 1: Feature Selection & Dependencies

**See**: [selection.md](selection.md)

- Read backlog and find/select feature
- Check for unmet dependencies
- Set terminal context for status line
- Handle blocked features with user options

### Phase 2: Requirements Deep Dive

**See**: [requirements.md](requirements.md)

- Create feature directory
- Optional: Run code-archaeologist for legacy code
- Run project-manager agent for requirements analysis
- Effort-based scaling (Low/Medium/Large)

### Phase 3: System Design (Adaptive)

**See**: [design.md](design.md)

- Classify feature type (Backend/Frontend/Full-Stack/Infrastructure)
- Dispatch appropriate specialized agents
- Save design documents

| Feature Type | Agents Used |
|--------------|-------------|
| Backend-Only | api-designer |
| Frontend-Only | ux-optimizer + frontend-architect |
| Full-Stack | api-designer + frontend-architect + integration-designer |
| UI-Heavy | ux-optimizer → then full-stack agents |
| Infrastructure | system-designer |

### Phases 4-6: Implementation & Kickoff

**See**: [implementation.md](implementation.md)

- Create plan.md with implementation steps
- Trigger hook-based status transition (backlog → in-progress)
- Stage changes with git
- Display kickoff summary with next steps

---

## Completing a Feature

When the feature is done, use the `/feature-ship` command:

```
/feature-ship [feature-id]
```

This runs quality gates before marking the feature complete:
1. **Security Review** - Scans for vulnerabilities (OWASP Top 10, CVEs)
2. **QA Validation** - Verifies test coverage and acceptance criteria
3. **Final Verification** - Runs tests, type checks, and build
4. **Status Update** - Updates status to "completed" via hook

**Files stay in place** - `docs/planning/features/[feature-id]/` remains as a permanent record

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Backlog not found | Create empty backlog.json and inform user |
| Feature not found | List available items, ask to select |
| Agent errors | Retry with more context or continue without that design phase |
| Directory missing | Create `docs/planning/features/` if needed |
| Hook failure | Check result.json for error details |

---

## Philosophy: "Never Code Without a Plan"

By completing these 6 phases, you ensure:
- Requirements are clearly understood
- Architecture is properly designed
- Implementation is broken into manageable steps
- Documentation will stay current
- Testing is considered upfront
- Risks are identified and mitigated

---

**Let's get started!**
