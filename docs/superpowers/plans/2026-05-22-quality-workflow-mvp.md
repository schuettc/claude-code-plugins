# Quality-Workflow Plugin: MVP Implementation Plan (v0.1.0 → v0.2.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship the three MVP skills (`quality-audit`, `quality-unblock`, `quality-verify-hook`) plus the data contract and per-rule playbook scaffolding, taking `quality-workflow` from scaffold (v0.1.0) to functional (v0.2.0).

**Architecture:** Mirrors `feature-workflow`'s shape (skills + shared lib + hooks + tests). Each skill is markdown + a Python helper. Snapshots are JSON files under `.claude/quality-snapshots/`. Rule playbooks live in `quality-workflow/playbooks/` as YAML. No databases, no daemons — just files Claude can read.

**Spec:** `docs/superpowers/specs/2026-05-22-quality-workflow-plugin-design.md`

**Tech Stack:** Python 3 (stdlib + optional `yaml`), pytest, markdown skill files. Shells out to `uvx skylos` and `npx fallow`.

---

## Decisions baked in (push back before executing)

1. **Plugin name: `quality-workflow`.** Symmetric with `feature-workflow`. The spec lists `code-quality` and `quality-ratchet` as alternatives; the marketplace and scaffold are already wired with `quality-workflow`.
2. **Snapshots live at `.claude/quality-snapshots/` per project**, gitignored by default. Mirrors how feature-workflow uses `docs/features/`.
3. **No new pytest hookup for now.** Tests live in `quality-workflow/skills/shared/tests/` with sys.path injection (same pattern as feature-workflow). A `pytest.ini` at the plugin root keeps configs isolated.
4. **Rule playbooks ship as YAML** under `quality-workflow/playbooks/skylos.yaml` and `playbooks/fallow.yaml`. Day-1 cover the top 20 rule_ids each. Unknown rules get a generic "fix/suppress/defer" prompt.
5. **`quality-unblock` does NOT auto-fix code.** It produces a structured proposal (which option, what code change, what justification text); the user accepts or rejects. The plugin is opinionated about WHAT but not WHEN.
6. **Hook self-test runs at install via a slash command, not as a daily background process.** `quality-verify-hook` is invoked manually after editing `.pre-commit-config.yaml`. No watcher daemon.
7. **Skylos `--diff` is not usable** for staged-files gating per the spec. Only `skylos agent pre-commit --format json` is suitable for hook-level gating. Full `skylos -a` runs are for the snapshot path.

---

## Open questions (default if no answer)

| # | Question | Default |
|---|---|---|
| Q1 | Where does the per-project config live? | `.claude/quality-workflow.local.md` (matching the plugin-settings pattern) |
| Q2 | Test-fixture symlink-write false positives in skylos | Day-1 ship a generic `ignore_test_patterns: ["**/tests/**"]` config option; revisit when we hit a project without that convention |
| Q3 | What happens if `skylos` or `fallow` isn't installed? | Surface a one-line error pointing at the install command; do NOT silently no-op |
| Q4 | Snapshot retention | Keep all snapshots indefinitely (they're small JSON, gitignored). Add a `quality-prune` skill in v0.3 if it becomes a problem |
| Q5 | Should `quality-audit` also run security tools (e.g., `gitleaks`)? | No — keep MVP focused on skylos + fallow. Multi-tool composition is v0.3 |

---

## File structure

### New
- `quality-workflow/.claude-plugin/plugin.json` — exists from scaffold
- `quality-workflow/skills/quality-audit/SKILL.md` — read-only snapshot
- `quality-workflow/skills/quality-unblock/SKILL.md` — triage failed hooks
- `quality-workflow/skills/quality-verify-hook/SKILL.md` — fixture self-test
- `quality-workflow/skills/shared/lib/snapshot.py` — write/read/diff snapshots
- `quality-workflow/skills/shared/lib/skylos_adapter.py` — wrap `skylos agent pre-commit --format json` and `skylos -a --format json`
- `quality-workflow/skills/shared/lib/fallow_adapter.py` — wrap `fallow health`, `fallow dupes`, `fallow audit`
- `quality-workflow/skills/shared/lib/fingerprint.py` — stable identity helpers (from skylos `fingerprint` field; synthesized for fallow)
- `quality-workflow/skills/shared/lib/playbook.py` — load YAML rule playbooks, resolve rule_id → action template
- `quality-workflow/skills/shared/lib/hook_verify.py` — fixture-injection + assert-exit-code helper
- `quality-workflow/skills/shared/tests/` — tests for each lib module
- `quality-workflow/playbooks/skylos.yaml` — day-1 rule mappings
- `quality-workflow/playbooks/fallow.yaml` — day-1 rule mappings
- `quality-workflow/pytest.ini` — test config
- `quality-workflow/skills/shared/lib/audit_suppressions.py` — exists; needs `REPO` parameterization
- `quality-workflow/skills/shared/lib/stale_suppressions_check.py` — exists; needs `REPO` parameterization

### Modified
- `quality-workflow/README.md` — status update from "scaffold" to "MVP"
- `quality-workflow/.claude-plugin/plugin.json` — version bump 0.1.0 → 0.2.0

### Not in MVP
- `quality-epic` — uses MVP outputs to call `feature-workflow:feature-capture`. v0.3
- `quality-suppressions` (full audit skill wrapping the existing prototypes)
- `quality-baseline`, `quality-trend`

---

## Phase A: Data + Adapters

### Task A1: `snapshot.py` — write/read/diff

**Files:**
- Create: `quality-workflow/skills/shared/lib/snapshot.py`
- Create: `quality-workflow/skills/shared/tests/test_snapshot.py`

`QualityFinding` and `QualitySnapshot` dataclasses + read/write JSON + fingerprint-keyed diff (NEW / RESOLVED / PERSISTING).

- [ ] **Step 1: Tests first** — round-trip dataclasses through JSON; diff returns three correct sets given fixture snapshots.
- [ ] **Step 2: Implement** — pure stdlib, no third-party dependencies.
- [ ] **Step 3: Commit** — `feat(snapshot): QualityFinding/QualitySnapshot data + fingerprint diff`.

### Task A2: `skylos_adapter.py`

**Files:**
- Create: `quality-workflow/skills/shared/lib/skylos_adapter.py`
- Create: `quality-workflow/skills/shared/tests/test_skylos_adapter.py`

Two modes: `agent_pre_commit_json(staged_files)` for hook gating, `full_audit_json(project_root)` for snapshots. Both return `list[QualityFinding]`.

- [ ] **Step 1: Tests** — feed fixture JSON output, assert correct mapping to `QualityFinding`. Use captured real outputs from now-playing (`.claude/quality-snapshots/suppressions-2026-05-22.json` is one starting point).
- [ ] **Step 2: Implement** — subprocess to `uvx skylos ... --format json --no-upload`. Banner-line stripping (the prototype already shows the pattern).
- [ ] **Step 3: Error handling** — if `uvx`/`skylos` missing, surface a clear error.
- [ ] **Step 4: Commit**.

### Task A3: `fallow_adapter.py`

**Files:**
- Create: `quality-workflow/skills/shared/lib/fallow_adapter.py`
- Create: `quality-workflow/skills/shared/tests/test_fallow_adapter.py`

`health_json(project_root)` → grade + per-file scores; `dupes_json(project_root)` → clone groups; `audit_json(project_root, base_ref)` → changeset-scoped findings (for hook gating, matches the `fallow audit` pattern that's already in now-playing's pre-commit).

- [ ] **Step 1: Tests** — same as A2; fixture outputs.
- [ ] **Step 2: Implement** — `npx fallow <subcommand> --json` (verify flag names match real CLI).
- [ ] **Step 3: Fingerprint synthesis** — fallow doesn't expose `fingerprint` field; synthesize from `{file, rule, function_name or line_range}` so diffs are stable across runs.
- [ ] **Step 4: Commit**.

### Task A4: `playbook.py` + day-1 YAML

**Files:**
- Create: `quality-workflow/skills/shared/lib/playbook.py`
- Create: `quality-workflow/playbooks/skylos.yaml`
- Create: `quality-workflow/playbooks/fallow.yaml`
- Create: `quality-workflow/skills/shared/tests/test_playbook.py`

Loader resolves `rule_id` → `[Action]` (where Action = fix-suggestion / suppress-with-required-Why / defer-to-feature-capture). Day-1 playbooks cover the top 20 rule_ids per tool as observed in real now-playing output.

- [ ] **Step 1: Tests** — load YAML, resolve known rule, resolve unknown rule (gets fallback action set), validate `require_why: true` is honored.
- [ ] **Step 2: Implement** — minimal YAML loader (stdlib `yaml` if available, else simple key:value parser matching feature-workflow's frontmatter approach).
- [ ] **Step 3: Author day-1 YAML** — pick the top 20 rule_ids from real now-playing snapshot output. SKY-Q302, SKY-D216, SKY-L029, SKY-Q501, SKY-D211, SKY-D215 are starters. Add fallow's most common (complexity, dead-export, clone-group).
- [ ] **Step 4: Commit**.

---

## Phase B: `quality-verify-hook` (the safety-net skill)

This goes first among the user-facing skills because the entire plugin's value depends on it. The spec is explicit: hooks must be self-verified or they don't count.

### Task B1: `hook_verify.py`

**Files:**
- Create: `quality-workflow/skills/shared/lib/hook_verify.py`
- Create: `quality-workflow/skills/shared/tests/test_hook_verify.py`

API: `verify_hook(hook_id, project_root, bad_fixture, good_fixture) -> VerifyResult`. Stages the bad fixture, runs `pre-commit run <hook_id>`, asserts exit 1 + that the JSON output references the fixture's fingerprint. Then stages the good fixture, asserts exit 0. Always reverts the working tree.

- [ ] **Step 1: Tests** — mock subprocess to simulate exit codes; verify the staging/revert dance is correct.
- [ ] **Step 2: Implement**.
- [ ] **Step 3: Fixture library** — ship a small `quality-workflow/fixtures/` directory with at least one bad+good pair for skylos (complexity bomb) and fallow (dead export). Per-hook fixtures keyed by hook-id.
- [ ] **Step 4: Commit**.

### Task B2: `quality-verify-hook` SKILL.md

**Files:**
- Create: `quality-workflow/skills/quality-verify-hook/SKILL.md`

User-facing skill. Reads `.pre-commit-config.yaml`, identifies skylos/fallow hooks, dispatches `hook_verify.verify_hook(...)` for each, reports pass/fail. **Refuses to consider a hook "installed" until verified.**

- [ ] **Step 1: Write SKILL.md** with the workflow procedure.
- [ ] **Step 2: Manual verification** — run against now-playing's `.pre-commit-config.yaml`, confirm both hooks pass.
- [ ] **Step 3: Commit**.

---

## Phase C: `quality-audit` (the snapshot skill)

### Task C1: `quality-audit` SKILL.md

**Files:**
- Create: `quality-workflow/skills/quality-audit/SKILL.md`

Workflow: run skylos full-audit + fallow health/dupes, fingerprint-key the findings, write to `.claude/quality-snapshots/YYYY-MM-DD.json`, diff against previous snapshot, render grade card + delta.

- [ ] **Step 1: Write SKILL.md**.
- [ ] **Step 2: Manual verification** — run against now-playing; capture before/after snapshot pair; verify diff math.
- [ ] **Step 3: Commit**.

---

## Phase D: `quality-unblock` (the triage skill)

### Task D1: `quality-unblock` SKILL.md

**Files:**
- Create: `quality-workflow/skills/quality-unblock/SKILL.md`

Workflow: parse pre-commit failure output (JSON or text-extracted-to-JSON), for each finding load the playbook entry for its `rule_id`, present three options (fix / suppress with `# Why:` / defer to feature-capture). The triage decision is user-driven; the plugin produces structured prompts.

- [ ] **Step 1: Write SKILL.md**.
- [ ] **Step 2: Manual verification** — feed it a real now-playing pre-commit failure JSON; verify all three paths produce useful output.
- [ ] **Step 3: Commit**.

---

## Phase E: Existing prototype refactor

### Task E1: Parameterize `audit_suppressions.py`

**Files:**
- Modify: `quality-workflow/skills/shared/lib/audit_suppressions.py`
- Create: `quality-workflow/skills/shared/tests/test_audit_suppressions.py`

Today: hardcoded `REPO = Path("/Users/courtschuett/GitHub/schuettc/now-playing")`. Change to a `scan(project_root: Path)` function. Keep the CLI entrypoint for direct invocation. Add tests with fixture repos.

- [ ] **Step 1: Tests** — fixture repo with two files: one with a Why'd suppression, one with a bare suppression. Assert correct classification.
- [ ] **Step 2: Refactor** — extract `scan(project_root)` from `main()`. `main()` parses argv and calls scan.
- [ ] **Step 3: Commit**.

### Task E2: Parameterize `stale_suppressions_check.py`

**Files:**
- Modify: `quality-workflow/skills/shared/lib/stale_suppressions_check.py`
- Create: `quality-workflow/skills/shared/tests/test_stale_suppressions_check.py`

Same pattern as E1. Strip-and-rescan logic stays the same; `REPO` becomes a parameter.

- [ ] **Step 1: Tests** — fixture file with a known-stale suppression; assert detected.
- [ ] **Step 2: Refactor**.
- [ ] **Step 3: Commit**.

(Both are prerequisites for the eventual `quality-suppressions` skill in v0.3.)

---

## Phase F: Polish

### Task F1: Version bump + README update

- [ ] Bump `quality-workflow/.claude-plugin/plugin.json` 0.1.0 → 0.2.0
- [ ] Bump `.claude-plugin/marketplace.json` entry for quality-workflow → 0.2.0
- [ ] Update `quality-workflow/README.md` — status from "scaffold" to "MVP (v0.2.0)"
- [ ] Add an "Installation + first run" section to the plugin README — how to install, how to run `quality-verify-hook` first, what `quality-audit` produces
- [ ] Commit

### Task F2: PR + merge + tag + release

- [ ] Open PR titled `feat(quality-workflow): v0.2.0 MVP — audit, unblock, verify-hook`
- [ ] Merge
- [ ] Cut tag `quality-workflow-v0.2.0`
- [ ] Create GitHub release with notes

---

## Self-review checklist

After all phases:

1. **Spec coverage** — sections 1-5, 10 of the spec are fully covered. Sections 6 (feature-workflow integration), 8 (open questions to investigate during build), 9 (existing artifacts) are explicitly deferred or rolled into respective tasks.
2. **Hook contract enforcement** — `quality-verify-hook` exists, is documented in the plugin README's "first run" section, and rejects unverified hooks. The "hook silence ≠ hook working" lesson is the README's lead.
3. **Tool independence** — adapter files (`skylos_adapter.py`, `fallow_adapter.py`) are separate. Adding a new tool means writing a new adapter, not editing skills.
4. **No new pytest collection collisions** — `stale_suppressions_check.py` is correctly renamed from the prototype's `test_stale_suppressions.py`; new tests live under `tests/` with `test_*` filenames.

---

## Risks

| Risk | Mitigation |
|---|---|
| `fallow` CLI flags don't match what we assume in A3 | Verify against now-playing's existing fallow invocation before writing the adapter |
| Skylos JSON format changes between versions | Pin a specific `uvx skylos` version requirement in plugin docs; consider a `skylos_version` field in snapshots |
| Playbook YAML grows unwieldy | If the count grows past 50 rules per tool, split per-category (security.yaml / quality.yaml / dead-code.yaml) |
| Fingerprint instability for fallow | If our synthesized fingerprint produces too many false positives in NEW (a finding appears "new" because the line number shifted), bias toward `{file, rule, function_name}` instead of line numbers |
| `quality-verify-hook` is slow because of `pre-commit run` overhead | If it noticeably drags install, batch verifications across all hooks in one `pre-commit run --all-files` pass + filter |

---

## Execution order

1. **Phase A** — data + adapters + playbooks (foundation; nothing user-facing yet)
2. **Phase B** — `quality-verify-hook` (the safety net; ships first among skills because everything else depends on it)
3. **Phase C** — `quality-audit` (the read-only snapshot)
4. **Phase D** — `quality-unblock` (the active triage skill)
5. **Phase E** — port the existing prototypes (defensive: their value is the same after refactor, the refactor just unlocks reuse in v0.3+)
6. **Phase F** — version bump + PR + ship

Estimated wall-clock for subagent-driven execution: half a day, with Phase A being roughly half of it.

---

## What this leaves for v0.3+

- `quality-suppressions` (the full audit skill — wraps the prototypes ported in E1/E2)
- `quality-epic` (calls `feature-workflow:feature-capture`)
- `quality-baseline` (named-baseline ratchet)
- `quality-trend` (per-file movement over N snapshots)
- Multi-tool adapters (ruff, eslint, semgrep)
- Per-project YAML config (`.claude/quality-workflow.local.md` rather than just code-level defaults)
