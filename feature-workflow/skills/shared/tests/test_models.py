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

    def test_depends_on_array(self, tmp_path: Path):
        """Test parsing dependsOn array from frontmatter."""
        feature_dir = tmp_path / "dependent-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
name: Dependent Feature
dependsOn: [feature-a, feature-b]
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None
        assert ctx.depends_on == ["feature-a", "feature-b"]
        assert ctx.blocked_by == []

    def test_blocked_by_array(self, tmp_path: Path):
        """Test parsing blockedBy array from frontmatter."""
        feature_dir = tmp_path / "blocking-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
name: Blocking Feature
blockedBy: [feature-x, feature-y]
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None
        assert ctx.depends_on == []
        assert ctx.blocked_by == ["feature-x", "feature-y"]

    def test_depends_on_single_string(self, tmp_path: Path):
        """Test dependsOn with single string value (backward compatibility)."""
        feature_dir = tmp_path / "single-dep-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
name: Single Dep Feature
dependsOn: feature-a
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None
        assert ctx.depends_on == ["feature-a"]

    def test_has_unmet_dependencies_all_missing(self, tmp_path: Path):
        """Test has_unmet_dependencies when dependencies don't exist."""
        feature_dir = tmp_path / "test-feature"
        feature_dir.mkdir()
        (feature_dir / "idea.md").write_text("""---
name: Test Feature
dependsOn: [feature-a, feature-b]
---

# Content
""")

        ctx = FeatureContext.from_directory(feature_dir)
        assert ctx is not None

        all_features = {ctx.feature_id: ctx}
        unmet = ctx.has_unmet_dependencies(all_features)
        assert unmet == ["feature-a", "feature-b"]

    def test_has_unmet_dependencies_some_completed(self, tmp_path: Path):
        """Test has_unmet_dependencies when some deps are completed."""
        # Create the dependent feature
        dep_feature_dir = tmp_path / "dep-feature"
        dep_feature_dir.mkdir()
        (dep_feature_dir / "idea.md").write_text("""---
name: Dependent Feature
dependsOn: [feature-a, feature-b]
---
""")

        # Create completed dependency (feature-a)
        feature_a_dir = tmp_path / "feature-a"
        feature_a_dir.mkdir()
        (feature_a_dir / "idea.md").write_text("""---
name: Feature A
---
""")
        (feature_a_dir / "plan.md").write_text("---\nstarted: 2024-01-01\n---")
        (feature_a_dir / "shipped.md").write_text("---\nshipped: 2024-01-10\n---")

        # Create incomplete dependency (feature-b)
        feature_b_dir = tmp_path / "feature-b"
        feature_b_dir.mkdir()
        (feature_b_dir / "idea.md").write_text("""---
name: Feature B
---
""")

        dep_ctx = FeatureContext.from_directory(dep_feature_dir)
        a_ctx = FeatureContext.from_directory(feature_a_dir)
        b_ctx = FeatureContext.from_directory(feature_b_dir)

        all_features = {
            dep_ctx.feature_id: dep_ctx,
            a_ctx.feature_id: a_ctx,
            b_ctx.feature_id: b_ctx,
        }

        unmet = dep_ctx.has_unmet_dependencies(all_features)
        assert unmet == ["feature-b"]
        assert "feature-a" not in unmet

    def test_has_unmet_dependencies_all_completed(self, tmp_path: Path):
        """Test has_unmet_dependencies when all deps are completed."""
        # Create the dependent feature
        dep_feature_dir = tmp_path / "dep-feature"
        dep_feature_dir.mkdir()
        (dep_feature_dir / "idea.md").write_text("""---
name: Dependent Feature
dependsOn: [feature-a]
---
""")

        # Create completed dependency
        feature_a_dir = tmp_path / "feature-a"
        feature_a_dir.mkdir()
        (feature_a_dir / "idea.md").write_text("""---
name: Feature A
---
""")
        (feature_a_dir / "plan.md").write_text("---\nstarted: 2024-01-01\n---")
        (feature_a_dir / "shipped.md").write_text("---\nshipped: 2024-01-10\n---")

        dep_ctx = FeatureContext.from_directory(dep_feature_dir)
        a_ctx = FeatureContext.from_directory(feature_a_dir)

        all_features = {
            dep_ctx.feature_id: dep_ctx,
            a_ctx.feature_id: a_ctx,
        }

        unmet = dep_ctx.has_unmet_dependencies(all_features)
        assert unmet == []
