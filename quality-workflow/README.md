# quality-workflow

Sister plugin to [feature-workflow](../feature-workflow). Surfaces, triages, and drives resolution of static-analysis findings (skylos for Python, fallow for TS/JS) with the same backlog-and-epic discipline that `feature-workflow` provides for feature work.

> **Status: MVP (v0.2.1).** Three user-invocable skills, day-1 playbooks for skylos (13 rules) + fallow (12 rules), and the hook self-verification safety net. v0.2.1 honors skylos's `reason` field so suppressed findings (`# skylos: ignore`) no longer inflate active counts. Spec: [`docs/superpowers/specs/2026-05-22-quality-workflow-plugin-design.md`](../docs/superpowers/specs/2026-05-22-quality-workflow-plugin-design.md). Plan: [`docs/superpowers/plans/2026-05-22-quality-workflow-mvp.md`](../docs/superpowers/plans/2026-05-22-quality-workflow-mvp.md).

## Origin

`now-playing` was running pre-commit hooks for `skylos` and `fallow`. A manual `skylos pi/ -a` on 2026-05-22 reported **Grade F (57/100)** despite a week of clean commits. The skylos hook had been silently misconfigured for 7 days — the `entry:` line passed `pi/` as the path argument, causing skylos to look for staged files at `pi/pi/nowplaying/...` and report "No Python files found" → exit 0 every time. Several real quality regressions slipped through.

The lesson — **hook silence ≠ hook working** — became the central design property of this plugin: every hook the plugin installs MUST be self-verified by injecting a known-bad fixture and asserting exit 1.

## What's in scope (MVP — v0.2.1)

Three user-invocable skills plus the supporting library:

| Skill | What it does |
|---|---|
| `/quality-verify-hook` | Stages a known-bad fixture, runs `pre-commit run <hook-id>`, asserts non-zero exit. Then a clean fixture, asserts zero exit. **Run this first** after installing pre-commit hooks or editing `.pre-commit-config.yaml`. The hook silence-equals-working failure mode is the whole reason this skill exists. |
| `/quality-audit` | Read-only. Runs `skylos --quality --danger --secrets --sca --format json` + `fallow health` / `dupes` / `dead-code`. Writes a fingerprinted snapshot to `.claude/quality-snapshots/YYYY-MM-DD.json`. Renders a grade card + delta vs. previous snapshot (NEW / RESOLVED / PERSISTING) — **active counts only**. Suppressed findings (skylos `reason: "inline ignore comment"`) are retained in the snapshot for delta-tracking but excluded from headlines. |
| `/quality-unblock` | Triggered when a pre-commit hook fails. Per finding, looks up the rule in the day-1 playbook and presents three options: **fix in code**, **suppress with a required `# Why:`**, or **defer to a feature-workflow tech-debt epic**. Refuses bare suppressions; caps at 2 per session (mirrors feature-workflow v9.8.1's reviewer enforcement). Produces structured proposals — does not execute fixes itself. |

### v0.2.1 fix: honor skylos's `reason` field

Discovered while dogfooding in `now-playing`: skylos emits findings it knows are
suppressed by inline directives, just with `"reason": "inline ignore comment"`.
v0.2.0 ingested every item regardless and reported 180 findings when only 126
were genuinely active. v0.2.1's adapter sets `suppressed=True` on those items
and exposes `QualitySnapshot.active_findings()` / `SnapshotDiff.active_*` so the
audit headlines reflect what actually needs attention. Fallow does not surface
suppressions in JSON; its `// fallow-ignore-next-line` directives are audited
separately by the post-MVP `/quality-suppressions` skill.

## Installation + first run

1. Install the plugin: `/plugin install quality-workflow@schuettc-claude-code-plugins`
2. Ensure pre-commit is installed in your project: `pipx install pre-commit && pre-commit install`
3. **Verify your hooks before trusting them:**
   ```
   /quality-verify-hook
   ```
   If any hook reports `bad_passed=False`, fix the configuration before continuing — the hook is silently broken.
4. Take a baseline audit: `/quality-audit`
5. When a pre-commit hook fails: `/quality-unblock`

## What's NOT in MVP (deferred to v0.3+)

- `quality-suppressions` — audit ignores across the repo (rationale check, stale check). The library modules (`audit_suppressions.py`, `stale_suppressions_check.py`) are already in place; v0.3 wraps them as a user-facing skill.
- `quality-epic` — group PERSISTING findings into themed epics via `feature-workflow:feature-capture`
- `quality-baseline` — snapshot the current floor for ratchet-down enforcement
- `quality-trend` — show per-file / per-category movement across N snapshots
- Multi-tool composition (ruff, eslint, semgrep adapters)
- Per-project config loader (`.claude/quality-workflow.local.md`) — MVP uses code-level defaults

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
├── README.md
├── pytest.ini
├── fixtures/                                  Known-good/bad fixtures for quality-verify-hook
│   ├── skylos-bad.py / skylos-good.py
│   └── fallow-bad.ts / fallow-good.ts
├── playbooks/
│   ├── skylos.yaml                            13 day-1 rules + fallback
│   └── fallow.yaml                            12 day-1 rules + fallback
└── skills/
    ├── quality-audit/SKILL.md                 Read-only snapshot + diff
    ├── quality-unblock/SKILL.md               Triage failing hooks
    ├── quality-verify-hook/SKILL.md           Hook self-verification
    └── shared/
        ├── lib/
        │   ├── snapshot.py                    QualityFinding/QualitySnapshot + diff
        │   ├── skylos_adapter.py              skylos → unified findings
        │   ├── fallow_adapter.py              fallow → unified findings
        │   ├── playbook.py                    YAML rule→action loader
        │   ├── hook_verify.py                 Fixture-injection self-test
        │   ├── audit_suppressions.py          Walk repo, classify suppressions
        │   └── stale_suppressions_check.py    Strip + re-scan to find dead ignores
        └── tests/                             56 tests
```

## Tool requirements

- **Python projects**: [skylos](https://github.com/skylos-tool/skylos) installable via `uvx skylos`
- **TS/JS projects**: [fallow](https://github.com/fallow-tool/fallow) installable via `npx fallow`

The plugin shells out to both as subprocess; it doesn't bundle them. Always uses the latest version unless your project pins one.

## Cross-plugin integration

`quality-unblock`'s **defer** action and (post-MVP) `quality-epic` skill call `feature-workflow:feature-capture` with `category: tech-debt`. No protocol changes needed in `feature-workflow` — it already accepts metadata. The integration is one-way (quality → feature-workflow), and `feature-workflow` is unaware of `quality-workflow`.

## License

Same as the parent repo.
