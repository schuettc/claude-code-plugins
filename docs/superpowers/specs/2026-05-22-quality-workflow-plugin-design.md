# Handoff: `code-quality` plugin

A sister plugin to `feature-workflow`. Built to surface, triage, and drive resolution of code-quality findings (skylos for Python, fallow for TS/JS) — with the same backlog-and-epic discipline that `feature-workflow` already provides for feature work.

This document captures everything learned in the now-playing session on 2026-05-22 that should shape the plugin design.

---

## 0. Context: what triggered this

The now-playing project ships with pre-commit hooks for `skylos` (Python) and `fallow` (TypeScript). On 2026-05-22 a manual `skylos pi/ -a` reported **Grade F (57/100)** despite a week of clean commits. Investigation revealed:

1. **The skylos hook had been silently misconfigured for 7 days.** The `entry:` line passed `pi/` as the path argument, causing skylos to look for staged files at `pi/pi/nowplaying/...`. It always reported "No Python files found" → exit 0. Several real quality regressions slipped through (listener.py cyclomatic 45, state.py 148-line `__init__`, etc.).
2. **Fixed by changing `pi/` → `.` in `.pre-commit-config.yaml`** (commit `f52dce1`).
3. **Skylos's bundled "baseline" feature only captures dead-code fingerprints.** It doesn't silence quality/security debt — so a naive `--baseline --gate` won't shield against existing F-grade noise. Skylos's `--diff` flags don't see staged-only changes either. The standalone command isn't suited for staged-files gating; only `skylos agent pre-commit` is.
4. **`skylos agent pre-commit --format json`** produces clean, structured output with stable `fingerprint` fields — perfect input for plugin skills.

The lesson — **hook silence ≠ hook working** — is the single most important property the plugin must enforce going forward.

---

## 1. Plugin scope

**Name**: `code-quality` (or `quality-workflow` to match `feature-workflow`'s naming).

**Sister-plugin to**: `feature-workflow`. Calls into `feature-workflow:feature-capture` to convert findings into backlog items.

**Languages supported on day 1**:
- Python via `skylos` (security, secrets, complexity, structure, dependencies)
- TypeScript/JavaScript via `fallow` (dead code, complexity, duplication, health)

**Not in scope**:
- Test coverage analysis
- Performance profiling
- Bundle-size auditing

---

## 2. Skill suite

Organized by purpose. All skills consume `--format json` from the tools; never parse human-readable output.

### Operational (daily use)

| Skill | Triggers | What it does |
|---|---|---|
| `quality-audit` | "what's my code health?", "run skylos/fallow", "audit quality", "snapshot quality" | Read-only. Runs full skylos `-a --format json` + fallow `health` + `dupes`. Writes a structured snapshot to `.claude/quality-snapshots/YYYY-MM-DD.json`. Renders a grade card plus delta vs. previous snapshot (NEW / RESOLVED / PERSISTING via fingerprint diff). |
| `quality-unblock` | Pre-commit hook just failed; "the commit is blocked"; user pastes skylos output | Parses `agent pre-commit --format json` output. Per finding offers three options: **fix in code**, **suppress with required `# Why:`**, or **defer → feature-capture**. Per-rule playbooks (see §4). Never adds a suppression without a rationale. |
| `quality-suppressions` | "audit ignores", "are these still needed?", "find stale ignores" | Walks every `# skylos: ignore`, `# noqa`, `# type: ignore`, `// fallow-ignore`, `// eslint-disable`. Three checks: (a) has rationale (Why-token OR em-dash convention — configurable per project); (b) still needed (strip + re-scan + match rule_id); (c) referenced rule still exists. |
| `quality-verify-hook` | "is the hook working?", "test pre-commit"; runs after editing `.pre-commit-config.yaml` | Stages a fixture with a known violation, runs `pre-commit run <hook>`, asserts exit 1. Then a clean fixture, asserts exit 0. The hook silence ≠ hook working lesson, codified. |

### Strategic (composes with feature-workflow)

| Skill | Triggers | What it does |
|---|---|---|
| `quality-epic` | "turn this into work", "plan a quality push", after a `quality-audit` | Groups PERSISTING findings by `rule_id` + file-cluster into themed epics. For each, calls `feature-workflow:feature-capture` with `category: tech-debt`, severity → priority, includes audit snapshot ref. One epic per cluster, not one per finding. |
| `quality-baseline` | "save the current floor", after intentional cleanup | Names a snapshot as the floor. Future `quality-audit` and CI diff against it. Lets you ratchet — once listener.py drops from 45 → 20, save baseline, 21+ becomes failure threshold. |
| `quality-trend` | "did we get better?", "where are we drifting?" | Loads last N snapshots and shows per-file, per-category, per-rule_id movement. Surfaces silent regressions (a file touched recently is now worse). |

---

## 3. Data contracts

Small, file-based, all under `.claude/quality-snapshots/`. Gitignored by default; can be opted-in to version-control per project.

```python
QualityFinding = {
    "fingerprint": str,        # stable identity across runs; from skylos JSON
    "rule_id": str,            # e.g. SKY-Q302, SKY-D216, FAL-DUP-01
    "category": str,           # quality | security | secrets | dependency | duplication | dead-code
    "severity": str,           # CRITICAL | HIGH | MEDIUM | LOW
    "file": str,               # repo-relative
    "line": int,
    "message": str,            # human-readable, often contains the actionable hint
    "tool": str,               # "skylos" | "fallow"
    "confidence": float | None,
}

QualitySnapshot = {
    "date": str,               # YYYY-MM-DD
    "commit": str,             # git rev-parse HEAD at scan time
    "tool_versions": {
        "skylos": str,
        "fallow": str,
    },
    "findings": [QualityFinding],
    "grade": str,              # skylos overall, for at-a-glance trend
}

QualityEpic = {
    "title": str,              # e.g., "Reduce sonos/listener.py complexity"
    "fingerprints": [str],     # the findings this epic resolves
    "feature_workflow_id": str | None,  # set after feature-capture
    "parent_snapshot": str,    # date of the audit that surfaced it
    "owner": str | None,
    "status": str,             # proposed | accepted | in_progress | resolved | abandoned
}
```

### Why fingerprint-keyed diffing matters

Two snapshots → set arithmetic on fingerprints:
- `new = B.fingerprints - A.fingerprints` — regressions to attribute
- `resolved = A.fingerprints - B.fingerprints` — wins to celebrate
- `persisting = A.fingerprints ∩ B.fingerprints` — debt still standing

No semantic logic, no diff heuristics. The skill code is small.

---

## 4. Per-rule playbooks (for `quality-unblock`)

The plugin should ship a YAML/JSON table mapping rule_id → suggested action(s). Examples:

```yaml
rules:
  SKY-Q302:  # nesting depth
    category: quality
    actions:
      - kind: refactor
        suggestion: "Use early returns to flatten guard clauses."
        agent_prompt: "Refactor {file}:{line} to use early-return pattern for guards; preserve behavior."
      - kind: suppress
        require_why: true
        why_template: "Nesting is intrinsic to {domain reason} — splitting would scatter {logic}."
      - kind: defer
        epic_title_template: "Reduce nesting in {file}"

  SKY-D216:  # SSRF
    category: security
    actions:
      - kind: fix
        suggestion: "Validate URL against an allow-list before HTTP call."
        agent_prompt: "Wrap the HTTP call at {file}:{line} with a host allow-list check; reject untrusted schemes."
      - kind: suppress
        require_why: true
        require_severity_ack: true
        why_template: "URL source is trusted: {explain provenance}."
      # No 'defer' — SSRF should be fixed or explicitly accepted, not backlogged.

  SKY-L029:  # bool positional arg
    category: quality
    actions:
      - kind: fix
        suggestion: "Make bool param keyword-only via `*,`."
      - kind: suppress
        require_why: true
        why_template: "Positional bool kept for {test/API stability reason}."
```

The plugin's value-add: turning rule_ids into actionable, repeatable agent prompts.

---

## 5. Hook contract

Every pre-commit (or pre-push) hook the plugin installs MUST include a self-test invocation of `quality-verify-hook` in the plugin's own CI / install verification. Reason: the now-playing bug shipped a hook that silently scanned zero files for 7 days. The plugin should refuse to consider a hook "installed" until it has been proven to fire on a known-bad fixture and pass on a known-good one.

Concretely:
- `quality-verify-hook` writes a fixture (complexity bomb for Python, dead-code clone for TS) into a temp staged area.
- Runs `pre-commit run <hook-id>`.
- Asserts exit 1 and that the JSON output contains the fixture's fingerprint.
- Reverts the fixture.
- Repeats with a known-clean fixture, asserts exit 0.

If a project author bypasses this and the hook is silently broken later, that's on them — but the plugin's default path should make it impossible to skip.

---

## 6. Cross-plugin integration with feature-workflow

The contract is minimal. `quality-epic` calls a single function on `feature-workflow`:

```
feature-workflow:feature-capture(
    title=epic_title,
    category="tech-debt",
    body=structured_findings_summary,
    metadata={
        "source_plugin": "code-quality",
        "quality_epic_id": <uuid>,
        "snapshot_ref": "2026-05-22",
        "fingerprints": [...]
    }
)
→ returns feature_id
```

`code-quality` then stores `feature_id` in its `QualityEpic` record. When `feature-workflow:feature-ship` runs on that feature, the plugin can optionally check: did the snapshot's PERSISTING fingerprints actually disappear in the new code? That's a satisfying close-loop check.

**No protocol changes needed in feature-workflow.** It already accepts metadata. The integration is one direction (quality → feature-workflow), and the feature-workflow side is unaware of code-quality.

---

## 7. Configuration

Per-project config lives at `.claude/code-quality.local.md` (matching the plugin-settings pattern). Example:

```yaml
---
suppression_rationale_style: em-dash   # or "why-token"
ignore_test_patterns: ["pi/tests/**"]  # for symlink-write false positives
fingerprint_baseline: "2026-05-22"     # last accepted baseline
rule_overrides:
  SKY-Q501:  # too-many-attributes
    severity: medium  # downgrade from default; we have a known "god-object by design"
hooks:
  pre_commit:
    skylos_path: "."   # the now-playing-saved-us setting
    verify_on_install: true
---

# Code-quality config notes

Project-specific notes go here. CLAUDE.md-compatible format.
```

---

## 8. Open questions / experiments worth running before / during plugin build

Each of these was deferred from the now-playing session — answers will sharpen the spec.

1. **Test-fixture symlink-write false positives**: ~25 of the 48 "high-severity" skylos findings in now-playing are tests writing to `tmp_path`. Either (a) skylos has a flag to skip test directories, (b) add a bulk suppression with project-level rationale, or (c) the plugin filters them out. Which is right?

2. **Fallow / Python equivalence**: Fallow has rich snapshot/baseline features (`--health-baseline`, `--dupes-baseline`, named baselines). Skylos doesn't. The plugin will have to do its own snapshotting for the Python side. Worth confirming what fallow gives us natively vs. what we have to synthesize.

3. **Rule-id playbook coverage**: We have rule_ids from skylos (~50 unique observed in this project) and fallow. The plugin needs playbooks for the common ones. Day-1 deliverable: cover the top 20 most-frequent rule_ids across both tools. Open: what's the discovery mechanism for new rule_ids — does the plugin warn when it sees an unrecognized one?

4. **Skylos `--gate` thresholds**: The default `--gate` uses absolute counts (`max 10 quality`, `max 5 high`) regardless of `--diff` scope. Worth confirming whether there's a way to scope the gate's *counts* to diff'd files. If not, the plugin can't easily ship a "gate-on-regression" hook with skylos alone — it'd need to wrap skylos and do the counting itself.

5. **Multi-tool composition**: Today: skylos for Py, fallow for TS. Future: ruff for Py style, eslint for TS style, semgrep for SAST. The plugin's architecture should make adding a new tool a matter of writing a JSON-output adapter — not rewriting every skill.

---

## 9. Artifacts from the 2026-05-22 session

These are concrete starting inputs already produced:

| Artifact | Path | Use |
|---|---|---|
| Suppression audit JSON | `now-playing/.claude/quality-snapshots/suppressions-2026-05-22.json` | 141 entries with file/line/mechanism/rule/has_why; valid input for the first `quality-suppressions` run |
| Suppression auditor prototype | `/tmp/audit_suppressions.py` | ~80 LOC; shows the algorithm. Should be ported to plugin's `lib/` directory |
| Stale-suppression prototype | `/tmp/test_stale_suppressions.py` | ~80 LOC; demonstrates the strip-and-re-scan check |
| Working hook config | `now-playing/.pre-commit-config.yaml` post-commit `f52dce1` | Reference for what "correctly configured" looks like |

The first two prototypes should be moved into the plugin repo and turned into proper libraries before the skills layer is built.

---

## 10. Minimum-viable first cut

If we want to ship something useful within one focused session:

1. `quality-audit` (read-only snapshot + diff vs. previous)
2. `quality-unblock` (parse JSON failure, offer fix/suppress/defer)
3. `quality-verify-hook` (the must-have safety net)
4. The data contracts and snapshot format

That's a small surface that delivers daily value. Everything else (epics, trends, suppressions auditor) can land in v0.2.

---

## 11. Naming the plugin

Options to consider:
- `code-quality` — descriptive, matches the domain
- `quality-workflow` — symmetric with `feature-workflow`, hints at the lifecycle
- `quality-ratchet` — emphasizes the directional improvement-only property

Recommend `quality-workflow` to match the sibling plugin's vocabulary.
