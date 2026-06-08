---
name: feature-deploy
description: Coordinate a multi-repo deploy across a workspace's member repos in producer-first order. Use after a cross-repo epic's children have all merged and you need to release the members in dependency order (e.g. deploy the API producer before its consumers).
user-invocable: true
---

# Coordinated Deploy

You are executing the **COORDINATED DEPLOY** workflow — releasing a multi-repo
workspace's members in the order the manifest declares, so a producer ships
before the consumers that depend on it.

This skill only applies inside a **multi-repo workspace** (a `.feature-workspace.yml`
at the root). A single repo deploys itself; there is nothing to coordinate.

## Step 1: Confirm Workspace + Read Deploy Groups

```python
import sys
sys.path.insert(0, "<plugin>/skills/shared/lib")   # CLAUDE_PLUGIN_ROOT
from workspace import is_workspace, load_deploy_groups, resolve_target_repo

if not is_workspace("."):
    # Not a workspace — refuse.
    ...

groups = load_deploy_groups(".")   # [{group, dir}, ...] in authored order
```

If `groups` is empty, tell the user:

> "No `deploy:` groups in `.feature-workspace.yml`. Add them in producer-first
> order, one per member to release, e.g.:
> ```
> deploy:
>   - { group: engine-stack, dir: engine }
>   - { group: app-stack, dir: app }
> ```
> Order is the deploy order — the producer of a contract goes above its consumers."

The order in the manifest **is** the deploy order. Do not reorder it. The author
encodes producer-first sequencing by listing the producer's group first.

## Step 2: Scope (optional)

`/feature-deploy` with no argument walks **all** groups in order.

`/feature-deploy <epic-id>` scopes to the members touched by that epic: read the
epic's `children:` (in the workspace `docs/features/<epic-id>/`), map each child's
`repo:id` to its member dir with `parse_feature_ref`, and keep only the deploy
groups whose `dir` is in that set — still in manifest order. Tell the user which
groups were selected and which were skipped.

## Step 3: Preflight Each Member

Before deploying anything, verify every selected member is releasable. For each
group's `dir`, resolve the repo and check it's clean and merged:

```bash
git -C <dir> status --porcelain        # must be empty (no uncommitted changes)
git -C <dir> rev-parse --abbrev-ref HEAD   # expect the member's release branch (its branch.target)
```

Resolve the member's release branch from **its own** `.feature-workflow.yml`
(`branch.target`) via `resolve_target_repo`, not the workspace's. If any member
is dirty or not on its release branch, stop and report — do not start a partial
deploy.

## Step 4: Deploy Group by Group, In Order

Walk `groups` top to bottom. For each group, **stop and confirm** before running:

> "Deploy group `engine-stack` (member `engine`)? This is step 1 of N. [y/N]"

Each repo owns its deploy command — this skill does not assume one. Look in the
member for its release entry point, in this order:
1. A `just deploy` / `just release` recipe (`just -f <dir>/justfile --list`)
2. A documented deploy command in the member's `README.md` or `CLAUDE.md`
3. Ask the user for the command if none is discoverable

Run it scoped to the member (`just -f <dir>/justfile deploy`, or `cd <dir> && ...`).

**Gate before advancing.** A producer must be live and healthy before its
consumers deploy. After each group:
- Success → log it (Step 5) and move to the next group.
- Failure → **halt the sequence**. Report which groups deployed, which failed,
  and which were not attempted. Do not continue to consumers of a failed producer.

There is no automatic rollback across groups — earlier groups stay deployed.
Surface the partial state clearly so the user decides whether to roll the
producer back or fix forward.

## Step 5: Record the Deploy

Append a deploy log to the epic's `plan.md` (workspace `docs/features/<epic-id>/`),
or to the workspace `docs/` if unscoped:

```markdown
## Deploy Log

- 2026-06-07 — engine-stack (engine) ✅
- 2026-06-07 — app-stack (app) ✅ (after engine-stack healthy)
```

## What This Does NOT Do

- **No deploy command of its own.** It orders and gates; each member defines how it ships.
- **No cross-group rollback.** Each member's deploy is atomic to that member.
- **No health probing beyond the member's own deploy exit status** unless the
  member's deploy command includes its own smoke check. If you need a contract
  gate (can-i-deploy / contract tests) between producer and consumer, run it as
  the producer group's final step before confirming the next group.
- **No reordering.** Manifest order is authoritative; fix ordering by editing `deploy:`.
