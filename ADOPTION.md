# Adopting these plugins — bringing a project up to standard

**The overriding goal: AI-slop resistance.** These plugins exist to make a project structurally resistant to the low-quality code AI assistants (this one included) tend to generate — so what lands is clean, consistently organized, easy to understand and maintain, and every repo looks the same. The plugins are the guardrails and enforcement that protect against slop.

This marketplace is a **set of plugins that compose**, each owning one phase of a project's life. This doc is the orchestration layer: how they fit together, and the step-by-step for a **new** project and an **existing** one.

It lives at the repo root *on purpose* — orchestration that spans plugins must not live *inside* a plugin, because plugins can be disabled. (Claude Code has no "orchestrator skill" pattern, and a reference from one plugin into a disabled one dangles. A doc never does.)

## The plugin map

| Plugin | Owns | Lifespan | Entry |
|---|---|---|---|
| **project-workflow** | Standing a repo up (branches, CI, repo protection, install the quality tooling) | **one-shot → disposable** | `/project-init` |
| **engineering-standards** | Evergreen coding/ops standards (project-structure, GitHub API discipline, …) | forever, advisory | fires on situation |
| **quality-workflow** | Operating the quality tooling (verify, audit, triage) + the suppression rule | forever | `/quality-verify-hook`, `/quality-audit`, `/quality-unblock` |
| **feature-workflow** | The feature dev lifecycle (capture → plan → implement → review → ship) | forever | `/feature-init`, then `/feature-*` |
| **sprint-planner** | Backlog triage + sprint planning | forever | `/sprint-plan`, `/sprint-triage` |

**Dependency direction:** `project-workflow` declares the other standards plugins as dependencies, so installing the *setup* plugin pulls in the whole suite. The direction matters — nothing depends on `project-workflow`, so once a repo is set up you can disable it (see [Disabling the setup plugin](#disabling-the-setup-plugin)) and everything else keeps working.

## The anti-slop guardrails

Two kinds of guardrail, both required. **Mechanical** ones are deterministic and tool-enforced (you can't argue with them); **judgment** ones are advisory rules the agent consults for the things tools can't decide.

### Mechanical — the quality stack (yes, this includes git hooks)

| Guardrail | Python | TS/JS | Catches |
|---|---|---|---|
| Format | ruff format | prettier | inconsistent style (auto-fixed) |
| Lint | ruff | eslint | error-prone patterns, unused code |
| Type-check | mypy | tsc `--noEmit` | hallucinated APIs, wrong shapes |
| Static analysis | skylos | fallow | dead code, complexity, clones, secrets, AI regressions |
| Test + coverage | pytest `--cov` | vitest/jest `--coverage` | untested generated code |

The checks are defined **once** in a **`justfile`** (single source of truth). **lefthook** dispatches them by git stage and **CI** runs the same recipe — so local and CI can't drift. Three enforcement points (`project-workflow` installs them, `quality-workflow` operates them):

1. **pre-commit** (lefthook, every `git commit`) — fast, staged-file **auto-fixers** (format, lint `--fix`) + the static scan. Kept fast so nobody reaches for `--no-verify`.
2. **pre-push** (lefthook, every `git push`) — **`just verify`**: format-check, lint, type-check, test + coverage. The whole-project checks (which can't be scoped to staged files) caught **before code leaves the machine**, for humans and Claude alike.
3. **CI required check** (`ci.yml`, every PR) — the **unbypassable backstop**: runs the *same* `just verify` (+ build) on a clean env. Local hooks *can* be skipped (`--no-verify`, `lefthook install` not run); a required status check can't.

Why the overlap: fast feedback on commit, full verification before push, unskippable re-verification in CI — defense in depth, and because pre-push and CI invoke the identical `just verify`, "passed locally → passes in CI" holds by construction. Prove every layer fires with **`/quality-verify-hook`**. The standing rule governing all suppressions — every ignore carries an inline rationale — is `quality-workflow`'s `suppression-discipline`, enforced by `/quality-unblock`.

### Judgment — engineering-standards

Tools can't decide whether code is *well-organized* or *in the right place*. `engineering-standards` carries the advisory rules that shape that:

- **`project-structure`** — consistent layout + naming so every repo looks the same and generated code has one obvious home (feature-colocation, one-module-one-responsibility, no `utils`/`misc` junk drawers). This is the direct lever for "all our projects look the same."
- **`github-api-discipline`** — runtime GitHub fetch patterns (zipball, backoff).

> Reuse-don't-reinvent, dead code, over-complexity, and god-files are largely caught *mechanically* by skylos/fallow, so they aren't separate judgment skills — the judgment layer covers only what tooling genuinely can't (placement, organization, naming).

---

## Track A — New project

Top-to-bottom apply. Each phase names the driving skill.

**Phase 1 · Foundation** — `/project-init`
Creates `dev` off `main`; drops `deploy-dev.yml`, `deploy-prod.yml`, `ci.yml`; installs the `justfile` + `lefthook.yml` (then `lefthook install`). Detects an empty repo and lays it all fresh.

**Phase 2 · GitHub-side setup** — `github-repo-setup` (inside `/project-init`)
Create `dev`/`prod` environments, required reviewers on `prod`, environment-scoped secrets, OIDC trust, and branch protection with `ci` as a **required** check. *Do this before the first deploy* or the workflows fail "environment not found."

**Phase 3 · Prove the hooks** — `/quality-verify-hook`
Immediately after the hooks are installed. One command; asserts they fail on known-bad fixtures. Skipping this is how silent-pass hooks happen.

**Phase 4 · Baseline** — `/quality-audit`
A clean baseline snapshot to diff future audits against.

**Phase 5 · Feature tracking** — `/feature-init`
Creates `docs/features/`, `.feature-workflow.yml`, optional GitHub Actions AI review. Then every feature flows `/feature-capture → /feature-plan → /feature-implement → /feature-ship`.

**Phase 6 · Cadence** — `/sprint-plan` once you have a backlog and a deadline.

---

## Track B — Existing project

Same destination, but **front-load assessment** and route through the migration/audit paths the skills already carry. The plugins are adaptive — they detect what's present and fill only gaps.

**Phase 1 · Assess** — `/project-init` (detection) + `/quality-audit`
`/project-init` Step 1 reports what's already wired (dev branch? CI gate? protection? hooks?) and applies only the missing pieces. `/quality-audit` snapshots current code health — on an existing repo this is where the **debt surfaces** (grade card + findings).

**Phase 2 · Migrate the branch model (if needed)** — `branch-promotion-model`
If the repo already deploys on `main`, use the skill's **cutover order** (the workflow trigger is read from the pushed commit, so sequence matters). Not the same as the greenfield path.

**Phase 3 · Add the quality stack to existing code** — `quality-stack-setup` → `/quality-verify-hook`
Install hooks, then **verify they fire against your existing patterns**. Expect existing violations: `suppression-discipline` says sweep bare suppressions in passing; `/quality-unblock` triages what's blocking a commit.

**Phase 4 · Audit existing GitHub-API usage** — `github-api-discipline` (engineering-standards)
If the repo already fetches from GitHub at runtime, walk its **audit checklist** (zipball vs per-file, backoff, caching), ranked by payoff. This fires on its own when you touch such code.

**Phase 5 · Retrofit feature tracking** — `/feature-init`
Adds tracking without disturbing code; retroactively `/feature-capture` in-flight work. Then `/sprint-triage` to clean the backlog you now have visibility into.

The difference between the tracks: **new** is a straight apply; **existing** leads with `/quality-audit` + `/project-init` detection and uses the *migration/audit* paths — and `/quality-verify-hook` matters more, because you're adding hooks to a codebase that already contains the patterns they catch.

---

## Multi-repo: coordinating several repos

When several repos in one org are developed together (shared contracts, lockstep releases), stand up a **workspace** instead of juggling them separately: a thin coordination repo with each member nested as an independent, gitignored clone. `/project-init` offers this on-ramp (it delegates to `feature-workflow`'s `/feature-init --workspace`). From then on the workspace gives you an aggregated cross-repo dashboard, cross-repo **epics** (one child per member), contract-edit warnings, and `/feature-deploy` for producer-first releases.

Apply the standards in **two places**: the **workspace repo itself** (its own branch model + CI + quality stack, via `/project-init` at the root) and **each member** (run `/project-init` inside it — members stay independent repos with their own `dev → main`). Launch Claude at the workspace root so cross-repo edits never prompt. Day-to-day model: [`feature-workflow/skills/shared/workspace.md`](./feature-workflow/skills/shared/workspace.md).

---

## Disabling the setup plugin

`project-workflow` is **setup-only and disposable**. Once a repo is stood up, `/project-init` has nothing left to do. To stop it lingering, disable it *for that repo*:

- `/plugin` → disable `project-workflow`, **or**
- add to the project's `.claude/settings.json`:
  ```json
  { "enabledPlugins": { "project-workflow@schuettc-claude-code-plugins": false } }
  ```
  (takes effect next session; mid-session self-disable isn't supported)

This is safe because **nothing depends on `project-workflow`** — the evergreen plugins it pulled in (`engineering-standards`, `quality-workflow`, `feature-workflow`) stay enabled and keep working. The standards you keep consulting never lived in the disposable plugin.

## Cross-plugin seams

| Seam | Direction | How it's wired |
|---|---|---|
| Setup installs hooks → verify them | project-workflow → quality-workflow | `quality-stack-setup` hands off to `/quality-verify-hook` |
| No config found → how to get one | quality-workflow → project-workflow | graceful pointer in `/quality-verify-hook` (never hard-requires it enabled) |
| Failing hook → tech-debt epic | quality-workflow → feature-workflow | `/quality-unblock` DEFER → `/feature-capture` |
| Suppression rule | shared | `suppression-discipline` (rule) ↔ `/quality-unblock` (enforcer) |
| Runtime GitHub fetch | engineering-standards | `github-api-discipline` fires on situation, independent of setup |

The rule for all seams: **forward references** (from the disposable plugin into permanent ones) are fine; **reverse references** into the disposable plugin are always graceful pointers, never hard invocations.
