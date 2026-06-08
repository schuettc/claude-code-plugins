"""Tests for the aggregated multi-repo workspace dashboard."""

import json
import os
import subprocess
import sys
from pathlib import Path

from workspace import scaffold_workspace, load_members, is_workspace
from run_dashboard import (
    generate_workspace_dashboard,
    generate_workspace_dashboard_content,
)

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]


def _write_idea(features_dir: Path, fid: str, name: str, ftype: str = "Feature", extra: str = "") -> None:
    d = features_dir / fid
    d.mkdir(parents=True)
    (d / "idea.md").write_text(
        f"---\nid: {fid}\nname: {name}\ntype: {ftype}\n"
        f"priority: P1\neffort: Medium\nimpact: High\ncreated: 2024-01-15\n{extra}---\n\n# {name}\n"
    )


def test_load_members_reads_manifest(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    members = load_members(tmp_path)
    assert {"dir": "engine", "repo": "acme/engine"} in members
    assert {"dir": "app", "repo": "acme/app"} in members
    assert len(members) == 2


def test_load_members_empty_when_no_manifest(tmp_path: Path):
    assert load_members(tmp_path) == []


def test_is_workspace_detects_manifest(tmp_path: Path):
    assert is_workspace(tmp_path) is False
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    assert is_workspace(tmp_path) is True


def test_workspace_dashboard_aggregates_every_repo(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    _write_idea(tmp_path / "docs" / "features", "ws-coord", "Workspace Coord")
    _write_idea(tmp_path / "engine" / "docs" / "features", "engine-api", "Engine API")
    _write_idea(tmp_path / "app" / "docs" / "features", "app-ui", "App UI")

    content = generate_workspace_dashboard_content(tmp_path)

    assert "# Workspace Dashboard" in content
    # roll-up table names every repo, including the workspace itself
    assert "(workspace)" in content
    assert "| engine |" in content
    assert "| app |" in content
    # each repo's feature is surfaced, tagged with its repo
    assert "ws-coord" in content
    assert "engine-api" in content
    assert "app-ui" in content


def test_workspace_dashboard_writes_to_workspace_features(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    generate_workspace_dashboard(tmp_path)
    dash = tmp_path / "docs" / "features" / "DASHBOARD.md"
    assert dash.exists()
    assert "# Workspace Dashboard" in dash.read_text()


def test_workspace_dashboard_surfaces_cross_repo_epics(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    _write_idea(
        tmp_path / "docs" / "features",
        "big-epic",
        "Big Epic",
        ftype="Epic",
        extra="children: [engine:engine-api, app:app-ui]\n",
    )
    content = generate_workspace_dashboard_content(tmp_path)
    assert "## Epics (cross-repo coordinators)" in content
    assert "big-epic" in content


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
HOOK_PY = PLUGIN_ROOT / "hooks" / "post_tool_use.py"


def test_post_tool_use_hook_refreshes_aggregate_on_member_edit(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    feat = tmp_path / "engine" / "docs" / "features" / "engine-api"
    feat.mkdir(parents=True)
    idea = feat / "idea.md"
    idea.write_text(
        "---\nid: engine-api\nname: Engine API\ntype: Feature\n"
        "priority: P1\neffort: Medium\nimpact: High\ncreated: 2024-01-15\n---\n\n# Engine API\n"
    )

    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(idea)}})
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    result = subprocess.run(
        [sys.executable, str(HOOK_PY)], input=payload, capture_output=True, text=True, env=env
    )
    assert result.returncode == 0, result.stderr

    # member's own dashboard regenerated (single-repo form)
    assert (tmp_path / "engine" / "docs" / "features" / "DASHBOARD.md").exists()
    # workspace aggregate refreshed via walk-up, now carrying the member's feature
    ws_dash = (tmp_path / "docs" / "features" / "DASHBOARD.md").read_text()
    assert "# Workspace Dashboard" in ws_dash
    assert "engine-api" in ws_dash


def test_workspace_dashboard_handles_member_without_features(tmp_path: Path):
    # app has no docs/features at all — must not crash, just shows zeros.
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    _write_idea(tmp_path / "engine" / "docs" / "features", "engine-api", "Engine API")
    content = generate_workspace_dashboard_content(tmp_path)
    assert "| app | 0 | 0 | 0 |" in content
