"""Tests for dependency-graph utilities."""

from pathlib import Path

import pytest

from deps import detect_cycles, compute_blocked_by, find_unknown_refs, compute_dispatch_waves
from models import FeatureContext, FeatureStatus, FeatureState


def _ctx(feature_id: str, *, depends_on=None, status=FeatureStatus.BACKLOG, state=FeatureState.ACTIVE, epic="", ftype="Feature", children=None) -> FeatureContext:
    """Build a minimal FeatureContext for graph tests (no on-disk file)."""
    return FeatureContext(
        feature_id=feature_id,
        feature_dir=Path(f"/fake/{feature_id}"),
        status=status,
        name=feature_id,
        type=ftype,
        depends_on=list(depends_on or []),
        state=state,
        epic=epic,
        children=list(children or []),
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


class TestComputeDispatchWaves:
    """Sequential of waves where each wave is a parallel-dispatchable group.

    Within an epic's children:
    - Already-shipped / tombstoned / paused children are excluded
    - Remaining children are topo-sorted by `dependsOn:` (restricted to siblings within the same epic)
    - Children at the same dependency depth form a wave
    - Order within a wave follows the epic's `children:` array order
    """

    def test_empty_children(self):
        epic = _ctx("ep", ftype="Epic", children=[])
        assert compute_dispatch_waves("ep", {"ep": epic}) == []

    def test_unknown_epic(self):
        assert compute_dispatch_waves("missing", {}) == []

    def test_target_not_epic(self):
        regular = _ctx("regular")
        # No waves for non-epic targets
        assert compute_dispatch_waves("regular", {"regular": regular}) == []

    def test_no_dependencies_single_wave(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b", "c"])
        a = _ctx("a"); b = _ctx("b"); c = _ctx("c")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b, "c": c})
        # All independent → one wave with all three, in children: order
        assert waves == [["a", "b", "c"]]

    def test_linear_chain(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b", "c"])
        a = _ctx("a")
        b = _ctx("b", depends_on=["a"])
        c = _ctx("c", depends_on=["b"])
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b, "c": c})
        assert waves == [["a"], ["b"], ["c"]]

    def test_diamond(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b", "c", "d"])
        a = _ctx("a")
        b = _ctx("b", depends_on=["a"])
        c = _ctx("c", depends_on=["a"])
        d = _ctx("d", depends_on=["b", "c"])
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b, "c": c, "d": d})
        # a alone, then b+c together (both depend only on a), then d
        assert waves == [["a"], ["b", "c"], ["d"]]

    def test_children_order_resolves_ties(self):
        """Within a wave, order matches the epic's children: array."""
        epic = _ctx("ep", ftype="Epic", children=["c", "a", "b"])  # explicit order
        a = _ctx("a"); b = _ctx("b"); c = _ctx("c")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b, "c": c})
        assert waves == [["c", "a", "b"]]

    def test_shipped_children_excluded(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b", "c"])
        a = _ctx("a", status=FeatureStatus.COMPLETED)  # already shipped
        b = _ctx("b", depends_on=["a"])  # b can dispatch — its dep is shipped
        c = _ctx("c")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b, "c": c})
        # a omitted; b and c both unblocked (a is complete) → one wave
        assert waves == [["b", "c"]]

    def test_tombstoned_children_excluded(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b"])
        a = _ctx("a", state=FeatureState.REPLACED)
        b = _ctx("b")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b})
        assert waves == [["b"]]

    def test_paused_children_excluded(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "b"])
        a = _ctx("a", state=FeatureState.PAUSED)
        b = _ctx("b")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "b": b})
        assert waves == [["b"]]

    def test_dependency_outside_epic_ignored(self):
        """deps on non-children don't affect wave structure (the dispatcher only walks the epic's tree)."""
        epic = _ctx("ep", ftype="Epic", children=["a"])
        a = _ctx("a", depends_on=["external-thing"])  # external dep
        external = _ctx("external-thing")
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a, "external-thing": external})
        # a stays in its own wave, dep-on-external doesn't add external to the dispatch
        assert waves == [["a"]]

    def test_missing_child_skipped(self):
        epic = _ctx("ep", ftype="Epic", children=["a", "ghost"])
        a = _ctx("a")
        # ghost doesn't exist in features dict
        waves = compute_dispatch_waves("ep", {"ep": epic, "a": a})
        assert waves == [["a"]]
