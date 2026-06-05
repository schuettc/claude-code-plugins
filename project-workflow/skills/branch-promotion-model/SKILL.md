---
name: branch-promotion-model
description: Use when bootstrapping a new repo's CI, setting up deploy workflows, deciding what branch a feature PR should target, or whenever someone proposes "auto-deploy prod on every main merge". Captures the feat → dev → main promotion model with separate Deploy Dev (push to dev) and Deploy Prod (push to main), and links the templates that implement it.
---

# Branch promotion model

## The rule

Adopt a real promotion flow across every deploying repo:

```
feature/<id>  →  PR into dev  →  merge fires Deploy Dev
                                          ↓
                                       soak / validate
                                          ↓
                  PR `dev` into `main`  →  merge fires Deploy Prod
```

- `dev` is the integration branch. Feature PRs target `dev`, not `main`.
- `main` is production. The only PRs to `main` are `dev → main` promotion PRs.
- `Deploy Dev` workflow trigger: `on: push: branches: [dev]`.
- `Deploy Prod` workflow trigger: `on: push: branches: [main]`.
- Keep `workflow_dispatch` on both as a manual escape hatch, **not** as the normal trigger.

For non-deploying repos in the same org (docs, templates, plugin bundles) — still create a `dev` branch and route feature PRs through it, even if no workflow fires. Uniform process across repos prevents "wait, where do I PR this?" friction.

## Why

**Real incident (2026-05-29, learning-with-court/platform).** The repo's initial setup had `Deploy Dev` AND `Deploy Prod` both triggering on push to `main`. A single feature merge auto-deployed to dev and prod in lockstep — no soak gate. The pattern looked safe until it wasn't:

- A correctness-fine feature (walker-post-lesson-summary) was promoted under that model.
- An unrelated CI/quota issue (workshop fetch hammering GitHub REST per file) surfaced mid-burst because cumulative PR + deploy activity exhausted the GitHub App installation's 15000/hr rate limit.
- Under the lockstep model, that would have failed *in prod*. Under the promotion model, it failed at the `dev → main` promotion PR — visible, recoverable, not a prod incident.

The promotion model didn't catch the API quota issue *per se* — but it gave a clean place to ship the *fix* for that issue (`workshop-fetch-rate-limit-fix`) onto `dev`, observe the deploy succeed in 1m13s with the new code, then deliberately promote to prod with confidence. That's the structural payoff: every fix gets a soak before prod, every prod deploy is a chosen moment, not a side effect.

The cost is one extra PR cycle per feature. Worth it.

## How to apply

### When bootstrapping a fresh repo

1. Create `main` (usual) and `dev` off `main`. Push both.
2. Drop in the workflows from `templates/github-workflows/`:
   - `deploy-dev.yml` triggers on `push: branches: [dev]`.
   - `deploy-prod.yml` triggers on `push: branches: [main]`.
   - `ci.yml` triggers on `pull_request: [dev, main]` — the **server-side gate**. The promotion soak only catches what's deployed; `ci.yml` is what blocks a red PR from merging in the first place. It's the enforceable third leg alongside the lefthook commit/push hooks (which have an escape path — `--no-verify`, or not running `lefthook install` — see `quality-stack-setup`).
   - All keep `workflow_dispatch` for manual reruns.
3. Enforce it server-side — this is what separates the promotion model from a naming convention. See the `github-repo-setup` skill for the exact `gh` commands: branch protection on `main` (PR required, `ci` a *required* status check, no direct push), `dev`/`prod` deploy environments, and **required reviewers on `prod`** — the literal mechanism behind "every prod deploy is a chosen moment." Without protection, nothing stops a direct push to `main` that skips the soak entirely.

### When migrating an existing repo from "merge to main = both envs"

The cutover order matters because the workflow file's trigger is read from the pushed commit:

1. Create `dev` off `main` and push it.
2. On a `chore/branch-promotion-model` branch, edit `deploy-dev.yml`'s trigger from `branches: [main]` → `branches: [dev]`.
3. PR that change into `main`. Merging triggers one no-op Deploy Prod (only the workflow file changed); after that, `main` deploys prod only.
4. Fast-forward `dev` to `main` so `dev` carries the new workflow config too. Push `dev`.
5. If a feature PR was in-flight against `main` mid-cutover, retarget it to `dev` (`gh pr edit <n> --base dev`) or close-and-reopen for a cleaner title.
6. From here on, the normal flow: feature → `dev` → soak/validate → `dev → main` PR → prod.

### When someone proposes "auto-deploy prod on every main merge"

Push back. The collapsed model looks cheap until the day a deploy needs to be staged or paused. The right move is the promotion model from the start; retrofitting later (as in the 2026-05-29 cutover) is more work than the small initial setup cost.

## Templates referenced

- `${CLAUDE_PLUGIN_ROOT}/templates/github-workflows/deploy-dev.yml`
- `${CLAUDE_PLUGIN_ROOT}/templates/github-workflows/deploy-prod.yml`
- `${CLAUDE_PLUGIN_ROOT}/templates/github-workflows/ci.yml` — the `pull_request` gate.

Customize the `secrets.*`, `with:` paths, smoke-check URLs, bundling steps, and `ci.yml`'s lint/test/build commands — keep the trigger blocks and concurrency groups as written. The GitHub-side enforcement (protection, environments, secrets) lives in the `github-repo-setup` skill.
