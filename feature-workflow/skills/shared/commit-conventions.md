# Commit Message Conventions

Every commit this workflow prescribes MUST use a **Conventional Commits** message.
Projects commonly enforce a `commit-msg` git hook that rejects anything else — a
non-conventional verb like `plan(...)`, `implement(...)`, `ship(...)`,
`review(...)`, or `feature(...)` will be **rejected** and break the workflow.

## Allowed types

```
feat | fix | docs | style | refactor | perf | test | build | ci | chore | revert
```

Format: `type(<scope>): <subject>` with an optional `!` for breaking changes,
e.g. `docs(my-feature): submit plan for review`.

The enforcing regex looks like:

```
^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: 
```

## Which type for which artifact

| Artifact committed | Type |
|--------------------|------|
| `idea.md`, `plan.md`, `shipped.md` (and other feature docs) | `docs(<id>): ...` |
| Implementation code | `feat(<id>): ...` / `fix(<id>): ...` as appropriate |
| Review-feedback fixes | `fix(<id>): ...` |
| Config / gitignore / CI wiring | `chore(<id>): ...` / `ci(<id>): ...` |

The plan, idea, and shipped files are **documentation**, so they always commit as
`docs(<id>): ...`. Do **not** invent a `plan` type or any other non-conventional
verb — there is no `plan` Conventional Commits type, and the `commit-msg` hook
will reject it.
