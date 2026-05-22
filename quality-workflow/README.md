# quality-workflow

Sister plugin to [feature-workflow](../feature-workflow). Surfaces, triages, and drives resolution of static-analysis findings (skylos for Python, fallow for TS/JS) with the same backlog-and-epic discipline that `feature-workflow` provides for feature work.

> **Status: scaffold (v0.1.0).** Spec is in [`docs/superpowers/specs/2026-05-22-quality-workflow-plugin-design.md`](../docs/superpowers/specs/2026-05-22-quality-workflow-plugin-design.md). MVP implementation plan is in [`docs/superpowers/plans/2026-05-22-quality-workflow-mvp.md`](../docs/superpowers/plans/2026-05-22-quality-workflow-mvp.md). Skills are not yet implemented.

## Origin

`now-playing` was running pre-commit hooks for `skylos` and `fallow`. A manual `skylos pi/ -a` on 2026-05-22 reported **Grade F (57/100)** despite a week of clean commits. The skylos hook had been silently misconfigured for 7 days — the `entry:` line passed `pi/` as the path argument, causing skylos to look for staged files at `pi/pi/nowplaying/...` and report "No Python files found" → exit 0 every time. Several real quality regressions slipped through.

The lesson — **hook silence ≠ hook working** — became the central design property of this plugin: every hook the plugin installs MUST be self-verified by injecting a known-bad fixture and asserting exit 1.

## What's in scope (MVP)

Three skills + the data contract + per-rule playbooks:

| Skill | What it does |
|---|---|
| `quality-audit` | Read-only. Runs `skylos -a --format json` + `fallow health` + `fallow dupes`. Writes a structured snapshot to `.claude/quality-snapshots/YYYY-MM-DD.json`. Renders a grade card + delta vs. previous snapshot (NEW / RESOLVED / PERSISTING by fingerprint diff). |
| `quality-unblock` | Triggered when a pre-commit hook fails. Parses the JSON output. Per finding offers three choices: **fix in code**, **suppress with a required `# Why:`**, or **defer → `feature-workflow:feature-capture`**. Refuses bare suppressions. |
| `quality-verify-hook` | Stages a known-bad fixture, runs `pre-commit run <hook-id>`, asserts exit 1. Then a clean fixture, asserts exit 0. Run at install and after editing `.pre-commit-config.yaml`. The lesson, codified. |

## What's NOT in MVP

Deferred to v0.2+:

- `quality-suppressions` — audit ignores across the repo (rationale check, stale check)
- `quality-epic` — group PERSISTING findings into themed epics via `feature-workflow:feature-capture`
- `quality-baseline` — snapshot the current floor for ratchet-down enforcement
- `quality-trend` — show per-file / per-category movement across N snapshots
- Multi-tool composition (ruff, eslint, semgrep adapters)

## Cross-plugin integration

`quality-epic` (post-MVP) calls `feature-workflow:feature-capture` with `category: tech-debt`. No protocol changes needed in `feature-workflow` — it already accepts metadata. The integration is one-way (quality → feature-workflow), and `feature-workflow` is unaware of `quality-workflow`.

## Tool requirements

- **Python projects**: [skylos](https://github.com/skylos-tool/skylos) installable via `uvx skylos`
- **TS/JS projects**: [fallow](https://github.com/fallow-tool/fallow) installable via `npx fallow`

The plugin shells out to both as subprocess; it doesn't bundle them.

## Layout

```
quality-workflow/
├── .claude-plugin/
│   └── plugin.json
├── skills/                       (MVP skills go here)
│   └── shared/
│       ├── lib/                  (Python helpers)
│       │   ├── audit_suppressions.py        # prototype: walk repo, classify suppressions
│       │   └── stale_suppressions_check.py  # prototype: strip + re-scan, find dead ignores
│       └── tests/
└── hooks/                        (PostToolUse / PreCommit installers)
```

The two `lib/` files are working prototypes from the 2026-05-22 now-playing session. They hard-code `REPO = "/Users/courtschuett/GitHub/schuettc/now-playing"`; the MVP turns them into proper modules that take `project_root` as a parameter.

## License

Same as the parent repo.
