# project-workflow

**One-shot setup** for a new repo's standards, captured as Claude Code skills + templates so I don't have to re-derive them every time. Each pattern carries the *why* (lessons from a real incident or working setup) — not theoretical best practice.

This plugin is deliberately **setup-only and disposable**: once a repo is stood up, you can disable it (via `/plugin`) without losing anything ongoing. The *evergreen* standards — the ones you keep consulting while writing code — live in the [`engineering-standards`](../engineering-standards) and [`quality-workflow`](../quality-workflow) plugins, which `project-workflow` pulls in as dependencies. See the repo's top-level [`ADOPTION.md`](../ADOPTION.md) for how the plugins compose.

## What's in here

| | Lives in | Triggers when |
|---|---|---|
| **Entry-point skill** (`project-init`) | `skills/project-init/SKILL.md` | invoked by name (`/project-init`) |
| **Advisory skills** (behavioral guidance) | `skills/<name>/SKILL.md` | the situation matches the description |
| **Templates** (literal files to copy in) | `templates/<area>/` | referenced from skills or `/project-init` |

## Skills

`project-init` is the one you invoke; the rest fire on their own when the situation matches (the same two-tier split as `feature-workflow`).

- **`project-init`** *(user-invocable)* — interactively apply the right subset of these patterns to the current repo. Detects what's already in place and applies only the gaps, so it works on new repos and existing ones alike.
- **`branch-promotion-model`** — feat → dev → main with separate Deploy Dev (push to `dev`) and Deploy Prod (push to `main`), plus a `pull_request` CI gate. Soak gate before prod. Saved after a 2026-05-29 incident where "merge to main deploys both envs" collapsed the gate.
- **`github-repo-setup`** — the GitHub-side settings that make the promotion model *enforced* rather than convention: branch protection with a required `ci` check, `dev`/`prod` deploy environments, required reviewers on `prod`, and OIDC trust scoped to the environment. Without these the deploy workflows fail on first run and direct pushes to `main` bypass the soak.
- **`quality-stack-setup`** — language-agnostic install of the static-analysis + test stack. A `justfile` is the single source of truth for the checks; **lefthook** runs auto-fixers on commit and `just verify` on push; CI runs the *same* `just verify` — so local and CI can't drift. Installs the tooling, then hands off to `quality-workflow` to verify and operate it.

> **Moved out:** `github-api-discipline` (evergreen) now lives in [`engineering-standards`](../engineering-standards); the suppression rule now lives in [`quality-workflow`](../quality-workflow)'s `suppression-discipline`. Both are evergreen, so they don't belong in a disposable setup plugin.

## Templates

- `templates/github-workflows/deploy-dev.yml` and `deploy-prod.yml` — starting-point CI for the promotion model (push to `dev` deploys dev; push to `main` deploys prod).
- `templates/github-workflows/ci.yml` — the `pull_request` gate (build/test/lint); mark it a required status check so it actually blocks merges.
- `templates/justfile` — the single source of truth for checks (`verify`, `fix`, and `lint`/`typecheck`/`test`/`format-check` sub-recipes); called by both the pre-push hook and CI.
- `templates/lefthook.yml` — git-hook dispatcher: auto-fixers (ruff/prettier/eslint) + static scan (skylos/fallow) on pre-commit; `just verify` on pre-push.
- `templates/fallowrc.example.json` — sane fallow ignores (test files, docs).

## Adding a new pattern

1. Capture the lesson in a new skill: `skills/<kebab-name>/SKILL.md`. Lead with the rule, then **why** (link the real incident or working setup), then **how to apply**. Advisory skills get descriptive names; a new user-invocable action gets a `project-<verb>` name (mirroring `feature-init` / `feature-plan`).
2. If the lesson has a literal config/file artifact, drop it under `templates/<area>/` and reference it from the skill.
3. Bump the version in `.claude-plugin/plugin.json` and the marketplace entry in the parent `.claude-plugin/marketplace.json`.

This is a living catalog — every painful incident worth not repeating earns an entry.
