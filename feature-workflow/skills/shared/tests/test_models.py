"""Tests for feature-workflow data models."""

from datetime import date
from pathlib import Path

import pytest

from models import FeatureStatus, FeatureContext


class TestFeatureStatus:
    """Tests for FeatureStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert FeatureStatus.BACKLOG.value == "backlog"
        assert FeatureStatus.IN_PROGRESS.value == "in_progress"
        assert FeatureStatus.COMPLETED.value == "completed"


class TestFeatureContext:
    """Tests for FeatureContext dataclass."""

    def test_from_directory_backlog(self, feature_in_backlog: Path):
        """Test creating context from backlog feature."""
        ctx = FeatureContext.from_directory(feature_in_backlog)

        assert ctx is not None
        assert ctx.feature_id == "test-feature"
        assert ctx.status == FeatureStatus.BACKLOG
        assert ctx.name == "Test Feature"
        assert ctx.type == "Feature"
        assert ctx.priority == "P1"
        assert ctx.effort == "Medium"
        assert ctx.impact == "High"
        assert ctx.created == date(2024, 1, 15)
        assert ctx.started is None
        assert ctx.shipped is None

    def test_from_directory_in_progress(self, feature_in_progress: Path):
        """Test creating context from in-progress feature."""
        ctx = FeatureContext.from_directory(feature_in_progress)

        assert ctx is not None
        assert ctx.status == FeatureStatus.IN_PROGRESS
        assert ctx.started == date(2024, 1, 20)
        assert ctx.shipped is None

    def test_from_directory_completed(self, feature_completed: Path):
        """Test creating context from completed feature."""
        ctx = FeatureContext.from_directory(feature_completed)

        assert ctx is not None
        assert ctx.status == FeatureStatus.COMPLETED
        assert ctx.shipped == date(2024, 1, 25)

    def test_from_directory_no_idea(self, tmp_path: Path):
        """Test that directory without idea.md returns None."""
        feature_dir = tmp_path / "no-idea-feature"
        feature_dir.mkdir()
        (feature_dir / "plan.md").write_text("Some plan")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is None

    def test_from_directory_empty(self, tmp_path: Path):
        """Test that empty directory returns None."""
        feature_dir = tmp_path / "empty-feature"
        feature_dir.mkdir()

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is None

    def test_fallback_name(self, tmp_path: Path):
        """Test that feature_id is used as fallback name."""
        feature_dir = tmp_path / "unnamed-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
priority: P1
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None
        assert ctx.name == "unnamed-feature"

    def test_invalid_date(self, tmp_path: Path):
        """Test handling of invalid date values."""
        feature_dir = tmp_path / "bad-date-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
name: Bad Date Feature
created: not-a-date
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None
        assert ctx.created is None
