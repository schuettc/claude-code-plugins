"""Tests for dependency-graph utilities."""

from pathlib import Path

import pytest

from deps import detect_cycles, compute_blocked_by, find_unknown_refs
from models import FeatureContext, FeatureStatus, FeatureState


def _ctx(feature_id: str, *, depends_on=None, status=FeatureStatus.BACKLOG, state=FeatureState.ACTIVE, epic="") -> FeatureContext:
    """Build a minimal FeatureContext for graph tests (no on-disk file)."""
    return FeatureContext(
        feature_id=feature_id,
        feature_dir=Path(f"/fake/{feature_id}"),
        status=status,
        name=feature_id,
        depends_on=list(depends_on or []),
        state=state,
        epic=epic,
    )


class TestDetectCycles:
    def test_no_cycle(self):
        features = {
            "a": _ctx("a"),
            "b": _ctx("b", depends_on=["a"]),
            "c": _ctx("c", depends_on=["b"]),
        }
        assert detect_cycles(features) == []

    def test_simple_cycle(self):
        features = {
            "a": _ctx("a", depends_on=["b"]),
            "b": _ctx("b", depends_on=["a"]),
        }
        cycles = detect_cycles(features)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b"}

    def test_self_loop(self):
        features = {"a": _ctx("a", depends_on=["a"])}
        cycles = detect_cycles(features)
        assert cycles == [["a"]]

    def test_three_cycle(self):
        features = {
            "a": _ctx("a", depends_on=["b"]),
            "b": _ctx("b", depends_on=["c"]),
            "c": _ctx("c", depends_on=["a"]),
        }
        cycles = detect_cycles(features)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b", "c"}


class TestComputeBlockedBy:
    def test_no_blockers(self):
        features = {"a": _ctx("a")}
        assert compute_blocked_by("a", features) == []

    def test_one_blocker(self):
        """If b depends on a (not completed), then a is blocking b — so a's blocked_by includes b."""
        features = {
            "a": _ctx("a"),  # backlog
            "b": _ctx("b", depends_on=["a"]),
        }
        # a is blocking b, so b "blocks completion of a-dependents". The
        # compute_blocked_by(feature) function returns features that CANNOT
        # START because `feature` is one of their unmet dependencies.
        # So compute_blocked_by("a") = [b].
        assert compute_blocked_by("a", features) == ["b"]

    def test_completed_blocker_clears(self):
        features = {
            "a": _ctx("a", status=FeatureStatus.COMPLETED),
            "b": _ctx("b", depends_on=["a"]),
        }
        # a is completed, so a no longer blocks b → "blocked features by a" = []
        assert compute_blocked_by("a", features) == []

    def test_tombstone_blocker_clears(self):
        features = {
            "a": _ctx("a", state=FeatureState.ABANDONED),
            "b": _ctx("b", depends_on=["a"]),
        }
        # a is abandoned → effectively complete for blocking purposes? Design call:
        # tombstoned features still BLOCK because they aren't shipped. b stays blocked.
        assert compute_blocked_by("a", features) == ["b"]


class TestFindUnknownRefs:
    def test_all_known(self):
        features = {
            "a": _ctx("a"),
            "b": _ctx("b", depends_on=["a"]),
        }
        assert find_unknown_refs(features) == []

    def test_unknown_dependson(self):
        features = {
            "a": _ctx("a", depends_on=["missing-feat"]),
        }
        refs = find_unknown_refs(features)
        assert refs == [("a", "dependsOn", "missing-feat")]

    def test_unknown_epic(self):
        features = {
            "a": _ctx("a", epic="missing-epic"),
        }
        refs = find_unknown_refs(features)
        assert refs == [("a", "epic", "missing-epic")]
