"""Tests for the auto-sync of `replaces:` → tombstone targets."""

from pathlib import Path

import pytest

from sync_replaces import sync_replaces


def _write_idea(path: Path, frontmatter: str, body: str = "Stub") -> None:
    """Helper: write an idea.md with the given frontmatter block."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n")


@pytest.fixture
def project_with_replaces(tmp_path: Path) -> Path:
    """A project where new-thing declares it replaces old-a and old-b."""
    features = tmp_path / "docs" / "features"
    _write_idea(
        features / "new-thing" / "idea.md",
        "id: new-thing\nname: New Thing\nreplaces: [old-a, old-b]\ncreated: 2026-05-15",
    )
    _write_idea(
        features / "old-a" / "idea.md",
        "id: old-a\nname: Old A\ncreated: 2026-04-01",
    )
    _write_idea(
        features / "old-b" / "idea.md",
        "id: old-b\nname: Old B\ncreated: 2026-04-02",
    )
    return tmp_path


class TestSyncReplaces:
    def test_no_replaces_no_changes(self, tmp_path: Path):
        features = tmp_path / "docs" / "features"
        _write_idea(features / "solo" / "idea.md", "id: solo\nname: Solo")
        assert sync_replaces(tmp_path) == 0

    def test_sets_state_and_replaced_by_on_targets(self, project_with_replaces: Path):
        modified = sync_replaces(project_with_replaces)
        assert modified == 2

        old_a = (project_with_replaces / "docs" / "features" / "old-a" / "idea.md").read_text()
        old_b = (project_with_replaces / "docs" / "features" / "old-b" / "idea.md").read_text()
        new = (project_with_replaces / "docs" / "features" / "new-thing" / "idea.md").read_text()

        assert "state: replaced" in old_a
        assert "replacedBy: new-thing" in old_a
        assert "state: replaced" in old_b
        assert "replacedBy: new-thing" in old_b
        # The new feature must NOT be touched
        assert "state: replaced" not in new
        assert "replacedBy:" not in new

    def test_idempotent(self, project_with_replaces: Path):
        """Running sync twice in a row makes no changes the second time."""
        first = sync_replaces(project_with_replaces)
        assert first == 2
        second = sync_replaces(project_with_replaces)
        assert second == 0

    def test_missing_target_skipped(self, tmp_path: Path):
        """If a `replaces:` target doesn't exist on disk, we skip it silently."""
        features = tmp_path / "docs" / "features"
        _write_idea(
            features / "new" / "idea.md",
            "id: new\nname: New\nreplaces: [ghost]",
        )
        # No `ghost` directory on disk
        assert sync_replaces(tmp_path) == 0

    def test_updates_existing_state_line(self, tmp_path: Path):
        """If the target already has state set (to something else), we overwrite it."""
        features = tmp_path / "docs" / "features"
        _write_idea(features / "new" / "idea.md", "id: new\nreplaces: [old]")
        _write_idea(
            features / "old" / "idea.md",
            "id: old\nstate: paused\npausedReason: Was waiting",
        )
        sync_replaces(tmp_path)
        content = (features / "old" / "idea.md").read_text()
        assert "state: replaced" in content
        assert "state: paused" not in content
        assert "replacedBy: new" in content

    def test_no_features_dir(self, tmp_path: Path):
        """No docs/features/ dir → no-op, no error."""
        assert sync_replaces(tmp_path) == 0
