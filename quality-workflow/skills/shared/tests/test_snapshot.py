"""Tests for the snapshot module: QualityFinding/QualitySnapshot data + fingerprint diff."""

import json
from datetime import date
from pathlib import Path

import pytest

from snapshot import (
    QualityFinding,
    QualitySnapshot,
    SnapshotDiff,
    diff_snapshots,
    read_snapshot,
    write_snapshot,
)


def _finding(fp: str, **overrides) -> QualityFinding:
    """Helper: build a QualityFinding with sensible defaults."""
    kwargs = dict(
        fingerprint=fp,
        rule_id="SKY-Q302",
        category="quality",
        severity="MEDIUM",
        file="pi/foo.py",
        line=10,
        message="nesting depth exceeds threshold",
        tool="skylos",
        confidence=None,
    )
    kwargs.update(overrides)
    return QualityFinding(**kwargs)


class TestQualityFinding:
    def test_roundtrip_json(self):
        f = _finding("fp1", line=42, confidence=0.85)
        d = f.to_dict()
        f2 = QualityFinding.from_dict(d)
        assert f == f2

    def test_required_fields(self):
        f = _finding("fp1")
        d = f.to_dict()
        assert d["fingerprint"] == "fp1"
        assert d["rule_id"] == "SKY-Q302"
        assert d["tool"] == "skylos"


class TestQualitySnapshot:
    def test_roundtrip_to_json_file(self, tmp_path: Path):
        snap = QualitySnapshot(
            date="2026-05-22",
            commit="abc123",
            tool_versions={"skylos": "1.2.3", "fallow": "0.4.5"},
            findings=[_finding("fp1"), _finding("fp2", rule_id="FAL-DUP-01", tool="fallow")],
            grade="C",
        )
        path = tmp_path / "snap.json"
        write_snapshot(snap, path)
        assert path.exists()

        loaded = read_snapshot(path)
        assert loaded.date == "2026-05-22"
        assert loaded.commit == "abc123"
        assert loaded.grade == "C"
        assert len(loaded.findings) == 2
        assert loaded.findings[0].fingerprint == "fp1"
        assert loaded.findings[1].tool == "fallow"

    def test_read_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            read_snapshot(tmp_path / "nope.json")

    def test_write_creates_parents(self, tmp_path: Path):
        snap = QualitySnapshot(
            date="2026-05-22", commit="abc", tool_versions={}, findings=[], grade="A",
        )
        nested = tmp_path / "a" / "b" / "snap.json"
        write_snapshot(snap, nested)
        assert nested.exists()


class TestDiffSnapshots:
    def test_empty_to_empty(self):
        a = QualitySnapshot(date="d1", commit="c1", tool_versions={}, findings=[], grade="A")
        b = QualitySnapshot(date="d2", commit="c2", tool_versions={}, findings=[], grade="A")
        d = diff_snapshots(a, b)
        assert d.new == []
        assert d.resolved == []
        assert d.persisting == []

    def test_all_new(self):
        a = QualitySnapshot(date="d1", commit="c1", tool_versions={}, findings=[], grade="A")
        b = QualitySnapshot(
            date="d2", commit="c2", tool_versions={},
            findings=[_finding("fp1"), _finding("fp2")], grade="B",
        )
        d = diff_snapshots(a, b)
        assert sorted(f.fingerprint for f in d.new) == ["fp1", "fp2"]
        assert d.resolved == []
        assert d.persisting == []

    def test_all_resolved(self):
        a = QualitySnapshot(
            date="d1", commit="c1", tool_versions={},
            findings=[_finding("fp1"), _finding("fp2")], grade="C",
        )
        b = QualitySnapshot(date="d2", commit="c2", tool_versions={}, findings=[], grade="A")
        d = diff_snapshots(a, b)
        assert d.new == []
        assert sorted(f.fingerprint for f in d.resolved) == ["fp1", "fp2"]
        assert d.persisting == []

    def test_mixed_movement(self):
        # fp1 persists; fp2 resolved; fp3 new
        a = QualitySnapshot(
            date="d1", commit="c1", tool_versions={},
            findings=[_finding("fp1"), _finding("fp2")], grade="C",
        )
        b = QualitySnapshot(
            date="d2", commit="c2", tool_versions={},
            findings=[_finding("fp1"), _finding("fp3")], grade="C",
        )
        d = diff_snapshots(a, b)
        assert [f.fingerprint for f in d.new] == ["fp3"]
        assert [f.fingerprint for f in d.resolved] == ["fp2"]
        assert [f.fingerprint for f in d.persisting] == ["fp1"]

    def test_persisting_returns_b_side(self):
        """If a finding's line moves between snapshots, the diff should keep B's coordinates."""
        a = QualitySnapshot(
            date="d1", commit="c1", tool_versions={},
            findings=[_finding("fp1", line=10)], grade="C",
        )
        b = QualitySnapshot(
            date="d2", commit="c2", tool_versions={},
            findings=[_finding("fp1", line=22)], grade="C",
        )
        d = diff_snapshots(a, b)
        assert len(d.persisting) == 1
        assert d.persisting[0].line == 22  # newer location wins

    def test_diff_is_serializable(self, tmp_path: Path):
        a = QualitySnapshot(date="d1", commit="c1", tool_versions={}, findings=[_finding("fp1")], grade="C")
        b = QualitySnapshot(date="d2", commit="c2", tool_versions={}, findings=[_finding("fp2")], grade="C")
        d = diff_snapshots(a, b)
        # Should be able to serialize the diff itself for CLI output
        payload = {
            "new": [f.to_dict() for f in d.new],
            "resolved": [f.to_dict() for f in d.resolved],
            "persisting": [f.to_dict() for f in d.persisting],
        }
        json.dumps(payload)  # raises if any field isn't JSON-safe


class TestSuppressionAwareness:
    """Snapshots store ALL findings (active + suppressed) so we can detect when
    a suppression is added/removed. Counts and headlines show ACTIVE only.
    """

    def test_active_findings_filters_suppressed(self):
        snap = QualitySnapshot(
            date="d1", commit="c1", tool_versions={}, grade="B",
            findings=[
                _finding("fp_active"),
                _finding("fp_suppressed", suppressed=True, suppression_reason="inline ignore comment"),
            ],
        )
        active = snap.active_findings()
        suppressed = snap.suppressed_findings()
        assert [f.fingerprint for f in active] == ["fp_active"]
        assert [f.fingerprint for f in suppressed] == ["fp_suppressed"]

    def test_finding_roundtrip_includes_suppression(self, tmp_path: Path):
        f = _finding("fp1", suppressed=True, suppression_reason="inline ignore comment")
        d = f.to_dict()
        assert d["suppressed"] is True
        assert d["suppression_reason"] == "inline ignore comment"
        f2 = QualityFinding.from_dict(d)
        assert f2.suppressed is True
        assert f2.suppression_reason == "inline ignore comment"

    def test_diff_exposes_active_views(self):
        # a: fp1 active, fp2 suppressed
        # b: fp1 active (unchanged), fp2 still suppressed, fp3 NEW active, fp4 NEW suppressed
        a = QualitySnapshot(
            date="d1", commit="c1", tool_versions={}, grade="B",
            findings=[
                _finding("fp1"),
                _finding("fp2", suppressed=True, suppression_reason="inline ignore comment"),
            ],
        )
        b = QualitySnapshot(
            date="d2", commit="c2", tool_versions={}, grade="B",
            findings=[
                _finding("fp1"),
                _finding("fp2", suppressed=True, suppression_reason="inline ignore comment"),
                _finding("fp3"),
                _finding("fp4", suppressed=True, suppression_reason="inline ignore comment"),
            ],
        )
        d = diff_snapshots(a, b)
        # Full diff includes everything (suppressed transitions are still movement)
        assert sorted(f.fingerprint for f in d.new) == ["fp3", "fp4"]
        # Active-filtered views drop suppressed
        assert [f.fingerprint for f in d.active_new] == ["fp3"]
        assert d.active_resolved == []
        assert [f.fingerprint for f in d.active_persisting] == ["fp1"]

    def test_default_finding_is_active(self):
        # Existing call sites that don't pass `suppressed` keep working
        f = QualityFinding(
            fingerprint="fp",
            rule_id="SKY-Q301",
            category="quality",
            severity="HIGH",
            file="x.py",
            line=1,
            message="m",
            tool="skylos",
        )
        assert f.suppressed is False
        assert f.suppression_reason is None
