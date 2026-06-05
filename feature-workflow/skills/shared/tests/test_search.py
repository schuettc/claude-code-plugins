"""Tests for feature-search."""

import sys
from pathlib import Path

# Add the search scripts dir to path
SEARCH_DIR = Path(__file__).parent.parent.parent / "feature-search" / "scripts"
if str(SEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(SEARCH_DIR))

import pytest
from search import search_features


@pytest.fixture
def search_corpus(tmp_path: Path) -> Path:
    features_dir = tmp_path / "docs" / "features"
    features_dir.mkdir(parents=True)

    (features_dir / "alpha").mkdir()
    (features_dir / "alpha" / "idea.md").write_text("""---
id: alpha
name: Alpha
type: Feature
priority: P0
effort: Small
impact: High
assignee: court
state: active
created: 2026-01-01
---
# Alpha""")

    (features_dir / "beta").mkdir()
    (features_dir / "beta" / "idea.md").write_text("""---
id: beta
name: Beta
type: Feature
priority: P1
effort: Medium
impact: Medium
assignee: alex
state: paused
pausedReason: Waiting
created: 2026-01-01
---
# Beta""")

    (features_dir / "gamma").mkdir()
    (features_dir / "gamma" / "idea.md").write_text("""---
id: gamma
name: Gamma
type: Feature
priority: P0
effort: Small
impact: Low
state: replaced
replacedBy: alpha
created: 2026-01-01
---
# Gamma""")

    (features_dir / "delta").mkdir()
    (features_dir / "delta" / "idea.md").write_text("""---
id: delta
name: Delta
type: Feature
priority: P2
effort: Large
impact: Low
epic: my-epic
dependsOn: [alpha]
created: 2026-01-01
---
# Delta""")

    return tmp_path


class TestSearchFeatures:
    def test_no_filters_excludes_archive(self, search_corpus: Path):
        results = search_features(search_corpus, filters={})
        ids = sorted(r.feature_id for r in results)
        assert ids == ["alpha", "beta", "delta"]  # gamma (replaced) excluded

    def test_archive_flag_includes_tombstones(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"archive": True})
        ids = sorted(r.feature_id for r in results)
        assert ids == ["alpha", "beta", "delta", "gamma"]

    def test_filter_by_state(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"state": "paused"})
        ids = sorted(r.feature_id for r in results)
        assert ids == ["beta"]

    def test_filter_by_assignee(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"assignee": "court"})
        ids = [r.feature_id for r in results]
        assert ids == ["alpha"]

    def test_filter_by_priority(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"priority": "P0"})
        ids = sorted(r.feature_id for r in results)
        assert ids == ["alpha"]  # gamma is P0 but tombstoned

    def test_filter_by_epic(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"epic": "my-epic"})
        ids = [r.feature_id for r in results]
        assert ids == ["delta"]

    def test_filter_by_depends_on(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"depends_on": "alpha"})
        ids = [r.feature_id for r in results]
        assert ids == ["delta"]

    def test_combined_filters(self, search_corpus: Path):
        results = search_features(search_corpus, filters={"state": "active", "priority": "P0"})
        ids = sorted(r.feature_id for r in results)
        assert ids == ["alpha"]
