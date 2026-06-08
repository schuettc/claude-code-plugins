# Multi-repo workspace for Claude Code + feature-workflow

**Status:** design spec (awaiting review)
**Date:** 2026-06-08
**Scope:** a generic, shippable system in `claude-code-plugins` for operating across several
interconnected repositories in one org as if they were one — locally (Claude Code) and in the
feature workflow (tracking + autopilot across repos). Written to work for *any* multi-repo project.

A running synthetic example is used throughout: an org `<org>` whose **`engine`** repo exposes
**`engine-api`** (a stable HTTP contract) consumed by **`app`** and **`cli`**; a shared **`tooling`**
repo used by every repo; and a library **`sdk`**.

---

## 1. Problem

Some systems are intentionally split into several repos that are nonetheless tightly
interconnected — a common shape:

- A **core service** (`engine`) exposes an **HTTP contract** (`engine-api`) that two or more
  **apps** (`app`, `cli`) consume.
- A **shared tooling** repo (`tooling`) — conventions, lint/format config, a private Claude Code
  plugin marketplace — is used by every repo.
- **Libraries** (`sdk`) are depended on by the core and others.

The repos are split on purpose (independent histories, CI, release cycles) but change together.

Two needs follow, and they must be solved together:

1. **Local setup.** Treat the repos you own as one: cross-repo reads/edits with **no permission
   friction**, shared topology context, but each repo keeps its own git history, CI, and releases.
2. **Feature workflow.** Track and *execute* features that span repos — including changes to a shared
   contract (update producer + consumers safely) and coordinated deploys — without breaking the
   single-repo flow that works today.

## 2. Goals / non-goals

**Goals**
- Generic and shippable in `claude-code-plugins`; usable by anyone for multi-repo work.
- Coexist with per-repo `feature-workflow` *and* other marketplaces (e.g. a team's private plugins) —
  **enable, don't duplicate**.
- Zero disruption to single-repo work: a member-only feature behaves exactly as today.

**Non-goals**
- Not a monorepo migration; not git submodules/subtree (members stay independent peers).
- Not automatic SHA pinning (optional add-on via `vcstool`, out of scope here).
- Does not replace each repo's own CI, reviewers, branch model, or PRs.

## 3. Background: the Claude Code mechanics this relies on

(From the Claude Code docs — permissions, large-codebases, memory, worktrees.)

- File reads/edits are friction-free **only inside the launch cwd's subtree**; outside → permission
  prompts. `permissions.additionalDirectories` grants file *access* to outside dirs **but does not
  load their `CLAUDE.md`/skills** (only the `--add-dir` flag does). → **Nest members inside the
  workspace cwd** so they're in-tree (no prompts, full CLAUDE.md loading), and address member git
  via `git -C <dir>` / `gh -R <owner/repo>`, both allowlisted.
- `CLAUDE.md` loads in tiers: parent (workspace root) automatically, child (per-member) on demand
  when Claude touches that repo. Perfect for "workspace topology + per-repo detail."
- Launching from a bare parent of several repos is otherwise discouraged because `git`/`gh` break at
  the parent — neutralized here by making the workspace itself a (tiny) git repo and allowlisting
  `git -C`/`gh -R`.

## 4. The workspace model

A **workspace repo**: a thin, real git repo that holds only coordination, with the member repos
nested inside it as ordinary, independent, **gitignored** clones. (This pattern is proven in
practice — a workspace repo whose `.gitignore` lists every member because each is an independent
repo tracked on its own.)

The workspace is **identified by its `.feature-workspace.yml` manifest, not by its name** — the
scaffolder defaults the repo/dir to `workspace`, but any name works, so an existing convention keeps
running unchanged.

### 4.1 Local + git layout

```
~/<workspace>/                   ← LOCAL workspace dir (a proj "project"; launch Claude here)
│                                  = a checkout of the workspace repo  <org>/workspace
├── .git/                        ← workspace repo's OWN git (tiny: coordination only)
├── .gitignore                   ← engine/ app/ cli/ tooling/ sdk/ + node_modules .claude/
├── README.md                    ← topology, live envs, deploy runbooks, cloud profile
├── CLAUDE.md                    ← workspace instructions + topology table
├── .feature-workspace.yml       ← the manifest (§5)
├── .feature-workflow.yml        ← the workspace repo's OWN feature config (workspace features + epics)
├── .claude/settings.json        ← allow: Bash(git -C *), Bash(gh -R *); enable the org's marketplace
├── scripts/clone-members.sh     ← one-command bootstrap (reads the manifest)
├── docs/                        ← cross-repo coordination docs (architecture, contracts, runbooks, ADRs)
│   └── features/               ← workspace features + cross-repo EPICS + aggregated DASHBOARD.md
│
├── engine/   ← member · producer (engine-api)   remote: <org>/engine  — independent repo
│   ├── .feature-workflow.yml    ← its own config
│   └── docs/features/           ← its own features + epic children
├── app/      ← member · consumer
├── cli/      ← member · consumer
├── tooling/  ← member · shared harness (its marketplace is enabled from the workspace .claude/)
└── sdk/      ← member · library
```

### 4.2 Git rules

- The workspace is a **real but tiny repo** committing only README / CLAUDE.md / manifest / config /
  `docs/features` / scripts. Members are **gitignored**, so `git status` at the root never sees
  member code (and `git add` can't accidentally embed a member as a gitlink).
- Each member is an **ordinary independent repo** — own remote, branches, CI, PRs, and **its own
  worktrees** (`engine/.worktrees/…`, registered in engine's `.git`, invisible to the workspace).
- Member operations from the root: `git -C <dir> …`, `gh -R <owner/repo> …` (allowlisted → no
  prompts). A human just `cd <member>` and works normally. `claude --worktree` from the root
  worktrees the *workspace*; member worktrees are created via the member's git.
- **Bootstrap / share:** `git clone <workspace> ~/<workspace> && cd ~/<workspace> && ./scripts/clone-members.sh`
  clones every member per the manifest. A teammate runs the same two commands.
- Integrates with an existing `proj`/tmux/worktree habit: the workspace dir is a `proj` project;
  launching there puts every member in the cwd subtree.

## 5. The manifest — `.feature-workspace.yml`

The machine-readable topology graph (nodes = repos, edges = contracts). The workspace
README/CLAUDE.md remains the human view; this is what the tooling reads.

```yaml
org: <org>
members:
  - { dir: engine,  repo: <org>/engine,  role: core, provides: [engine-api] }
  - { dir: app,     repo: <org>/app,     consumes: [engine:engine-api] }
  - { dir: cli,     repo: <org>/cli,     consumes: [engine:engine-api] }
  - { dir: tooling, repo: <org>/tooling, provides: [claude-harness, lint-config] }
  - { dir: sdk,     repo: <org>/sdk }
contracts:
  - { id: engine:engine-api,      owner: engine,  consumers: [app, cli], kind: http, note: "REST+SSE, stable" }
  - { id: tooling:claude-harness, owner: tooling, consumers: ["*"],       kind: tooling }
deploy:                          # optional ordered groups for coordinated releases
  - { group: engine-stack, dir: engine }
  - { group: app-stack,    dir: app, after: [engine-stack] }
```

It drives three things: **cloning members**, **warning on contract edits**, and **ordering** epic
children + deploys.

## 6. Feature organization (the rule)

> A change touching **one repo** lives in **that repo's** `docs/features/`. A change touching **only
> the workspace** (manifest, topology docs, deploy orchestration, coordination tooling) is a normal
> feature **in the workspace repo**. A change touching **several repos** is an **epic** in the
> workspace, decomposed into **one child per member repo** (each a normal feature in its own repo).
> The workspace dashboard **aggregates** all member backlogs + its own into one view.

| Scope | Doc lives in | Runs as |
|---|---|---|
| one member | that member's `docs/features/` | normal feature (in that repo) |
| only the workspace | workspace `docs/features/` | normal feature (in the workspace repo) |
| several repos | workspace `docs/features/` (an **epic**) | epic → one child per member repo |

- **IDs** are repo-namespaced only when crossing repos (`app:adopt-x`); bare inside a repo.
- The **epic doc** carries the cross-repo specifics: `children` (`repo:id`), `dependsOn` ordering,
  `contract`, `rollout` (expand/contract), `deploy_order`. It builds on feature-workflow's existing
  `epic`/`children`/`dependsOn` fields and epic-dispatch.

## 7. Contract coordination

Two homes, two jobs:

- **Standing contracts → the manifest.** `engine:engine-api → [app, cli]` is always true. Payoff:
  the tooling can **warn proactively** — *"you're editing `engine`'s server; `app` and `cli` consume
  that contract — promote this to an epic?"* — turning "I forgot the consumer" from a production
  incident into a prompt.
- **Per-change rollout → the epic.** The expand/contract steps, child ordering, and deploy order are
  specific to one change and live with it.

The rollout discipline (from the research) is the same shape for API contracts and for coordinated
infra stacks: **expand/contract** (producer adds the new shape first → consumers migrate → producer
removes the old shape last), **explicit ordering** (producer-first), and **a gate** (contract tests
/ `can-i-deploy`; for infra, decouple via parameter store, *not* live CloudFormation exports, which
deadlock). An epic that touches `engine-api` therefore becomes: `engine:expand-x` → `app:adopt-x` +
`cli:adopt-x` → `engine:contract-x`, deployed in `deploy_order`.

## 8. Plugin changes

**Placement.** **`feature-workflow` owns the multi-repo capability end-to-end** — workspace setup
(a `feature-init --workspace` mode), the manifest, and cross-repo tracking + execution
(features/epics/dashboard/autopilot). It already has `epic`/`children`/`dependsOn` + epic-dispatch
(parent → child autopilots in worktrees), so most of this is *teaching the existing machinery to
target a named repo*; and it's the dependency base everything else builds on, so one install delivers
the whole capability.

**`project-workflow` provides the on-ramp.** Its `project-init`, when it detects a repo that's part
of a larger multi-repo system (or when the user says so), **offers a multi-repo setup guide** and
hands off to feature-workflow's `--workspace` scaffolding — so people setting up a project the right
way are pointed at the workspace path instead of discovering it later. Guidance, not ownership.

**Tier 1 — Foundation (repo-awareness)**
1. **Workspace scaffolding** (`feature-workflow`): a `feature-init --workspace` mode that creates the
   workspace repo — `.feature-workspace.yml`, `.gitignore` (members), workspace `CLAUDE.md` skeleton
   + topology table, `.claude/settings.json` (allow `git -C`/`gh -R`; enable the org marketplace),
   `docs/features/`, `scripts/clone-members.sh`. **`project-workflow`'s `project-init` offers this as
   a guided on-ramp** when it detects a multi-repo system.
2. **Repo-scoped config/paths** (`feature-workflow`): a `resolve_target_repo()` helper (from cwd /
   explicit `--repo` / inference). Skills read *that repo's* `.feature-workflow.yml` and write *that
   repo's* `docs/features/` rather than a hardcoded root. *Fixes coupling C, D, I, J.*
3. **Repo-namespaced IDs**: `member:id` across repos; bare within. *Fixes M.*
4. **Aggregated dashboard**: `run_dashboard.py` gains a workspace mode — scan the workspace's
   `docs/features/` + every member's (from the manifest), render three lanes with epic→child
   rollup. The regen hook detects workspace context. *Fixes L.*

**Tier 2 — Epic execution across repos**
5. **Epic as coordinator**: a child names its repo; the epic doc gains `contract`, `rollout`,
   `deploy_order`. Builds on existing `children`/`dependsOn`.
6. **Repo-aware autopilot**: `check-base-sync.sh`, `submit.md`, `wait-for-review.sh`, `feature-ship`
   take a target repo: `git -C <dir>`, `gh -R <owner/repo>`. An epic dispatches each child's *normal*
   single-repo flow **in its member**, in `dependsOn`/`deploy_order` order, each child using its own
   repo's reviewer/CI. *Fixes A, B, E, F, G, K, N.*

**Tier 3 — Coordination (the payoff)**
7. **Contract-edit warning**: when a change touches a repo that `provides` a contract with
   consumers, warn + offer to promote to an epic (reads the manifest). The "I forgot the consumer"
   guardrail.
8. **Coordinated deploy** (optional/later): a `/feature-deploy <epic>` that walks `deploy:` groups in
   order with health gates between (the multi-stack case; parameter-store-decoupled).

## 9. Worked example: an `engine-api` field addition

1. You edit `engine`'s server from the workspace root. The contract-edit warning fires: *"app + cli
   consume `engine:engine-api` — make this an epic?"* → yes.
2. An epic `engine-api-add-x` is created in the workspace `docs/features/`, with children
   `engine:expand-x` → `app:adopt-x`, `cli:adopt-x` → `engine:contract-x`,
   `deploy_order: [engine-stack, app-stack]`.
3. Autopilot runs `engine:expand-x` in `engine` (branch/PR/review/CI all in that repo), merges +
   deploys; then `app:adopt-x` and `cli:adopt-x` in their repos; then (if needed) `engine:contract-x`.
   Each child is today's single-repo flow, pointed at the right repo.
4. The workspace dashboard shows the epic with per-child state across the three repos.

## 10. Decisions (all resolved)

- **Workspace identity & name** — identified by the `.feature-workspace.yml` manifest, not the name;
  scaffolder defaults to `workspace`, fully configurable.
- **Cross-repo docs** — "reach decides placement": docs serving 2+ repos live in the **workspace
  repo's `docs/`** (beside the epics + manifest); single-repo docs stay in that member; leave a stub
  link when migrating one up.
- **Plugin split** — `feature-workflow` owns the multi-repo capability end-to-end (setup + tracking +
  exec); `project-workflow`'s `project-init` offers a guided multi-repo on-ramp that hands off to it.
- **SHA pinning** — out of scope for v1; members float on their own branches. `vcstool .repos` is
  documented as the drop-in add-on if reproducible pinning is ever needed.

## 11. Implementation phasing

Each tier is a separate plan → implementation cycle:

- **Phase 1 = Tier 1** (scaffolding + repo-aware config/IDs + aggregated dashboard). Delivers the
  workspace + correct single-repo behavior from inside it. Validate on a fresh workspace repo.
- **Phase 2 = Tier 2** (repo-aware autopilot + epic-as-coordinator). Delivers cross-repo epics.
- **Phase 3 = Tier 3** (contract warning + coordinated deploy). Delivers the guardrails + deploy.
