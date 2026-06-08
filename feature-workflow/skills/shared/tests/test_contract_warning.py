"""Tests for the contract-edit warning (builder + hook integration)."""

import json
import os
import subprocess
import sys
from pathlib import Path

from workspace import build_contract_warning

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]

FILLED_MANIFEST = """\
org: acme
members:
  - { dir: engine, repo: acme/engine }
  - { dir: app, repo: acme/app }
contracts:
  - { id: engine:engine-api, owner: engine, consumers: [app, cli], kind: http }
"""

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
HOOK_PY = PLUGIN_ROOT / "hooks" / "post_tool_use.py"


def _make_workspace(tmp_path: Path) -> Path:
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    (tmp_path / ".git").mkdir()  # marker home; stands in for a real repo
    (tmp_path / "engine" / "src").mkdir(parents=True)
    return tmp_path


def test_builder_warns_for_producer(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    msg = build_contract_warning(tmp_path, "engine")
    assert msg is not None
    assert "engine:engine-api" in msg
    assert "app, cli" in msg
    assert "epic" in msg.lower()


def test_builder_silent_for_non_producer(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    assert build_contract_warning(tmp_path, "app") is None


def _run_hook(file_path: Path) -> str:
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}})
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    result = subprocess.run(
        [sys.executable, str(HOOK_PY)], input=payload, capture_output=True, text=True, env=env
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_hook_warns_on_producer_source_edit_once(tmp_path: Path):
    ws = _make_workspace(tmp_path)
    src = ws / "engine" / "src" / "api.py"
    src.write_text("x = 1\n")

    first = _run_hook(src)
    assert "engine:engine-api" in first  # warned the first time

    second = _run_hook(src)
    assert "engine:engine-api" not in second  # deduped by marker thereafter


def test_hook_silent_on_consumer_edit(tmp_path: Path):
    ws = _make_workspace(tmp_path)
    (ws / "app" / "src").mkdir(parents=True)
    src = ws / "app" / "src" / "ui.py"
    src.write_text("y = 2\n")
    assert "engine:engine-api" not in _run_hook(src)


def test_hook_silent_on_feature_doc_edit(tmp_path: Path):
    # Editing a producer's feature docs is not a contract reshape.
    ws = _make_workspace(tmp_path)
    feat = ws / "engine" / "docs" / "features" / "x"
    feat.mkdir(parents=True)
    idea = feat / "idea.md"
    idea.write_text(
        "---\nid: x\nname: X\ntype: Feature\npriority: P1\neffort: Low\nimpact: Low\ncreated: 2024-01-15\n---\n# X\n"
    )
    assert "engine:engine-api" not in _run_hook(idea)
