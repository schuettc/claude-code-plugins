# Phase 2: Security Review (Medium/Large Effort)

**Note**: For Low effort items, skip this phase and run `npm audit --audit-level=high` instead.

**AGENT**: `epcc-workflow:security-reviewer`

**CRITICAL**: This phase can BLOCK completion if Critical or High severity issues are found.

## Launch Security Reviewer

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

---

## Handle Security Results

**If BLOCKED (Critical/High issues found)**:
```
## Security Review: BLOCKED

Critical/High severity issues must be fixed before completion:

[List of issues with fixes]

Please fix these issues and run `/feature-ship [id]` again.
```
STOP the workflow here.

**If PASSED**:
```
## Security Review: PASSED

No Critical or High severity issues found.

Recommendations (optional fixes):
[Medium/Low issues if any]
```
Continue to Phase 3.

**Output**: Security review results
