# Feature-Workflow v9.7.0 Release & Dogfood Plan (Plan 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or execute manually. Most tasks here are procedural (verify, install, test) rather than TDD — there's still implementation work to do (version bumps, fixing issues found during dogfooding), so use the same checkbox flow.

**Goal:** Ship feature-workflow v9.7.0 (Plan 1 foundations + Plan 2 internal review) and dogfood it against `~/GitHub/schuettc/slay-the-spire` to surface issues before broader use.

**Architecture:** This is a release + validation plan, not a new-feature plan. It has three concerns:
1. **Version reconciliation** — origin/main already has a separate v9.6.0 (873594f), so Plan 1's PR needs to rebase + bump to 9.7.0.
2. **Merge sequence** — Plan 1 PR → main → Plan 2 PR → main → tag v9.7.0 → dogfood.
3. **Dogfood in slay-the-spire** — real backlog (200+ features), real `reviewer: gemini`, real users (the developer). Exercise every new concept and write up findings.

**Tech Stack:** git, gh CLI, the Claude Code plugin marketplace.

**Precondition:** Plan 1 PR (`feature/foundations-v9.6.0`, PR #5) is currently open. Plan 2 plan exists at `docs/superpowers/plans/2026-05-15-feature-workflow-internal-review.md` but hasn't been executed yet.

---

## Phase A: Reconcile Plan 1 Version Conflict

Origin/main has `873594f feat(reviewers): add pre-flight verification + unverifiable-safety-claim finding (v9.6.0)` — bumped to v9.6.0 in a parallel session. Plan 1 also bumped to v9.6.0. They don't conflict on code (different files), but the version field collides.

### Task A1: Rebase Plan 1 onto current origin/main + bump to 9.7.0

**Working in:** the Plan 1 worktree at `/Users/courtschuett/GitHub/schuettc/claude-code-plugins/.worktrees/feature-foundations`.

- [ ] **Step 1: Fetch + rebase**

```bash
cd /Users/courtschuett/GitHub/schuettc/claude-code-plugins/.worktrees/feature-foundations
git fetch origin
git rebase origin/main
```

Expected: clean rebase (Plan 1 touches feature-workflow/skills/ and tests; 873594f touches feature-workflow/reviewers/ and templates/ — no file overlap except plugin.json and marketplace.json).

If conflicts arise on `plugin.json` and `marketplace.json`: both sides bumped to 9.6.0. Take the incoming version (9.6.0 from main), so Plan 1's commits read the rebased baseline as 9.6.0.

- [ ] **Step 2: Bump version 9.6.0 → 9.7.0**

The original "chore: bump to v9.6.0" commit is now redundant (main already has 9.6.0). Either:

**Option a (recommended):** Use `git rebase -i origin/main` to edit the bump commit. Change its diff to bump from 9.6.0 → 9.7.0 and update its message to `chore: bump feature-workflow to v9.7.0 (foundations + state, assignee, search, deps)`.

**Option b (simpler):** Drop the original bump commit and add a fresh commit at the tip:

```bash
git rebase -i origin/main
# Mark the original bump commit as 'd' (drop)
# Save and exit

# Then make a new bump commit at the tip
sed -i '' 's/"version": "9.6.0"/"version": "9.7.0"/' feature-workflow/.claude-plugin/plugin.json
# Edit marketplace.json by hand (only the feature-workflow entry) to 9.7.0

git add feature-workflow/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump feature-workflow to v9.7.0 (foundations + state, assignee, search, deps)"
```

Pick whichever feels less risky.

- [ ] **Step 3: Verify tests still pass**

```bash
cd feature-workflow && venv/bin/pytest skills/shared/tests/ 2>&1 | tail -5
```

Expected: 148 passed (or whatever the latest count is).

- [ ] **Step 4: Force-push the rebased branch**

```bash
git push --force-with-lease origin feature/foundations-v9.6.0
```

`--force-with-lease` is safer than `--force` — it refuses to overwrite if someone else pushed to the branch since you last fetched.

- [ ] **Step 5: Update the PR title + description**

```bash
gh pr edit 5 --title "feat(feature-workflow): v9.7.0 foundations — state, assignee, search, deps"
```

Update the PR body to mention the rebase + version change. The substantive description from the original PR is fine; just amend the title/version note.

- [ ] **Step 6: Optionally rename the branch**

The branch is named `feature/foundations-v9.6.0` but the version is now 9.7.0. Rename for clarity (optional — branch names are arbitrary):

```bash
git branch -m feature/foundations-v9.7.0
git push origin -u feature/foundations-v9.7.0
git push origin --delete feature/foundations-v9.6.0
# Re-target the PR via gh — depends on whether GitHub auto-tracks; if not, close + reopen
```

Skip this step unless the branch name bothers you — it's a cosmetic change with PR-link risk.

---

### Task A2: Get Plan 1 reviewed + merged

- [ ] **Step 1: Trigger external review if configured**

If the repo has Gemini/Codex configured at the repo level (separate from feature-workflow's per-project reviewer setting), the rebased push should trigger CI. Watch:

```bash
gh pr checks 5 --watch
```

- [ ] **Step 2: Address review feedback**

If the reviewer surfaces findings, address them via `/feature-review-impl <id> --respond` mechanics or directly. The branch is on `feature/foundations-v9.7.0` (or original name); the workflow is the same as any feature.

- [ ] **Step 3: Merge when clean**

```bash
gh pr merge 5 --squash --delete-branch  # or --merge if preferring preserve commits
```

Squash vs merge: 21 commits is a clean history; **prefer `--merge`** to preserve the per-task commits — they're a useful reference. If repo policy is squash-only, use that.

- [ ] **Step 4: Pull main and confirm**

```bash
cd /Users/courtschuett/GitHub/schuettc/claude-code-plugins
git checkout main
git pull origin main
git log --oneline -3
```

Expected: main is at v9.7.0 with the foundations work.

---

## Phase B: Execute Plan 2

After Plan 1 is merged, execute Plan 2 (internal review path).

### Task B1: Create Plan 2 worktree + execute

- [ ] **Step 1: Create worktree for Plan 2**

```bash
cd /Users/courtschuett/GitHub/schuettc/claude-code-plugins
git worktree add .worktrees/internal-review -b feature/internal-review-v9.7.1 main
cd .worktrees/internal-review
```

Version note: this is an additive feature, so 9.7.0 → 9.7.1 is appropriate semver if no breaking changes. If we're combining Plan 2 with Plan 3 later, treat as 9.8.0. **Default: 9.7.1.**

- [ ] **Step 2: Set up venv**

```bash
cd feature-workflow && python3 -m venv venv && venv/bin/pip install --quiet pytest
```

- [ ] **Step 3: Execute Plan 2 via subagent-driven development**

Open the plan file:
```
docs/superpowers/plans/2026-05-15-feature-workflow-internal-review.md
```

Run through the phases A → B → C → D using the subagent-driven-development pattern. Each task has its own commit. Expect ~14 commits total.

The version bump task (D2) should target **9.7.1**, not 9.7.0 (since Plan 1 already shipped 9.7.0).

- [ ] **Step 4: Push and open PR**

```bash
git push -u origin feature/internal-review-v9.7.1
gh pr create --base main --title "feat(feature-workflow): v9.7.1 internal review path" --body "..."
```

PR body should describe the per-feature `review:` override, the shared internal-review workflow, and the autopilot's effective-mode handling.

- [ ] **Step 5: Review + merge**

Same flow as Phase A's A2. Watch CI if configured, address feedback, merge when clean.

---

## Phase C: Tag the Release

After both Plan 1 and Plan 2 are merged to main, tag the release for marketplace consumers.

### Task C1: Cut v9.7.x tags

- [ ] **Step 1: Verify main state**

```bash
cd /Users/courtschuett/GitHub/schuettc/claude-code-plugins
git checkout main
git pull
cat feature-workflow/.claude-plugin/plugin.json | grep version
cat .claude-plugin/marketplace.json | grep -A1 '"feature-workflow"' | grep version
```

Expected: both show `"version": "9.7.1"`.

- [ ] **Step 2: Run the release skill (or tag manually)**

The repo has a `release` skill listed in available skills:
> "release: Version management for feature-workflow plugin. Bumps version in both plugin.json and marketplace.json, commits, and pushes with confirmation."

This skill handles the bump+push but not tagging. Either:

**Skill path:** `/release` — confirms the version is correct, may push (already done).

**Manual tag path:**
```bash
git tag -a feature-workflow-v9.7.1 -m "feature-workflow v9.7.1 — foundations + internal review"
git push origin feature-workflow-v9.7.1
```

The tag uses a plugin-scoped name (`feature-workflow-v9.7.1`) since the repo hosts multiple plugins. Tag whichever way matches your existing conventions — if there are no prior tags, plugin-scoped is the safer pattern.

- [ ] **Step 3: Verify the tag**

```bash
git tag -l 'feature-workflow-*'
gh release view feature-workflow-v9.7.1 --json url --jq '.url' 2>/dev/null || echo "no GitHub release yet — skip or create one via 'gh release create'"
```

Creating a GitHub release with notes is optional but helps users see what changed. If you do:

```bash
gh release create feature-workflow-v9.7.1 \
  --title "feature-workflow v9.7.1" \
  --notes "$(cat <<'EOF'
## What's new

### v9.7.0 (Plan 1) — Foundations
- New `state:` field (active/paused/superseded/abandoned) with required companion fields
- New `assignee:` field (single or list)
- New `/feature-state` skill for state transitions
- New `/feature-search` skill with state/assignee/epic/dependency filters
- Stronger dependency markers: `relatedTo`, `parallelSafe`
- Dashboard sections: Paused, Archive (collapsed), Epics, Validation Warnings
- Dependency cycle detection + unknown-ref validation
- Dynamic `blockedBy` computation (stored field deprecated)

### v9.7.1 (Plan 2) — Internal Review
- Per-feature `review:` override (external | internal | skip)
- Internal review dispatches a same-session subagent with the CI reviewer prompt
- Verdict format and autopilot integration unchanged from external

### Plan 3 (coming) — Epic Dispatch
- `type: Epic` parallel/sequential dispatch via worktrees + subagents
EOF
)"
```

---

## Phase D: Dogfood in slay-the-spire

The slay-the-spire project at `~/GitHub/schuettc/slay-the-spire` has:
- 200+ features in `docs/features/`
- `.feature-workflow.yml` with `reviewer: gemini`, `branch.prefix: feature/`, `branch.target: dev`
- A real-world backlog with diverse priorities, efforts, and categories

This makes it an ideal test target. The plan: install v9.7.1 there, run the new flows against real features, capture issues.

### Task D1: Install / update the plugin in slay-the-spire

- [ ] **Step 1: Choose install mode**

| Mode | When to use | How |
|---|---|---|
| Marketplace install | Normal user flow; tests the published version | In slay-the-spire: `/plugin update feature-workflow@schuettc-claude-code-plugins` (or however the plugin manager refreshes) |
| Local symlink | Fast iteration; you'll be patching as you find issues | Symlink the worktree into Claude Code's plugin cache |

**For Phase D dogfooding, use marketplace install** — it's what real users will experience. If issues come up that need same-day fixes, switch to local symlink mid-stream.

- [ ] **Step 2: Refresh the plugin**

In a Claude Code session targeting slay-the-spire:

```
/plugin update feature-workflow
```

Or, depending on plugin-manager UX: `/plugin remove feature-workflow && /plugin install feature-workflow@schuettc-claude-code-plugins`.

Verify the new version is active:

```bash
# In a Claude Code session, run a slash command unique to v9.7.0 (didn't exist before)
/feature-search --state active --priority P1
```

If the command runs, v9.7.0+ is loaded. If not, the cache may need clearing (`~/.claude/plugins/cache/...`).

- [ ] **Step 3: Smoke test dashboard regen**

```bash
cd ~/GitHub/schuettc/slay-the-spire
# Touch any idea.md to trigger the post-write hook
```

In a Claude Code session, open and re-save any feature's idea.md (no content change). The hook should regenerate DASHBOARD.md with the new sections (Paused, Epics, Validation Warnings — likely empty initially).

Verify by reading the new DASHBOARD.md and confirming:
- `## Paused` section header exists (even if "no paused features")
- `## Epics` section header exists (even if empty)
- No new errors in the hook's logs

---

### Task D2: Exercise new flows against real features

Pick a handful of real features from the slay-the-spire backlog to exercise each new capability. Use a fresh Claude Code session for each test so context doesn't bleed.

#### D2.1: Paused state

- [ ] **Find a candidate:** `live-streaming-premium`, `multiplayer-runs`, or any large effort that's likely waiting on something external.

- [ ] **Run:** `/feature-state live-streaming-premium paused --reason "Waiting on AWS infrastructure approval"`

- [ ] **Verify:**
  - `docs/features/live-streaming-premium/idea.md` now has `state: paused` and `pausedReason: "..."`
  - DASHBOARD.md shows the feature under `## Paused` with the reason
  - `/feature-status` no longer shows it in Backlog
  - `/feature-search --state paused` returns it

- [ ] **Reverse:** `/feature-state live-streaming-premium active` — confirm it returns to Backlog and the `pausedReason` field is removed.

#### D2.2: Superseded / abandoned

- [ ] **Find candidates:** Pick two features that look related but are still both listed — they may be a superseded pair the user hasn't formalized. Examples: there are several `live-viewer-*` features that might consolidate.

- [ ] **Run:** `/feature-state <older-id> superseded --superseded-by <newer-id>` and `/feature-state <unrelated-id> abandoned --reason "Out of scope"`.

- [ ] **Verify:**
  - Both move to the Archive section in DASHBOARD.md
  - `/feature-status` no longer shows them
  - `/feature-search --archive` returns them
  - Searching without `--archive` does NOT return them

#### D2.3: Assignee

- [ ] **Pick a feature you're actively working on** (or pretend to be): e.g. `mod-install-ux`.

- [ ] **Edit its idea.md** to add `assignee: court` (manual edit — no slash command for assignee yet).

- [ ] **Verify:**
  - DASHBOARD.md shows the assignee in the In Progress / Backlog tables (depending on state)
  - `/feature-search --assignee court` returns it
  - `/feature-status` includes the column

#### D2.4: Dependency strengthening

- [ ] **Identify a chain:** several features like `live-viewer-*` may depend on `live-streaming-premium` or `cloud-streaming`. Add `dependsOn: [cloud-streaming]` and `relatedTo: [live-viewer-mode]` to one.

- [ ] **Verify:**
  - DASHBOARD.md shows `Blocked By` column computed dynamically
  - If you create a deliberate cycle (`a → b → a`), DASHBOARD.md surfaces it in the Validation Warnings section
  - Removing the cycle clears the warning on next regen

#### D2.5: Search filters

- [ ] **Run a battery:**

```
/feature-search --state active --priority P1 --category Product
/feature-search --assignee court
/feature-search --depends-on cloud-streaming
/feature-search --state abandoned --archive
/feature-search --format json --priority P0
```

- [ ] **Verify:** Each returns the expected subset. JSON output is parseable. Empty filters produce "(no matches)" cleanly.

#### D2.6: Internal review (requires Plan 2 to be merged)

- [ ] **Find a small feature:** e.g. `not-found-route`, `spacing-standardization` — anything Small/P3.

- [ ] **Edit its idea.md to add:** `review: internal`

- [ ] **Run:** `/feature-plan not-found-route`

- [ ] **Run:** `/feature-review-plan not-found-route`

- [ ] **Verify:**
  - A PR is opened (or it skips PR opening if not pushed yet — confirm the behavior matches what the SKILL says)
  - No `plan-review` label applied
  - An internal-review subagent runs in the session
  - A `## Plan Review` comment is posted to the PR with a verdict
  - `wait-for-review.sh` (or direct comment reading) can classify the verdict
  - `docs/features/not-found-route/reviews/internal-review-plan-1.md` exists as an audit copy

- [ ] **Continue:** `/feature-implement not-found-route` (a tiny implementation) and then `/feature-review-impl not-found-route`. Confirm the impl review also runs internally.

---

### Task D3: Capture findings + iterate

- [ ] **Step 1: Create a follow-ups doc**

```bash
mkdir -p docs/superpowers/dogfood
cat > docs/superpowers/dogfood/2026-05-15-slay-the-spire-findings.md <<'EOF'
# slay-the-spire Dogfood Findings — feature-workflow v9.7.1

**Date:** YYYY-MM-DD
**Tester:** Court Schuett
**Plugin version tested:** 9.7.1

## What worked

(Bullets — flows that just worked, no friction)

## Issues found

| # | Severity | Area | Description | Repro |
|---|---|---|---|---|
| 1 | | | | |

## UX gripes (non-blocking)

(Friction points worth fixing but didn't break anything)

## Documentation gaps

(Things that should be in the README but aren't)

## Recommendations for Plan 3

(What slay-the-spire's epic-like clusters tell us about how Plan 3 should land)
EOF
```

- [ ] **Step 2: Fill it in as you test**

Capture every surprise. The format is for **you** to scan later — verbose is fine. Each issue gets:
- Severity (Critical / Important / Minor)
- Steps to reproduce
- Expected vs actual

- [ ] **Step 3: File patches for Critical / Important issues**

For each Critical / Important finding, decide:
- **Fix in a patch release** (v9.7.2): worth a same-day PR + merge + reinstall
- **Defer to a follow-up backlog** in the feature-workflow plugin itself (or capture via `/feature-capture` if that ever becomes meta)
- **Document as a known limitation**: README addendum, no code change

- [ ] **Step 4: Commit findings to main**

```bash
cd ~/GitHub/schuettc/claude-code-plugins
git checkout main
git pull
git add docs/superpowers/dogfood/2026-05-15-slay-the-spire-findings.md
git commit -m "docs(dogfood): slay-the-spire findings for v9.7.1"
git push
```

This gives future plans (esp. Plan 3) something concrete to design against.

---

## Phase E: Decide on Plan 3 Trigger

- [ ] **Step 1: Review dogfood findings**

Did anything in Phase D suggest the epic concept is needed sooner rather than later? Examples:
- Multiple `live-viewer-*` features — natural epic candidate
- `auth-consolidation` + `clerk-integration` + `clerk-powered-settings` + `clerk-ui-package` — all auth umbrella
- The `data-pipeline-redesign` + `dynamo-restructure` cluster

If the dogfood surfaces obvious epic candidates with real coordination pain, that motivates writing Plan 3 (Epic Dispatch).

- [ ] **Step 2: Decide cadence**

Three reasonable paths:

1. **Write Plan 3 now** if dogfood showed epic-shaped friction
2. **Wait for more data** — let v9.7.1 settle for a week, then revisit
3. **Switch focus** — if dogfood showed bigger issues in v9.7.x, fix those first before adding more surface area

Document the decision somewhere visible — either in the dogfood findings file or as a brief note in the spec doc.

---

## Self-Review Checklist

1. **Version handling:** Plan 1 rebases + bumps to 9.7.0. Plan 2 bumps to 9.7.1. Plan 4 cuts the tag. No more version collisions.
2. **Merge sequence:** Plan 1 → main → Plan 2 → main → tag → dogfood. Each PR is independent and reviewable.
3. **Dogfood coverage:** Every new concept (state, assignee, search, deps, internal review) has at least one test against real slay-the-spire data.
4. **Findings doc:** Persistent artifact for follow-ups; informs Plan 3.
5. **Plan 3 trigger:** Phase E forces an explicit decision rather than drifting.

---

## Risks

- **The rebase in A1 could go badly** if branch protection or the PR has accumulated review comments. If conflicts on plugin.json/marketplace.json are non-trivial, fall back to creating a fresh branch from current main and cherry-picking Plan 1's commits manually.
- **Marketplace install propagation** may not be instant. If the dogfood project doesn't see v9.7.x within a few minutes of `gh release create`, the user may need to manually purge the plugin cache.
- **slay-the-spire is a real project** — if dogfooding lands a half-baked change in its docs/features/, it'll be confusing. Use the `/feature-state` and `/feature-search` flows but **avoid running `/feature-plan` on real features** unless you genuinely want to start that work. State/search/dashboard are read-mostly safe; plan/implement/ship are not.

---

## What This Plan Does NOT Cover

- The full Plan 3 implementation (epic dispatch). That gets written after this plan's dogfood phase informs the design.
- Marketing or external announcement. No changelog post, no Twitter, etc. — internal-only release for now.
- Automated tests against slay-the-spire's real data. The dogfood is manual + observational.
