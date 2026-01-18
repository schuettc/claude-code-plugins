---
name: feature-audit
description: Runtime behavior auditing through systematic log injection. Use when user wants to understand what code is doing at runtime, debug complex flows, or audit a process.
argument-hint: "[process-to-audit]"
---

# Runtime Audit Command

You are executing the **RUNTIME AUDIT** workflow - a process that bridges static analysis with actual execution observation. Unlike static code analysis, this command actively injects logs, captures runtime data, and produces verifiable reports.

## Contents

- [Audit Target](#audit-target)
- [What Makes This Different](#what-makes-this-different)
- [File Organization](#file-organization)
- [Workflow Overview](#workflow-overview)
- [Phase Details](#phase-details)
- [Log Injection Design](#log-injection-design)
- [Error Handling](#error-handling)

---

## Audit Target

$ARGUMENTS

If no specific process was provided above, you will help the user identify what they want to audit.

---

## What Makes This Different

**Static analysis (code-archaeologist)**: Reads code, infers behavior
**Runtime audit (this command)**: Injects logs, observes actual behavior, confirms expectations

**Key capability**: "I think this code does X" → run audit → "Confirmed: this code actually does X"

This provides evidence-based verification rather than inference.

---

## File Organization

All audit artifacts are stored in:

```
docs/audits/
├── registry.json                   # Index of all audits
└── [audit-id]/
    ├── report.md                   # Final audit report
    ├── session.json                # Audit metadata
    ├── injections.json             # Track all injected logs for cleanup
    └── logs/
        └── captured-[timestamp].log
```

**Key Principles**:
- Every injected log is tracked in `injections.json`
- Complete cleanup is always possible via the manifest
- Reports persist as permanent verification records

---

## Workflow Overview

This command orchestrates a 7-phase workflow:

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Target Identification | User describes process to audit, identify entry points |
| 2 | Code Exploration | Map execution paths, identify strategic log points |
| 3 | Injection Strategy | Plan non-invasive logs, get user approval |
| 4 | Log Injection | Add approved log statements (tracked for cleanup) |
| 5 | Runtime Capture | User executes process, capture log output |
| 6 | Analysis & Report | Analyze data, verify behavior, generate report |
| 7 | Cleanup | Remove injected logs, restore code to pre-audit state |

---

## Phase Details

### Phase 1: Target Identification

**See**: [target.md](target.md)

- Understand what process/behavior to audit
- Identify entry points and key questions
- Create audit session with unique ID
- Initialize audit directory structure

### Phase 2: Code Exploration

**See**: [exploration.md](exploration.md)

- Map execution paths from entry points
- Identify data flows and transformations
- Find strategic locations for log injection
- Document assumptions to verify

### Phase 3: Injection Strategy

**See**: [injection-strategy.md](injection-strategy.md)

- Plan specific log statements for each location
- Use language-appropriate patterns
- Present plan to user for approval
- Explain what each log will reveal

### Phase 4: Log Injection (Requires Approval)

**See**: [injection-active.md](injection-active.md)

- Inject approved log statements
- Mark each with `// AUDIT-INJECTED` comment
- Track all changes in `injections.json`
- Verify code still compiles/runs

### Phase 5: Runtime Capture

**See**: [runtime-capture.md](runtime-capture.md)

- User chooses capture method (paste or direct execution)
- Capture log output from process execution
- Store captured data in audit directory
- Support multiple capture rounds if needed

### Phase 6: Analysis & Report

**See**: [analysis.md](analysis.md)

- Parse captured log output
- Compare actual behavior to expectations
- Identify verified behaviors vs unexpected findings
- Generate comprehensive audit report

### Phase 7: Cleanup

**See**: [cleanup.md](cleanup.md)

- Remove all injected log statements
- Verify code is restored to pre-audit state
- Update audit session as complete
- Present final report summary

---

## Log Injection Design

### Safety Principles

- All injected code tagged with language-appropriate marker
- Tracked in `injections.json` for reliable cleanup
- User approval required before any code modification
- Logs are observational only (no behavior changes)

### Language-Agnostic Templates

| Language | Log Pattern | Marker |
|----------|-------------|--------|
| TypeScript/JS | `console.log('[AUDIT:id:N]', data);` | `// AUDIT-INJECTED` |
| Python | `print(f'[AUDIT:id:N] {data}')` | `# AUDIT-INJECTED` |
| Go | `fmt.Printf("[AUDIT:id:N] %v\n", data)` | `// AUDIT-INJECTED` |
| Rust | `println!("[AUDIT:{}:{}] {:?}", id, n, data);` | `// AUDIT-INJECTED` |
| Java | `System.out.println("[AUDIT:id:N] " + data);` | `// AUDIT-INJECTED` |

Language is detected from file extension and appropriate template applied.

### Rollback Guarantee

Every modification is tracked in `injections.json`:
```json
{
  "auditId": "auth-flow-001",
  "injections": [
    {
      "id": 1,
      "file": "src/auth/login.ts",
      "line": 42,
      "originalContent": "",
      "injectedContent": "console.log('[AUDIT:auth-flow-001:1]', user);",
      "purpose": "Log user object at login entry"
    }
  ]
}
```

Cleanup phase uses this manifest to restore exact original state.

---

## Runtime Capture Options

User chooses per-audit:

| Method | Use When | How It Works |
|--------|----------|--------------|
| **Paste output** | Complex environments, CI/CD, remote systems | User runs process externally, pastes logs back |
| **Direct execution** | Local development, simple commands | Command runs via Bash, captures stdout/stderr |

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Cannot identify entry point | Ask user for more specific process description |
| Injection causes compile error | Rollback that injection, try different approach |
| No logs captured | Verify process was executed with injected code |
| Partial cleanup failure | Show remaining injections, offer manual cleanup |
| Audit directory missing | Create `docs/audits/` if needed |

---

## Integration Points

- **Complements feature workflow**: `/feature-plan` → implement → `/feature-audit` → `/feature-ship`
- **Standalone use**: Audit any existing process without feature context
- **Works with code-archaeologist**: Static analysis → audit to verify assumptions

---

## Philosophy: "Trust, But Verify"

Static analysis tells you what code *should* do.
Runtime auditing shows you what code *actually* does.

This command helps you:
- Verify assumptions about code behavior
- Debug unexpected runtime behavior
- Document actual execution paths
- Build confidence before shipping

---

**Let's identify what you want to audit!**
