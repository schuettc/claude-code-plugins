# Feature-Workflow Autopilot Hardening + Epic Dispatch Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Context:** Two consecutive dogfood passes (slay-the-spire, now-playing) surfaced eight distinct problems with v9.7.x. They cluster into two releases:

- **v9.7.3** (patch): autopilot reliability — pre-flight checks, workflow YAML race conditions, parallel-dispatch safety, documentation
- **v9.8.0** (minor): the long-deferred Plan 3 — epics actually drive their children to completion, with safe parallel dispatch as a first-class feature

Both ship without breaking changes (additive only). v9.7.3 lands first; v9.8.0 builds on its hardening.

---

## Decisions baked into this plan (call out objections before execution)

1. **Sequential epic dispatch is the MVP for parallel-safe children too.** Parallel mode is implemented but **opt-in** (`--parallel` flag on the autopilot, or `parallelSafe: true` on every child in a wave). Default behavior is one child at a time. Rationale: the now-playing incident (B's code overlaid by C's branch switch) shows the failure mode is severe. Sequential is the safe default; opt into parallel deliberately.

2. **Parallel dispatch ALWAYS uses worktree isolation.** No "shared tree, parallel branches" path. Every parallel child gets its own worktree under `.worktrees/<child-id>`. We use the Agent tool's `isolation: "worktree"` param. The plugin does not implement its own worktree management — we lean on the harness.

3. **Subagent-per-child is mandatory.** Each child's autopilot runs as a fresh subagent. The orchestrator only tracks IDs + verdicts; child PR diffs and review threads stay in the child's context. Sequential and parallel modes both use this.

4. **Bidirectional epic ↔ children sync via the hook**, same pattern as `replaces:` in v9.7.2. Writing `epic: <id>` on a child auto-adds the child to the epic's `children:`. Writing `children: [a, b]` on an epic auto-sets `epic:` on each.

5. **Workflow YAML fixes ship as template updates.** Users update via the existing `/feature-init --update` command. No data migration. We document this in release notes.

6. **`children:` order in the epic's idea.md IS the dispatch order**, modulated by `dependsOn:` (topo-sort overrides explicit order on conflicts). No separate "build order" field.

7. **Epic auto-ships when last child ships.** The dispatcher offers to write the epic's `shipped.md` with a summary. User can decline; epic stays in_progress until manually shipped.

---

## Open questions (answer before execution begins)

| # | Question | Default if no answer |
|---|---|---|
| Q1 | When dispatching parallel children, what's the max concurrent worktree count? | 3 — covers most real waves without exhausting machine resources |
| Q2 | When a child fails mid-epic, should sibling children-already-in-flight (parallel mode) finish, or get cancelled? | Finish — cancellation is harder and might leave half-written worktrees |
| Q3 | Should `feature-init --update` also overwrite the user's `feature-review-*.yml` workflow, or just warn? | Overwrite (with a confirmation prompt) — the workflow YAML is the source of bugs we're fixing |
| Q4 | If epic dispatch sees a child with `state: paused`, should it skip silently or pause the epic? | Skip with a one-line log; epic doesn't pause |
| Q5 | Pre-commit hooks like skylos/fallow that block autopilot commits — do we ship a `pre_commit_compat.md` doc, or actually intercept and translate failures? | Doc only for v9.7.3; intercept is a v9.9 candidate |

If you don't override these, execution proceeds with the defaults.

---

# Release 1: v9.7.3 — Autopilot Hardening (patch)

Five focused bug fixes from the dogfood. No new features. Each is small and independently shippable; bundling for one PR because they share themes.

## Phase A: Pre-flight + Parallel-Safety

### Task A1: Pre-flight check — local base in sync with origin

**Files:**
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md` (preconditions section)
- Create: `feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh`

The 31-unrelated-commits incident in now-playing's last session was nearly catastrophic. Autopilot needs to refuse to branch off a stale or ahead base.

- [ ] **Step 1: Write the check script**

Create `feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh`:

```bash
#!/usr/bin/env bash
# Check that local base branch is in sync with origin/<base>.
# Exit 0 if in sync, 1 if local is ahead (unpushed work), 2 if behind,
# 3 if diverged. Writes a one-line summary to stderr.
#
# Usage: check-base-sync.sh <base-branch>

set -euo pipefail

BASE="${1:-main}"
git fetch origin "$BASE" --quiet

LOCAL=$(git rev-parse "$BASE")
REMOTE=$(git rev-parse "origin/$BASE")

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "check-base-sync: local $BASE matches origin/$BASE" >&2
  exit 0
fi

AHEAD=$(git rev-list --count "origin/$BASE..$BASE")
BEHIND=$(git rev-list --count "$BASE..origin/$BASE")

if [[ "$AHEAD" -gt 0 && "$BEHIND" -eq 0 ]]; then
  echo "check-base-sync: local $BASE is $AHEAD commit(s) ahead of origin — UNPUSHED WORK" >&2
  echo "Consider: git push origin $BASE  (or investigate which commits)" >&2
  exit 1
elif [[ "$AHEAD" -eq 0 && "$BEHIND" -gt 0 ]]; then
  echo "check-base-sync: local $BASE is $BEHIND commit(s) behind origin — needs pull" >&2
  echo "Consider: git pull origin $BASE" >&2
  exit 2
else
  echo "check-base-sync: local $BASE has DIVERGED from origin ($AHEAD ahead, $BEHIND behind)" >&2
  exit 3
fi
```

- [ ] **Step 2: Wire into autopilot preconditions**

In `feature-workflow/skills/feature-autopilot/SKILL.md`, find the **Preconditions** section. Add a new precondition between "Working tree is clean" and "Read `.feature-workflow.yml`":

```markdown
3. **Local base branch is in sync with origin.** Run:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/skills/feature-autopilot/scripts/check-base-sync.sh" <base-branch>
   ```
   Exit codes:
   - 0 → in sync, proceed
   - 1 → local is ahead (unpushed work). **Pause and surface to user.** Branching off an ahead-base means the upcoming PR will include those unpushed commits, which is almost certainly not what the user wants. Recommend: push first, OR investigate whether those commits belong on a different branch.
   - 2 → local is behind. Run `git pull origin <base>` and re-run the check.
   - 3 → diverged. Pause and surface; resolution is manual.

   This catches the "parallel session left commits unpushed" failure mode.
```

- [ ] **Step 3: Manual verification**

```bash
chmod +x feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh
# Simulate ahead state:
mkdir -p /tmp/sync-check && cd /tmp/sync-check
git init && git commit --allow-empty -m "remote head"
git remote add origin /tmp/fake-origin.git
git init --bare /tmp/fake-origin.git
git push origin main
git commit --allow-empty -m "local ahead"
/Users/courtschuett/GitHub/schuettc/claude-code-plugins/feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh main
# Expected: exit 1, "1 commit(s) ahead" message
```

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh feature-workflow/skills/feature-autopilot/SKILL.md
chmod +x feature-workflow/skills/feature-autopilot/scripts/check-base-sync.sh
git add -u  # capture chmod
git commit -m "feat(autopilot): pre-flight check that local base is in sync with origin"
```

---

### Task A2: Mandatory worktree isolation for parallel subagents

**Files:**
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md`

The now-playing incident (B's implementation overlaid by C's branch switch) was the predictable consequence of two subagents sharing one working tree. Autopilot must mandate worktree isolation any time it spawns parallel subagents.

- [ ] **Step 1: Add a Parallel Dispatch Safety section to autopilot SKILL.md**

Insert after the existing "Reviewer-mode adaptations" section:

```markdown
## Parallel Dispatch Safety

Any time the autopilot spawns multiple subagents that touch the working tree concurrently, EACH subagent MUST run in its own worktree. Two subagents in the same checkout will clobber each other on branch switches.

**Rule:** when calling the Agent tool with intent to do git work, pass `isolation: "worktree"` if there is any other agent active in the same repo.

**This applies to:**
- Epic parallel-wave dispatch (Plan 3 / v9.8.0)
- Multiple `--respond` cycles running concurrently
- Any user-driven `/feature-autopilot X` followed by `/feature-autopilot Y` in adjacent sessions

**This does NOT apply to:**
- Reviewer subagents (read-only — no git operations)
- Subagents that only read files

**Recovery from a clobber:**
If a clobber has already happened (untracked files survived but tracked files were overwritten on branch checkout):
1. Check the loser's branch in `git ls-remote origin <branch>` — if it was pushed, recover from origin
2. Check `git fsck --lost-found` — orphaned commits may survive
3. Read the plan.md to identify what was lost; rebuild from any surviving artifacts (e.g., test files) plus the plan
4. **Never `--no-verify` the recovery commit** — pre-commit hooks may catch regressions

The recovery checklist itself is a sign of failure. Prefer worktree isolation upfront.
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/SKILL.md
git commit -m "feat(autopilot): mandate worktree isolation for parallel subagents"
```

---

## Phase B: Workflow YAML Race Conditions

The now-playing PR #141 logs show plan-review running 6 times for one plan, including AFTER a clean PASS. Root cause analysis points at two issues:

- **Plan-review label remained on PR after PASS.** Any subsequent push fires `synchronize`; the workflow's plan-review job re-runs (label still present + impl-review still absent = condition still true).
- **No concurrency control.** Same PR can have multiple workflow runs in flight — the latest verdict wins by timestamp but earlier ones leave noise + can confuse polling.

### Task B1: Workflow YAML — add concurrency control

**Files:**
- Modify: `feature-workflow/templates/feature-review-gemini.yml`
- Modify: `feature-workflow/templates/feature-review-codex.yml`

- [ ] **Step 1: Add concurrency block to both templates**

In each YAML, insert at the top level (between `env:` and `jobs:`):

```yaml
# Cancel in-progress runs for the same PR; the latest event wins.
# Prevents duplicate review comments from interleaving label-swap +
# synchronize events.
concurrency:
  group: feature-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

This ensures only one feature-review run is alive per PR at a time.

- [ ] **Step 2: Commit (each template separately for clean history)**

```bash
git add feature-workflow/templates/feature-review-gemini.yml feature-workflow/templates/feature-review-codex.yml
git commit -m "feat(workflow): cancel-in-progress runs per PR — prevents duplicate review comments"
```

---

### Task B2: Autopilot — remove plan-review label after PASS, before any push

**Files:**
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md`
- Modify: `feature-workflow/skills/feature-review-impl/submit.md`

The race that caused 23:45 plan-review re-fire AFTER a 23:37 PASS: the plan-review label was still on the PR when subsequent commits pushed. Synchronize fires → plan-review job re-runs (label condition still true) → reviewer re-evaluates → produces new verdict.

Fix: explicit "remove plan-review label IMMEDIATELY after PASS" in autopilot's verdict-handling.

- [ ] **Step 1: Update autopilot's "auto-advance on PASS" guidance**

In `feature-workflow/skills/feature-autopilot/SKILL.md`, find the section "Auto-advance rules at review gates". Update the Exit 0 rule:

```markdown
- **Exit 0 (PASS / CONDITIONAL PASS)** — advance immediately. **First action: remove the active review label from the PR (`plan-review` or `impl-review`)** to prevent subsequent pushes from re-firing the workflow:
  ```bash
  gh pr edit <pr-number> --remove-label plan-review   # or impl-review, as appropriate
  ```
  Then proceed to the next phase. Don't chase Should-fix nits after a clean pass; material recommendations can become **backlog items via the "Defer to backlog" classification in `respond.md`** (see Step 5/8 of the respond flow).
```

- [ ] **Step 2: Update feature-review-impl/submit.md label swap step**

Find the existing label-swap step (currently `gh pr edit ... --remove-label plan-review --add-label impl-review`). Replace with a TWO-STEP process to avoid the brief window when both labels are present:

```markdown
## Step 5: Swap Labels (external mode only)

The CI workflow's plan-review and impl-review jobs are mutually exclusive (the conditional check `contains 'plan-review' && !contains 'impl-review'` would still pass briefly if both labels are present during a swap). Do this as TWO separate operations with a short wait between, so the workflow sees a clean state at each step:

```bash
# Step 5a: remove plan-review and wait a moment for the workflow to register
gh pr edit <pr-number> --remove-label plan-review
sleep 3

# Step 5b: add impl-review (this is the trigger we want)
gh pr edit <pr-number> --add-label impl-review
```

The `sleep 3` gives GitHub Actions time to process the unlabeled event (which doesn't fire any job — workflow only listens to `labeled`, not `unlabeled`) before the labeled event arrives.
```

- [ ] **Step 3: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/SKILL.md feature-workflow/skills/feature-review-impl/submit.md
git commit -m "feat(autopilot): remove review label immediately after PASS; split label swap for clean events"
```

---

### Task B3: feature-init --update — refresh workflow YAML with confirmation

**Files:**
- Modify: `feature-workflow/skills/feature-init/SKILL.md`
- Modify: `feature-workflow/skills/feature-init/scripts/init.py`

`feature-init --update` already exists. We need it to overwrite the user's `.github/workflows/feature-review.yml` so the v9.7.3 concurrency fix actually propagates. Today the script may skip overwrite to be safe.

- [ ] **Step 1: Verify current behavior**

Read `feature-workflow/skills/feature-init/scripts/init.py`. Check what `--update` does to existing workflow files. If it already overwrites, document the v9.7.3-required refresh and move on. If it skips, add overwrite-with-confirmation.

- [ ] **Step 2: Add confirmation + overwrite path**

If `--update` skips: add a prompt before overwrite. Pseudocode:

```python
if existing_workflow_path.exists():
    existing = existing_workflow_path.read_text()
    if existing != template_text:
        print(f"Existing {existing_workflow_path} differs from current template.")
        print(f"  Local version may have customizations; template includes v9.7.3 fixes.")
        answer = input("Overwrite with current template? [y/N]: ")
        if answer.lower() != "y":
            print("Skipped. Re-run --update later or manually merge fixes.")
            return
```

If `--update` already does this, skip Step 2.

- [ ] **Step 3: Commit**

```bash
git add feature-workflow/skills/feature-init/
git commit -m "feat(init): --update prompts before overwriting workflow YAML"
```

---

## Phase C: Documentation

### Task C1: Pre-commit hook compatibility doc

**Files:**
- Create: `feature-workflow/skills/feature-autopilot/pre-commit-compat.md`
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md` (link to new doc)

The skylos/fallow pattern in now-playing showed pre-commit hooks can drag and block autopilot commits. Need a doc telling users (and subagents) how to handle it.

- [ ] **Step 1: Write the doc**

Create `feature-workflow/skills/feature-autopilot/pre-commit-compat.md`:

```markdown
# Pre-commit Hook Compatibility

Projects with pre-commit hooks (skylos, fallow, ruff, prettier, husky, etc.) can interact poorly with autopilot's per-task-commit pattern:

- Each task's commit runs the hooks. 20 tasks × 5s of hooks = 100s of overhead per feature.
- A hook failure breaks the subagent loop. The subagent sees `git commit` exit non-zero and reports BLOCKED.
- The temptation to use `--no-verify` is real but forbidden — see autopilot's "Never" list.

## What autopilot does NOT do

- Use `--no-verify` — ever. Pre-commit hooks exist for a reason; bypassing them ships regressions.
- Auto-fix hook output — fixing is a code change, requires task context.

## What autopilot SHOULD do

When a subagent's commit fails because a pre-commit hook rejected the change:

1. Subagent reports `DONE_WITH_CONCERNS` with the hook's stderr captured.
2. Orchestrator surfaces to user with the exact hook name and offending line(s).
3. User decides: fix the offense (re-dispatch subagent) or escalate.

## Recommended project setup

If you use autopilot heavily, prefer running heavy linters (skylos, fallow, ESLint-with-many-rules) in **CI only**, not as pre-commit hooks. Pre-commit is for quick local checks (formatting, basic syntax). Heavy analysis belongs in PR-level checks where:

- It runs once per push, not once per commit
- Output goes to the PR as a comment or check, not to the user's terminal
- Failure stops the PR, not the local workflow

For now-playing-style setups (skylos pre-commit + skylos CI both running):
- Drop the pre-commit version; keep the CI version
- Or configure skylos pre-commit to use `agent` mode only (which is lighter than full SAST)

## Bot comment noise in respond.md

If your CI runs many bot reviewers (skylos, dependabot, sonarcloud, gemini, codex), the PR thread fills with comments that aren't the structured review. `respond.md` Step 2 filters by `## Plan Review` / `## Implementation Review` prefix so non-review bot comments don't pollute the verdict classifier. If a bot's output is signal (e.g., a real security finding), surface it manually — autopilot's respond flow only processes the structured-review comments.
```

- [ ] **Step 2: Link from autopilot SKILL.md**

In `feature-workflow/skills/feature-autopilot/SKILL.md`, in the "Preconditions" or "Recovery patterns" section, add:

```markdown
## Pre-commit Hook Interaction

If your project has pre-commit hooks (skylos, fallow, ruff, prettier, husky, etc.), see [pre-commit-compat.md](pre-commit-compat.md) for how autopilot interacts with them. **Never** use `--no-verify` to bypass hooks — if a hook fails, the subagent should report BLOCKED with the failure detail.
```

- [ ] **Step 3: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/pre-commit-compat.md feature-workflow/skills/feature-autopilot/SKILL.md
git commit -m "docs(autopilot): pre-commit-compat guide; document --no-verify ban"
```

---

## Phase D: Polish

### Task D1: Version bump 9.7.2 → 9.7.3

**Files:**
- Modify: `feature-workflow/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump versions** (both files — use a careful sed or Python edit that preserves em-dashes in marketplace.json)

- [ ] **Step 2: Run the full test suite**

```bash
cd feature-workflow && venv/bin/pytest skills/shared/tests/ 2>&1 | tail -3
```

Expect 167 passed (no new tests in v9.7.3 — all changes are skill docs + workflow YAML + scripts).

- [ ] **Step 3: Commit**

```bash
git add feature-workflow/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump feature-workflow to v9.7.3 (autopilot hardening + workflow YAML fixes)"
```

### Task D2: PR, merge, tag, release

- [ ] Push branch, open PR titled `feat(feature-workflow): v9.7.3 — autopilot hardening from dogfood`
- [ ] Merge via gh
- [ ] Cut tag `feature-workflow-v9.7.3`
- [ ] Create GitHub release with notes covering all four phases

---

# Release 2: v9.8.0 — Epic Dispatch (minor)

Plan 3 from the original foundations spec, redesigned with the now-playing parallel-clobber incident as a forcing function.

**Headline:** `/feature-autopilot <epic-id>` walks the epic's children in dispatch order. Parallel children run in isolated worktrees. The epic completes when its last child ships.

**Premises:**
- Sequential is the default; parallel is opt-in
- Parallel-mode children EACH get their own worktree via `isolation: "worktree"`
- Sub-feature autopilots run in their own subagents (orchestrator only tracks IDs)
- `children:` ↔ `epic:` is bidirectional with auto-sync (mirrors `replaces:`)

---

## Phase A: Schema Sync — `epic:` ↔ `children:`

Mirrors the `replaces:` auto-sync from v9.7.2 but for the epic-relationship pair.

### Task A1: sync_epics.py helper

**Files:**
- Create: `feature-workflow/skills/shared/lib/sync_epics.py`
- Create: `feature-workflow/skills/shared/tests/test_sync_epics.py`

- [ ] **Step 1: Write tests first** (TDD)

Tests cover:
- Writing `children: [a, b]` on epic X auto-sets `epic: X` on a and b
- Writing `epic: X` on a feature auto-adds it to X's `children:` (appended, not reordered)
- Both directions, idempotent
- Missing target features skipped silently (validation surfaces them)
- Mutual references converge (no infinite recursion)
- Sync does NOT remove relationships — only adds (manual removal is user-driven)

- [ ] **Step 2: Implement sync_epics.py**

Structure follows sync_replaces.py:
```python
def sync_epics(project_root: Path) -> int:
    """Mirror epic ↔ children relationships across all features."""
    # Scan: build the union graph from both directions
    # Write: for each epic, ensure all referenced children have epic:<self>
    #        for each child with epic: X, ensure X's children: contains it
    # Idempotent: skip if already correct
```

- [ ] **Step 3: Wire into post_tool_use hook**

In `feature-workflow/hooks/post_tool_use.py`, add `sync_epics` BEFORE `run_dashboard` (alongside `sync_replaces`).

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/shared/lib/sync_epics.py feature-workflow/skills/shared/tests/test_sync_epics.py feature-workflow/hooks/post_tool_use.py
git commit -m "feat(hook): bidirectional sync of epic: ↔ children: (mirrors replaces: pattern)"
```

---

### Task A2: Validation — epic without children OR children without epic

**Files:**
- Modify: `feature-workflow/skills/shared/lib/run_dashboard.py` (extend _render_warnings)

Today the Validation Warnings section flags unknown refs + cycles. Add: when `type: Epic` but `children:` empty (after sync), warn the user. Their epic is effectively non-functional.

- [ ] **Step 1: Add check**

In `_render_warnings`, after the existing checks:

```python
for fid, ctx in by_id.items():
    if ctx.is_epic() and not ctx.children:
        lines.append(f"- ⚠️ Epic `{fid}` has no children — set `children: [...]` or change `type:` from Epic to Feature")
```

- [ ] **Step 2: Test + commit**

```bash
git add feature-workflow/skills/shared/lib/run_dashboard.py feature-workflow/skills/shared/tests/test_dashboard.py
git commit -m "feat(dashboard): warn on Epic features with no children"
```

---

## Phase B: Capture-Time Epic Improvements

### Task B1: Interview Q9e refinement

**Files:**
- Modify: `feature-workflow/skills/feature-capture/interview.md`

Q9e already asks about epics. Tighten the validation so the user gets a hint when the epic ID doesn't exist on disk.

- [ ] **Step 1: Update Q9e**

Add to the question's instructions:

```markdown
## Question 9e: Epic (Optional)

```
Is this part of a larger initiative (epic)? (epic ID, or leave blank)
Example: auth-overhaul
```

If the user provides an ID, validate it:
1. Check that `docs/features/<epic-id>/idea.md` exists
2. If it exists, verify its frontmatter has `type: Epic`
3. If either check fails:
   - Don't refuse — accept the value with a warning: "Note: `<epic-id>` doesn't exist (yet) as an Epic feature. You may want to capture the epic first with `/feature-capture` (type: Epic), then come back to this feature."
4. After the new feature's idea.md is written, the post_tool_use hook's sync_epics step will mirror this onto the epic's `children:` automatically.
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/skills/feature-capture/interview.md
git commit -m "feat(capture): validate epic reference at capture time; soft warning if epic doesn't exist"
```

---

## Phase C: Dispatch Engine

The core of v9.8.0. The autopilot detects `type: Epic` and switches behavior.

### Task C1: Epic detection in autopilot SKILL.md

**Files:**
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md`

- [ ] **Step 1: Add "Epic mode detection" at the top of autopilot logic**

Insert after the existing preconditions, before "Step 1: Plan":

```markdown
## Step 0: Detect Epic vs. Feature

Read `docs/features/<id>/idea.md`. If `type: Epic`, switch to **Epic Dispatch Mode** (see [epic-dispatch.md](epic-dispatch.md)). Otherwise continue with the standard linear pipeline below.

| `type:` value | Behavior |
|---|---|
| Feature / Enhancement / Bug Fix / Tech Debt | Standard linear plan → review → implement → review → ship |
| Epic | Epic Dispatch Mode — walk children in topo order |
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/SKILL.md
git commit -m "feat(autopilot): detect Epic type and route to dispatch mode"
```

---

### Task C2: epic-dispatch.md — the dispatcher procedure

**Files:**
- Create: `feature-workflow/skills/feature-autopilot/epic-dispatch.md`

This is the workflow document the autopilot follows when it sees `type: Epic`.

- [ ] **Step 1: Write the procedure**

```markdown
# Epic Dispatch Workflow

Invoked from `feature-autopilot/SKILL.md` Step 0 when the target feature has `type: Epic`.

## Step 1: Validate Epic Has Children

Read the epic's `idea.md` frontmatter. If `children: [...]` is empty or absent, refuse:
> "Epic `<id>` has no `children: [...]` in its frontmatter. Add the list of child feature IDs and re-run."

(The dashboard's Validation Warnings section also catches this — see Phase A2.)

## Step 2: Build Dispatch Plan

Read each child's `idea.md`. Build:
- The set of valid children (those whose idea.md exists)
- The dependency graph (each child's `dependsOn:`)
- The lifecycle state of each child (already-shipped children are skipped)

Compute dispatch order:
1. Filter out already-shipped children (lifecycle == completed)
2. Filter out tombstoned children (state in [replaced, abandoned])
3. Filter out paused children (state == paused — log "skipping paused child <id>")
4. Topo-sort remaining children by `dependsOn:`. Children at the same depth form a **wave**.
5. The `children:` array order within the epic resolves ties within a wave (preserves user intent).

Write the dispatch plan to `docs/features/<epic-id>/plan.md`:

```markdown
---
started: <YYYY-MM-DD>
---

# Dispatch Plan: <Epic Name>

## Wave 1 (no prerequisites)
- child-a
- child-b

## Wave 2 (depends on Wave 1)
- child-c

## Skipped
- child-d (already shipped)
- child-e (state: paused — waiting on vendor)
```

## Step 3: Mode Selection — Sequential or Parallel

Determine dispatch mode:

- **`--parallel` flag** OR all children in a wave have `parallelSafe: true` → parallel mode
- **Otherwise** → sequential mode (default)

Confirm with user before starting the first wave:
> "Dispatching <N> children in <mode> mode. First wave: <list>. Proceed? [y/N]"

## Step 4: Dispatch the Wave

### Sequential mode

For each child in the wave (one at a time):
1. Spawn subagent (NO `isolation` param — shares main checkout):
   ```
   Agent({
     subagent_type: "general-purpose",
     model: "sonnet",
     description: "Epic <epic-id>: autopilot child <child-id>",
     prompt: "Run /feature-workflow:feature-autopilot <child-id> from start to merged PR. Report DONE on success, BLOCKED if any review FAILs persist past the cap."
   })
   ```
2. Wait for completion. Capture verdict (DONE / BLOCKED).
3. If BLOCKED: pause epic, surface child's reason to user. Epic resumes when user re-runs `/feature-autopilot <epic-id>`.
4. If DONE: log success to epic's plan.md progress section. Continue to next child.

### Parallel mode

For all children in the wave (concurrently):
1. Spawn each subagent with `isolation: "worktree"`:
   ```
   Agent({
     subagent_type: "general-purpose",
     model: "sonnet",
     isolation: "worktree",
     description: "Epic <epic-id>: autopilot child <child-id> (parallel)",
     prompt: "Run /feature-workflow:feature-autopilot <child-id> from start to merged PR..."
   })
   ```
2. Wait for ALL to complete (don't cancel siblings on failure per Q2 default).
3. Aggregate results. If ANY child BLOCKED, pause epic.
4. Move to next wave only when current wave is fully done.

Concurrency cap (Q1 default): max 3 parallel subagents. If wave > 3, split into sub-batches of 3.

## Step 5: Advance Through Waves

After each wave completes, log to epic's plan.md and move to the next wave. Repeat Step 4 until all non-shipped children are shipped.

## Step 6: Epic Completion

When the last non-skipped child ships, offer to write the epic's `shipped.md`:

```markdown
---
shipped: <YYYY-MM-DD>
---

# Shipped: <Epic Name>

All <N> children landed:
- child-a (shipped <date>, PR #<N>)
- child-b (shipped <date>, PR #<N>)
- ...

Skipped:
- child-d (already shipped before epic started)
- child-e (paused — re-evaluate when unblocked)
```

User can decline. If declined, epic stays in_progress; user can ship manually with `/feature-ship <epic-id>` later.

## Recovery

If the epic dispatcher is interrupted (network failure, user pause), re-run `/feature-autopilot <epic-id>`. The dispatcher reads child lifecycle states from disk and resumes from the first non-shipped child. Idempotent.

## What's NOT in this dispatcher

- **No global rollback** if Wave 3 fails after Waves 1+2 shipped. Each child's PR is its own atomic unit. If you need to revert, revert each child's PR individually.
- **No cross-child code sharing.** Each child is its own PR, its own branch, its own review. The epic is coordination, not a meta-branch.
- **No live progress display** beyond the plan.md updates. Use `/feature-status <epic-id>` to check progress.
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/epic-dispatch.md
git commit -m "feat(autopilot): epic-dispatch workflow doc (sequential default, parallel opt-in)"
```

---

### Task C3: Update tests + integration verification

**Files:**
- Modify: `feature-workflow/skills/shared/tests/test_models.py` (epic-related model methods)
- Create test fixtures for an epic with children

- [ ] **Step 1: Add fixtures**

In `conftest.py`, add:

```python
@pytest.fixture
def epic_with_children(temp_project: Path) -> Path:
    """An epic with two children, all on disk."""
    features = temp_project / "docs" / "features"

    # The epic
    (features / "the-epic").mkdir(parents=True)
    (features / "the-epic" / "idea.md").write_text("""---
id: the-epic
name: The Epic
type: Epic
priority: P0
effort: Large
impact: High
children: [child-a, child-b]
created: 2026-05-16
---
# The Epic
""")

    # Child A
    (features / "child-a").mkdir()
    (features / "child-a" / "idea.md").write_text("""---
id: child-a
name: Child A
type: Feature
priority: P1
effort: Small
impact: Medium
epic: the-epic
created: 2026-05-16
---
# Child A
""")

    # Child B — depends on A
    (features / "child-b").mkdir()
    (features / "child-b" / "idea.md").write_text("""---
id: child-b
name: Child B
type: Feature
priority: P1
effort: Small
impact: Medium
epic: the-epic
dependsOn: [child-a]
created: 2026-05-16
---
# Child B
""")

    return temp_project
```

- [ ] **Step 2: Add a topo-sort helper in deps.py + tests**

`compute_dispatch_waves(epic_id, all_features) -> list[list[str]]` returns the waves.

- [ ] **Step 3: Run full suite**

```bash
cd feature-workflow && venv/bin/pytest skills/shared/tests/ 2>&1 | tail -3
```

Expect 175+ passing (167 baseline + 6 sync_epics + 2 epic validation + topo-sort tests).

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/shared/lib/deps.py feature-workflow/skills/shared/tests/test_deps.py feature-workflow/skills/shared/tests/conftest.py feature-workflow/skills/shared/tests/test_models.py
git commit -m "feat(deps): compute_dispatch_waves for epic topo-sort"
```

---

## Phase D: Polish

### Task D1: README — Epic Dispatch section

**Files:**
- Modify: `feature-workflow/README.md`

Document the epic dispatch UX with a small example.

- [ ] **Step 1: Add the section** (after "Per-Feature Review Override")

```markdown
## Epic Dispatch

Multi-feature initiatives can be coordinated as an Epic. The epic is a feature with `type: Epic` and a `children:` list:

```yaml
# docs/features/auth-overhaul/idea.md
---
id: auth-overhaul
name: Auth Overhaul
type: Epic
priority: P0
children: [user-roles, sso-saml, mfa-totp]
---
```

Each child references the epic:

```yaml
# docs/features/user-roles/idea.md
---
id: user-roles
type: Feature
epic: auth-overhaul
---
```

The hook auto-syncs both directions — write `epic:` on a child and the epic's `children:` updates, or vice versa.

Run `/feature-autopilot auth-overhaul` and the dispatcher walks the children in topo order. Sequential by default; pass `--parallel` to run independent children concurrently (each in its own worktree via `isolation: "worktree"`).

When the last child ships, the dispatcher offers to write the epic's `shipped.md`. Decline to keep the epic open.

See [skills/feature-autopilot/epic-dispatch.md](skills/feature-autopilot/epic-dispatch.md) for the full procedure.
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/README.md
git commit -m "docs(README): document Epic Dispatch (sequential + parallel modes)"
```

### Task D2: Version bump 9.7.3 → 9.8.0

Same pattern as previous versions.

### Task D3: Smoke test on a real epic

Pick an epic from now-playing or slay-the-spire. Wire `children:` properly. Run `/feature-autopilot <epic-id>` against it. Watch the dispatch. Capture findings.

### Task D4: PR, merge, tag, release

---

# Cross-cutting: Self-Review Checklist

After both releases ship:

1. **Spec coverage** — every one of the 8 dogfood items has a corresponding task. List any gaps.
2. **Type consistency** — `compute_dispatch_waves` signature stable across deps.py, epic-dispatch.md, tests.
3. **Backward compat** — pre-9.7.x and 9.7.x features keep working. The `epic:` field is optional everywhere; epics with empty children just generate a warning.
4. **Worktree safety** — every place autopilot spawns parallel subagents uses `isolation: "worktree"`. No exceptions.

---

# Risks

| Risk | Mitigation |
|---|---|
| Epic dispatcher in parallel mode generates worktree-clobber bugs (the very thing we're fixing) | Mandate `isolation: "worktree"`; smoke-test in D3 before tagging |
| Workflow YAML concurrency block breaks something in CI | Test against a real PR first (the v9.7.3 PR itself can serve as the test case) |
| `feature-init --update` overwrites user customizations | Confirmation prompt; diff displayed before overwrite |
| Epic dispatch + parallel + 3 children = subagent budget explosion | Q1 cap of 3 concurrent; document that running multiple `/feature-autopilot <epic>` calls compounds |
| `sync_epics` infinite-loops on circular epic refs | `is_epic()` already excludes nested epics; sync_epics will reject if a child has `type: Epic` |

---

# Execution Order

1. **v9.7.3 Phase A** (pre-flight + worktree-safety docs) — 2 tasks, ~1 hour
2. **v9.7.3 Phase B** (workflow YAML + label timing) — 3 tasks, ~2 hours
3. **v9.7.3 Phase C** (docs) — 1 task, ~30 min
4. **v9.7.3 Phase D** (polish + ship) — 2 tasks, ~30 min
5. **PR + merge + tag v9.7.3** — ~15 min
6. **v9.8.0 Phase A** (schema sync) — 2 tasks, ~2 hours
7. **v9.8.0 Phase B** (capture interview) — 1 task, ~15 min
8. **v9.8.0 Phase C** (dispatch engine) — 3 tasks, ~4 hours (the largest chunk)
9. **v9.8.0 Phase D** (polish + ship) — 4 tasks, ~1 hour
10. **PR + merge + tag v9.8.0** — ~15 min

Total estimated: 1 day of focused work, of which v9.8.0 Phase C is 30-40%. Subagent-driven execution can compress this; sequential human execution is the upper bound.

---

# Out of Scope (deferred to v9.9 / v10.x)

- **Pre-commit hook interception/translation** (Q5 default: doc only) — the v9.7.3 doc explains the pattern; auto-handling hook failures in autopilot is its own design
- **Internal review for Epic-level work** — Plan 2's internal review applies to individual children; the epic itself doesn't get reviewed today
- **Cross-epic dependencies** — Epic A depending on Epic B finishing first. Tractable but adds a second axis of topo-sort
- **Live progress UI** beyond plan.md updates — a `feature-status --epic <id> --live` would be nice; not in scope here
- **Subagent budget tracking** — knowing how many subagent invocations an epic dispatch will burn, before starting
