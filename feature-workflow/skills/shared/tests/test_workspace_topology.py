"""Tests for workspace topology helpers: target resolution, feature refs,
contracts, and deploy groups read from the manifest."""

import pytest
from pathlib import Path

from workspace import (
    scaffold_workspace,
    resolve_target_repo,
    parse_feature_ref,
    format_feature_ref,
    load_contracts,
    load_deploy_groups,
    select_deploy_groups,
    contract_consumers,
)

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]

# A manifest with contracts + deploy groups filled in (uncommented).
FILLED_MANIFEST = """\
org: acme
members:
  - { dir: engine, repo: acme/engine }
  - { dir: app, repo: acme/app }
contracts:
  - { id: engine:engine-api, owner: engine, consumers: [app, cli], kind: http }
  - { id: app:events, owner: app, consumers: [], kind: queue }
deploy:
  - { group: engine-stack, dir: engine }
  - { group: app-stack, dir: app }
"""


# --- resolve_target_repo -------------------------------------------------

def test_resolve_workspace_itself(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    r = resolve_target_repo(tmp_path, None)
    assert r["is_workspace"] is True
    assert r["repo"] is None
    assert r["root"] == tmp_path


def test_resolve_member(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    r = resolve_target_repo(tmp_path, "engine")
    assert r["is_workspace"] is False
    assert r["repo"] == "acme/engine"
    assert r["root"] == tmp_path / "engine"


def test_resolve_unknown_member_raises(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    with pytest.raises(ValueError, match="not a member"):
        resolve_target_repo(tmp_path, "nope")


# --- feature refs --------------------------------------------------------

def test_parse_namespaced_ref():
    assert parse_feature_ref("engine:engine-api") == ("engine", "engine-api")


def test_parse_bare_ref():
    assert parse_feature_ref("engine-api") == (None, "engine-api")


def test_format_ref_roundtrip():
    assert format_feature_ref("engine", "engine-api") == "engine:engine-api"
    assert format_feature_ref(None, "engine-api") == "engine-api"


# --- contracts & deploy groups ------------------------------------------

def test_load_contracts(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    contracts = load_contracts(tmp_path)
    ids = {c["id"] for c in contracts}
    assert ids == {"engine:engine-api", "app:events"}
    api = next(c for c in contracts if c["id"] == "engine:engine-api")
    assert api["owner"] == "engine"
    assert api["consumers"] == ["app", "cli"]
    assert api["kind"] == "http"


def test_load_contracts_ignores_commented_examples(tmp_path: Path):
    # The scaffolded manifest leaves contracts commented out -> none parsed.
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    assert load_contracts(tmp_path) == []


def test_load_deploy_groups_preserves_order(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    groups = load_deploy_groups(tmp_path)
    assert [g["group"] for g in groups] == ["engine-stack", "app-stack"]
    assert groups[0]["dir"] == "engine"


def test_deploy_groups_do_not_match_member_lines(tmp_path: Path):
    # Member entries also carry `dir:` but no `group:` — must not be picked up.
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    assert load_deploy_groups(tmp_path) == []


def test_select_deploy_groups_all(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    groups = select_deploy_groups(tmp_path)
    assert [g["group"] for g in groups] == ["engine-stack", "app-stack"]


def test_select_deploy_groups_scoped_to_members(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    groups = select_deploy_groups(tmp_path, member_dirs=["engine"])
    assert [g["group"] for g in groups] == ["engine-stack"]  # order preserved, app dropped


def test_contract_consumers_only_returns_owned_with_consumers(tmp_path: Path):
    (tmp_path / ".feature-workspace.yml").write_text(FILLED_MANIFEST)
    warn = contract_consumers(tmp_path, "engine")
    assert len(warn) == 1
    assert warn[0]["consumers"] == ["app", "cli"]
    # app:events has no consumers -> nothing to warn about
    assert contract_consumers(tmp_path, "app") == []
