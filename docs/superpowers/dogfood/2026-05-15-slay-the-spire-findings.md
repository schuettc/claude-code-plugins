# slay-the-spire Dogfood Findings — feature-workflow v9.7.1

**Date:** 2026-05-15
**Tester:** Court Schuett
**Plugin version tested:** 9.7.1 (Plan 1 foundations + Plan 2 internal review)
**Project:** `~/GitHub/schuettc/slay-the-spire`

---

## Pre-flight: Update the plugin

The installed cache is currently at v9.5.2. To dogfood v9.7.1, update via Claude Code:

```
/plugin update feature-workflow
```

Or if `update` doesn't refresh:

```
/plugin remove feature-workflow
/plugin install feature-workflow@schuettc-claude-code-plugins
```

Verify by checking:

```bash
cat ~/.claude/plugins/cache/schuettc-claude-code-plugins/feature-workflow/9.7.1/.claude-plugin/plugin.json 2>/dev/null | grep version
```

Expected: `"version": "9.7.1"`. If `9.7.1/` doesn't exist as a directory in the cache, the update didn't propagate yet.

## Smoke test: dashboard regen

Touch a feature's `idea.md` (no content change) to trigger the PostToolUse hook:

In a Claude Code session targeting slay-the-spire:
1. Open `docs/features/ai-coaching/idea.md`
2. Save without changes (or add then remove a trailing newline)
3. Re-read `docs/features/DASHBOARD.md`

Expected: dashboard now contains `## Paused`, `## Epics`, `## Archive`, `## Validation Warnings` section headers (likely empty initially). Existing In Progress / Backlog / Completed sections still present.

---

## Test scenarios

### Scenario 1: Pause a feature

**Picked:** `live-streaming-premium` (large, likely blocked on infra)

**Run:** `/feature-state live-streaming-premium paused --reason "Waiting on AWS infrastructure approval"`

**Verify:**
- [ ] `docs/features/live-streaming-premium/idea.md` has `state: paused` and `pausedReason: "..."` in frontmatter
- [ ] `DASHBOARD.md` shows it under `## Paused` with reason
- [ ] `/feature-status` no longer shows it in Backlog
- [ ] `/feature-search --state paused` returns it

**Notes:**



### Scenario 2: Revive paused

**Run:** `/feature-state live-streaming-premium active`

**Verify:**
- [ ] `pausedReason:` field removed from frontmatter
- [ ] Feature returns to Backlog in DASHBOARD.md
- [ ] `/feature-search --state paused` no longer returns it

**Notes:**



### Scenario 3: Supersede

**Picked:** `live-viewer-debug-harness` (likely superseded by `live-viewer-mode`)

**Run:** `/feature-state live-viewer-debug-harness superseded --superseded-by live-viewer-mode`

**Verify:**
- [ ] Feature moves to `## Archive` (collapsed `<details>`) in DASHBOARD.md
- [ ] `/feature-status` no longer shows it
- [ ] `/feature-search` (no flags) does NOT return it
- [ ] `/feature-search --archive` DOES return it
- [ ] `idea.md` has `state: superseded` and `supersededBy: live-viewer-mode`

**Notes:**



### Scenario 4: Abandon

**Picked:** Pick a P3 / Low-impact item that's clearly not worth pursuing

**Run:** `/feature-state <id> abandoned --reason "Out of scope for this quarter"`

**Verify:**
- [ ] In Archive section
- [ ] Searchable only with `--archive`
- [ ] `abandonedReason:` field present

**Notes:**



### Scenario 5: Assignee

**Picked:** `mod-install-ux` (something you'd actually work on)

**Action:** Manually edit `docs/features/mod-install-ux/idea.md` and add `assignee: court` to frontmatter.

**Verify:**
- [ ] DASHBOARD.md shows assignee in the table column
- [ ] `/feature-search --assignee court` returns it
- [ ] `/feature-status` includes the column

**Notes:**



### Scenario 6: Strengthened dependencies

**Picked:** Two related live-viewer features.

**Action:** Edit one feature's `idea.md` to add:
```yaml
relatedTo: [live-viewer-mode]
parallelSafe: false
```

**Verify:**
- [ ] DASHBOARD.md `Blocked By` column computed dynamically (no manual `blockedBy:` written)
- [ ] No errors

**Test cycle detection:** Temporarily add `dependsOn: [<self-id>]` to one feature. Re-trigger dashboard regen.

- [ ] Dashboard shows `## Validation Warnings` section with "Cycle detected: ..."
- [ ] Removing the cycle clears the warning on next regen

**Notes:**



### Scenario 7: Search filters

**Run a battery:**

```
/feature-search --state active --priority P1 --category Product
/feature-search --assignee court
/feature-search --depends-on cloud-streaming
/feature-search --state abandoned --archive
/feature-search --format json --priority P0
```

**Verify each returns the expected subset.**

**Notes:**



### Scenario 8: Internal review (the big one)

**Picked:** `not-found-route` or any Small/P3 feature

**Action:** Edit its `idea.md` to add `review: internal`.

**Run:**
1. `/feature-plan not-found-route` — write a plan
2. `/feature-review-plan not-found-route` — should detect `internal` mode

**Verify:**
- [ ] A PR is opened (no `plan-review` label applied)
- [ ] An internal-review subagent dispatches in-session
- [ ] A `## Plan Review` comment is posted to the PR with a verdict (`PASS` / `CONDITIONAL PASS` / `FAIL`)
- [ ] `docs/features/not-found-route/reviews/internal-review-plan-1.md` exists as audit copy
- [ ] If `wait-for-review.sh` is available, it classifies the verdict correctly

**Continue:**
3. `/feature-implement not-found-route` (small implementation)
4. `/feature-review-impl not-found-route`

**Verify:**
- [ ] Internal impl-review subagent runs
- [ ] Posts comment with impl-review verdict
- [ ] Plan-review label removed; no impl-review label added
- [ ] `internal-review-impl-1.md` audit file exists

**Notes:**



---

## Issues found

| # | Severity | Area | Description | Repro |
|---|---|---|---|---|
| 1 | **Important** | Schema gap — `supersedes:` | User wrote `supersedes: [user-facing-run-delete, run-export-csv-and-discoverability]` on an Epic's idea.md, expressing "this epic replaces those captures." Schema only defines `supersededBy:` (singular, reverse-direction) and `children:` (epic→members). `supersedes:` is silently ignored — no validation warning, no dashboard surface. The Epics rollup shows `Children: 0` because the user didn't write `children:`. Both ergonomic mismatches are real: (a) forward-direction supersession is a natural mental model and we don't support it, (b) the `type: Epic` schema needs `children:` but the slash-command flow (capture/manual edit) never enforces or hints at it. | Epic `run-data-self-service` in slay-the-spire; see `git log --all -- docs/features/run-data-self-service/idea.md` |
| 2 | **Minor** | Epic-as-multi-step-feature vs Epic-with-children | The user is treating Epic as "one big feature with phases A/B/C/D/E/F inline in the idea.md," not as an umbrella over multiple child features. Both mental models are valid; Plan 3 needs to pick one. The current schema (children:) supports umbrella-over-features, but real users may want both. Possible resolution: keep `children:` for true umbrella-style, but also allow Epic features to have their own plan.md with multi-phase work (which is what autopilot already supports). | (observation, not a bug) |
| 3 | **Minor** | Plan 1 still leaves `Children: 0` for Epic | When `type: Epic` is set but `children:` is absent, the Epics rollup table shows `Children: 0` which is technically correct but misleading. A reader scanning the dashboard might think "this epic is empty / broken." Either (a) require `children:` for Epic type (validation warning if absent), or (b) hide the row entirely until children are populated. | DASHBOARD.md "Epics" section after committing run-data-self-service idea.md |

## What worked end-to-end (observed during autopilot run)

Feature workflow scenario: epic `run-data-self-service` (P1), reviewer: gemini (external CI).

| Stage | What happened | Verdict |
|---|---|---|
| Plugin update | `/plugin update feature-workflow` swapped cache from 9.5.2 → 9.7.1 cleanly | ✅ |
| Dashboard regen on update | First idea.md write triggered hook, regenerated DASHBOARD.md with all new sections (Epics rollup present, Paused/Archive/Validation Warnings correctly omitted because empty) | ✅ |
| Epic detection | `type: Epic` was recognized — feature shows in BOTH Backlog row (dual-bucket via partition_features) AND Epics rollup | ✅ |
| Precondition check in autopilot | Detected dirty tree (DASHBOARD + new captures), surfaced cleanly to user, offered exact commit message | ✅ |
| feature-plan with new schema | Wrote a 129-line plan with real ground-truth code references (`file:line` callouts). `started:` frontmatter populated | ✅ |
| feature-review-plan with v9.7.1 effective-mode branching | Computed `effective_mode = external_gemini` (no per-feature override), applied `plan-review` label, opened draft PR #113 | ✅ |
| Real CI fires | GitHub Actions `plan-review` job started; `impl-review` correctly skipped (label-gated) | ✅ |
| /feature-search against real backlog (196 features) | All filters (state, priority, type, epic, depends-on, archive) returned correct results. `--type Epic` returned the one Epic. `--epic run-data-self-service` returned nothing (confirms finding #1: no children written) | ✅ |
| Dashboard scale | 196 active features, 168 shipped, single Epic — no errors, sub-second regen | ✅ |

## Open questions Plan 3 must answer

Based on what slay-the-spire actually did:

1. **Should Epic features have a plan.md at all?** The user wrote a single multi-phase plan.md on the Epic itself, NOT a dispatch DAG over child features. If Plan 3 keeps the "Epic dispatch = parallel waves over children" model, we need to either (a) reject Epics with their own plan.md, or (b) treat the Epic's plan.md as the dispatch plan (which would conflict with the freeform multi-phase plan the user wrote).
2. **What's the right move when a user writes `supersedes:` (forward) or `children:` is missing?** Capture-time validation (warn before committing idea.md) is the obvious answer.
3. **For multi-phase work bundled into one feature** (which is what the user did here): is autopilot's existing per-step checkbox flow good enough, or do we need an explicit "phased feature" type?

---

## UX gripes (non-blocking)

(Friction points worth fixing but didn't break anything)



---

## Documentation gaps

(Things that should be in the README but aren't)



---

## Recommendations for Plan 3 (Epic Dispatch)

Based on slay-the-spire's actual clusters:

**Obvious epic candidates seen:**
- `live-viewer-*` (8+ features) — clearly one umbrella
- `clerk-*` (4 features) + `auth-consolidation` — auth/identity epic
- `mod-*` (10+ features) — mod lifecycle epic
- `live-*` viewer/streaming bundle

What does this tell us about Plan 3's design?



---

## Decision

After this dogfood pass, the next step is:

- [ ] Write Plan 3 (Epic Dispatch) — proceed now
- [ ] Pause; let v9.7.1 settle for a week, gather more data
- [ ] Switch focus — issues found in Phase D need attention first
