---
name: feature-troubleshoot:hypothesis
description: "Phase 2: Hypothesis Formation"
user-invocable: false
---

# Phase 2: Hypothesis Formation

## Generate Hypotheses

Based on the problem definition, generate possible causes:

### Categories of Causes

| Category | Examples |
|----------|----------|
| **Code Logic** | Wrong conditional, missing validation, incorrect calculation |
| **Data** | Corrupt data, missing field, wrong format |
| **State** | Race condition, stale state, memory leak |
| **Configuration** | Wrong env var, missing config, incorrect setting |
| **Dependencies** | Version mismatch, breaking API change, missing package |
| **Infrastructure** | Network issue, service down, resource exhausted |
| **Integration** | API contract changed, auth expired, rate limited |
| **User Error** | Wrong input, incorrect usage, missing prerequisite |

### Hypothesis Format

For each hypothesis:

```json
{
  "id": "H1",
  "category": "[category]",
  "description": "[Clear statement of potential cause]",
  "likelihood": "high|medium|low",
  "evidence_needed": "[What would confirm or rule this out]",
  "how_to_test": "[Specific actions to test this]",
  "status": "untested|investigating|confirmed|ruled_out"
}
```

## Rank by Likelihood

Consider factors when ranking:

### Higher Likelihood
- Matches error message/symptoms closely
- Related to recent changes
- In frequently modified code
- Common failure pattern

### Lower Likelihood
- Requires multiple things to fail
- Would affect more than observed
- In stable, well-tested code
- Never happened before

## Create Investigation Plan

Order hypotheses by:
1. Likelihood (high to low)
2. Ease of testing (quick checks first)
3. Potential impact (critical paths first)

```
## Investigation Plan

### High Priority (Test First)

**H1: [Description]** - High likelihood
- Evidence needed: [specific evidence]
- How to test: [specific steps]
- Time estimate: Quick check

**H2: [Description]** - High likelihood
- Evidence needed: [specific evidence]
- How to test: [specific steps]
- Time estimate: 5-10 min

### Medium Priority

**H3: [Description]** - Medium likelihood
- Evidence needed: [specific evidence]
- How to test: [specific steps]
- Time estimate: 10-15 min

### Low Priority (If Others Rule Out)

**H4: [Description]** - Low likelihood
- Evidence needed: [specific evidence]
- How to test: [specific steps]
- Time estimate: Extensive investigation
```

## Document Hypotheses

Store in session:

```json
{
  "hypotheses": [
    {
      "id": "H1",
      "category": "Code Logic",
      "description": "Validation function returns false for valid input",
      "likelihood": "high",
      "evidenceNeeded": "Check validation with test input",
      "howToTest": "Add log before/after validation, test with known good input",
      "status": "untested",
      "notes": ""
    },
    {
      "id": "H2",
      "category": "Data",
      "description": "User object missing required field",
      "likelihood": "high",
      "evidenceNeeded": "Inspect user object at failure point",
      "howToTest": "Log user object structure, compare to expected schema",
      "status": "untested",
      "notes": ""
    }
  ],
  "investigationOrder": ["H1", "H2", "H3", "H4"]
}
```

## Present to User

```
## Hypotheses

Based on the problem, here are possible causes ranked by likelihood:

### Most Likely

| ID | Hypothesis | Evidence Needed |
|----|------------|-----------------|
| H1 | Validation function returns false for valid input | Check validation logic |
| H2 | User object missing required field | Inspect object structure |

### Possible

| ID | Hypothesis | Evidence Needed |
|----|------------|-----------------|
| H3 | Cache returning stale data | Clear cache and retry |
| H4 | Race condition in async flow | Add timing logs |

### Less Likely

| ID | Hypothesis | Evidence Needed |
|----|------------|-----------------|
| H5 | Database connection timeout | Check DB logs |

---

**Investigation Plan**:
1. Start with H1 (quick validation check)
2. Then H2 if H1 ruled out
3. Continue down the list

Do these hypotheses make sense? Any others to add?
```

## Handle User Input

### If user suggests new hypothesis:
- Add to list
- Rank appropriately
- Update investigation plan

### If user disagrees with ranking:
- Adjust based on their domain knowledge
- They may know something that changes likelihood

### If user has additional context:
- Update problem definition if needed
- Re-evaluate hypotheses
- May rule out some hypotheses immediately

## Prepare for Investigation

Before moving to Phase 3:

1. Ensure at least 3 testable hypotheses
2. Have clear evidence criteria for each
3. Know how to test each one
4. Have investigation order established

**Output**: Ranked hypotheses with investigation plan
