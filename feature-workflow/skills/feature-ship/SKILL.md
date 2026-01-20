---
name: feature-ship
description: Complete a feature with quality gates - security review, QA validation, and final verification. Use when user says they're done implementing, wants to ship a feature, or asks to complete/finish work.
user-invocable: true
---

# Complete Feature Command

You are executing the **COMPLETE FEATURE** workflow - a quality gate process that ensures features meet security, quality, and testing standards before being marked as completed.

> **CRITICAL: Never write directly to backlog.json, in-progress.json, or completed.json!**
>
> To mark a feature as completed, you MUST write to `docs/planning/.transition/intent.json` with the transition type. The hook will handle moving items between files atomically. Direct writes will cause data inconsistency and break statusline tracking.

## Contents

- [Feature Target](#feature-target)
- [Workflow Overview](#workflow-overview)
- [Phase Details](#phase-details)
- [Error Handling](#error-handling)

---

## Feature Target

$ARGUMENTS

If no specific feature ID was provided above, you will help the user select from in-progress items.

---

## Workflow Overview

This command orchestrates a 6-phase quality gate workflow:

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Pre-flight Check | Verify feature is in-progress, has implementation artifacts |
| 2 | Security Review | Scan for vulnerabilities (OWASP Top 10, CVEs) |
| 3 | QA Validation | Verify test coverage and acceptance criteria |
| 4 | Final Verification | Run tests, type check, lint, build |
| 5 | Status Update | Update status to "completed" via hook |
| 6 | Summary | Display completion report |

### Effort-Based Scaling

| Effort | Phase 2 (Security) | Phase 3 (QA) |
|--------|-------------------|--------------|
| **Low** (< 8 hours) | `npm audit` only | `npm test` only |
| **Medium/Large** | Full security-reviewer agent | Full qa-engineer agent |

---

## Phase Details

### Phase 1: Pre-flight Check & Effort Selection

**See**: [preflight.md](preflight.md)

- Read in-progress.json and find/select feature
- Verify implementation artifacts exist
- Determine effort level for workflow scaling

### Phase 2: Security Review

**See**: [security.md](security.md)

- **Low effort**: Run `npm audit --audit-level=high`
- **Medium/Large**: Run security-reviewer agent
- **BLOCKS** completion if Critical/High issues found

### Phase 3: QA Validation

**See**: [qa.md](qa.md)

- **Low effort**: Run `npm test`
- **Medium/Large**: Run qa-engineer agent
- **BLOCKS** completion if critical issues or test failures

### Phases 4-6: Verification & Completion

**See**: [completion.md](completion.md)

- Run full test suite, type check, lint, build
- Review implementation checklist from plan.md
- Get user confirmation
- Trigger hook-based status transition (in-progress → completed)
- Display completion summary with unblocked features

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Feature not in-progress | Direct user to correct command or status |
| Security issues found | BLOCK and provide fixes |
| QA issues found | BLOCK and list what needs fixing |
| Tests failing | BLOCK and show failures |
| Backlog file missing | Error with instructions to create |
| Feature artifacts missing | Ask user to verify implementation was done |
| Hook failure | Check result.json for error details |

---

## Philosophy: "Quality is Not Optional"

This workflow ensures:
- Security vulnerabilities are caught before production
- Quality standards are met consistently
- Test coverage is verified
- Features are properly documented
- Clean transition from in-progress to completed

No feature should be marked complete without passing these quality gates.

---

**Let's verify your feature is ready for completion!**
