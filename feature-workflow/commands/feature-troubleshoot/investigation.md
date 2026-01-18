# Phase 3: Investigation

## Systematic Hypothesis Testing

Test hypotheses in order, gathering evidence for each.

### Investigation Loop

For each hypothesis (in order):

```
1. State what we're testing
2. Gather evidence
3. Evaluate evidence
4. Update hypothesis status
5. If not found, move to next
6. If stuck, ask for help
```

## Evidence Gathering Methods

### 1. Code Reading

```
Reading relevant code to understand:
- Logic flow
- Error handling
- Edge cases
- Recent changes (git blame)
```

### 2. Log Analysis

```
Examining logs for:
- Error messages
- Stack traces
- Timing information
- Data values at failure point
```

### 3. Test Execution

```
Running tests to verify:
- Failing test confirms issue location
- Passing test rules out hypothesis
- New test can isolate problem
```

### 4. Targeted Logging (Audit-Style)

When needed, inject temporary logs:

```
For quick investigation:
console.log('[DEBUG] value at line 42:', variable); // TEMP-DEBUG

Remove after investigation!
```

### 5. Interactive Debugging

Ask user to run with debugger:

```
## Debugger Investigation

Can you run with these breakpoints?

1. Set breakpoint at `src/auth/login.ts:42`
2. Trigger the failure
3. When stopped, check:
   - Value of `user` variable
   - Value of `isValid` variable
4. Share the values

This will help confirm/rule out H1.
```

### 6. Environment Comparison

Compare working vs non-working:

```
- Same code version?
- Same configuration?
- Same data?
- Same environment?
```

## Update Hypothesis Status

After each investigation step:

```json
{
  "id": "H1",
  "status": "ruled_out",
  "evidence": "Validation logic is correct, tested with debug log",
  "investigatedAt": "[timestamp]"
}
```

Status options:
- `untested` - Not yet investigated
- `investigating` - Currently gathering evidence
- `confirmed` - Root cause found!
- `ruled_out` - Evidence shows this isn't the cause
- `inconclusive` - Need more data

## Present Progress

After each hypothesis tested:

```
## Investigation Progress

### H1: Validation function returns false ❌ Ruled Out
**Evidence**: Added debug log, validation returns true for test input
**Conclusion**: Validation is working correctly

### H2: User object missing required field 🔍 Investigating
**Current action**: Checking user object structure at failure point

---

**Remaining hypotheses**: H3, H4, H5
```

## When Root Cause Found

If hypothesis confirmed:

```
## Root Cause Identified!

**Hypothesis H2 Confirmed**: User object missing `emailVerified` field

### Evidence
```
[DEBUG] user object: { id: 123, email: "test@example.com" }
Expected field 'emailVerified' not present
```

### Location
`src/auth/login.ts:67` - accessing `user.emailVerified` on object without field

### Cause
Migration script didn't backfill `emailVerified` for existing users

---

**Next**: Proceed to resolution?
```

## Ask for Help Mechanism

### Trigger Conditions

Ask for help when:

1. **Exhausted hypotheses**: Tested all without finding cause
2. **Conflicting evidence**: Evidence doesn't make sense
3. **Stuck investigating**: Can't gather needed evidence
4. **Time threshold**: Significant time without progress

### How to Ask

```
## Seeking Additional Input

I've investigated [N] hypotheses but haven't identified the root cause.

### What I've Tried

| Hypothesis | Result |
|------------|--------|
| H1: Validation issue | Ruled out - validation correct |
| H2: Missing field | Ruled out - all fields present |
| H3: Stale cache | Inconclusive - can't access cache |

### What I'm Stuck On
[Specific blocker or confusion]

### What Would Help
- [ ] Access to [specific resource]
- [ ] Answer to: [specific question]
- [ ] Domain expertise in [area]

### Questions for You

1. Have you seen similar issues before?
2. Any context I might be missing?
3. Are there other areas I should look?
4. Should we try a different approach?
```

## Generate New Hypotheses

If all hypotheses ruled out:

```
## Generating New Hypotheses

Original hypotheses exhausted. Based on investigation:

### New Evidence Gathered
- [What we learned during investigation]
- [Patterns observed]
- [Unexpected findings]

### New Hypotheses

| ID | Hypothesis | Based On |
|----|------------|----------|
| H6 | [New theory] | [Evidence that suggests this] |
| H7 | [New theory] | [Evidence that suggests this] |

Continue investigation with new hypotheses?
```

## Integration with Feature-Audit

If runtime evidence is needed:

```
## Runtime Evidence Needed

To test H3, we need to observe actual runtime behavior.

Options:
1. **Quick debug logging** - Add temporary logs manually
2. **Full audit** - Run `/feature-audit` for comprehensive observation

Which approach do you prefer?
```

## Store Investigation Results

Update session with all findings:

```json
{
  "investigation": {
    "startedAt": "[timestamp]",
    "hypothesesTested": 3,
    "rootCauseFound": true,
    "confirmedHypothesis": "H2",
    "evidence": ["[evidence 1]", "[evidence 2]"],
    "ruledOut": ["H1", "H3"],
    "timeline": [
      {"time": "...", "action": "Tested H1", "result": "Ruled out"},
      {"time": "...", "action": "Tested H2", "result": "Confirmed"}
    ]
  }
}
```

**Output**: Root cause identified with evidence, or new hypotheses formed
