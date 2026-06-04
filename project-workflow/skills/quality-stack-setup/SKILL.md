---
name: quality-stack-setup
description: Use when setting up a repo's lint / static-analysis / test tooling — wiring lefthook git hooks (pre-commit auto-fixers + pre-push full verify) and a justfile that is the single source of truth both the hooks and CI call, so local checks and CI can't drift. Language-agnostic: ruff/skylos for Python, prettier/eslint/fallow for TS/JS, same pattern for any language. Installs the tooling; ongoing operation lives in quality-workflow (/quality-audit, /quality-unblock, /quality-verify-hook) and the standing suppression rule in suppression-discipline.
---

# Quality stack setup

## The stack (language-agnostic)

The point of this stack is **AI-slop resistance**: deterministic guardrails so generated code can't land unformatted, untyped, dead, duplicated, or untested. The tools change per language; the guardrail categories don't.

| Guardrail | Python | TS/JS | Catches the slop symptom |
|---|---|---|---|
| **Format** | ruff format | prettier | inconsistent style (auto-fixed) |
| **Lint** | ruff | eslint | error-prone patterns, unused code |
| **Type-check** | mypy | tsc `--noEmit` | hallucinated APIs, wrong shapes |
| **Static analysis** | skylos | fallow | dead code, complexity, clones, secrets, AI regressions |
| **Test + coverage** | pytest `--cov` | vitest/jest `--coverage` | untested generated code |

Other languages wire the same categories (golangci-lint + gofmt, clippy + rustfmt, …).

## The architecture: one definition, three callers

The checks are defined **once**, in a **`justfile`**. Everything else just calls those recipes, so local and CI run identical commands with the project's own pinned tools — parity is structural, not maintained.

- **`just verify`** = `format-check` + `lint` + `typecheck` + `test` (+coverage). The full gate.
- **`just fix`** = auto-format + lint-`--fix`. The fast pre-commit layer.

Three callers, earliest first:

1. **pre-commit** (lefthook) — fast **auto-fixers** on *staged files* (format, lint `--fix`) + the staged-file static scan (skylos/fallow). Fixes what it can; kept fast so nobody reaches for `--no-verify`.
2. **pre-push** (lefthook) — runs **`just verify`**: the whole-project gate (type-check + tests + coverage can't be scoped to staged files, so they belong here, not on every commit). Catches slop **before it leaves your machine**, for humans and Claude alike.
3. **CI required check** (`ci.yml`) — runs the **same `just verify`** as the unbypassable backstop. Local hooks can be skipped (`--no-verify`, `lefthook install` not run); a required status check cannot.

Because pre-push and CI invoke the *identical* `just verify`, "passed locally → passes in CI" holds by construction. Prove the hooks actually fire (a hook that doesn't fail on bad input is not a hook) with `/quality-verify-hook`.

> **Why lefthook + just, not the pre-commit framework:** the pre-commit framework installs tools into its own pinned envs, which can drift from the versions CI uses — the exact "passed locally, failed in CI" failure we're killing. `just`-calls-`uvx`/`pnpm` uses the project's pinned tools everywhere. And whole-project checks (typecheck, full test suite) don't fit pre-commit's per-file model. lefthook (fast, parallel, language-agnostic, single binary) dispatches stages and calls the shared `just` recipes — the right tool for this shape.

## Why

**Real working setup (`now-playing` repo).** skylos's `agent pre-commit` mode is built for AI-assisted development — it scans staged files for AI-introduced regressions (security, secrets, prompt-injection, dependency hallucinations); fallow does the equivalent for TS/JS. The original gap that motivated all this: a Phase-3 cleanup regressed on a `gh pr merge` because the local hook never fired on that path. The fix that actually closes it is the **CI required check** running `just verify` — the merge can't complete until it's green — backed by lefthook catching it earlier on commit/push.

## How to apply

### Install the stack

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/justfile` and `${CLAUDE_PLUGIN_ROOT}/templates/lefthook.yml` to the repo root.
2. Adjust both to the project's languages: the recipes auto-detect Python (`pyproject.toml`) and TS/JS (`package.json`); delete the language commands you don't use, fix the `kiosk` TS dir in `lefthook.yml`, and point `test` at your runner. The tools need their config present — `ruff`/`mypy` read `pyproject.toml`, `eslint`/`tsc` need their configs, `prettier` is configless by default.
   - **Subdir / monorepo layout (no root manifest):** the justfile's `[ -f pyproject.toml ]` guards check the *repo root*. If code lives in subdirs (each with its own manifest) and there's no root one, the guards are false and `just verify` **silently passes without checking anything** — the no-op gate this stack exists to prevent. Edit the recipes to `cd` into each subdir (e.g. `cd packages/api && uv run pytest`), then **run `/quality-verify-hook`**, which stages a known-bad fixture and will catch a recipe that no-ops instead of failing.
3. Install the tools once and enable the hooks:
   ```bash
   brew install just lefthook   # or: cargo install just; npm i -D lefthook
   lefthook install             # wires .git/hooks → lefthook
   ```
   Add these to the project README so contributors do the same.
4. Make sure `ci.yml` (from the branch-promotion-model templates) is present and calls `just verify` — that's the unbypassable backstop and the parity anchor. Mark its `ci` job a **required status check** (see `github-repo-setup`).
5. Document the rules in the project `CLAUDE.md`:
   > **Quality stack:** `lefthook` runs auto-fixers on commit and `just verify` on push; CI runs the same `just verify`. Don't bypass with `--no-verify`. Suppressions require an inline rationale — see the `suppression-discipline` skill.

### Existing / legacy repo: gate new, fix old incrementally

A repo with history almost always has a large backlog of findings (slay-the-spire had ~2160). If the hooks blocked on the whole backlog, **every commit would fail** and the team would reach for `--no-verify` — defeating the stack. So on an existing repo the rule is **gate new, report old**: the scanners fail only on findings you *introduce*; the inherited backlog is reported but never blocks. This is a property of *how you invoke the scanners*, so wire them new-only:

- **fallow** (TS/JS dead-code / complexity / duplication) → `npx fallow audit --changed-since HEAD` — scopes the gate to the diff; inherited findings are excluded. In CI use `--changed-since <base-sha>` against the PR base.
- **skylos** (security / secrets / high-signal AI regressions on staged **TS/JS/C#/JSON — not just Python**) → `uvx skylos agent pre-commit .` — the `agent pre-commit` mode is conservative by design and only surfaces new, high-confidence issues, so the backlog's low-signal noise stays quiet. (skylos's *full* audit is Python-centric and belongs in `/quality-audit`, not the hook.)

Then the backlog is a separate, non-blocking workstream — **this is the plan for a legacy repo**:

1. **Add the gates first** (this PR) — stops the bleeding; no *new* slop can land.
2. **Snapshot the backlog** with `/quality-audit` so it's visible and tracked.
3. **Burn it down incrementally** — fix inherited findings in their own PRs over time (not a flag-day); each fix shrinks the next audit's number.

Tuning that made it usable on slay-the-spire: pick skylos's `agent pre-commit` mode (not full audit) so backlog false-positives stay quiet; scope fallow with `.fallowrc.json` (ignore tests / dist / build-output / vendored / docs); pin fallow as a devDep for reproducible, fast runs; and document both — with the tuning knobs (`skylos --conf`, `.fallowrc.json`) and a `/quality-audit` pointer — in the project `CLAUDE.md`. **Local prereq:** committers need `uv` (for `uvx skylos`) alongside lefthook/just; fallow auto-installs via npm.

Verify the new-vs-old behavior empirically before declaring done: a clean commit must **pass** (scanners report the backlog but exit 0), and a deliberately-bad new change must **block** (exit 1). The pre-commit/pre-push gates can still be skipped with `--no-verify`; to make them unbypassable on the PR diff, add a CI job running `fallow audit --changed-since <base>` + `skylos --diff-base <base>`.

### After installing — verify and hand off

- **Run `/quality-verify-hook`** (quality-workflow) immediately. It stages a known-bad fixture and asserts the hook fails — the only way to know a silently-misconfigured gate isn't waving everything through.
- **Run `/quality-audit`** (quality-workflow) for a baseline snapshot — on an existing repo this surfaces the debt the gates will start enforcing.
- For the standing rule on suppressions (every `# skylos: ignore` / `# noqa` / `// eslint-disable` carries a rationale), see **`suppression-discipline`**; when a hook blocks a commit, **`/quality-unblock`** triages it.

## Templates referenced

- `${CLAUDE_PLUGIN_ROOT}/templates/justfile` — the single source of truth for checks (`verify`, `fix`, and sub-recipes).
- `${CLAUDE_PLUGIN_ROOT}/templates/lefthook.yml` — git-hook dispatcher (pre-commit fixers + pre-push `just verify`).
- `${CLAUDE_PLUGIN_ROOT}/templates/github-workflows/ci.yml` — CI backstop that runs the same `just verify`.
- `${CLAUDE_PLUGIN_ROOT}/templates/fallowrc.example.json` — fallow config for the TS scan.

## Related

- `quality-workflow` — operates the installed stack: `/quality-verify-hook` (prove the hooks fire), `/quality-audit` (health snapshots), `/quality-unblock` (triage a failing hook), `suppression-discipline` (the standing rule).
