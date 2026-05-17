---
name: feature-autopilot
description: End-to-end autopilot for driving a captured feature from idea.md through to merged PR. Chains feature-plan, feature-review-plan, feature-implement, feature-review-impl, and feature-ship with reviewer gates between phases. Auto-advances on PASS/CONDITIONAL PASS, pauses on FAIL. Use when the user says "ship feature X", "autopilot X", "drive X end-to-end", or hands over a feature ID with intent to complete it.
user-invocable: true
---

# Feature Autopilot

End-to-end runbook for taking an `idea.md` entry in `docs/features/<id>/` and landing the change on the configured base branch. Chains the existing per-phase skills, gates on the configured reviewer between phases, and auto-advances when the reviewer is happy.

This skill **does not replace** `feature-plan`, `feature-implement`, `feature-review-plan`, `feature-review-impl`, or `feature-ship`. It calls them in order and adds the wait/classify/auto-advance logic between phases.

## When to use

- User says "ship feature X", "autopilot X", "drive X end-to-end"
- User wants the full pipeline run without per-phase prompting
- An idea is captured and ready to plan + ship without further design discussion

## When NOT to use

- The plan needs design discussion → use `/feature-plan` directly first, then optionally autopilot from review onward
- The user is iterating on a single phase (e.g. just responding to review feedback) → use the per-phase skill directly
- No `idea.md` exists → run `/feature-capture` first
- The user wants a different review path than what's configured — edit the `review:` field in the feature's `idea.md` frontmatter (`external` / `internal` / `skip`) BEFORE running autopilot.

## Preconditions

Verify in this order before starting:

1. **`docs/features/<id>/idea.md` exists.** If not: tell the user to run `/feature-capture` first.
2. **Working tree is clean** on the configured base branch. Run `git status` — if anything unrelated is modified or untracked, ask the user before doing anything (don't auto-commit). Rationale: `feature-plan` branches off current HEAD, so a dirty tree drags unrelated work onto the feature branch.
3. **Local base branch is in sync with origin.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/skills/feature-autopilot/scripts/check-base-sync.sh" <base-branch>
   ```
   Exit semantics:
   - `0` — in sync, proceed
   - `1` — local is **ahead** of origin (unpushed work). **Pause and surface to user.** Branching off an ahead-base means the upcoming PR will include those unpushed commits, which is almost certainly not what the user wants. Recommend: push first OR investigate which commits don't belong on the base.
   - `2` — local is behind origin. Run `git pull origin <base>` and re-check.
   - `3` — diverged. Manual resolution required; do not proceed.
   - `4` — usage error (typo in base name, branch doesn't exist locally, etc.).

   This catches the "parallel Claude Code session left unpushed commits" failure mode.
4. **Read `.feature-workflow.yml`** for the `reviewer:` setting. The autopilot adapts:
   - `reviewer: gemini` or `reviewer: codex` — review gates are active. The `feature-review.yml` GitHub Action fires on the `plan-review` / `impl-review` label and posts a comment classifiable by `wait-for-review.sh`.
   - `reviewer: none` — review gates are skipped. Autopilot goes plan → implement → ship without polling for external review.
5. **Read `.feature-workflow.yml`** for the `base_branch:` setting (default `main`). Use this as the merge target.

## Steps

### 1. Plan

```
/feature-workflow:feature-plan <id>
```

Creates `docs/features/<id>/plan.md` with implementation steps, test approach, acceptance criteria, and open questions.

**Gate before moving on.** Read the plan back to yourself. Does the step list match the idea's intent? Any obvious gaps or scope creep? If the plan looks wrong, stop and surface it to the user — don't proceed to review/implement a bad plan. Edit `plan.md` directly or re-run the skill.

### 2. Plan review (skip if `reviewer: none`)

```
/feature-workflow:feature-review-plan <id>
```

Creates the feature branch, opens a draft PR, and applies the `plan-review` label. The CI reviewer picks up the label, runs against the plan, and posts a comment prefixed `## Plan Review` with a `### Verdict: PASS|CONDITIONAL PASS|FAIL` line.

**Don't idle-wait — poll:**

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/feature-autopilot/scripts/wait-for-review.sh" <PR#> plan
```

Blocks on `gh pr checks --watch` and classifies the verdict. Exit semantics:

- **0 — PASS / CONDITIONAL PASS**: auto-advance to Step 3 (implement). **Do NOT chase Should-fix items after a clean pass** — recommendations can be filed as follow-up backlog items if material (see "Defer to backlog" in `respond.md`).
- **1 — FAIL**: **auto-respond.** The whole point of autopilot is to drive through review cycles without manual intervention. Invoke `/feature-workflow:feature-review-plan <id> --respond` immediately, push the changes, and loop back to wait-for-review. See "FAIL handling" below for the retry cap and escalation rules.
- **2 — workflow failure / timeout / no review comment**: pause. Diagnose with `gh run list --branch feature/<id>` and `gh run view <run-id>`. Common causes: missing `GEMINI_API_KEY` / `OPENAI_API_KEY` secret, transient reviewer error, required check failing unrelated to the review. Once fixed, re-trigger by removing and re-adding the `plan-review` label.

### FAIL handling — auto-respond loop

Autopilot's job is to drive review cycles, including FAIL → respond → re-review. Default cap: **2 consecutive FAILs on the same phase before pausing for the user.**

```
FAIL #1 → run --respond → push → re-poll
FAIL #2 → run --respond → push → re-poll
FAIL #3 → STOP. Surface findings to user, ask for direction.
```

The cap exists because if the reviewer rejects the same plan/implementation twice after revisions, the issue is probably one of:
- A genuine design tradeoff the user needs to weigh in on
- A reviewer-implementer disagreement that needs human arbitration
- Scope creep the autopilot can't resolve via defer-to-backlog

When invoking `--respond` autonomously, the autopilot should:
- Use the **Defer to backlog** classification freely for findings that expand scope past the current `idea.md` — this is the autopilot's main escape valve. See `respond.md` for the classification matrix.
- Use **Disagree** sparingly. Autopilot disagreement should be reserved for findings that contradict the plan's stated constraints or ask for code that already exists. When unsure, prefer Agree (fix it) or Defer (capture for later).
- After 2 FAILs, stop and print: the verdict line, Summary, Critical Findings, and a one-line note on which classifications were tried each round. Ask the user: continue with `--respond` (override the cap), override the verdict ("ship anyway — I disagree with finding X"), or halt.

The cap is per-phase. Plan review and impl review have independent counters; a clean impl review after 2 plan-review FAILs is fine.

### 3. Implement

```
/feature-workflow:feature-implement <id>
```

Executes `plan.md` step by step. Between steps: run the relevant tests, then mark the step complete via `/feature-workflow:tracking-progress`.

**Guardrails during implementation:**
- If a step's scope drifts, use `/feature-workflow:guarding-scope` before expanding. Scope creep is the #1 reason shipments stall.
- If blocked, add a Progress Log entry in `plan.md` describing the blocker, then surface to the user. Don't silently work around.
- Never proceed to review with a failing test suite. If a pre-existing failure blocks progress, that's a scope call — discuss with the user.

### 4. Implementation review (skip if `reviewer: none`)

```
/feature-workflow:feature-review-impl <id>
```

Pushes the implementation to the existing feature branch and swaps the label from `plan-review` to `impl-review`. The CI reviewer runs against the diff and posts a `## Implementation Review` comment with the same `### Verdict:` convention.

**Poll the same way:**

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/feature-autopilot/scripts/wait-for-review.sh" <PR#> impl
```

Exit semantics identical to Step 2 — 0 auto-advances to Step 5, 1 triggers the auto-respond loop (cap 2 FAILs before pausing — see "FAIL handling" above), 2 diagnoses CI.

### 5. Pre-ship checklist

Before invoking `feature-ship`, verify:

- [ ] Project test command (e.g. `venv/bin/pytest tests/`, `npm test`) is green
- [ ] Every box in `plan.md` → Implementation Steps is checked
- [ ] Working tree is clean (`feature-ship` refuses dirty)
- [ ] If the change touches a stable public API surface called out in the project's `CLAUDE.md`, downstream consumers are updated or noted

If anything in the checklist is red, pause and surface it.

### 6. Ship

```
/feature-workflow:feature-ship <id>
```

Writes `docs/features/<id>/shipped.md`, commits it, pushes the branch, marks the PR ready (non-draft), merges it, and deletes the branch. Cleans up locally on the base branch.

After merge, the dashboard moves the feature from In Progress → Completed automatically.

## Loop diagram

```
plan ─► review-plan ─► implement ─► review-impl ─► pre-ship ─► ship
              │ ▲                       │ ▲
              │ │ wait-for-review       │ │ wait-for-review
              │ │   0  → advance        │ │   0  → advance
              │ │   1  → auto-respond ──┤ │   1  → auto-respond ──┐
              │ │       (cap 2/phase)   │ │       (cap 2/phase)   │
              │ │   2  → diagnose ──────┤ │   2  → diagnose ──────┤
              │ └────────  3rd FAIL: pause for user  ─────────────┘
```

## Auto-advance rules at review gates

- **Exit 0 (PASS / CONDITIONAL PASS)** — advance immediately. Don't chase Should-fix nits after a clean pass; material recommendations can become **backlog items via the "Defer to backlog" classification in `respond.md`** (see Step 5/8 of the respond flow).
- **Exit 1 (FAIL)** — **auto-respond.** Run `--respond` for the current phase, classify findings (Agree / Disagree / Already addressed / Defer to backlog / Deferred), push, and re-poll. Cap at 2 consecutive FAILs per phase before pausing for human input — see "FAIL handling" in Step 2 above.
- **Exit 2 (workflow failure / timeout / no comment)** — stop. Diagnose CI with `gh run list --branch feature/<id>` and `gh run view <run-id>`. Once fixed, re-trigger the review by removing and re-adding the label.

Also stop and ask if:
- The plan has non-obvious design tradeoffs the user should weigh in on
- A step introduces a breaking change to the project's stable public API
- Tests need fixtures/data outside the repo
- The pre-ship checklist surfaces anything red

For everything else, proceed without narration beyond the per-skill output and a one-line "wait-for-review exit N" update at each gate. The user knows the runbook; they don't need a play-by-play.

## Reviewer push-back: scope creep vs. defer to backlog

If the reviewer comes back asking for a substantial expansion that goes beyond the original `idea.md` scope, **do not silently expand the feature**. The respond flow (`shared/respond.md`) has an explicit "Defer to backlog" classification for this — capture a new backlog item via `/feature-capture`, reply on the thread pointing to the new feature ID, resolve the thread, and continue with the current feature's stated scope.

This keeps each feature focused and prevents the autopilot from getting stuck in a multi-feature refactor disguised as one PR.

## Recovery patterns

- **Plan came out wrong** → edit `plan.md` directly and re-run `/feature-workflow:feature-implement`. It picks up from the first unchecked box.
- **Implementation stuck mid-step** → add a Progress Log entry, discuss with user, amend the plan if needed, resume.
- **Tests pass locally but CI fails** → pull the CI log (`gh run view`), diagnose, push a fix commit to the feature branch, re-run from the appropriate gate.
- **PR merge conflicts** → resolve on the feature branch (`git fetch origin <base> && git rebase origin/<base>`), push, re-run `feature-ship`.
- **Reviewer keeps requesting expansion** → defer to backlog (see above), don't expand the feature.
- **Shipped something broken** → `shipped.md` is just a marker; the merge commit is the hard-to-reverse part. Revert via a new PR, then re-open the feature (remove `shipped.md`) and re-plan.

## Reviewer-mode adaptations

The autopilot's behavior at each review gate is driven by the **effective** review mode for the feature being processed:

| Effective mode | Step 2 (plan review) | Step 4 (impl review) |
|---|---|---|
| `external_gemini` / `external_codex` | Active — apply label, wait-for-review polls CI | Active — same |
| `external_default` (feature says external, project says none) | **Error** — surface to user; can't dispatch without a configured reviewer | Same — error |
| `internal` | Dispatch internal-review subagent → post comment → wait-for-review polls comments | Same — post impl-review comment, same poll |
| `skip` | Skip review gate entirely; advance to implement | Skip; advance to ship |

The effective mode is computed per-feature using:
- Project default from `.feature-workflow.yml` (`reviewer:` setting)
- Per-feature override from `idea.md` frontmatter (`review:` field)

See `feature-workflow/skills/shared/lib/effective_review.py` for precedence rules.

**Important:** `wait-for-review.sh` works identically across external and internal modes. Internal-review comments use the same `## Plan Review` / `## Implementation Review` headers and `### Verdict:` line that the external CI reviewer posts. No special flag is needed.

For `internal` mode, the autopilot's FAIL → respond loop also works unchanged: the respond flow reads PR comments, classifies findings, replies, and pushes — exactly as for external review. The subagent re-runs on the next round because the orchestrator detects the new commits and dispatches it again.

## Worktree Isolation (mandatory)

Every time the autopilot dispatches a subagent that may write to the working tree or do git operations, the dispatch MUST pass `isolation: "worktree"` to the Agent tool. The harness creates a temporary git worktree, runs the subagent there, and returns the worktree path on completion.

**Applies to:**
- Implementer subagents (subagent-driven-development pattern)
- Fix subagents (after a review surfaces issues)
- Child autopilots dispatched by epic dispatch (Plan 3 / v9.8.0)
- Any subagent the orchestrator instructs to `git commit`, `git push`, or `git checkout`

**Does NOT apply to:**
- Reviewer subagents — read-only, no git ops, no isolation needed
- Subagents that only read files (research, exploration)

**Why:** even when only one autopilot is "running," the user may open another Claude Code session against the same repo. Worktree isolation removes the entire class of "two agents in one tree clobber each other on branch switches" bugs. The now-playing 2026-05-16 incident — Feature B's uncommitted implementation overlaid by Feature C's branch checkout in a shared tree — is the canonical example.

**Cost:** ~1-2 seconds for `git worktree add` per subagent, plus per-worktree setup (venv, node_modules) that varies by project. Acceptable in exchange for eliminating clobber bugs.

There is no opt-out. The autopilot does not check a config flag before isolating. If a project's worktree setup is painfully slow, fix it at the project level (shared venv via `uv`, pnpm content-addressable store, etc.) rather than disabling isolation.
