---
name: quality-verify-hook
description: Verify that a project's static-analysis git hooks actually fire on bad code — works with lefthook or the pre-commit framework. Use after installing the quality stack (lefthook install), after editing lefthook.yml / .pre-commit-config.yaml, or whenever the user asks "is the hook working?" / "test the hooks" / "verify hooks". Stages known-bad fixtures and asserts non-zero exit; stages known-good fixtures and asserts zero exit. The hook silence-equals-working failure mode is the whole reason this plugin exists.
user-invocable: true
allowed-tools: Read, Bash
---

# Verify Git Hooks

You are executing the **VERIFY HOOK** workflow — the safety net that the rest of quality-workflow depends on. It is **hook-manager-agnostic**: it works whether the project uses lefthook (the current standard) or the pre-commit framework.

## Why this skill exists

A hook can be configured to scan zero files (wrong path argument), to silently skip (broken interpreter), or to find findings but not fail. None of those show up in normal commits — the user sees "Passed" every time and assumes the hook works, until a manual audit reveals a grade of F.

This skill stages a fixture with a deliberate violation, runs the hook, and asserts it fails. Then a clean fixture, asserts it passes. **A hook that doesn't fail on a known-bad input is not a hook.**

## Arguments

`$ARGUMENTS` is optional. If empty, verify every static-analysis hook found. If a hook/command ID is given (lefthook command name like `py-scan`/`ts-scan`, or pre-commit hook ID like `skylos-agent`), verify just that one.

## Step 1: Detect the hook manager and the scan hooks

```bash
ls lefthook.yml lefthook.yaml .pre-commit-config.yaml 2>/dev/null
```

- `lefthook.yml`/`lefthook.yaml` present → **lefthook** (the static-scan commands live under `pre-commit:`, typically `py-scan` (skylos) and `ts-scan` (fallow)). Read it: `cat lefthook.yml`.
- only `.pre-commit-config.yaml` → **pre-commit framework** (hook IDs like `skylos-agent`, `fallow-audit-*`). Read it: `cat .pre-commit-config.yaml`.

(`verify_hook` auto-detects the same way — prefers lefthook, falls back to pre-commit — so you don't have to pass the manager explicitly.)

If neither exists, tell the user:
> "No `lefthook.yml` or `.pre-commit-config.yaml` found — the quality stack isn't installed. The quickest path is `project-workflow`'s `/project-init` (or its `quality-stack-setup` skill), which drops in `lefthook.yml` + `justfile`. Then `brew install just lefthook && lefthook install` and re-run this skill."

The plugin ships fixtures for these scanners (match by the tool the hook runs):

| Hook runs… | Typical ID (lefthook / pre-commit) | Fixture pair |
|---|---|---|
| `skylos` | `py-scan` / `skylos-agent` | `fixtures/skylos-bad.py` + `fixtures/skylos-good.py` |
| `fallow audit` | `ts-scan` / `fallow-audit-*` | `fixtures/fallow-bad.ts` + `fixtures/fallow-good.ts` |

If a hook runs a tool the plugin has no fixture for, surface "no fixture available for `<id>` — skipping". Don't make one up.

## Step 2: For each scan hook, run verification

Invoke `hook_verify.verify_hook(...)`. It auto-detects the manager and runs the right command (`lefthook run pre-commit --commands <id>` or `pre-commit run <id>`). The lib is at `${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/`.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"  # provided by Claude Code at runtime
python3 -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/skills/shared/lib')
from pathlib import Path
from hook_verify import verify_hook

result = verify_hook(
    hook_id='<id>',                  # 'py-scan' (lefthook) or 'skylos-agent' (pre-commit)
    project_root=Path('.').resolve(),
    bad_fixture=Path('$PLUGIN_ROOT/fixtures/<bad-fixture>'),
    good_fixture=Path('$PLUGIN_ROOT/fixtures/<good-fixture>'),
    # manager='lefthook'|'pre-commit'  # optional; auto-detected if omitted
)
print(f'manager={result.manager}  hook_id={result.hook_id}')
print(f'ok={result.ok}')
print(f'bad_passed={result.bad_passed} (exit={result.bad_exit_code})')
print(f'good_passed={result.good_passed} (exit={result.good_exit_code})')
if result.error:
    print(f'error={result.error}')
"
```

## Step 3: Interpret the result

| Result | Meaning | Action |
|---|---|---|
| `ok=True` | Fires on bad, passes on good — working | "✅ `<id>` verified — fails on known-bad fixtures, passes on clean ones." |
| `bad_passed=False` | Accepted a known violation — **silently broken** | "❌ `<id>` did NOT fail on the known-bad fixture. Misconfigured — likely a wrong glob/path, missing tool, or wrong command. Same class as now-playing's 7-day silent skylos misconfig." |
| `good_passed=False` | Rejected clean input — overzealous | "⚠️ `<id>` failed on the known-good fixture. The fixture drifted, or thresholds are too tight." |
| `error` is set | Verification itself failed | Report verbatim. Common: the manager binary missing (`brew install lefthook`) or a tool dep absent (`uvx`/`npx`). |

## Step 4: Refuse to consider hooks "installed" until they pass

If any hook fails verification, print this banner:

```
⚠️ Git hooks NOT VERIFIED
The following hooks failed:
  - <id>: <reason>

Until fixed, commits/pushes will appear to pass but may not actually be
scanned. Edit lefthook.yml (or .pre-commit-config.yaml), re-run this skill,
fix until all report ok=True.
```

## Step 5: Cleanup verification

`verify_hook` reverts the working tree on its own, but spot-check:

```bash
git status --short
```

If anything unexpected appears (a leftover staged fixture, a `.quality-workflow-verify/` dir), surface it but DO NOT auto-clean — the user may want to inspect.

## When to run this skill

- **After `lefthook install`** (or `pre-commit install`) — first-time setup
- **After editing `lefthook.yml` / `.pre-commit-config.yaml`** — any change to a command's glob/args
- **After upgrading skylos or fallow** — tool versions can shift exit-code semantics
- **As part of CI** — wire it in for ongoing assurance

## Notes

- **Idempotent** and **non-destructive** — always cleans up; re-running is safe.
- Fixtures live under `${CLAUDE_PLUGIN_ROOT}/fixtures/` — don't read them from the user's repo.
- To support a new scanner, add a `<name>-bad.<ext>` / `<name>-good.<ext>` fixture pair under `fixtures/` and extend the table above.
- This verifies the **scan** hooks (skylos/fallow) that BLOCK on findings. The pre-commit *fixers* (format/lint-`--fix`) auto-fix rather than fail, so they aren't verified this way; the full `just verify` (lint/typecheck/test) is verified by CI running the identical recipe.
