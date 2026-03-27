# Pre-Ship Review

Detailed instructions for the final independent assessment before shipping.

## Prerequisites

You should have already read:
- `docs/features/<id>/idea.md` — the original problem statement
- `docs/features/<id>/plan.md` — the implementation plan
- Any prior reviews in `docs/features/<id>/reviews/`

## Review Process

### Step 1: Comprehensive Evidence Gathering

This is the final gate. Be thorough:

1. **Full git diff**: Run `git diff main...HEAD` to see ALL changes for this feature
2. **Read all changed files**: Don't skim — read the actual implementation
3. **Run full test suite**: Execute the project's test command and capture results
4. **Run linter/type checker**: Execute lint and type check commands if available
5. **Run build**: Verify the project builds successfully
6. **Check prior reviews**: Read any `reviews/plan-review.md` or `reviews/impl-review-*.md` — were their concerns addressed?
7. **Check plan completion**: Are all plan.md steps checked off?

### Step 2: Read the Rubric

Review the **Pre-Ship Review** criteria in [rubrics.md](rubrics.md). You will score against these 5 criteria:

1. **Problem-Solution Completeness** — Does the final implementation fully address the original problem?
2. **Test Coverage & Quality** — Are tests comprehensive and meaningful?
3. **Code Quality** — Would this pass review by someone unfamiliar with the project?
4. **Documentation** — Are changes documented where needed?
5. **Shipping Readiness** — Is this safe to ship?

### Step 3: Evaluate Each Criterion

For each criterion, provide evidence-based scores. This is the final review — be more stringent than implementation reviews.

**Key questions to answer:**
- Would a user hit the problem described in idea.md after this ships? (Problem-Solution Completeness)
- If a test fails tomorrow, will the test name tell you what broke? (Test Coverage)
- Could a new team member understand this code without the conversation history? (Code Quality)
- Can a user find how to use new functionality? (Documentation)
- Are there any ticking time bombs? (Shipping Readiness)

### Step 4: Check Prior Review Concerns

If prior reviews exist:
- Were blocking issues from plan review addressed in the implementation?
- Were blocking issues from implementation review resolved?
- Were "conditional pass" recommendations addressed?

Flag any unresolved prior concerns as additional findings.

### Step 5: Compute Verdict

Apply the verdict rules (same as other phases):
- Average >= 4.0: **PASS**
- Average >= 3.0, no criterion below 2: **CONDITIONAL PASS**
- Any criterion at 1, or average < 3.0: **FAIL**

**Pre-ship note**: A CONDITIONAL PASS here means "can ship with acknowledged risks." A FAIL means "should not ship without addressing blocking issues."

### Step 6: Write Review Files

Write two files:

#### 1. `reviews/pre-ship-review.md`

```markdown
---
phase: pre-ship
reviewer-session: YYYY-MM-DD HH:MM:SS
criteria-version: 1.0
---

# Pre-Ship Review: [Feature Name]

## Scores

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Problem-Solution Completeness | X | [evidence] |
| Test Coverage & Quality | X | [evidence] |
| Code Quality | X | [evidence] |
| Documentation | X | [evidence] |
| Shipping Readiness | X | [evidence] |

## Average: X.X | Verdict: [PASS/CONDITIONAL PASS/FAIL]

## Test Results
[Output of test suite run]

## Build Status
[Output of build command]

## Prior Review Concerns
- [Were previous blocking issues resolved?]

## Detailed Findings

### Ship-Ready Aspects
- [What's good and ready]

### Concerns
- [Issues found, with severity]

### Unresolved Prior Issues
- [Any issues from earlier reviews that weren't addressed]

## Recommendations
- [Final suggestions before shipping]
```

#### 2. `reviews/review-status.md`

Update with final verdict:

```markdown
---
phase: pre-ship
verdict: [pass/conditional-pass/fail]
updated: YYYY-MM-DD HH:MM:SS
blocking-issues: [count]
---

## Verdict: [PASS/CONDITIONAL PASS/FAIL]

### Blocking Issues
- [Issues that must be resolved before shipping, or "(none)"]

### Recommendations
- [Non-blocking suggestions for post-ship improvement]
```
