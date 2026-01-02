---
name: complete
description: Complete a feature with quality gates - security review, QA validation, and final verification
version: 1.2.0
argument-hint: "[feature-id-from-backlog]"
---

# Complete Feature Command

You are executing the **COMPLETE FEATURE** workflow - a quality gate process that ensures features meet security, quality, and testing standards before being marked as completed.

## Feature Target
$ARGUMENTS

If no specific feature ID was provided above, you will help the user select from in-progress items.

---

## Workflow Overview

This command orchestrates a 6-phase quality gate workflow:

1. **Pre-flight Check** - Verify feature is in-progress, has implementation artifacts
2. **Security Review** - Run security-reviewer agent to scan for vulnerabilities
3. **QA Validation** - Run qa-engineer agent for quality assessment
4. **Final Verification** - Run tests, confirm no critical issues
5. **Status Update** - Update backlog.json status to "completed"
6. **Summary** - Display completion report

---

## Phase 1: Pre-flight Check

### Read Backlog
Read `docs/planning/backlog.json` to get current items.

### If Feature ID Provided ($ARGUMENTS not empty)
1. Find item in `items` array where `id` matches the argument
2. Verify status is "in-progress"
   - If status is "backlog": Ask user to run `/feature-workflow:implement` first
   - If status is "completed": Inform user feature is already completed
3. Verify implementation artifacts exist:
   - `docs/planning/features/[feature-id]/plan.md`
   - `docs/planning/features/[feature-id]/requirements.md`

### If No Feature ID Provided
1. Filter items where `status === "in-progress"`
2. Display available items:
   ```
   ## In-Progress Features Ready for Completion

   - [id]: [name] - Started [startedAt]
   ```
3. Ask user to select by ID

### Pre-flight Checklist
Display and verify:
```
## Pre-flight Check: [feature-name]

✓ Feature status: in-progress
✓ Implementation plan exists
✓ Requirements documented

Ready to proceed with quality gates.
```

**Output**: Feature validated and ready for quality review

---

## Phase 2: Security Review

**AGENT**: `epcc-workflow:security-reviewer`

**CRITICAL**: This phase can BLOCK completion if Critical or High severity issues are found.

Launch the security-reviewer agent:

```
Launch Task tool with:
subagent_type: "epcc-workflow:security-reviewer"
description: "Security scan for feature"
prompt: "
Perform a comprehensive security review for this feature:

Feature ID: [id]
Feature Name: [name]
Feature Directory: docs/planning/features/[feature-id]/
Implementation Plan: docs/planning/features/[feature-id]/plan.md

Tasks:
1. Read the implementation plan to understand what was built
2. Identify all files that were created or modified for this feature
3. Scan for OWASP Top 10 vulnerabilities:
   - A01: Broken Access Control
   - A02: Cryptographic Failures
   - A03: Injection (SQL, Command, XSS)
   - A07: Cross-Site Scripting
   - A09: Security Logging Failures
4. Check for:
   - Hardcoded secrets or credentials
   - Unvalidated user input
   - Missing authentication/authorization checks
   - Insecure data handling
5. If package.json exists, check for dependency vulnerabilities:
   - Run: npm audit (if available)
   - Check for outdated packages with known CVEs

Output Format:
- List all findings with severity (Critical/High/Medium/Low)
- Provide specific file:line locations
- Include remediation code for each issue
- BLOCK if any Critical or High severity issues found

If BLOCKED:
  List issues that MUST be fixed before completion
  Provide exact code fixes

If PASSED:
  Confirm no Critical/High issues
  List any Medium/Low recommendations
"
```

### Handle Security Results

**If BLOCKED (Critical/High issues found)**:
```
## ⛔ Security Review: BLOCKED

Critical/High severity issues must be fixed before completion:

[List of issues with fixes]

Please fix these issues and run `/feature-workflow:complete [id]` again.
```
STOP the workflow here.

**If PASSED**:
```
## ✓ Security Review: PASSED

No Critical or High severity issues found.

Recommendations (optional fixes):
[Medium/Low issues if any]
```
Continue to Phase 3.

**Output**: Security review results

---

## Phase 3: QA Validation

**AGENT**: `epcc-workflow:qa-engineer`

Launch the qa-engineer agent:

```
Launch Task tool with:
subagent_type: "epcc-workflow:qa-engineer"
description: "QA validation for feature"
prompt: "
Perform QA validation for this feature:

Feature ID: [id]
Feature Name: [name]
Requirements: docs/planning/features/[feature-id]/requirements.md
Implementation Plan: docs/planning/features/[feature-id]/plan.md

Tasks:
1. Review requirements and acceptance criteria
2. Verify implementation matches requirements
3. Check test coverage:
   - Unit tests exist for new code
   - Integration tests for API changes
   - E2E tests for user flows (if applicable)
4. Run existing tests if test command available:
   - npm test
   - npm run test:unit
   - npm run test:integration
5. Assess quality metrics:
   - Code coverage percentage
   - Test pass rate
   - Missing test scenarios

Output Format:
- Test Summary: Tests run, passed, failed
- Coverage Assessment: What's tested, what's missing
- Acceptance Criteria: Verified / Not Verified for each
- Risk Assessment: Areas of concern
- Release Recommendation: Go / No-Go with reasoning

Go/No-Go Criteria:
MUST PASS:
  - All existing tests passing
  - No critical acceptance criteria unmet
  - Core functionality works

SHOULD PASS:
  - Test coverage > 80%
  - All acceptance criteria verified
"
```

### Handle QA Results

**If No-Go (critical issues)**:
```
## ⛔ QA Validation: NO-GO

Issues that must be addressed:

[List of critical issues]

Please fix these issues and run `/feature-workflow:complete [id]` again.
```
STOP the workflow here.

**If Go**:
```
## ✓ QA Validation: GO

Test Results:
- Tests Run: [N]
- Tests Passed: [N]
- Tests Failed: [N]
- Coverage: [X]%

Acceptance Criteria: [N/N] verified

[Any recommendations for future improvements]
```
Continue to Phase 4.

**Output**: QA validation results

---

## Phase 4: Final Verification

### Run Full Test Suite
```bash
# Run all tests
npm test 2>/dev/null || echo "No test command found"

# Run type check if available
npm run type-check 2>/dev/null || npm run typecheck 2>/dev/null || echo "No type-check"

# Run lint if available
npm run lint 2>/dev/null || echo "No lint command"
```

### Verify Build
```bash
# Verify build succeeds
npm run build 2>/dev/null || echo "No build command"
```

### Review Implementation Checklist
Check that all items in `docs/planning/features/[feature-id]/plan.md` are marked complete:
- Read the plan file
- Count checked `- [x]` vs unchecked `- [ ]` items
- If unchecked items remain, ask user:
  ```
  ## Incomplete Tasks Found

  The following tasks in plan.md are not marked complete:
  - [ ] [Task 1]
  - [ ] [Task 2]

  Options:
  1. Mark these as complete (if actually done)
  2. Remove from scope (if not needed)
  3. Cancel completion (finish tasks first)
  ```

### User Confirmation
```
## Final Verification Summary

✓ Security Review: Passed
✓ QA Validation: Passed
✓ Tests: [N] passing
✓ Build: Successful
✓ Plan Tasks: [N/N] complete

Ready to mark feature as completed?

This will:
- Update backlog.json status to "completed"
- Set completedAt timestamp
- Feature files will remain in docs/planning/features/[id]/ as a record

Proceed? (yes/no)
```

**Output**: Final verification complete, user confirmation received

---

## Phase 5: Status Update

1. **Read** `docs/planning/backlog.json`

2. **Find and update the item**:
   ```json
   {
     "status": "completed",
     "updatedAt": "[current ISO timestamp]",
     "completedAt": "[current ISO timestamp]"
   }
   ```

3. **Recalculate summary**:
   - Decrement `byStatus.in-progress`
   - Increment `byStatus.completed`
   - Update `lastUpdated`

4. **Write** updated JSON back to `docs/planning/backlog.json`

5. **Stage changes**:
   ```bash
   git add docs/planning/backlog.json
   ```

**Output**: Backlog JSON updated with completed status

---

## Phase 6: Completion Summary

Display comprehensive completion report:

```markdown
# Feature Completed: [Name]

**ID**: [id]
**Completed**: [YYYY-MM-DD]

---

## Timeline
- Created: [createdAt]
- Started: [startedAt]
- Completed: [completedAt]
- Duration: [days] days

---

## Quality Gates Passed

### Security Review ✓
- No Critical/High vulnerabilities
- [N] Medium/Low recommendations noted

### QA Validation ✓
- Tests: [N] passing
- Coverage: [X]%
- Acceptance Criteria: [N/N] verified

### Final Verification ✓
- Build: Successful
- Type Check: Passed
- Lint: Passed

---

## Artifacts (preserved as record)
- `docs/planning/features/[feature-id]/requirements.md`
- `docs/planning/features/[feature-id]/design.md` (if applicable)
- `docs/planning/features/[feature-id]/plan.md`

---

## Backlog Status
- Previous: in-progress
- Current: completed

---

## Next Steps
1. Consider creating a commit for this completion:
   ```
   git commit -m "Complete feature: [feature-name]"
   ```
2. Review backlog for next feature to implement:
   ```
   /feature-workflow:implement
   ```

---

Congratulations on completing this feature!
```

**Output**: Complete summary displayed

---

## Error Handling

- **Feature not in-progress**: Direct user to correct command or status
- **Security issues found**: BLOCK and provide fixes
- **QA issues found**: BLOCK and list what needs fixing
- **Tests failing**: BLOCK and show failures
- **Backlog file missing**: Error with instructions to create
- **Feature artifacts missing**: Ask user to verify implementation was done

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
