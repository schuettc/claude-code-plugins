# Epic Dispatch Workflow

Invoked from `feature-autopilot/SKILL.md` Step 0 when the target feature has `type: Epic`.

The dispatcher walks the epic's children in topo order, running `/feature-autopilot <child-id>` in a subagent for each. Sequential by default; opt into parallel with the `--parallel` flag on the autopilot invocation. Parallel subagents each run in their own worktree via `isolation: "worktree"` (mandatory per autopilot's Worktree Isolation rule).

## Step 1: Validate Epic Has Children

Read the epic's `idea.md` frontmatter. If `children: [...]` is empty or absent, refuse:

> "Epic `<id>` has no `children: [...]` in its frontmatter. Set the list of child feature IDs and re-run. The dashboard hook's `sync_epics` step also auto-populates `children:` from any feature with `epic: <id>` set."

(The dashboard's Validation Warnings section catches this gap on dashboard regen too — see `_render_warnings` in `run_dashboard.py`.)

## Step 2: Compute Dispatch Waves

Use the shared helper:

```python
from deps import compute_dispatch_waves
waves = compute_dispatch_waves(epic_id, by_id)
```

**Single repo:** build `by_id` from this repo's `docs/features/` (the standard scan).

**Multi-repo workspace** (a `.feature-workspace.yml` exists at the root, and the epic's `children:` use `repo:id` refs like `engine:engine-api`): build a namespaced `by_id` spanning every member, then dispatch unchanged:

```python
from run_dashboard import build_workspace_by_id
by_id = build_workspace_by_id(workspace_root)   # bare id for workspace-own; "<dir>:<id>" for members
waves = compute_dispatch_waves(epic_id, by_id)   # cross-repo deps via "<dir>:<id>" in dependsOn
```

A cross-repo child names its prerequisites in the same namespaced form (`dependsOn: [engine:engine-api]`), so producer-first ordering falls out of the normal topo-sort.

`waves` is `list[list[str]]`. Each inner list is a parallel-safe wave. Filters applied:
- Already-shipped children skipped (lifecycle == completed)
- Tombstoned children skipped (state in [replaced, abandoned])
- Paused children skipped (state == paused — log "skipping paused child <id>")
- Order within a wave follows the epic's `children:` array order

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
- child-d (already shipped, PR #N)
- child-e (state: paused — waiting on vendor)
```

## Step 3: Mode Selection

Determine dispatch mode from autopilot arguments:

- `--parallel` flag on the autopilot invocation → parallel mode
- Otherwise → sequential mode (default)

Confirm with the user before starting the first wave:

> "Dispatching `<N>` children in `<sequential|parallel>` mode. First wave: `<list>`. Proceed? [y/N]"

## Step 4: Dispatch the Wave

### Sequential mode (default)

For each child in the wave, one at a time:

```python
# REQUIRED: isolation:"worktree" per autopilot's Worktree Isolation rule
result = Agent(
    subagent_type="general-purpose",
    model="sonnet",
    isolation="worktree",
    description=f"Epic {epic_id}: autopilot child {child_id}",
    prompt=(
        f"Run /feature-workflow:feature-autopilot {child_id} from start to merged PR. "
        f"Report DONE on success, BLOCKED if any review FAILs persist past the cap."
    ),
)
```

After each child:
- DONE → log success to the epic's plan.md progress section, continue to next child
- BLOCKED → pause the epic, surface the reason to user. Epic resumes when user re-runs `/feature-autopilot <epic-id>` (the dispatcher reads each child's lifecycle state from disk and resumes from the first non-shipped child — idempotent).

### Parallel mode

For all children in the wave, concurrently:

```python
# Each subagent gets its own worktree — mandatory for parallel dispatch
results = [
    Agent(
        subagent_type="general-purpose",
        model="sonnet",
        isolation="worktree",
        description=f"Epic {epic_id}: autopilot child {child_id} (parallel)",
        prompt=(
            f"Run /feature-workflow:feature-autopilot {child_id} from start to merged PR. "
            f"Report DONE on success, BLOCKED if any review FAILs persist past the cap."
        ),
    )
    for child_id in wave
]
```

Concurrency cap: max 3 parallel subagents per wave. If a wave has more than 3 children, split it into sub-batches of 3 and dispatch sequentially-of-parallel-batches.

Wait for ALL subagents in a batch to complete. Sibling cancellation on failure is NOT done — let in-flight siblings finish, then pause the epic if any failed.

Aggregate results:
- All DONE → advance to next wave
- Any BLOCKED → pause epic, surface aggregate to user with per-child status

### Cross-repo children (workspace)

When a child ref is namespaced (`engine:engine-api`), split it with `parse_feature_ref` and run the child **inside its member repo**, not the workspace root:

```python
from workspace import parse_feature_ref
member_dir, child_local_id = parse_feature_ref(child_ref)   # ("engine", "engine-api")
```

- `member_dir is None` → workspace-own child, dispatch exactly as the single-repo case above.
- otherwise → direct the subagent into `./<member_dir>` (a full nested clone) before running autopilot:

```python
prompt = (
    f"cd into the workspace member repo ./{member_dir}, then run "
    f"/feature-workflow:feature-autopilot {child_local_id} from start to merged PR. "
    f"That member is its own git repo — its branch/PR/merge all target the member's "
    f"own remote (use the member's .feature-workflow.yml for branch.target/reviewer). "
    f"Report DONE on success, BLOCKED if any review FAILs persist past the cap."
)
```

The child's worktree is created **within its member clone** (the autopilot's Worktree Isolation rule applies inside `./<member_dir>`), so parallel cross-repo children never collide — they're in different repos entirely. The epic doc, plan.md, and progress log stay in the **workspace** `docs/features/<epic-id>/`; only the child's code/feature-docs live in the member.

> Cross-repo dispatch coordinates independent member-repo PRs. There is no meta-branch and no cross-repo rollback — revert a shipped child by reverting its member PR. Validate the end-to-end flow against a real workspace before relying on unattended cross-repo autopilot.

## Step 5: Advance Through Waves

After each wave completes, append a progress entry to the epic's `plan.md`:

```markdown
## Progress Log

- 2026-05-16 14:30 — Wave 1 dispatched (sequential): child-a → PR #142 merged, child-b → PR #143 merged
- 2026-05-16 15:15 — Wave 2 dispatched (sequential): child-c → PR #144 merged
```

Move to the next wave only when the current wave is fully complete (no BLOCKED children).

## Step 6: Epic Completion

When the last non-skipped child ships, offer to write the epic's `shipped.md`:

```markdown
---
shipped: <YYYY-MM-DD>
---

# Shipped: <Epic Name>

All `<N>` children landed:
- child-a (shipped 2026-05-16, PR #142)
- child-b (shipped 2026-05-16, PR #143)
- child-c (shipped 2026-05-16, PR #144)

Skipped:
- child-d (already shipped before epic started)
- child-e (state: paused — re-evaluate when unblocked)
```

The user can decline. If declined, the epic stays in_progress; user can ship manually with `/feature-ship <epic-id>` later.

After shipping, the epic appears in the dashboard's Completed section, and its Epics-rollup row shows N/N done.

## Recovery

Re-running `/feature-autopilot <epic-id>` after an interruption (network failure, user pause, BLOCKED child) is safe and idempotent:

1. The dispatcher re-computes waves from disk (each child's lifecycle reflects its file state)
2. Already-shipped children are skipped
3. Tombstoned and paused children are skipped
4. The dispatcher resumes from the first remaining wave

No state is held in memory across runs.

## What This Dispatcher Does NOT Do

- **No global rollback.** Each child's PR is its own atomic unit. If Wave 3 fails after Waves 1+2 shipped, revert each shipped child's PR individually.
- **No cross-child code sharing.** Each child is its own PR, branch, review cycle. The epic is coordination, not a meta-branch.
- **No live progress UI** beyond the plan.md updates. Use `/feature-status <epic-id>` to check progress; the Epics rollup on the dashboard shows aggregate counts.
- **No nested epic dispatch.** A child with `type: Epic` is rejected by `sync_epics` and excluded from dispatch. Nested epics aren't supported in v9.8.0.
- **No internal-review propagation to children.** The epic's own `review:` field doesn't apply to its children — each child's effective review mode is computed from its own `review:` and the project default. Children with `review: internal` run internal review; children with no override run the project's CI reviewer.
