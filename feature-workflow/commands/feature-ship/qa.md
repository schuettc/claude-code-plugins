# Phase 3: QA Validation (Medium/Large Effort)

**Note**: For Low effort items, skip this phase and run `npm test` instead.

**AGENT**: `epcc-workflow:qa-engineer`

## Launch QA Engineer

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

---

## Handle QA Results

**If No-Go (critical issues)**:
```
## QA Validation: NO-GO

Issues that must be addressed:

[List of critical issues]

Please fix these issues and run `/feature-ship [id]` again.
```
STOP the workflow here.

**If Go**:
```
## QA Validation: GO

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
