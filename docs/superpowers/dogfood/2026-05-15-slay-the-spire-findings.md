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
| | | | | |

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
