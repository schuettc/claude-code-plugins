# Pre-commit Hook Compatibility

Projects with pre-commit hooks (skylos, fallow, ruff, prettier, husky, etc.) can interact poorly with autopilot's per-task-commit pattern:

- Each task's commit runs the hooks. Twenty tasks × a few seconds of hooks adds up.
- A hook failure breaks the subagent loop. The subagent sees `git commit` exit non-zero and reports BLOCKED.
- The temptation to use `--no-verify` is real but forbidden — see below.

## The `--no-verify` ban

The autopilot must never use `git commit --no-verify` (or its equivalents like `--no-gpg-sign`, `-c commit.gpgsign=false`). Pre-commit hooks exist for a reason; bypassing them ships regressions. This rule has no exceptions.

If a subagent's commit fails because a pre-commit hook rejected the change:

1. The subagent reports `DONE_WITH_CONCERNS` with the hook's stderr captured.
2. The orchestrator surfaces the failure to the user with the exact hook name and the offending lines.
3. The user decides: fix the offense (re-dispatch the subagent with the fix in scope) or escalate.

The autopilot never silently bypasses a hook.

## Suppressions are a last resort

Static analysis tools (fallow, skylos, ESLint, Pylint, Ruff, mypy, etc.) provide inline suppression directives:

- `// fallow-ignore-next-line complexity`
- `# skylos: ignore SKY-Q501`
- `// eslint-disable-next-line`
- `# noqa: E501`
- `# type: ignore[arg-type]`

These are **legitimate tools** for cases where the finding is genuinely a false positive or where the fix is worse than the suppression (e.g., a deliberately-coalesced state container, a parameterized SQL query that the linter mis-flags as injection). They are **not** a generic escape hatch for "I want this commit to pass."

The failure mode the autopilot has demonstrated in practice: hit a complexity finding → add `// fallow-ignore-next-line complexity` above the unchanged function → the gate goes green → repo-wide technical debt is unmoved. The "fix" was the silence, not the code.

**Before adding any suppression, the autopilot MUST:**

1. **Try to fix the finding first.** Most complexity findings extract cleanly into helpers. Most dead-code findings are actually dead. Most clone groups reduce to a shared function. Most type-ignore findings reflect a real type mismatch the suppression hides.

2. **If the fix is genuinely worse than living with the finding, write a justification.** Every suppression added by autopilot MUST have an adjacent comment explaining:
   - Why the finding is a false positive, OR
   - Why the refactor would be worse than the suppression (e.g., would scatter related mutations, would force premature abstraction, would violate a stated architectural constraint).

   "complexity" with no rationale is not a justification. A reader (or a future reviewer) must be able to evaluate the choice from the comment alone.

3. **Cap at 2 new suppressions per PR.** If a single feature needs more than two suppressions, the refactor pass was skipped or the feature is doing too much. Stop. Either split the work or do the refactor.

### Comment shape

Use a `# Why:` / `// Why:` line adjacent to the suppression:

```python
# Why: State is intentionally one container — splitting scatters
# mutations across the codebase for no maintainability gain.
# skylos: ignore SKY-Q501
class State:
    ...
```

```typescript
// Why: this function is the bridge between two type domains;
// extracting helpers would obscure the conversion rather than
// simplify it (see issue #214 for the explored alternatives).
// fallow-ignore-next-line complexity
function parseReleaseId(search: string): number | null {
  ...
}
```

A drive-by `// fallow-ignore-next-line complexity` above an unmodified function with no `// Why:` is exactly what the **reviewer prompt** will catch as a Critical Finding (FAIL verdict) — see `feature-workflow/templates/review-prompt-impl.md`. The autopilot will then be forced into a respond cycle to either refactor or justify.

### Legitimate examples in the wild

These ARE good suppressions (and would pass review):

- A `State` container with intentionally consolidated mutations, suppressed with a justification about scatter-cost.
- A bulk `IN`-clause SQL query that's safely parameterized, suppressed because the linter pattern-matches on string concat without seeing the parameterization.
- A test fixture with deliberately convoluted setup, suppressed because the test's whole purpose is to exercise the convoluted path.

The common thread: each one has an English-language explanation of why the rule doesn't apply here. Drive-by suppressions don't.

## Recommended project setup

If you use autopilot heavily, prefer running heavy linters (skylos full-SAST, fallow audit, ESLint-with-many-rules) in **CI only**, not as pre-commit hooks. Pre-commit is for quick local checks (formatting, basic syntax). Heavy analysis belongs in PR-level checks where:

- It runs once per push, not once per commit
- Output goes to the PR as a comment or check, not to the user's terminal
- Failure stops the PR, not the local workflow

For projects that already run a linter both as pre-commit AND in CI (e.g., now-playing's skylos pre-commit + skylos CI):

- Drop the pre-commit version. The CI version provides the gate; the pre-commit version is redundant cost.
- Or downscope the pre-commit version to a fast subset (e.g., skylos `agent pre-commit` mode rather than full SAST) and keep full analysis in CI.

## Bot comment noise in respond.md

If your CI runs many bot reviewers (skylos, dependabot, sonarcloud, gemini, codex), the PR thread fills with comments that aren't the structured review.

`respond.md` Step 2 filters by `## Plan Review` / `## Implementation Review` prefix so non-review bot comments don't pollute the verdict classifier. `wait-for-review.sh` uses the same prefix filter. If a bot's output is signal (e.g., a real security finding), surface it manually — autopilot's respond flow only processes the structured-review comments.

For dense PR threads, prefer running heavier bots as **status checks** rather than as PR comments. Status checks appear in the checks list (one row per check); they don't add comments to the conversation.
