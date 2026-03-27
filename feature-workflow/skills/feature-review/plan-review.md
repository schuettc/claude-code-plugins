# Plan Review

Detailed instructions for reviewing a feature's implementation plan.

## Prerequisites

You should have already read:
- `docs/features/<id>/idea.md` — the original problem statement
- `docs/features/<id>/plan.md` — the implementation plan to review

## Review Process

### Step 1: Read the Rubric

Review the **Plan Review** criteria in [rubrics.md](rubrics.md). You will score against these 5 criteria:

1. **Problem-Solution Alignment** — Does every plan step trace to a stated problem?
2. **Step Testability** — Can each step be verified done/not-done without subjective judgment?
3. **Risk Coverage** — Are risks identified with specific mitigations?
4. **Testing Strategy** — Specific scenarios and coverage targets, not "will add tests"?
5. **Scope Appropriateness** — Matches effort estimate, no over/under-engineering?

### Step 2: Evaluate Each Criterion

For each criterion:

1. Re-read the relevant sections of idea.md and plan.md
2. Compare against the rubric score descriptions (1-5)
3. Assign a score with specific evidence from the documents
4. Write a brief note explaining the score

**Be specific in your notes.** Instead of "good alignment", write "Steps 1-3 trace to requirement R1 (auth flow); Step 4 addresses R2 (session management); Step 5 has no clear requirement connection."

### Step 3: Check for Common Plan Issues

Look for these specific problems:

- [ ] **Orphan steps**: Plan steps that don't connect to any requirement in idea.md
- [ ] **Missing requirements**: Problems stated in idea.md with no corresponding plan step
- [ ] **Vague steps**: Steps using words like "improve", "enhance", "optimize" without measurable criteria
- [ ] **Missing error cases**: Happy path only with no error handling steps
- [ ] **Dependency gaps**: Steps that depend on external systems/APIs not mentioned
- [ ] **Testing gaps**: Functionality described without corresponding test plans
- [ ] **Scope creep indicators**: Steps that go beyond what idea.md describes

### Step 4: Compute Verdict

Apply the verdict rules:
- Average >= 4.0: **PASS**
- Average >= 3.0, no criterion below 2: **CONDITIONAL PASS**
- Any criterion at 1, or average < 3.0: **FAIL**

### Step 5: Write Review Files

Write two files:

#### 1. `reviews/plan-review.md`

Use this format:

```markdown
---
phase: plan
reviewer-session: YYYY-MM-DD HH:MM:SS
criteria-version: 1.0
---

# Plan Review: [Feature Name]

## Scores

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Problem-Solution Alignment | X | [specific evidence] |
| Step Testability | X | [specific evidence] |
| Risk Coverage | X | [specific evidence] |
| Testing Strategy | X | [specific evidence] |
| Scope Appropriateness | X | [specific evidence] |

## Average: X.X | Verdict: [PASS/CONDITIONAL PASS/FAIL]

## Detailed Findings

### Strengths
- [What the plan does well]

### Issues
- [Specific problems found, with references to plan sections]

### Missing Elements
- [Requirements from idea.md not addressed in plan]

## Recommendations
- [Actionable suggestions for improvement]
```

#### 2. `reviews/review-status.md`

```markdown
---
phase: plan
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
