"""Tests for the auto-sync of `epic:` ↔ `children:` relationships."""

from pathlib import Path

import pytest

from sync_epics import sync_epics


def _write_idea(path: Path, frontmatter: str, body: str = "Stub") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n")


@pytest.fixture
def epic_with_one_child_referenced_both_ways(tmp_path: Path) -> Path:
    """Both directions correctly set — sync should be a no-op."""
    features = tmp_path / "docs" / "features"
    _write_idea(
        features / "the-epic" / "idea.md",
        "id: the-epic\ntype: Epic\nchildren: [child-a]\ncreated: 2026-05-16",
    )
    _write_idea(
        features / "child-a" / "idea.md",
        "id: child-a\ntype: Feature\nepic: the-epic\ncreated: 2026-05-16",
    )
    return tmp_path


@pytest.fixture
def epic_with_child_only_from_parent(tmp_path: Path) -> Path:
    """Epic lists child-a in children:, but child-a has no epic: field. Sync should set it."""
    features = tmp_path / "docs" / "features"
    _write_idea(
        features / "the-epic" / "idea.md",
        "id: the-epic\ntype: Epic\nchildren: [child-a]\ncreated: 2026-05-16",
    )
    _write_idea(
        features / "child-a" / "idea.md",
        "id: child-a\ntype: Feature\ncreated: 2026-05-16",
    )
    return tmp_path


@pytest.fixture
def child_only_pointing_to_epic(tmp_path: Path) -> Path:
    """Child has epic:the-epic, but the epic's children: doesn't include it. Sync should append."""
    features = tmp_path / "docs" / "features"
    _write_idea(
        features / "the-epic" / "idea.md",
        "id: the-epic\ntype: Epic\ncreated: 2026-05-16",
    )
    _write_idea(
        features / "child-a" / "idea.md",
        "id: child-a\ntype: Feature\nepic: the-epic\ncreated: 2026-05-16",
    )
    return tmp_path


class TestSyncEpics:
    def test_already_in_sync_no_changes(self, epic_with_one_child_referenced_both_ways: Path):
        assert sync_epics(epic_with_one_child_referenced_both_ways) == 0

    def test_child_gets_epic_field_from_parent(self, epic_with_child_only_from_parent: Path):
        modified = sync_epics(epic_with_child_only_from_parent)
        assert modified == 1
        child = (epic_with_child_only_from_parent / "docs" / "features" / "child-a" / "idea.md").read_text()
        assert "epic: the-epic" in child

    def test_epic_gets_children_appended_from_child(self, child_only_pointing_to_epic: Path):
        modified = sync_epics(child_only_pointing_to_epic)
        assert modified == 1
        epic = (child_only_pointing_to_epic / "docs" / "features" / "the-epic" / "idea.md").read_text()
        assert "children:" in epic
        assert "child-a" in epic

    def test_idempotent(self, epic_with_child_only_from_parent: Path):
        sync_epics(epic_with_child_only_from_parent)
        assert sync_epics(epic_with_child_only_from_parent) == 0

    def test_existing_children_order_preserved_on_append(self, tmp_path: Path):
        """Appending a new child must not reorder the existing children: array."""
        features = tmp_path / "docs" / "features"
        _write_idea(
            features / "the-epic" / "idea.md",
            "id: the-epic\ntype: Epic\nchildren: [first, second]\ncreated: 2026-05-16",
        )
        _write_idea(features / "first" / "idea.md", "id: first\ntype: Feature\nepic: the-epic")
        _write_idea(features / "second" / "idea.md", "id: second\ntype: Feature\nepic: the-epic")
        # NEW child pointing at the epic — should be appended, not inserted
        _write_idea(features / "third" / "idea.md", "id: third\ntype: Feature\nepic: the-epic")

        sync_epics(tmp_path)
        epic = (features / "the-epic" / "idea.md").read_text()
        # Order must be first, second, third (NOT alphabetical or any reorder)
        first_pos = epic.find("first")
        second_pos = epic.find("second")
        third_pos = epic.find("third")
        assert first_pos < second_pos < third_pos

    def test_missing_target_skipped(self, tmp_path: Path):
        """If epic: points at a non-existent epic, skip silently (dashboard validation flags it)."""
        features = tmp_path / "docs" / "features"
        _write_idea(features / "child-a" / "idea.md", "id: child-a\ntype: Feature\nepic: ghost-epic")
        # No ghost-epic on disk
        assert sync_epics(tmp_path) == 0

    def test_does_not_remove_anything(self, tmp_path: Path):
        """Sync only ADDS the missing direction. Removing a relationship is user-driven."""
        features = tmp_path / "docs" / "features"
        # Epic says children: [orphan], but orphan doesn't point back
        _write_idea(
            features / "the-epic" / "idea.md",
            "id: the-epic\ntype: Epic\nchildren: [orphan]\ncreated: 2026-05-16",
        )
        _write_idea(features / "orphan" / "idea.md", "id: orphan\ntype: Feature\ncreated: 2026-05-16")
        sync_epics(tmp_path)
        epic = (features / "the-epic" / "idea.md").read_text()
        assert "orphan" in epic  # still there
        orphan = (features / "orphan" / "idea.md").read_text()
        assert "epic: the-epic" in orphan  # was added

    def test_no_features_dir(self, tmp_path: Path):
        assert sync_epics(tmp_path) == 0

    def test_nested_epic_rejected(self, tmp_path: Path):
        """If a child is itself type:Epic, don't mark it as another epic's child (nested epics not supported)."""
        features = tmp_path / "docs" / "features"
        _write_idea(
            features / "outer" / "idea.md",
            "id: outer\ntype: Epic\nchildren: [inner]\ncreated: 2026-05-16",
        )
        _write_idea(
            features / "inner" / "idea.md",
            "id: inner\ntype: Epic\ncreated: 2026-05-16",  # inner is itself an Epic
        )
        sync_epics(tmp_path)
        inner = (features / "inner" / "idea.md").read_text()
        # inner.epic: should NOT have been set — nested epics aren't supported
        assert "epic: outer" not in inner
