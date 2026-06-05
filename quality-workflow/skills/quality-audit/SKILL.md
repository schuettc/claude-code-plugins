---
name: quality-audit
description: Read-only static-analysis snapshot. Runs skylos (Python) and fallow (TS/JS) full audits, writes a fingerprinted snapshot to .claude/quality-snapshots/YYYY-MM-DD.json, and renders a grade card plus delta vs the previous snapshot (NEW / RESOLVED / PERSISTING findings). Use when the user asks "what's my code health?", "run skylos", "run fallow", "audit quality", "snapshot quality", or after a cleanup pass to confirm wins.
user-invocable: true
allowed-tools: Read, Bash, Write
---

# Quality Audit

You are executing the **AUDIT** workflow — a read-only snapshot of every static-analysis finding active across the project, plus the delta vs. the previous snapshot.

## What this skill does

1. Detects which tools to run (skylos for Python, fallow for TS/JS).
2. Runs each tool with full options (`--quality --danger --secrets --sca` for skylos; `health + dupes + dead-code` for fallow).
3. Maps findings to a unified `QualityFinding` shape with stable fingerprints.
4. Writes the snapshot to `.claude/quality-snapshots/YYYY-MM-DD.json`.
5. Computes the delta vs. the most recent prior snapshot (NEW / RESOLVED / PERSISTING).
6. Renders a grade card with the highlights.

This skill **does not modify code, suggest fixes, or auto-suppress anything.** For triage on a failing pre-commit hook, use `/quality-unblock`. For testing whether hooks fire correctly, use `/quality-verify-hook`.

## Arguments

`$ARGUMENTS` is optional:
- Empty — full audit (skylos + fallow if both apply)
- `--skylos-only` — Python only
- `--fallow-only` — TS/JS only
- `--no-write` — show the report but don't persist a snapshot file

## Step 1: Detect project shape

```bash
# Python project? Look for pyproject.toml, requirements.txt, or *.py at the root
ls pyproject.toml requirements.txt 2>/dev/null

# TypeScript project? Look for package.json
ls package.json 2>/dev/null
```

For now-playing-style projects with both, run both tools. For a monorepo where the Python is in `pi/` and the TS is in `kiosk/`, run skylos against `pi/` and fallow against `kiosk/` (the per-tool roots).

If neither is found, refuse:
> "No Python (pyproject.toml/requirements.txt) or TypeScript (package.json) detected at the project root. quality-audit needs at least one to run."

## Step 2: Run the audits

Use the plugin's adapters. The lib is at `${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/`.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
import sys, json
from datetime import date
from pathlib import Path
sys.path.insert(0, '$PLUGIN_ROOT/skills/shared/lib')

from snapshot import QualitySnapshot, QualityFinding, write_snapshot, read_snapshot, diff_snapshots
from skylos_adapter import run_full_audit as skylos_audit, SkylosError
from fallow_adapter import run_full_audit as fallow_audit, FallowError

project = Path('.').resolve()
findings = []
tool_versions = {}

# Adjust project sub-paths if you're in a monorepo (e.g., pi/ and kiosk/)
PY_ROOT = project / 'pi' if (project / 'pi').is_dir() else project
TS_ROOT = project / 'kiosk' if (project / 'kiosk').is_dir() else project

try:
    py = skylos_audit(PY_ROOT)
    findings.extend(py)
    tool_versions['skylos'] = 'auto'  # version is in the snapshot's payload if needed
except SkylosError as e:
    print(f'skylos: {e}', file=sys.stderr)

try:
    ts = fallow_audit(TS_ROOT)
    findings.extend(ts)
    tool_versions['fallow'] = 'auto'
except FallowError as e:
    print(f'fallow: {e}', file=sys.stderr)

# Build snapshot
import subprocess
commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
snap = QualitySnapshot(
    date=date.today().isoformat(),
    commit=commit,
    tool_versions=tool_versions,
    findings=findings,
    grade='',  # filled in below
)

# Write
out_dir = project / '.claude' / 'quality-snapshots'
out_path = out_dir / f'{snap.date}.json'
write_snapshot(snap, out_path)
print(f'Wrote {len(findings)} findings → {out_path.relative_to(project)}')

# Active vs suppressed split (headlines use ACTIVE only)
active = snap.active_findings()
suppressed = snap.suppressed_findings()
print(f'Active: {len(active)}  |  Suppressed (tool-honored): {len(suppressed)}')

# Diff vs previous — display ACTIVE views; full diff still tracks suppressed transitions
prev_files = sorted(p for p in out_dir.glob('*.json') if p.name != out_path.name)
if prev_files:
    prev = read_snapshot(prev_files[-1])
    d = diff_snapshots(prev, snap)
    print(f'Δ vs {prev.date}: {len(d.active_new)} NEW, {len(d.active_resolved)} RESOLVED, {len(d.active_persisting)} PERSISTING  (active only)')
"
```

## Step 3: Render the grade card

Format the output as a scannable summary. **Headline counts use ACTIVE findings** —
those skylos did NOT recognize as suppressed by an inline `# skylos: ignore`
directive. Suppressed findings remain in the snapshot for delta-tracking but
do not inflate the user-facing totals.

```
# Quality Audit — 2026-05-22

## Summary
- Active findings: 126 (skylos 113, fallow 13)
- Suppressed (tool-honored): 54  (raw total before suppression: 180)
- By severity (active): 1 CRITICAL, 22 HIGH, 88 MEDIUM, 15 LOW
- By category (active): 64 quality, 48 security, 13 duplication, 1 dead-code

## Delta vs 2026-05-21 (commit abc123 → def456) — active only
- NEW (3):
  - SKY-Q301 pi/orchestrator/listener.py:45 — cyclomatic complexity 17
  - …
- RESOLVED (12):
  - SKY-D216 pi/api/_routes.py:88 — SSRF (now fixed)
  - …
- PERSISTING (111): see snapshot for full list

## Hotspots (active only)
- pi/orchestrator/state.py: 8 findings
- pi/control/_shared.py: 6 findings
- kiosk/src/App.tsx: 4 findings
```

Cap the NEW and RESOLVED lists at ~10 entries each in the rendered output. Reference the snapshot file for the full list.

If `Suppressed (tool-honored)` is non-zero, note in the output that the
suppressed list can be inspected via the raw snapshot JSON (`.suppressed`
entries) and that the post-MVP `/quality-suppressions` skill will audit
their rationales.

## Step 4: Suggest follow-ups

Based on the delta:

- **Many NEW findings, few RESOLVED** → suggest `/quality-unblock` to triage them one-by-one
- **Many RESOLVED, few NEW** → congratulate the cleanup pass; optionally run `/feature-search --epic <id>` if a tech-debt epic was driving the cleanup
- **All PERSISTING, no movement** → suggest reviewing whether the persisting findings should be deferred to a tech-debt epic via `/feature-capture` (manual; quality-epic skill ships in v0.3)

## Step 5: Done

The snapshot is persisted. Re-running the skill on a later date produces a new snapshot and a delta against this one.

## Notes

- Snapshots live at `.claude/quality-snapshots/`. Gitignored by default; safe to delete/clear if a project wants to reset its history.
- If no previous snapshot exists, the delta section reports "first snapshot — no comparison available".
- Skylos and fallow can each take 30-60s on a medium codebase; combined audits run sequentially in this MVP. v0.3+ may parallelize.
- The skill is **read-only** with respect to code. It writes only to `.claude/quality-snapshots/` and never touches source files.
- **Suppressed findings** (skylos `reason: "inline ignore comment"`) are stored in the snapshot with `suppressed: true` but excluded from headline counts and delta tables. They still participate in the raw fingerprint diff so a finding that loses or gains its suppression between snapshots is detectable. Fallow does not surface suppressions in its JSON; `// fallow-ignore-next-line` directives are audited by the (post-MVP) `/quality-suppressions` skill.
