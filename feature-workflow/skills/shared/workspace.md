# Multi-Repo Workspace Awareness

Most projects are a single repo — ignore this file. It applies only when the
current root holds a `.feature-workspace.yml` manifest: a **workspace**, a thin
coordination repo with member repos nested inside it as independent (gitignored)
clones. Set one up with `/feature-init --workspace`.

## The one rule that makes single-repo work "just work"

A member is a **full clone** living in the working tree (e.g. `./engine`). To do
ordinary single-repo feature work on a member, **`cd` into it and run the normal
commands**:

```bash
cd engine
/feature-capture            # idea.md lands in engine/docs/features/
/feature-plan <id>          # branch/PR/merge all target engine's own remote
/feature-ship <id>
```

Once cwd is the member, every path (`docs/features/…`), every `git`, and every
`gh` resolves to that member exactly as in a standalone repo. Its branch settings
come from the member's **own** `.feature-workflow.yml`. Nothing else changes.

From the workspace root, address a member without `cd` using the allowlisted
forms (already in `.claude/settings.json`): `git -C engine …`, `gh -R <owner/engine> …`.

## Where a feature's docs belong (3 scopes)

| Scope | Where the feature lives |
|-------|-------------------------|
| Touches **one** member | that member's `docs/features/` (`cd <member>`) |
| Workspace-only (coordination, cross-cutting docs) | the workspace's own `docs/features/` |
| Touches **2+** members | an **epic** in the workspace `docs/features/`, one child per member |

## Cross-repo epics

A cross-repo epic is a normal `type: Epic` feature in the workspace whose
`children:` use **namespaced refs** — `<member-dir>:<id>`:

```yaml
type: Epic
children: [engine:engine-api, app:app-ui]
```

A child names cross-repo prerequisites the same way: `dependsOn: [engine:engine-api]`,
which gives producer-first dispatch order for free. `/feature-autopilot <epic-id>`
dispatches each child inside its member repo. See
[../feature-autopilot/epic-dispatch.md](../feature-autopilot/epic-dispatch.md).

## Contracts and deploys

The manifest can declare standing **contracts** (producer → consumers) and ordered
**deploy** groups:

```yaml
contracts:
  - { id: engine:engine-api, owner: engine, consumers: [app], kind: http }
deploy:
  - { group: engine-stack, dir: engine }   # producer first
  - { group: app-stack, dir: app }
```

- Editing a producer member surfaces a one-time warning steering contract reshapes
  into a producer-first epic (post_tool_use hook → `build_contract_warning`).
- `/feature-deploy [<epic-id>]` releases members in the manifest's deploy order,
  gating each producer healthy before its consumers.

## Aggregated dashboard

In a workspace, the dashboard hook auto-detects the manifest and writes an
**aggregated** `docs/features/DASHBOARD.md` — a per-repo roll-up plus combined
In Progress / Backlog / Epics across the workspace and every member. Editing a
member feature also refreshes the workspace aggregate (walk-up in the hook).

## Helpers (shared/lib/workspace.py)

| Function | Purpose |
|----------|---------|
| `is_workspace(root)` | manifest present? |
| `load_members(root)` | `[{dir, repo}]` |
| `resolve_target_repo(root, target)` | which dir/root/gh-slug an op targets |
| `parse_feature_ref` / `format_feature_ref` | `repo:id` ↔ `(repo, id)` |
| `load_contracts` / `contract_consumers` / `build_contract_warning` | contract topology + warning |
| `load_deploy_groups` / `select_deploy_groups` | ordered deploy groups |
| `run_dashboard.build_workspace_by_id(root)` | namespaced `by_id` for cross-repo dispatch |
