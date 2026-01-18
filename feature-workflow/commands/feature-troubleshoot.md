---
name: feature-troubleshoot
description: Systematic debugging mode - Debug problems methodically with hypothesis-driven investigation
version: 1.0.0
argument-hint: "[problem-description]"
---

# Troubleshooting Command

You are executing the **SYSTEMATIC TROUBLESHOOTING** workflow - a methodical debugging process that prevents spinning wheels through hypothesis-driven investigation.

## Contents

- [Problem Context](#problem-context)
- [What Makes This Different](#what-makes-this-different)
- [Workflow Overview](#workflow-overview)
- [Phase Details](#phase-details)
- [Ask For Help Mechanism](#ask-for-help-mechanism)
- [Error Handling](#error-handling)

---

## Problem Context

$ARGUMENTS

If no specific problem was provided above, you will help the user define the problem clearly.

---

## What Makes This Different

**Ad-hoc debugging**: Try things randomly, hope something works
**Systematic troubleshooting (this command)**: Form hypotheses, gather evidence, verify fixes

**Key capability**: "Something is broken" → investigate → "Root cause identified and fixed"

This provides structured debugging rather than trial and error.

### Relationship to Feature-Audit

| Command | Mode | Purpose |
|---------|------|---------|
| `/feature-audit` | Proactive | "Verify this works as expected" |
| `/feature-troubleshoot` | Reactive | "This is broken, help me fix it" |

Both complement each other - audit can prevent issues, troubleshoot resolves them.

---

## Workflow Overview

This command orchestrates a 5-phase workflow:

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Problem Definition | Clearly define what's wrong and expected behavior |
| 2 | Hypothesis Formation | Generate possible causes ranked by likelihood |
| 3 | Investigation | Gather evidence to test hypotheses |
| 4 | Resolution | Apply fix based on evidence |
| 5 | Verification | Confirm the fix works and problem is resolved |

---

## Phase Details

### Phase 1: Problem Definition

**See**: [feature-troubleshoot/problem-definition.md](feature-troubleshoot/problem-definition.md)

- Gather problem details from user
- Establish expected vs actual behavior
- Identify when the problem started (if known)
- Document reproduction steps
- Scope the problem

### Phase 2: Hypothesis Formation

**See**: [feature-troubleshoot/hypothesis.md](feature-troubleshoot/hypothesis.md)

- Generate possible causes
- Rank by likelihood
- Identify evidence needed to test each
- Create investigation plan
- Track hypothesis status

### Phase 3: Investigation

**See**: [feature-troubleshoot/investigation.md](feature-troubleshoot/investigation.md)

- Systematically test hypotheses
- Gather evidence (logs, code reading, testing)
- Update hypothesis rankings based on evidence
- Use audit-style log injection if needed
- Ask for help if stuck

### Phase 4: Resolution

**See**: [feature-troubleshoot/resolution.md](feature-troubleshoot/resolution.md)

- Propose fix based on evidence
- Get user approval
- Apply the fix
- Document what was changed

### Phase 5: Verification

**See**: [feature-troubleshoot/verification.md](feature-troubleshoot/verification.md)

- Verify the fix works
- Confirm original problem is resolved
- Check for regressions
- Document resolution

---

## Ask For Help Mechanism

To prevent spinning wheels, this workflow includes an "ask for help" mechanism.

### When to Trigger

Ask the user for help when:

1. **No progress on hypothesis** - Investigated 3+ hypotheses with no root cause found
2. **Conflicting evidence** - Evidence doesn't match any hypothesis
3. **Access limitations** - Can't access needed logs, systems, or data
4. **Domain knowledge gap** - Problem requires specific domain expertise
5. **Time threshold** - Significant time spent without progress

### How to Ask

```
## Seeking Additional Input

I've investigated [N] hypotheses but haven't identified the root cause.

### What I've Tried
1. [Hypothesis 1] - Ruled out because [evidence]
2. [Hypothesis 2] - Ruled out because [evidence]
3. [Hypothesis 3] - Inconclusive, need more data

### What Would Help
- [ ] Access to [specific logs/system]
- [ ] Information about [specific question]
- [ ] Someone with [domain] expertise
- [ ] Permission to [specific action]

### Questions for You

1. Have you seen this issue before?
2. Any recent changes that might be related?
3. Can you provide [specific information]?
4. Should we escalate to [team/person]?
```

---

## Troubleshooting Session Storage

For complex issues, store session data:

```
docs/troubleshooting/
└── [session-id]/
    ├── session.json          # Problem definition, hypotheses, status
    ├── evidence/             # Captured logs, screenshots, test results
    └── resolution.md         # Final resolution documentation
```

---

## Integration Points

- **Use with feature-audit**: If you need runtime evidence, trigger `/feature-audit` for specific verification
- **Works with code-archaeologist**: For understanding unfamiliar code during investigation
- **Complements feature workflow**: Can debug issues found during `/feature-ship`

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Problem too vague | Ask clarifying questions in Phase 1 |
| No hypotheses match | Generate new hypotheses, ask for help |
| Can't reproduce | Ask for more specific reproduction steps |
| Fix doesn't work | Return to Phase 2, form new hypotheses |
| Multiple root causes | Address each systematically |

---

## Philosophy: "Debug with Evidence, Not Intuition"

This workflow ensures:
- Problems are clearly defined before debugging
- Investigation is systematic, not random
- Hypotheses are tested with evidence
- Fixes are verified, not assumed
- Knowledge is preserved for future issues

No more spinning wheels. No more "try this and see."

---

**Let's identify the problem and fix it systematically!**
