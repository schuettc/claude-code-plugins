---
name: quality-verify-hook
description: Verify that a project's static-analysis pre-commit hooks actually fire on bad code. Use after installing skylos/fallow hooks, after editing .pre-commit-config.yaml, or whenever the user asks "is the hook working?" / "test pre-commit" / "verify hooks". Stages known-bad fixtures and asserts non-zero exit; stages known-good fixtures and asserts zero exit. The hook silence-equals-working failure mode is the whole reason this plugin exists.
user-invocable: true
allowed-tools: Read, Bash
---

# Verify Pre-commit Hooks

You are executing the **VERIFY HOOK** workflow — the safety net that the rest of quality-workflow depends on.

## Why this skill exists

Pre-commit hooks can be configured to scan zero files (wrong path argument), to silently skip (broken interpreter), or to find findings but not fail the commit. None of those show up in normal commits — the user sees "Passed" on every commit and assumes the hook is working. Until they run a manual full audit and discover their grade is F.

This skill stages a fixture with a deliberate violation, runs the hook, and asserts the hook fails. Then a clean fixture, asserts the hook passes. **A hook that doesn't fail on a known-bad input is not a hook.**

## Arguments

`$ARGUMENTS` is optional. If empty, verify every static-analysis hook in `.pre-commit-config.yaml`. If a hook ID is given (e.g. `skylos-agent`, `fallow-audit-kiosk`), verify just that one.

## Step 1: Read the project's pre-commit config

```bash
cat .pre-commit-config.yaml
```

If the file doesn't exist, tell the user:
> "No `.pre-commit-config.yaml` found. Install pre-commit first: `pipx install pre-commit && pre-commit install`."

Identify the static-analysis hooks. The plugin ships fixtures for these IDs:

| Hook ID pattern | Fixture pair |
|---|---|
| Any hook running `skylos` (typically `skylos-agent`) | `fixtures/skylos-bad.py` + `fixtures/skylos-good.py` |
| Any hook running `fallow audit` (typically `fallow-audit-kiosk` or similar) | `fixtures/fallow-bad.ts` + `fixtures/fallow-good.ts` |

If a hook in `.pre-commit-config.yaml` runs a tool the plugin doesn't have fixtures for, surface it as "no fixture available for `<hook-id>` — skipping". Don't make up a fixture.

## Step 2: For each hook, run verification

Invoke `hook_verify.verify_hook(hook_id, project_root, bad_fixture, good_fixture)` via a short Python one-liner. The lib is at `${CLAUDE_PLUGIN_ROOT}/skills/shared/lib/`.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"  # provided by Claude Code at runtime
python3 -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/skills/shared/lib')
from pathlib import Path
from hook_verify import verify_hook

result = verify_hook(
    hook_id='<hook-id>',
    project_root=Path('.').resolve(),
    bad_fixture=Path('$PLUGIN_ROOT/fixtures/<bad-fixture>'),
    good_fixture=Path('$PLUGIN_ROOT/fixtures/<good-fixture>'),
)
print(f'hook_id={result.hook_id}')
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
| `ok=True` | Hook fires on bad, passes on good — working correctly | Report: "✅ `<hook-id>` verified — fires on known-bad fixtures, passes on clean fixtures." |
| `bad_passed=False` | Hook accepted a known-violation input — **silently broken** | Report: "❌ `<hook-id>` did NOT fail on the known-bad fixture. The hook is misconfigured — likely a wrong path argument, missing tool, or wrong `entry:` line. This is the same class of bug as now-playing's 7-day silent skylos misconfig (see plugin README)." |
| `good_passed=False` | Hook rejected a clean input — overzealous | Report: "⚠️ `<hook-id>` failed on the known-good fixture. Either the fixture has drifted (unlikely; we ship clean trivial fixtures) or the hook's thresholds are set too low." |
| `error` is set | Verification itself failed (missing tool, timeout) | Report the error verbatim. Common cause: `pre-commit` not installed (`pipx install pre-commit`) or the hook's dependency missing (`uvx`, `npx`). |

## Step 4: Refuse to consider hooks "installed" until they pass

If any hook fails verification, the user should NOT trust that pre-commit will catch issues. Print this banner:

```
⚠️ Pre-commit hooks NOT VERIFIED
The following hooks failed verification:
  - <hook-id>: <reason>

Until these are fixed, commits will appear to pass pre-commit but may not
actually be scanned. Edit `.pre-commit-config.yaml`, re-run this skill, and
fix until all hooks report ok=True.
```

## Step 5: Cleanup verification

`verify_hook` reverts the working tree on its own, but spot-check before exiting:

```bash
git status --short
```

If anything unexpected appears (a leftover staged file from the fixture stage, an `.quality-workflow-verify/` directory), surface it to the user but DO NOT auto-clean — the user might want to inspect.

## When to run this skill

- **After `pipx install pre-commit && pre-commit install`** — first-time setup
- **After editing `.pre-commit-config.yaml`** — any change to a hook's `entry:`, `args:`, `files:`, etc.
- **After upgrading skylos or fallow** — tool versions can change exit-code semantics
- **As part of a CI smoke test** — wire this skill into the project's CI for ongoing assurance

## Notes

- This skill is **idempotent** and **non-destructive**. It always cleans up after itself. Re-running is safe.
- The fixtures live under `${CLAUDE_PLUGIN_ROOT}/fixtures/` — don't try to read them from the user's repo.
- If you need to add support for a new hook, add a `<hookname>-bad.<ext>` and `<hookname>-good.<ext>` fixture pair in the plugin's `fixtures/` directory, then update the hook-id-pattern table above.
