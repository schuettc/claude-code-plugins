# Feature-Workflow Foundations: State, Assignee, Epics, Internal Review, Parallel Dispatch

**Date:** 2026-05-15
**Status:** Draft (awaiting approval)
**Plugin:** `feature-workflow`

---

## Context

The `feature-workflow` plugin currently models a feature's life with three artifacts (`idea.md` → `plan.md` → `shipped.md`) and a linear pipeline (capture → plan → review-plan → implement → review-impl → ship). This shape has carried us through dozens of features, but real-world backlogs surface gaps:

- **No way to "stop the clock"** on items we've started but can't finish (waiting on a vendor, decision, dependency). They drift between in-progress and abandoned with no honest place to live.
- **No tombstones.** Items we've decided not to do, or that got merged into a different effort, either sit forever in the backlog or get deleted (losing history).
- **No ownership signal.** Who is on the hook for each item? The dashboard is silent.
- **No first-class grouping.** Big efforts that fan out into 6 sub-features have to be tracked as 6 unrelated items, with no place to capture the umbrella goal or coordinate dispatch.
- **No knob for "this is a 10-line fix, skip external review."** The reviewer config is project-wide; small items pay the full CI-review tax.
- **Autopilot under-uses parallelism.** Subagents and worktrees are available; the autopilot rarely reaches for them. For epic-scale work, that leaves a lot of throughput on the table.

This spec is a **foundational, mostly additive** change. The goals:

1. Introduce **state** (paused / superseded / abandoned / active) overlaid on the existing lifecycle.
2. Add **assignee** to surface ownership.
3. Add a first-class **epic** concept that groups features and supports parallel/sequential dispatch.
4. Strengthen **dependency markers** to make wave dispatch reliable.
5. Add per-feature **internal review** opt-out from the external reviewer.
6. Document **subagent + worktree** patterns in autopilot for epic dispatch and respond loops.

Backward compatibility: every change is additive at the frontmatter level. Existing features without the new fields behave exactly as today. No data migration is required.

---

## 1. State Model

State is **orthogonal to lifecycle**. Lifecycle is still determined by file presence (`idea.md` → backlog, `+plan.md` → in_progress, `+shipped.md` → completed). State is a single frontmatter field on `idea.md`:

```yaml
state: active      # default if absent
state: paused      # work started, waiting on something external
state: superseded  # replaced by another feature; tombstoned
state: abandoned   # decided not to do; tombstoned
```

### Required companion fields

| State | Required field | Format |
|---|---|---|
| `paused` | `pausedReason: "Waiting on X"` | free-form string |
| `superseded` | `supersededBy: <feature-id>` | references another feature |
| `abandoned` | `abandonedReason: "Why we dropped it"` | free-form string |

Validation rules (enforced by `feature-state` skill and the dashboard generator):

- `superseded` without `supersededBy` → error
- `supersededBy` references must exist on disk → soft warning (allows pre-capture)
- Cannot mark `completed` features as `superseded` or `abandoned` (ship time-machine is silly)
- `state` transitions are unrestricted otherwise — users can resume from any tombstone

### Effective dashboard placement

| Lifecycle | State | Section |
|---|---|---|
| backlog | active | **Backlog** |
| in_progress | active | **In Progress** |
| completed | active | **Completed** |
| backlog or in_progress | paused | **Paused** (new section) |
| backlog or in_progress | superseded | **Archive** (collapsed `<details>` block) |
| backlog or in_progress | abandoned | **Archive** (collapsed `<details>` block) |

`feature-status` and `checking-backlog` **exclude archive items by default**; pass `--archive` to surface them. Paused items are always surfaced — visible but distinct.

### New skill: `/feature-state <id> <state> [--reason "..."] [--superseded-by <id>]`

Updates `idea.md` frontmatter, validates required companion fields, triggers dashboard regen. Lives at `skills/feature-state/`.

---

## 2. Assignee

Single frontmatter field on `idea.md`:

```yaml
assignee: court              # single owner
assignee: [court, alex]      # joint ownership
```

No validation (free-form strings, no directory of valid names). Absent = unassigned.

**Dashboard surfacing:** Add `Assignee` column to the **In Progress** and **Paused** tables. Backlog table stays uncluttered (one optional column would dominate; keep backlog scannable). Searchable via `feature-search`.

**Set via:** edit `idea.md` directly, or via the capture interview (new optional question). No dedicated skill needed.

---

## 3. Epic / Umbrella Model

### Decision: Epic-as-feature with `type: Epic`

An epic is a regular feature directory (`docs/features/<epic-id>/`) where `type: Epic`. This reuses every piece of existing infrastructure — frontmatter, hooks, dashboard generator, autopilot entry point — at the cost of giving the epic's `plan.md` a different shape (a dispatch DAG, not a code plan).

**Why this over the alternatives:**
- A separate top-level `docs/features/__epics__/` directory doubles the parser/dashboard surface for marginal clarity gain.
- A pure label (`epic:` field with no umbrella entity) leaves nowhere to write the epic's "why" or its dispatch plan, and makes the autopilot entry point for an epic awkward.

### Epic schema

`docs/features/<epic-id>/idea.md`:

```yaml
---
id: auth-overhaul
name: Auth Overhaul
type: Epic                        # new type
priority: P0
effort: Large
impact: High
category: security
created: 2026-05-15
children: [user-roles, sso-saml, mfa-totp, audit-log]
assignee: court
---

# Auth Overhaul

## Problem Statement
Our authentication layer has accumulated three different session models...

## Children
- user-roles — RBAC primitives
- sso-saml — SAML integration
- mfa-totp — TOTP-based MFA
- audit-log — security event log

## Success Criteria
- All four sub-features shipped
- Migration plan executed without downtime
```

Child feature `idea.md` gains an `epic` field:

```yaml
---
id: user-roles
type: Enhancement
epic: auth-overhaul          # reverse pointer to parent epic
dependsOn: [user-model-refactor]
parallelSafe: true
...
---
```

### Epic lifecycle

| Files present | Epic lifecycle |
|---|---|
| `idea.md` only | backlog (planning the epic) |
| `idea.md` + `plan.md` | in_progress (dispatching children) |
| `idea.md` + `plan.md` + `shipped.md` | completed (all non-tombstoned children shipped) |

**No PR, no branch, no merge for the epic itself.** It's a coordination artifact. Children open their own PRs as today.

Auto-completion: when the last non-tombstoned child ships, the autopilot/ship flow can offer to write the epic's `shipped.md` summarizing children outcomes.

### Epic plan.md shape (dispatch plan)

```markdown
---
started: 2026-05-15
---

# Auth Overhaul — Dispatch Plan

## Wave 1 (parallel, no dependencies)
- user-roles
- audit-log

## Wave 2 (after user-roles completes)
- sso-saml      (depends on user-roles)
- mfa-totp      (depends on user-roles)

## Notes
- audit-log and user-roles do not touch overlapping files (parallelSafe: true)
- sso-saml and mfa-totp can run in parallel within Wave 2
```

The dispatch plan is **inferred from child `dependsOn` + `parallelSafe`** by the autopilot, then written to `plan.md` for the human to confirm/edit before dispatch.

### Epic dispatch via `feature-autopilot <epic-id>`

`feature-autopilot` already handles a single feature linearly. We extend it: at the start, it detects `type: Epic` and switches to **dispatch mode**:

1. Read epic `idea.md` → get `children` list
2. Read each child's `idea.md` → build dependency DAG
3. Compute waves (topo sort with parallel groups respecting `parallelSafe`)
4. Write/refresh epic `plan.md`
5. For each wave:
   - Present the wave to the user, confirm dispatch
   - For each child: spawn a **subagent** running `feature-autopilot <child-id>` (in its own **worktree** if `parallelSafe`)
   - Wait for all subagents to complete or fail
   - Surface aggregate status; pause on any failure for human decision
6. After last wave: offer to write the epic's `shipped.md`

Subagent + worktree mechanics are detailed in §6 below.

### Epic constraints

- **No nested epics.** A child cannot have `type: Epic`. Rejected at capture and at dashboard generation (with a warning).
- **Abandoning an epic** with active children: blocked. User must abandon/decouple children first. A `--force` flag (manual edit only, not exposed in the skill) cascade-decouples.
- **Pausing an epic** does not pause children. The epic just stops dispatching; children remain individually addressable.

---

## 4. Dependency Model

Strengthen what `dependsOn` means and add complementary relations.

### Fields

| Field | Semantics | Storage |
|---|---|---|
| `dependsOn: [a, b]` | **Hard blocker.** Listed features must be `state==active` AND `lifecycle==completed` before this can leave backlog. | Forward (stored on dependent) |
| `relatedTo: [c, d]` | **Soft link.** Informational only; no blocking. Use for "see also" / "shares context with". | Forward (stored on related) |
| `parallelSafe: true` (default) | Whether this can run alongside siblings in the same epic wave. Set `false` when the feature touches files/areas likely to conflict with peers. | Self |
| `blockedBy: [...]` | **Deprecated as stored field.** Computed dynamically by the dashboard from `dependsOn` graphs. | (computed) |

### Migration of `blockedBy`

- Parser keeps reading `blockedBy` for backward compat (legacy idea.md files written it).
- Capture skill stops writing it.
- Dashboard computes blockers dynamically from `dependsOn` and ignores the stored value.
- Removes a source of staleness (bidirectional sync was a maintenance burden).

### Validation (dashboard generator + capture)

- Cycle detection in `dependsOn` graph. Cycles render a `⚠️ Cycle detected` banner in DASHBOARD.md naming the cycle members.
- Unknown ID references in `dependsOn` / `relatedTo` / `supersededBy` / `epic` / `children` → soft warning (allows forward references during epic planning).

### Wave inference algorithm

Pseudocode for epic dispatch:

```
wave_n = features where:
  - feature in epic.children
  - feature.state == active
  - all feature.dependsOn members are completed
  - feature not already shipped
group wave_n by parallel_safety:
  - parallelSafe=true features can dispatch concurrently
  - parallelSafe=false features must dispatch alone (split into sub-waves)
```

`parallelSafe: false` items get their own single-feature sub-wave. Two `parallelSafe: false` siblings in the same logical wave become wave-N-a and wave-N-b sequentially.

---

## 5. Internal Review

Per-feature opt-out from external CI reviewer with an in-session review pass instead.

### Schema

Per-feature override in `idea.md` frontmatter:

```yaml
review: external    # use project's configured CI reviewer (default if reviewer != none)
review: internal    # claude runs a review pass in-session
review: skip        # no review (rare; doc tweaks, typo fixes)
```

If absent: defer to `.feature-workflow.yml` `reviewer:` setting. Project-level `reviewer: none` + feature-level absent = no review.

### New skill: `feature-review-internal` (or sub-flow of existing review skills)

When autopilot reaches a review gate and the effective setting is `internal`:

1. Determine phase (plan vs impl).
2. Read the matching review prompt from `feature-workflow/templates/review-prompt-{plan,impl}.md` (same prompts the CI reviewer uses — single source of truth).
3. Spawn a fresh subagent with:
   - The review prompt as system context
   - Read access to the repo at the current branch
   - Plan/diff as input
4. Subagent produces the same `## Plan Review` / `## Implementation Review` markdown with `### Verdict: PASS|CONDITIONAL PASS|FAIL`.
5. Post the verdict to the existing PR as a top-level comment so `respond.md` and `wait-for-review.sh` work unchanged.
6. Also write a local copy to `docs/features/<id>/reviews/internal-review-<phase>-<n>.md` for audit.

### Reviewer subagent choice

Default: spawn a `general-purpose` agent loaded with the relevant template prompt. Same prompt CI uses; consistency over cleverness. For security-sensitive features (heuristic: `category: security` or `affectedAreas` mentions auth/crypto/secrets), also spawn `feature-workflow:security-reviewer` in parallel and concatenate verdicts (worst verdict wins).

### Autopilot integration

The reviewer-mode table grows:

| Effective review setting | Plan-review step | Impl-review step |
|---|---|---|
| external (gemini/codex) | CI workflow + `wait-for-review.sh` | CI workflow + `wait-for-review.sh` |
| internal | spawn reviewer subagent → post comment → classify locally | spawn reviewer subagent → post comment → classify locally |
| skip | bypass | bypass |

Effective setting = feature override (if set) else project default. If project = `none` and feature = absent: skip. If project = `none` and feature = `internal`: internal review runs (and a PR still gets created as the audit trail).

`wait-for-review.sh` gains an `--internal` flag that reads the verdict from the local file instead of polling CI.

---

## 6. Autopilot: Subagents & Worktrees

Two new sections in `feature-autopilot/SKILL.md`, plus a companion reference doc `skills/feature-autopilot/parallel-dispatch.md`.

### When worktrees are required

| Situation | Worktree needed? |
|---|---|
| User has unrelated uncommitted work on the base branch | Yes — isolate via `superpowers:using-git-worktrees` |
| Autopilot already running for another feature in the same repo | Yes — each gets its own worktree |
| Epic dispatching parallel children | **Yes — one worktree per parallel child** |
| Single feature, clean working tree | No |

### When subagents are used

| Situation | Subagent role |
|---|---|
| Epic wave dispatch | One subagent per child, each running `feature-autopilot <child-id>` |
| Long FAIL → respond loops on a single feature | Optional — delegate the respond phase to a subagent to keep main context clean |
| Internal review pass | Reviewer subagent loaded with the template prompt |
| Plan-phase analysis (architecture, security, UX) | Existing `feature-workflow:*` agents per phase, dispatched by `feature-plan` |

### Parallel dispatch pattern (epic mode)

```
For each wave:
  1. List children to dispatch in this wave
  2. Ask user to confirm wave (autopilot pauses for explicit OK on first wave; auto-advances on subsequent waves if previous wave was clean)
  3. For each child in wave:
       a. Create worktree: `git worktree add ../wt-<child-id> <base-branch>`
       b. Spawn subagent: invoke feature-autopilot with the child ID, cwd=worktree
       c. Record subagent ID + worktree path
  4. Wait for all subagents to complete
  5. Collect verdicts:
       - All children: shipped → continue
       - Any child: failed/paused → surface to user, pause epic dispatch
  6. Clean up worktrees for shipped children
```

The autopilot's main context only tracks **child IDs and verdicts**, not the per-child diffs or review threads — those live in the subagent contexts. This is the key reason subagents matter for epic mode: without them, the main autopilot context balloons with N children's worth of state.

### Fail-handling within epic dispatch

- A single child FAIL after 2 respond attempts pauses **that child's autopilot**, not the whole epic.
- The epic autopilot logs the child's failure, continues with siblings in the same wave, and stops at the wave boundary if any child is still unresolved.
- The user can re-engage with `feature-autopilot <child-id> --respond` to resume the stuck child, then re-run the epic autopilot from the next wave.

---

## 7. Search

New user-invocable skill `/feature-search`:

```
/feature-search --state paused
/feature-search --assignee court
/feature-search --epic auth-overhaul
/feature-search --priority P0 --state active
/feature-search --depends-on user-roles
/feature-search --archive             # include superseded + abandoned
```

Implementation: scans `docs/features/*/idea.md`, reuses `FeatureContext.from_directory`, applies filters, prints a table. No new index files; the directory is the index.

`feature-status` is also extended with these same filters as flags so users can compose status views.

---

## 8. Dashboard Layout

New DASHBOARD.md structure (top-down):

```
# Feature Dashboard

*Auto-generated by hooks. Do not edit directly.*

## In Progress
| ID | Name | Epic | Assignee | Category | Priority | Started |

## Paused
| ID | Name | Phase | Waiting On | Assignee | Paused Since |

## Backlog
| ID | Name | Epic | Category | Priority | Effort | Added |

## Epics
| ID | Name | Children | Done | In Progress | Backlog |

## Completed
| ID | Name | Assignee | Shipped |

## Archive
<details>
<summary>N superseded, M abandoned</summary>

| ID | Name | State | Reason / Replaced By |
</details>

## Validation Warnings (only when present)
- ⚠️ Cycle detected: a → b → c → a
- ⚠️ Unknown dependency: feat-x → missing-feat
```

`Epic` column in In Progress / Backlog: shows the parent epic ID if set, blank otherwise. Lets you see at a glance which work is part of a larger effort.

`Epics` section: rolls up child counts (done / in_progress / backlog) so epic progress is visible without drilling in.

---

## 9. Implementation Surface (files touched)

### Schema / data layer
- `skills/shared/lib/models.py` — add `FeatureState` enum, new fields on `FeatureContext` (state, paused_reason, superseded_by, abandoned_reason, assignee, epic, children, related_to, parallel_safe, review), helper for computed-blocked-by
- `skills/shared/lib/dashboard.py` — new sections (Paused, Epics, Archive, Warnings), new columns, cycle detection, dynamic blocked-by computation
- `skills/shared/lib/frontmatter.py` — no schema change; parser stays flat (a noted constraint for v1)
- `skills/shared/tests/test_models.py`, `test_dashboard.py`, `conftest.py` — new fixtures + tests

### Skills — modify existing
- `skills/feature-capture/{interview,capture,validation}.md` — new questions, new frontmatter fields, validation
- `skills/feature-status/SKILL.md` — surface state, filters
- `skills/checking-backlog/SKILL.md` — exclude archive by default
- `skills/feature-plan/SKILL.md` — refuse paused/superseded/abandoned; for epic IDs, route to epic dispatch flow
- `skills/feature-implement/SKILL.md` — refuse paused
- `skills/feature-review-plan/SKILL.md`, `feature-review-impl/SKILL.md` — honor per-feature `review:` field
- `skills/feature-ship/SKILL.md` — handle epic ship semantics (write epic shipped.md after last child)
- `skills/feature-autopilot/SKILL.md` — major: epic detection, internal-review branch, subagent + worktree sections, state guards
- `skills/feature-autopilot/scripts/wait-for-review.sh` — `--internal` mode reads local verdict file
- `skills/guarding-scope/SKILL.md` — when scope drift suggests a sibling feature, suggest capturing into the current epic

### Skills — new
- `skills/feature-state/` — set state with required companion fields, validation
- `skills/feature-search/` — query with filters
- `skills/feature-review-internal/` — internal review subagent dispatcher (or fold into existing review skills)

### Reference docs — new
- `skills/feature-autopilot/parallel-dispatch.md` — epic wave dispatch pattern, subagent + worktree mechanics

### Hooks
- `hooks/post_tool_use.py` — already regenerates on `idea.md` writes; no change needed (state lives there). Confirm that edits-not-just-writes also trigger.

### Templates / reviewers
- No changes to `templates/review-prompt-{plan,impl}.md` — internal review reuses them
- `reviewers/skills/` — no changes

### Config
- `.feature-workflow.yml` schema unchanged (per-feature override lives in idea.md)

### README + plugin metadata
- `feature-workflow/README.md` — describe new concepts
- `feature-workflow/plugin.json` and marketplace.json — version bump (this is a minor feature release, so 9.6.0)

---

## 10. Backward Compatibility & Migration

**No migration script required.** All new fields are optional; absent = today's behavior.

- Legacy `idea.md` files: parser tolerates missing fields. State defaults to `active`. Epic, assignee, etc. default to empty/absent.
- Legacy `blockedBy:` fields: still parsed (for read), no longer written. Dashboard ignores stored value and computes dynamically.
- Legacy `dependsOn:` semantics unchanged.

**Optional `feature-init --update` enhancement** (deferred to a follow-up): inject a comment block at the top of legacy idea.md files showing the new fields. Not required for the v1 ship.

---

## 11. Verification Plan

End-to-end tests after implementation:

1. **State transitions:**
   - Create a feature → pause it → resume it → ship it. Verify dashboard placement at each step.
   - Mark a feature superseded with required `supersededBy` → confirm it leaves active sections.
   - Mark an in-progress feature abandoned → confirm archive placement.
   - Try to abandon a completed feature → confirm rejection.

2. **Assignee:**
   - Single assignee in capture → dashboard shows column.
   - Multi-assignee via `[a, b]` → both names render.
   - `/feature-search --assignee court` → returns matching features.

3. **Epic dispatch:**
   - Create an epic with 4 children (2 in wave 1, 2 in wave 2 depending on a wave-1 child).
   - Run `feature-autopilot <epic-id>` → verify waves inferred correctly, worktrees created, subagents dispatched.
   - Force one child to fail twice → verify epic pauses cleanly.
   - Recover the failed child → verify epic resumes from next wave.

4. **Internal review:**
   - Set `review: internal` on a feature.
   - Run autopilot → verify internal-review subagent runs, posts verdict comment, autopilot classifies PASS and advances.
   - Force a FAIL verdict → verify `--respond` loop engages.

5. **Dependency strengthening:**
   - Create A → depends on B (B not completed). Try to start A via autopilot → verify it surfaces the unmet dependency.
   - Create a cycle A → B → A → verify dashboard warning.
   - Capture without `parallelSafe` → verify default `true`. Set `false` → verify epic dispatch serializes correctly.

6. **Backward compat:**
   - Open the existing repo's own backlog (real legacy data). Regenerate dashboard. Verify no crashes and dashboard renders.
   - Verify legacy features with stored `blockedBy:` still render correctly.

Test commands:
- `cd feature-workflow && venv/bin/pytest skills/shared/tests/`
- Manual E2E in a sandbox project initialized with `/feature-init`

---

## 12. Build Sequence

Each step is independently shippable; users see incremental value.

1. **Schema + dashboard** (state, assignee, search, archive section, validation warnings) — no behavior change for existing features.
2. **`/feature-state`** skill + capture interview updates.
3. **`/feature-search`** skill.
4. **Dependency strengthening** (`relatedTo`, `parallelSafe`, computed blocked-by, cycle detection).
5. **Internal review** path (per-feature override, new skill, autopilot integration).
6. **Epic concept** (type=Epic, `epic:` / `children:` fields, dashboard Epics section).
7. **Epic dispatch** in autopilot (waves, subagents, worktrees).
8. **Autopilot doc updates** (parallel-dispatch.md, worktree guidance).
9. **README + version bump (9.6.0).**

Plus tests at each step.

---

## 13. Decision Points (open for redirect)

These were calls I made where reasonable people could disagree. Flag any you want to revisit:

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| 1 | Epic representation | Feature with `type: Epic` | Separate top-level `__epics__/` dir, or pure label |
| 2 | `parallelSafe` default | `true` | `false` (safer but noisier in capture) |
| 3 | Stored `blockedBy` | Deprecate (compute instead) | Keep + bidirectional-sync |
| 4 | Internal-review verdict storage | PR comment + local audit copy | Local file only (skip PR) |
| 5 | Abandoning an epic with active children | Blocked (user must deal with children) | Cascade-abandon |
| 6 | Nested epics | Not allowed in v1 | Allow with depth limit |
| 7 | `review: skip` | Allowed for trivial work | Drop it; force at least internal review |
| 8 | Pausing an epic | Stops dispatch only; children unaffected | Cascade-pause children |
| 9 | Frontmatter parser | Stay flat (no PyYAML dep) | Adopt PyYAML for nested schemas |
| 10 | Auto-write epic `shipped.md` | Offer after last child ships | Always require manual ship |

---

## 14. Out of Scope (for this spec)

- **Real-time epic progress dashboard** (web UI, statusline integration beyond current). Future enhancement.
- **Conflict detection across siblings** (grep affected-areas, warn on overlap). Future enhancement; v1 trusts the human's `parallelSafe` flag.
- **Search index / caching** for large backlogs. v1 just scans on every invocation; revisit if it gets slow.
- **Time-tracking** on paused features ("how long has this been waiting?"). Frontmatter has `created`; we could add `pausedAt` later if useful.
- **Notifications** when a paused feature's blocker resolves. Out of scope; nice-to-have.
