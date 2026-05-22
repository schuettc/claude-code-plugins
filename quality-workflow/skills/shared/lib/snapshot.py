"""QualityFinding / QualitySnapshot data + fingerprint-keyed diff.

A snapshot is a JSON file under `.claude/quality-snapshots/<date>.json` capturing
every static-analysis finding active at one point in time. Fingerprint diffing
between two snapshots is set arithmetic — no semantic logic.

Pure stdlib. No third-party deps.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class QualityFinding:
    """A single static-analysis finding from skylos or fallow."""

    fingerprint: str
    rule_id: str
    category: str  # quality | security | secrets | dependency | duplication | dead-code
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    file: str
    line: int
    message: str
    tool: str  # "skylos" | "fallow"
    confidence: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "QualityFinding":
        return cls(**d)


@dataclass
class QualitySnapshot:
    """A point-in-time capture of every active finding across all tools."""

    date: str  # YYYY-MM-DD
    commit: str  # git rev-parse HEAD at scan time
    tool_versions: dict[str, str] = field(default_factory=dict)
    findings: list[QualityFinding] = field(default_factory=list)
    grade: str = ""  # tool-overall, e.g. skylos's letter grade or fallow's score

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "commit": self.commit,
            "tool_versions": dict(self.tool_versions),
            "findings": [f.to_dict() for f in self.findings],
            "grade": self.grade,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "QualitySnapshot":
        return cls(
            date=d.get("date", ""),
            commit=d.get("commit", ""),
            tool_versions=dict(d.get("tool_versions", {})),
            findings=[QualityFinding.from_dict(f) for f in d.get("findings", [])],
            grade=d.get("grade", ""),
        )


@dataclass
class SnapshotDiff:
    """Three sets keyed by fingerprint: what's new, what was resolved, what persists.

    `persisting` returns findings from the NEWER snapshot (so line numbers and other
    fields reflect current state, not the older snapshot's stale coordinates).
    """

    new: list[QualityFinding] = field(default_factory=list)
    resolved: list[QualityFinding] = field(default_factory=list)
    persisting: list[QualityFinding] = field(default_factory=list)


def write_snapshot(snap: QualitySnapshot, path: Path) -> None:
    """Write a snapshot to disk as JSON. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap.to_dict(), indent=2) + "\n", encoding="utf-8")


def read_snapshot(path: Path) -> QualitySnapshot:
    """Read a snapshot from disk. Raises FileNotFoundError if missing."""
    text = path.read_text(encoding="utf-8")
    return QualitySnapshot.from_dict(json.loads(text))


def diff_snapshots(a: QualitySnapshot, b: QualitySnapshot) -> SnapshotDiff:
    """Compute the fingerprint-keyed delta from snapshot `a` (older) to `b` (newer).

    Returns NEW (in b not in a), RESOLVED (in a not in b), PERSISTING (in both).
    Persisting findings carry b's coordinates so callers see current line numbers.
    """
    a_by_fp = {f.fingerprint: f for f in a.findings}
    b_by_fp = {f.fingerprint: f for f in b.findings}

    new_fps = sorted(set(b_by_fp) - set(a_by_fp))
    resolved_fps = sorted(set(a_by_fp) - set(b_by_fp))
    persisting_fps = sorted(set(a_by_fp) & set(b_by_fp))

    return SnapshotDiff(
        new=[b_by_fp[fp] for fp in new_fps],
        resolved=[a_by_fp[fp] for fp in resolved_fps],
        persisting=[b_by_fp[fp] for fp in persisting_fps],
    )
