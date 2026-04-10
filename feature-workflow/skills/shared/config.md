# Branch Configuration

All skills that create branches, open PRs, or merge code must read the project's branch config first.

## How to Read Config

Read `.feature-workflow.yml` in the project root. If it exists, use the values. If it doesn't exist, use defaults.

```yaml
branch:
  prefix: "feature/"    # default
  target: "dev"         # default
```

## How to Apply

| Config value | Used for | Example |
|---|---|---|
| `branch.prefix` | Branch naming: `<prefix><feature-id>` | `feat/auth-system` |
| `branch.target` | Base branch for `git checkout`, PR `--base`, and merge target | `dev` |

## Substitutions

Throughout the skill instructions, replace:
- `feature/<id>` → `<prefix><id>` (using the configured prefix)
- `dev` (as a branch name) → `<target>` (using the configured target)

For example, if config says `prefix: "feat/"` and `target: "main"`:
- `git checkout -b feature/auth-system` → `git checkout -b feat/auth-system`
- `gh pr create --base dev` → `gh pr create --base main`
- `git checkout dev && git pull` → `git checkout main && git pull`
