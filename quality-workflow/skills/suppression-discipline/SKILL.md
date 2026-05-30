---
name: suppression-discipline
description: The rule for suppressing static-analysis findings in any language — every suppression carries an inline rationale, and bare suppressions are a quality failure to fix. Use when someone adds or proposes a lint/analysis ignore (# skylos: ignore, # noqa, # type: ignore, # fallow-ignore, // eslint-disable, @ts-ignore, #[allow(...)], //nolint, etc.), proposes bypassing hooks with --no-verify, or when reviewing code that contains suppressions. Complements /quality-unblock, which triages a failing hook and enforces the per-PR cap.
---

# Suppression discipline

## The rule

Every suppression of a static-analysis finding — in **any language** — must carry an **inline rationale on the same line or directly above it**. A bare suppression is a quality failure to fix, not a workaround.

Canonical forms, by ecosystem:

| Directive | Language / tool | Required rationale form |
|---|---|---|
| `# skylos: ignore SKY-XXX` | Python (skylos) | `— <reason>` suffix or `# Why:` line above |
| `# noqa: E501` | Python (ruff/flake8) | `# Why:` line above |
| `# type: ignore[code]` | Python (mypy/pyright) | `— <reason>` on the same line |
| `# fallow-ignore` | TS/JS (fallow) | `// Why:` line above |
| `// eslint-disable-next-line rule` | TS/JS (eslint) | `-- <reason>` after the rule, or `// Why:` above |
| `// @ts-expect-error` / `@ts-ignore` | TypeScript | description text on the same line |
| `#[allow(clippy::x)]` | Rust | `// Why:` line above |
| `//nolint:linter` | Go (golangci-lint) | `// <reason>` after the directive |

The mechanism differs per tool; the rule does not. Example:

```python
# skylos: ignore SKY-D216 — url built from a hardcoded constant; host is not user-controlled
```
```typescript
// Why: third-party type is wrong here; upstream issue #4421 tracks the fix
// @ts-expect-error
```

## Why

It's trivial to silence a finding and never come back. The inline rationale forces the next reader to either **trust** the suppression (specific, defensible reason) or **rip it out** (vague-or-missing reason → the finding was real). A suppression without a reason is indistinguishable from "the linter was in my way," which is exactly the regression this discipline exists to prevent.

This is the same principle the whole quality stack enforces end to end: lefthook blocks the commit/push and the CI required check blocks the merge, and a defensible rationale is the only sanctioned way through. `--no-verify` and `LEFTHOOK=0` are not — they bypass the gate entirely rather than justifying a single finding.

## How to apply

### When you see a bare suppression in code

Either:
- **Restore the rule** — delete the suppression and fix what it flagged, or
- **Add the rationale** — a one-sentence reason why the rule's *application at this site* is wrong (not why the rule shouldn't exist).

Bare suppressions older than this rule are quality debt — sweep them in passing when you touch the file.

### When someone proposes `--no-verify` / `LEFTHOOK=0`

Push back unless there's a documented operator-escape rationale (e.g. a CLAUDE.md that explicitly documents `LEFTHOOK_EXCLUDE=bundle-dev,synth-dev` for a specific missing-token case). Otherwise the hook is firing for a reason — fix the issue or write a defensible per-site suppression.

### When a hook is actively failing and you need to triage

Use **`/quality-unblock`**. It walks each finding and offers FIX / SUPPRESS (requires a `# Why:`) / DEFER, refuses bare suppressions, and caps suppressions per PR (the autopilot's impl-review prompt flags overruns). This skill is the *standing rule*; `/quality-unblock` is the *interactive enforcer* when a commit is blocked.

## Related

- `/quality-unblock` — interactive triage of a failing hook; enforces this rule per-finding and caps suppressions per PR.
- `/quality-audit` — surfaces suppressed-vs-active counts so suppression growth is visible over time.
- `project-workflow`'s `quality-stack-setup` — installs the lefthook hooks + `just verify` gate this discipline governs.
