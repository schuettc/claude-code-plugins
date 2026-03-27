# Implementation Review

Detailed instructions for reviewing a feature's implementation against its plan.

## Prerequisites

You should have already read:
- `docs/features/<id>/idea.md` — the original problem statement
- `docs/features/<id>/plan.md` — the implementation plan

## Review Process

### Step 1: Gather Implementation Evidence

Before scoring, collect the evidence:

1. **Check plan progress**: Read plan.md and note which steps are checked off
2. **Review git changes**: Run `git log --oneline` and `git diff main...HEAD` (or appropriate base branch) to see what code was actually changed
3. **Read changed files**: Read the key files that were modified or created
4. **Run tests**: Execute `npm test` or the project's test command to see current test state
5. **Check for unplanned changes**: Compare git diff against plan steps — are there changes not in the plan?

### Step 2: Read the Rubric

Review the **Implementation Review** criteria in [rubrics.md](rubrics.md). You will score against these 4 criteria:

1. **Plan Adherence** — Does code match plan steps?
2. **Test Existence** — Tests for completed steps?
3. **Code-Problem Fit** — Does code solve the original problem from idea.md?
4. **Independent Quality** — Would this pass review by someone unfamiliar with the conversation?

### Step 3: Evaluate Each Criterion

For each criterion:

1. Cross-reference the evidence gathered in Step 1
2. Compare against the rubric score descriptions (1-5)
3. Assign a score with specific file/line references
4. Write a note with concrete evidence

**Be specific.** Instead of "tests exist", write "test_review_status.py covers read/write/parse (3 test classes, 12 tests); no tests for edge case when review-status.md is malformed."

### Step 4: Check for Common Implementation Issues

Look for these specific problems:

- [ ] **Plan deviation without justification**: Code does something different than planned with no documented reason
- [ ] **Missing tests**: Completed functionality without corresponding test coverage
- [ ] **Dead code**: Code written but not connected to anything
- [ ] **Hardcoded values**: Magic numbers or strings that should be configurable
- [ ] **Error handling gaps**: Happy path works but errors would crash
- [ ] **Security concerns**: Input validation, injection risks, auth checks
- [ ] **Incomplete steps**: Steps marked done that are only partially implemented

### Step 5: Compute Verdict

Apply the verdict rules:
- Average >= 4.0: **PASS**
- Average >= 3.0, no criterion below 2: **CONDITIONAL PASS**
- Any criterion at 1, or average < 3.0: **FAIL**

### Step 6: Write Review Files

Write two files:

#### 1. `reviews/impl-review-N.md` (numbered)

Check for existing impl-review files and increment the number.

```markdown
---
phase: implementation
reviewer-session: YYYY-MM-DD HH:MM:SS
criteria-version: 1.0
---

# Implementation Review: [Feature Name]

## Scores

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Plan Adherence | X | [specific evidence with file references] |
| Test Existence | X | [specific evidence with test file references] |
| Code-Problem Fit | X | [specific evidence] |
| Independent Quality | X | [specific evidence] |

## Average: X.X | Verdict: [PASS/CONDITIONAL PASS/FAIL]

## Detailed Findings

### Completed Plan Steps
- [x] Step 1: [status and quality assessment]
- [ ] Step 2: [not yet implemented]

### Code Quality Observations
- [File:line] — [specific finding]

### Test Coverage
- [What's tested and what's missing]

### Unplanned Changes
- [Any code changes not in the plan]

## Recommendations
- [Actionable suggestions with file references]
```

#### 2. `reviews/review-status.md`

Update with current verdict (overwrites previous):

```markdown
---
phase: implementation
verdict: [pass/conditional-pass/fail]
updated: YYYY-MM-DD HH:MM:SS
blocking-issues: [count]
---

## Verdict: [PASS/CONDITIONAL PASS/FAIL]

### Blocking Issues
- [Issues that scored 1-2, or "(none)"]

### Recommendations
- [Non-blocking suggestions]
```
