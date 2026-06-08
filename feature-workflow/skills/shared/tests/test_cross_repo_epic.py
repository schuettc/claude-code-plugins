"""Cross-repo epic dispatch: a workspace epic whose children live in member
repos resolves into the right parallel-safe waves via the existing dispatcher."""

from pathlib import Path

from workspace import scaffold_workspace
from run_dashboard import build_workspace_by_id
from deps import compute_dispatch_waves

MEMBERS = [
    {"dir": "engine", "repo": "acme/engine"},
    {"dir": "app", "repo": "acme/app"},
]


def _idea(features_dir: Path, fid: str, name: str, ftype: str = "Feature", extra: str = "") -> None:
    d = features_dir / fid
    d.mkdir(parents=True)
    (d / "idea.md").write_text(
        f"---\nid: {fid}\nname: {name}\ntype: {ftype}\n"
        f"priority: P1\neffort: Medium\nimpact: High\ncreated: 2024-01-15\n{extra}---\n\n# {name}\n"
    )


def test_build_workspace_by_id_namespaces_member_features(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    _idea(tmp_path / "docs" / "features", "big-epic", "Big Epic")
    _idea(tmp_path / "engine" / "docs" / "features", "engine-api", "Engine API")
    _idea(tmp_path / "app" / "docs" / "features", "app-ui", "App UI")

    by_id = build_workspace_by_id(tmp_path)
    assert "big-epic" in by_id  # workspace-own keeps bare id
    assert "engine:engine-api" in by_id  # members are namespaced
    assert "app:app-ui" in by_id


def test_cross_repo_epic_waves_respect_dependencies(tmp_path: Path):
    scaffold_workspace(tmp_path, org="acme", members=MEMBERS)
    # Epic in the workspace, children point at two member repos.
    _idea(
        tmp_path / "docs" / "features",
        "big-epic",
        "Big Epic",
        ftype="Epic",
        extra="children: [engine:engine-api, app:app-ui]\n",
    )
    # engine-api has no deps; app-ui depends on engine-api (cross-repo ref).
    _idea(tmp_path / "engine" / "docs" / "features", "engine-api", "Engine API")
    _idea(
        tmp_path / "app" / "docs" / "features",
        "app-ui",
        "App UI",
        extra="dependsOn: [engine:engine-api]\n",
    )

    by_id = build_workspace_by_id(tmp_path)
    waves = compute_dispatch_waves("big-epic", by_id)

    assert waves == [["engine:engine-api"], ["app:app-ui"]]
