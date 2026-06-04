---
name: project-init
description: Apply project-workflow standards to a repo — feat → dev → main promotion model + CI gate, GitHub repo setup (branch protection, environments, secrets, OIDC), and the quality stack (skylos/fallow via lefthook + a shared justfile, run identically in CI). Detects current state and applies only the *missing* patterns, so it works on both new repos and existing ones. Use when setting up a new project or bringing an existing one up to standard.
user-invocable: true
---

# Initialize project standards

You are applying the **project-workflow** standards to the current repo — either first-time setup for a new project, or bringing an existing repo up to standard. This skill detects what's already in place and applies only the gaps, so it's safe to run against either. Run through this checklist.

## Step 1: Detect the current state

Read the current repo's state quickly:

- `git remote -v` — confirm it's a real git repo with a remote.
- `git branch -a` — does a `dev` branch already exist?
- `ls .github/workflows/` — what CI is wired today? Is there a `pull_request` gate or only deploy-on-push?
- `ls lefthook.yml justfile .pre-commit-config.yaml 2>/dev/null` — does the quality stack already exist (lefthook+just, or legacy pre-commit)?
- `gh api repos/{owner}/{repo}/branches/main/protection 2>/dev/null` and `gh api repos/{owner}/{repo}/environments 2>/dev/null` — is `main` protected, do `dev`/`prod` environments exist? (A 404 means not set up.)
- **Languages** — don't key on a root manifest alone; a repo can have code without one. Detect:
  - Python → any `*.py`, **or** a `pyproject.toml`/`pytest.ini`/`setup.cfg` *anywhere* (incl. subdirs). `git ls-files '*.py' '*pyproject.toml' '*pytest.ini'`.
  - Node/TS → `package.json` (and `tsconfig.json` for a real TS project; a handful of stray `.ts` files with no `package.json` are scripts/templates, **not** a project — don't wire TS tooling for them).
  - Note the **layout**: is there a root manifest, or does the code live in subdirs (monorepo / plugin-style)? This decides where the quality stack points (see Finding-3 handling in `quality-stack-setup`).
- **Deployability** — does anything actually deploy? Look for IaC (`cdk.json`, `*.tf`, `serverless.yml`, `Dockerfile` + a host), a deploy script, or existing deploy workflows. **If nothing deploys, this is a library / CLI / docs / plugin-marketplace repo** → apply the branch model + CI gate, and **skip** `deploy-{dev,prod}.yml`, environments, secrets, and OIDC entirely.

Report what you found before asking anything. Don't apply patterns that are already in place, and don't propose deploy machinery for a repo with nothing to deploy.

## Step 2: Ask which patterns to apply

Use AskUserQuestion with one multi-select question covering only the *missing* patterns:

| Pattern | Skill to load for the rationale | Templates |
|---|---|---|
| Branch promotion model (`dev` + CI gate; **+ deploy workflows only if the repo deploys**) | `branch-promotion-model` | `github-workflows/ci.yml` always; `deploy-{dev,prod}.yml` only if deployable |
| GitHub repo setup — branch protection always; **environments/secrets/OIDC only if deployable** | `github-repo-setup` | none — `gh` commands |
| Quality stack (lefthook hooks + justfile, shared with CI) | `quality-stack-setup` | `justfile`, `lefthook.yml` (+ `fallowrc.example.json` if TS) |

**If the repo deploys:** the promotion model and repo setup are paired — the deploy workflows reference `environment:` / `secrets.*` that repo setup creates, so recommend them together or the first deploy fails. **If it doesn't deploy** (library/CLI/docs/marketplace — per the Step 1 deployability probe): offer only `dev` + `ci.yml` + branch protection; do **not** propose `deploy-{dev,prod}.yml`, environments, secrets, or OIDC.

This skill is **setup only**. Evergreen coding standards live elsewhere and don't belong in this one-shot menu — e.g. when the repo fetches from GitHub at runtime, the `github-api-discipline` skill (engineering-standards plugin) fires on its own; you don't wire it here.

Skip any pattern that's already in place. If nothing is missing, say so and stop.

## Step 3: For each selected pattern, in order

### Branch promotion model

1. If no `dev` branch exists locally and on `origin`: `git push origin refs/remotes/origin/main:refs/heads/dev` to create it.
2. Always copy `${CLAUDE_PLUGIN_ROOT}/templates/github-workflows/ci.yml` into `.github/workflows/` — the PR gate applies to every repo. **Don't overwrite existing files without confirming.**
3. **Only if the repo deploys** (Step 1 deployability probe): also copy `deploy-dev.yml` + `deploy-prod.yml`, and surface their CUSTOMIZE comments — cloud auth (AWS_ROLE_ARN_DEV/PROD by default), build/deploy steps, smoke-check URLs. Then flag that they reference `environment:` / `secrets.AWS_ROLE_ARN_*` that don't exist yet → do the **GitHub repo setup** section before the first deploy. **If it doesn't deploy, skip this step entirely** — no deploy workflows.
4. Adapt `ci.yml` to the repo: point its steps at the real check command (`just verify`), and for a non-deploy repo drop the `build` step if there's nothing to build. For Python-in-subdirs (no root manifest), make the steps run the subdir suites (see `quality-stack-setup`).
5. Note the suggested next move: make the change on a branch, PR into `main` (still the source of truth at setup time), and merge — that's the cutover. From then on, feature PRs target `dev`.

### GitHub repo setup (protection, environments, secrets, OIDC)

Load the `github-repo-setup` skill for the rationale and the exact `gh`/`gh api` commands. This is mostly **GitHub-side configuration, not files** — walk the user through it rather than copying templates. Do **not** run these silently; they change repo settings, so show each command and let the user run it (or confirm before you do).

**Branch protection applies to every repo. Environments / secrets / OIDC are deploy-only — skip them for a non-deploying repo.**

1. **Always — branch protection** on `main` (PR required, `ci` status check required, ≥1 approval, no force-push/deletion) and a lighter version on `dev` (PR + `ci` required). The `ci` check must have run at least once before it can be marked required — so land `ci.yml` first, let one PR run it, then enable the requirement.
2. **Deploy repos only —** create the `dev` and `prod` environments; add **required reviewers** to `prod` and a deployment-branch policy limiting `prod` to `main` (and `dev` to `dev`). This is what makes the promotion model's "deliberate prod deploy" real.
3. **Deploy repos only —** set **environment-scoped** secrets (`AWS_ROLE_ARN_DEV` on `dev`, `AWS_ROLE_ARN_PROD` on `prod`), not repo-scoped, so prod creds are only reachable from the reviewer-gated environment.
4. **Deploy repos only —** if using OIDC (the templates do), set up the cloud trust scoped to `…:environment:prod` / `:environment:dev`, not just the repo. The skill has the AWS trust-policy snippet.

### Quality stack

Load the `quality-stack-setup` skill for the full rationale. The model: a **`justfile`** holds the checks (single source of truth), **lefthook** dispatches them by git stage, and CI runs the same `just verify` — so local and CI can't drift. Install steps:

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/justfile` and `${CLAUDE_PLUGIN_ROOT}/templates/lefthook.yml` to the repo root.
2. Adjust to the project's languages: recipes auto-detect Python (`pyproject.toml`) / TS-JS (`package.json`); delete the language commands not used, set the `kiosk` TS dir in `lefthook.yml`, point `test` at the project's runner. Detect the languages from Step 1 and tailor rather than asking blindly.
3. (TS) Copy `${CLAUDE_PLUGIN_ROOT}/templates/fallowrc.example.json` to the TS dir as `.fallowrc.json`; adjust ignores.
4. Install + enable, and add to the project README:
   ```bash
   brew install just lefthook   # or: cargo install just; npm i -D lefthook
   lefthook install
   ```
5. Confirm `ci.yml` is present and runs `just verify` (it's installed with the promotion model) — that's the unbypassable backstop and the parity anchor. It must be a **required status check** (see the GitHub repo setup section).
6. Suggest adding to project `CLAUDE.md`: a "Quality stack" section — lefthook runs fixers on commit + `just verify` on push; CI runs the same; no `--no-verify`; suppressions need an inline rationale (point at the `suppression-discipline` skill).

### Verify and hand off (do this whenever the quality stack was installed)

The install is not done until the hooks are *proven to fire*:

1. **Run `/quality-verify-hook`** (quality-workflow) — stages known-bad fixtures and asserts the hook fails. A hook that doesn't fail on bad input is not a hook.
2. **Run `/quality-audit`** (quality-workflow) for a baseline snapshot. On an existing repo this surfaces the debt the new gates will start enforcing.
3. Point the user at the `suppression-discipline` skill (quality-workflow) for the standing rule, and `/quality-unblock` for when a hook later blocks a commit.

## Step 4: Summarize

- List what was applied (path of each file written + edited).
- List what still needs the user's manual customization (with the specific TODOs).
- Note the cross-plugin next steps that were handed off (`/quality-verify-hook`, `/quality-audit`, and `/feature-init` if they want feature tracking — see the repo's top-level `ADOPTION.md` for the full sequence).
- Suggest the next concrete action: typically "create a `chore/project-standards` branch, commit these, PR it into `main` to bring the standards in."
- Once setup is complete and verified, mention that `project-workflow` is a setup plugin — they can disable it for this repo via `/plugin` if they don't want `/project-init` lingering (the evergreen standards live in the other plugins, which stay enabled).

## Notes

- Don't push or commit on the user's behalf — let them review the staged changes.
- TypeScript projects: use **fallow** for the dead-code / complexity / duplication scan, and keep **skylos in `agent pre-commit` mode** for the security/secrets layer — that mode scans staged TS/JS/C#/JSON, *not just Python*, so it earns its place on a TS repo. Skip only skylos's *full Python audit* (that lives in `/quality-audit`). Never wire skylos behind a `*.py` glob on a TS repo — it'll silently scan nothing useful and confuse everyone.
- **Existing / legacy repo:** expect a large findings backlog (hundreds–thousands). Wire the scanners **new-only** so they gate what's introduced and merely *report* the backlog without blocking every commit — then plan an incremental cleanup. Full details + exact flags in the "Existing / legacy repo: gate new, fix old incrementally" section of `quality-stack-setup`.
- A critical failure mode when adapting the `lefthook.yml` template (especially for a monorepo): keeping the auto-fixers (prettier/eslint, ruff) but **dropping the static-analysis scans** (`py-scan`/`ts-scan`). The scans are the load-bearing AI-slop guardrail — pre-commit without them only formats. After customizing, confirm both `skylos` and `fallow` scan commands are still present and pointed at the real source dirs, and that `/quality-verify-hook` proves each fires.
- If the user is in a docs-only repo (no `package.json`, no `pyproject.toml`), only apply the branch promotion model — quality hooks would be ceremony with no value.
