# Workspace Scaffolder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `feature-init --workspace` mode that scaffolds a multi-repo *workspace repo* — a thin coordination repo (manifest, gitignore, CLAUDE.md, `.claude/settings.json`, `docs/features/`, clone script) with member repos nested as gitignored independent clones.

**Architecture:** The file-generating logic lives in a new importable `lib/workspace.py` (`scaffold_workspace(root, org, members)`), unit-tested via the existing pytest suite. `init.py` gains a `--workspace` mode that parses CLI args and calls it. The `feature-init` SKILL gains a workspace branch that collects org + members and invokes the script. This is **Phase 1a** of the multi-repo design (`docs/designs/2026-06-08-multi-repo-workspace.md`); repo-scoped config/IDs and the aggregated dashboard are follow-on plans.

**Tech Stack:** Python 3 (stdlib only — no PyYAML), pytest, bash.

---

## File Structure

- **Create** `feature-workflow/skills/shared/lib/workspace.py` — `scaffold_workspace()` + file templates. One responsibility: turn an `(org, members)` description into the on-disk workspace files. Importable (lives in `lib/`, which `conftest.py` puts on `sys.path`).
- **Create** `feature-workflow/skills/shared/tests/test_workspace.py` — unit tests for `scaffold_workspace()`.
- **Modify** `feature-workflow/skills/feature-init/scripts/init.py` — add `--workspace`, `--org`, `--member` args + a `workspace_mode()` that imports and calls `scaffold_workspace()`.
- **Modify** `feature-workflow/skills/feature-init/SKILL.md` — add a "Workspace mode" branch.

A workspace is **identified by `.feature-workspace.yml`**, not its name (per the design's resolved decision).

---

### Task 1: `scaffold_workspace()` — manifest + gitignore (the workspace identity)

**Files:**
- Create: `feature-workflow/skills/shared/lib/workspace.py`
- Test: `feature-workflow/skills/shared/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test**

Create `feature-workflow/skills/shared/tests/test_workspace.py`:

```python
"""Tests for the multi-repo workspace scaffolder."""

from pathlib import Path

import pytest

from workspace import scaffold_workspace

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]


def test_writes_manifest_with_org_and_members(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    manifest = (tmp_path / ".feature-workspace.yml").read_text()
    assert "org: acme" in manifest
    assert "dir: engine" in manifest
    assert "repo: acme/engine" in manifest
    assert "dir: app" in manifest


def test_gitignore_lists_every_member_and_dashboard(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    gitignore = (tmp_path / ".gitignore").read_text()
    assert "engine/" in gitignore
    assert "app/" in gitignore
    assert "docs/features/DASHBOARD.md" in gitignore


def test_does_not_clobber_existing_gitignore(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("custom-entry/\n")
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    gitignore = (tmp_path / ".gitignore").read_text()
    assert "custom-entry/" in gitignore   # preserved
    assert "engine/" in gitignore          # appended
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'workspace'`

- [ ] **Step 3: Write minimal implementation**

Create `feature-workflow/skills/shared/lib/workspace.py`:

```python
"""Scaffold a multi-repo workspace.

A workspace is a thin coordination repo with member repos nested inside it as
gitignored, independent clones. It is identified by its `.feature-workspace.yml`
manifest, not its name. Written by `feature-init --workspace`.
"""

from pathlib import Path

MANIFEST_TEMPLATE = """\
# .feature-workspace.yml — multi-repo workspace manifest.
# Identifies this directory as a workspace and lists member repos + the
# contracts between them. The topology graph the tooling reads (clone members,
# warn on contract edits, order epic children + deploys).
org: {org}
members:
{members_block}
# contracts:
#   - {{ id: engine:engine-api, owner: engine, consumers: [app], kind: http }}
# deploy:
#   - {{ group: engine-stack, dir: engine }}
"""

GITIGNORE_HEADER = "# Member repos are independent git repositories — tracked separately, not here."


def _members_block(members: list[dict]) -> str:
    lines = []
    for m in members:
        lines.append(f"  - {{ dir: {m['dir']}, repo: {m['repo']} }}")
    return "\n".join(lines)


def _append_if_missing(path: Path, block: str, marker: str) -> None:
    existing = path.read_text() if path.exists() else ""
    if marker in existing:
        return
    sep = "" if (not existing or existing.endswith("\n")) else "\n"
    with open(path, "a") as f:
        f.write(sep + block)


def scaffold_workspace(root: Path, org: str, members: list[dict]) -> None:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    # Manifest (workspace identity). Always (re)written — it's the source of truth.
    (root / ".feature-workspace.yml").write_text(
        MANIFEST_TEMPLATE.format(org=org, members_block=_members_block(members))
    )

    # .gitignore: members + node_modules + local Claude state + the derived dashboard.
    member_lines = "".join(f"{m['dir']}/\n" for m in members)
    block = (
        f"\n{GITIGNORE_HEADER}\n{member_lines}"
        "\n# Build artifacts / local state\nnode_modules/\n.claude/\n"
        "\n# Auto-generated locally by hooks — not committed\ndocs/features/DASHBOARD.md\n"
    )
    _append_if_missing(root / ".gitignore", block, "docs/features/DASHBOARD.md")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/workspace.py feature-workflow/skills/shared/tests/test_workspace.py
git commit -m "feat(feature-workflow): scaffold_workspace — manifest + gitignore"
```

---

### Task 2: `.claude/settings.json` + workspace `.feature-workflow.yml` + dashboard

**Files:**
- Modify: `feature-workflow/skills/shared/lib/workspace.py`
- Test: `feature-workflow/skills/shared/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test**

Append to `test_workspace.py`:

```python
import json


def test_settings_allow_member_git_and_gh(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    allow = settings["permissions"]["allow"]
    assert "Bash(git -C *)" in allow
    assert "Bash(gh -R *)" in allow


def test_workspace_feature_config_targets_main(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    cfg = (tmp_path / ".feature-workflow.yml").read_text()
    assert 'target: "main"' in cfg
    assert 'reviewer: "none"' in cfg


def test_creates_docs_features_with_dashboard(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    assert (tmp_path / "docs" / "features" / "DASHBOARD.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: FAIL — `KeyError`/`FileNotFoundError` on settings.json and the new files.

- [ ] **Step 3: Write minimal implementation**

In `feature-workflow/skills/shared/lib/workspace.py`, add the constants after `GITIGNORE_HEADER`:

```python
import json

SETTINGS_JSON = {
    "permissions": {
        # Member repos are addressed from the workspace root with git -C / gh -R.
        "allow": ["Bash(git -C *)", "Bash(gh -R *)"]
    }
}

WORKSPACE_CONFIG = """\
# Feature workflow configuration for the WORKSPACE repo's own features + epics.
# Written by /feature-init --workspace — edit anytime.
branch:
  prefix: "feature/"    # Branch naming: <prefix><feature-id>
  target: "main"        # Base branch for PRs and merges
reviewer: "none"        # External reviewer: gemini, codex, or none
"""

INITIAL_DASHBOARD = """\
# Feature Dashboard

*Auto-generated by hooks. Do not edit directly.*

## In Progress

*No features in progress*

## Backlog

*No features in backlog. Use `/feature-capture` to add one.*

## Completed

*No completed features*
"""
```

Then add to the end of `scaffold_workspace()`:

```python
    # .claude/settings.json — allowlist member git/gh so cross-repo ops don't prompt.
    claude_dir = root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text(json.dumps(SETTINGS_JSON, indent=2) + "\n")

    # The workspace repo's own feature config (it runs workspace features + epics).
    cfg_path = root / ".feature-workflow.yml"
    if not cfg_path.exists():
        cfg_path.write_text(WORKSPACE_CONFIG)

    # docs/features/ with an initial dashboard.
    features_dir = root / "docs" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    dashboard = features_dir / "DASHBOARD.md"
    if not dashboard.exists():
        dashboard.write_text(INITIAL_DASHBOARD)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/workspace.py feature-workflow/skills/shared/tests/test_workspace.py
git commit -m "feat(feature-workflow): scaffold settings.json + workspace config + dashboard"
```

---

### Task 3: `CLAUDE.md` topology skeleton

**Files:**
- Modify: `feature-workflow/skills/shared/lib/workspace.py`
- Test: `feature-workflow/skills/shared/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test**

Append to `test_workspace.py`:

```python
def test_claude_md_has_topology_table(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert "acme workspace" in claude_md
    assert "engine" in claude_md and "acme/engine" in claude_md
    assert "git -C" in claude_md   # documents the member-op convention
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py::test_claude_md_has_topology_table -v`
Expected: FAIL — `FileNotFoundError: CLAUDE.md`

- [ ] **Step 3: Write minimal implementation**

Add the constant to `workspace.py`:

```python
CLAUDE_MD_TEMPLATE = """\
# {org} workspace

Coordination root for the {org} multi-repo project. Launch Claude **here** — every
member repo is in the working tree, so cross-repo edits never prompt.

## Repos

| Local dir | Remote | Role |
|-----------|--------|------|
{repo_rows}

## Conventions

- Each member is an **independent git repo**. Operate on one from here with
  `git -C <dir> …` and `gh -R <owner/repo> …` (both allowlisted in
  `.claude/settings.json`).
- A **single-repo** feature lives in that member's `docs/features/`. **Cross-repo**
  work is an **epic** here in the workspace `docs/features/`, one child per member.
- **Cross-repo docs** (serving 2+ repos) live in this workspace's `docs/`.
"""
```

Add to `scaffold_workspace()` (before the `.claude/settings.json` block is fine):

```python
    # CLAUDE.md topology skeleton.
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        rows = "\n".join(f"| `{m['dir']}` | {m['repo']} | |" for m in members)
        claude_md.write_text(CLAUDE_MD_TEMPLATE.format(org=org, repo_rows=rows))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/workspace.py feature-workflow/skills/shared/tests/test_workspace.py
git commit -m "feat(feature-workflow): scaffold CLAUDE.md topology skeleton"
```

---

### Task 4: `scripts/clone-members.sh` bootstrap

**Files:**
- Modify: `feature-workflow/skills/shared/lib/workspace.py`
- Test: `feature-workflow/skills/shared/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test**

Append to `test_workspace.py`:

```python
import os
import stat


def test_clone_members_script_is_executable_and_reads_manifest(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    script = tmp_path / "scripts" / "clone-members.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)            # executable bit set
    body = script.read_text()
    assert ".feature-workspace.yml" in body      # reads the manifest, not a hardcoded list
    assert body.startswith("#!/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py::test_clone_members_script_is_executable_and_reads_manifest -v`
Expected: FAIL — `FileNotFoundError: scripts/clone-members.sh`

- [ ] **Step 3: Write minimal implementation**

Add the constant to `workspace.py`:

```python
CLONE_MEMBERS_SH = r"""#!/bin/bash
# Clone every member repo listed in .feature-workspace.yml into this workspace.
# Idempotent: skips members already present. Run after cloning the workspace repo.
set -u
cd "$(dirname "$0")/.." || exit 1

# Extract "dir repo" pairs from the manifest (stdlib python — no PyYAML needed).
python3 - <<'PY' | while read -r dir repo; do
import re, pathlib
text = pathlib.Path(".feature-workspace.yml").read_text()
for m in re.finditer(r'dir:\s*([\w.-]+)\s*,\s*repo:\s*([\w./-]+)', text):
    print(m.group(1), m.group(2))
PY
  [ -z "$dir" ] && continue
  if [ -d "$dir/.git" ]; then
    echo "OK  $dir (already present)"
    continue
  fi
  echo "==> cloning $repo -> $dir"
  gh repo clone "$repo" "$dir" 2>/dev/null || git clone "git@github.com:$repo.git" "$dir"
done
"""
```

Add to `scaffold_workspace()`:

```python
    # One-command bootstrap to clone members per the manifest.
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    clone_script = scripts_dir / "clone-members.sh"
    if not clone_script.exists():
        clone_script.write_text(CLONE_MEMBERS_SH)
        clone_script.chmod(0o755)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/workspace.py feature-workflow/skills/shared/tests/test_workspace.py
git commit -m "feat(feature-workflow): scaffold clone-members.sh bootstrap"
```

---

### Task 5: `init.py --workspace` mode

**Files:**
- Modify: `feature-workflow/skills/feature-init/scripts/init.py`
- Test: `feature-workflow/skills/shared/tests/test_workspace.py`

- [ ] **Step 1: Write the failing test** (drives the script end-to-end via subprocess)

Append to `test_workspace.py`:

```python
import subprocess
import sys

INIT_PY = Path(__file__).resolve().parents[2] / "feature-init" / "scripts" / "init.py"


def test_init_py_workspace_mode_scaffolds(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(INIT_PY), str(tmp_path), "--workspace",
         "--org", "acme", "--member", "engine=acme/engine", "--member", "app=acme/app"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".feature-workspace.yml").exists()
    assert (tmp_path / ".gitignore").read_text().count("engine/") == 1
    assert (tmp_path / "scripts" / "clone-members.sh").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py::test_init_py_workspace_mode_scaffolds -v`
Expected: FAIL — `init.py` exits non-zero (`--workspace` not recognized).

- [ ] **Step 3: Write minimal implementation**

In `feature-workflow/skills/feature-init/scripts/init.py`, add a workspace handler. After the imports (line ~30), add:

```python
def _load_scaffold_workspace():
    """Import scaffold_workspace from the shared lib (sibling of feature-init)."""
    lib_dir = Path(__file__).resolve().parent.parent.parent / "shared" / "lib"
    sys.path.insert(0, str(lib_dir))
    from workspace import scaffold_workspace  # noqa: E402
    return scaffold_workspace


def workspace_mode(project_root: Path, org: str, members: list[dict]) -> int:
    if not org:
        print("ERROR: --workspace requires --org <github-org>.")
        return 1
    if not members:
        print("ERROR: --workspace requires at least one --member dir=owner/repo.")
        return 1
    scaffold_workspace = _load_scaffold_workspace()
    scaffold_workspace(project_root, org=org, members=members)
    print(f"Workspace initialized at {project_root}")
    print(f"  org:     {org}")
    print(f"  members: {', '.join(m['dir'] for m in members)}")
    print("")
    print("Next: clone the members ->  ./scripts/clone-members.sh")
    print("Then launch Claude from this directory; every member is in-tree.")
    return 0
```

In `main()`, add the args (after the `--update` arg, line ~289):

```python
    parser.add_argument("--workspace", action="store_true",
                        help="Scaffold a multi-repo WORKSPACE repo instead of a single project.")
    parser.add_argument("--org", default=None, help="GitHub org for the workspace manifest.")
    parser.add_argument("--member", action="append", default=[], metavar="dir=owner/repo",
                        help="A member repo (repeatable), e.g. --member engine=acme/engine.")
```

And near the top of `main()`, right after `project_root = Path(args.project_root).resolve()` (line ~292), add:

```python
    if args.workspace:
        members = []
        for spec in args.member:
            if "=" not in spec:
                print(f"ERROR: --member must be dir=owner/repo, got: {spec}")
                return 1
            d, repo = spec.split("=", 1)
            members.append({"dir": d.strip(), "repo": repo.strip()})
        return workspace_mode(project_root, args.org, members)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd feature-workflow && python3 -m pytest skills/shared/tests/test_workspace.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/feature-init/scripts/init.py feature-workflow/skills/shared/tests/test_workspace.py
git commit -m "feat(feature-init): --workspace mode scaffolds a multi-repo workspace"
```

---

### Task 6: `feature-init` SKILL — workspace branch + docs

**Files:**
- Modify: `feature-workflow/skills/feature-init/SKILL.md`

- [ ] **Step 1: Add the workspace section**

Open `feature-workflow/skills/feature-init/SKILL.md`. Near the top, after the existing `--update` short-circuit note (line ~16), add:

```markdown
## Workspace mode (`/feature-init --workspace`)

If the user invokes `/feature-init --workspace` (or asks to "set up a multi-repo
workspace"), scaffold a **workspace repo** instead of a single-project init:

1. Ask for the **GitHub org** and the **member repos** (each as `dir=owner/repo`).
   If they're unsure, list the org's repos with `gh repo list <org>`.
2. Run the scaffolder:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/feature-init/scripts/init.py" . --workspace \
     --org <org> \
     --member <dir>=<owner/repo> [--member <dir>=<owner/repo> ...]
   ```

3. Tell the user to `./scripts/clone-members.sh` to pull the members in, then
   launch Claude from the workspace directory (every member is then in-tree, so
   cross-repo edits don't prompt).

The workspace is identified by its `.feature-workspace.yml` manifest, not its
name. See `docs/designs/2026-06-08-multi-repo-workspace.md` for the full model.
```

- [ ] **Step 2: Verify the full suite still passes**

Run: `cd feature-workflow && python3 -m pytest -q`
Expected: PASS (all existing tests + the 9 new workspace tests; no regressions).

- [ ] **Step 3: Smoke-test the scaffolder by hand**

Run:
```bash
cd /tmp && rm -rf ws-smoke && mkdir ws-smoke
python3 /Users/courtschuett/GitHub/schuettc/claude-code-plugins/feature-workflow/skills/feature-init/scripts/init.py \
  /tmp/ws-smoke --workspace --org acme --member engine=acme/engine --member app=acme/app
ls -la /tmp/ws-smoke && cat /tmp/ws-smoke/.feature-workspace.yml && rm -rf /tmp/ws-smoke
```
Expected: manifest with `org: acme` + both members; `.gitignore`, `.claude/settings.json`, `CLAUDE.md`, `docs/features/DASHBOARD.md`, `scripts/clone-members.sh` (executable) all present.

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/feature-init/SKILL.md
git commit -m "docs(feature-init): document --workspace mode"
```

---

## Self-Review

**Spec coverage (Phase 1a slice):** Task 1–4 produce the workspace files the design's §4.1 layout requires (manifest, gitignore-with-members, CLAUDE.md topology, `.claude/settings.json` with `git -C`/`gh -R` allow, `docs/features/`, clone script, workspace `.feature-workflow.yml`). Task 5 wires the `feature-init --workspace` entry point (design §8 Tier-1 item 1). Task 6 documents it. *Out of this slice (separate plans):* repo-scoped config/IDs, aggregated dashboard, the `project-workflow` on-ramp — all noted in the spec's phasing.

**Placeholder scan:** every code step shows complete, runnable code; no TBD/TODO.

**Type consistency:** `scaffold_workspace(root, org, members)` signature and the `members` shape (`list[dict]` with `dir`/`repo` keys) are identical across Tasks 1–5; `init.py` builds exactly that shape from `--member dir=owner/repo`.
