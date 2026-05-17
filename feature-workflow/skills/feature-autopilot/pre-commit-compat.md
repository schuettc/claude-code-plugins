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
