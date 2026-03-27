# Review Rubrics

Grading criteria for each review phase. All criteria scored 1-5.

## Verdict Rules

| Condition | Verdict |
|-----------|---------|
| Average >= 4.0 | **PASS** |
| Average >= 3.0, no criterion below 2 | **CONDITIONAL PASS** |
| Any criterion at 1, or average < 3.0 | **FAIL** |

---

## Plan Review (5 criteria)

### 1. Problem-Solution Alignment
Does every plan step trace to a stated problem from idea.md?

| Score | Description |
|-------|-------------|
| 5 | Every step directly addresses a stated requirement; no orphan steps |
| 4 | Most steps trace clearly; one minor gap |
| 3 | General alignment but some steps lack clear connection to requirements |
| 2 | Multiple steps don't connect to stated problems |
| 1 | Plan addresses different problems than idea.md describes |

### 2. Step Testability
Can each step be verified done/not-done without subjective judgment?

| Score | Description |
|-------|-------------|
| 5 | Every step has clear, binary completion criteria |
| 4 | Most steps are testable; one or two are slightly vague |
| 3 | Mix of testable and vague steps |
| 2 | Most steps require subjective judgment to verify |
| 1 | Steps are aspirational ("improve X") with no measurable criteria |

### 3. Risk Coverage
Are risks identified with specific mitigations?

| Score | Description |
|-------|-------------|
| 5 | All significant risks identified with concrete, actionable mitigations |
| 4 | Key risks covered; mitigations are specific |
| 3 | Some risks identified but mitigations are generic |
| 2 | Risks mentioned but without real mitigations |
| 1 | No risk analysis or completely missing obvious risks |

### 4. Testing Strategy
Specific scenarios and coverage targets, not "will add tests"?

| Score | Description |
|-------|-------------|
| 5 | Named test cases, specific scenarios, coverage targets, clear test types |
| 4 | Good test plan with specific scenarios; minor gaps |
| 3 | Test section exists with some specifics but mostly general |
| 2 | Testing mentioned but only generically ("will add tests") |
| 1 | No testing strategy or just a placeholder |

### 5. Scope Appropriateness
Matches effort estimate, no over/under-engineering?

| Score | Description |
|-------|-------------|
| 5 | Scope perfectly matches problem complexity and effort estimate |
| 4 | Slight mismatch but reasonable |
| 3 | Noticeable over- or under-engineering for the problem size |
| 2 | Significant scope mismatch (gold-plating a simple fix, or trivializing a complex problem) |
| 1 | Scope completely disconnected from problem or effort estimate |

---

## Implementation Review (4 criteria)

### 1. Plan Adherence
Does code match plan steps?

| Score | Description |
|-------|-------------|
| 5 | Every completed plan step is fully implemented; no unplanned additions |
| 4 | Plan steps implemented with minor deviations that are justified |
| 3 | Most plan steps implemented; some gaps or unplanned additions |
| 2 | Significant deviation from plan without documented justification |
| 1 | Implementation bears little resemblance to plan |

### 2. Test Existence
Tests for completed steps?

| Score | Description |
|-------|-------------|
| 5 | Every completed step has corresponding tests; tests are meaningful |
| 4 | Most steps have tests; minor gaps in coverage |
| 3 | Some tests exist but notable gaps |
| 2 | Minimal testing; most functionality untested |
| 1 | No tests or only trivial/placeholder tests |

### 3. Code-Problem Fit
Does code solve the original problem from idea.md?

| Score | Description |
|-------|-------------|
| 5 | Code directly solves stated problem; clean and focused |
| 4 | Solves the problem with minor unnecessary complexity |
| 3 | Solves the core problem but with notable issues |
| 2 | Partially solves the problem; significant gaps |
| 1 | Does not solve the stated problem |

### 4. Independent Quality
Would this pass review by someone unfamiliar with the conversation?

| Score | Description |
|-------|-------------|
| 5 | Clean, well-structured, self-documenting code; obvious what it does and why |
| 4 | Good quality with minor issues a reviewer might flag |
| 3 | Acceptable but a reviewer would have several questions |
| 2 | Multiple quality issues; hard to follow without conversation context |
| 1 | Would not pass a standard code review |

---

## Pre-Ship Review (5 criteria)

Combines plan + implementation criteria with shipping readiness:

### 1. Problem-Solution Completeness
Does the final implementation fully address the original problem?

_(Same scale as Plan Review: Problem-Solution Alignment, but evaluated against actual code)_

### 2. Test Coverage & Quality
Are tests comprehensive and meaningful?

_(Same scale as Implementation Review: Test Existence, but more stringent for shipping)_

### 3. Code Quality
Would this pass review by someone unfamiliar with the project?

_(Same scale as Implementation Review: Independent Quality)_

### 4. Documentation
Are changes documented where needed?

| Score | Description |
|-------|-------------|
| 5 | All user-facing changes documented; README/docs updated; clear commit messages |
| 4 | Good documentation with minor gaps |
| 3 | Some documentation but notable omissions |
| 2 | Minimal documentation |
| 1 | No documentation for significant changes |

### 5. Shipping Readiness
Is this safe to ship?

| Score | Description |
|-------|-------------|
| 5 | No known issues; all tests pass; no security concerns; clean build |
| 4 | Minor known limitations documented; all critical paths tested |
| 3 | Some concerns but manageable; would want monitoring after ship |
| 2 | Notable risks that should be addressed before shipping |
| 1 | Critical issues that would cause problems in production |
