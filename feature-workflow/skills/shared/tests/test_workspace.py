"""Tests for the multi-repo workspace scaffolder."""

import json
import os
import subprocess
import sys
from pathlib import Path

from workspace import scaffold_workspace

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]

INIT_PY = Path(__file__).resolve().parents[2] / "feature-init" / "scripts" / "init.py"


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


def test_claude_md_has_topology_table(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert "acme workspace" in claude_md
    assert "engine" in claude_md and "acme/engine" in claude_md
    assert "git -C" in claude_md   # documents the member-op convention


def test_clone_members_script_is_executable_and_reads_manifest(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    script = tmp_path / "scripts" / "clone-members.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)            # executable bit set
    body = script.read_text()
    assert ".feature-workspace.yml" in body      # reads the manifest, not a hardcoded list
    assert body.startswith("#!/")


def test_keeps_shared_settings_tracked_ignores_only_local(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    gitignore = (tmp_path / ".gitignore").read_text()
    assert ".claude/settings.local.json" in gitignore   # local override ignored
    # the shared settings.json must NOT be ignored (teammates need the allowlist)
    assert "\n.claude/\n" not in gitignore


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
