"""Tests for skylos_adapter — parse skylos JSON output into QualityFinding records."""

import json
from pathlib import Path

import pytest

from skylos_adapter import (
    SkylosError,
    parse_skylos_json,
    strip_banner,
)


# Fixture data: a minimal but realistic skylos output. Each top-level array
# represents one finding shape we need to support.
SAMPLE_SKYLOS_JSON = {
    "quality": [
        {
            "rule_id": "SKY-Q301",
            "kind": "complexity",
            "severity": "HIGH",
            "type": "function",
            "name": "_is_fresh_side_first_track",
            "value": 17,
            "threshold": 10,
            "message": "Cyclomatic complexity is 17 (threshold: 10).",
            "file": "/abs/path/pi/foo.py",
            "basename": "foo.py",
            "line": 35,
        },
        {
            "rule_id": "SKY-Q302",
            "kind": "nesting",
            "severity": "MEDIUM",
            "type": "function",
            "name": "process_record",
            "message": "Nesting depth exceeds threshold.",
            "file": "/abs/path/pi/bar.py",
            "line": 100,
        },
    ],
    "danger": [
        {
            "rule_id": "SKY-D324",
            "severity": "HIGH",
            "message": "Possible symlink-following write on attacker-controlled path.",
            "file": "/abs/path/pi/cache.py",
            "line": 96,
            "symbol": "_write_art",
        },
    ],
    "unused_functions": [
        {
            "name": "_orphan_helper",
            "simple_name": "_orphan_helper",
            "file": "/abs/path/pi/dead.py",
            "line": 12,
            "confidence": 95,
            "dead_code_classification": "likely_dead",
            "category": "unused_functions",
        },
    ],
    "secrets": [],  # empty arrays should not contribute findings
    "grade": {"overall": {"score": 87, "letter": "B+"}},
    "analysis_summary": {"total_files": 130},
}


class TestStripBanner:
    def test_no_banner(self):
        text = '{"key": "value"}'
        assert strip_banner(text) == text

    def test_banner_before_json(self):
        text = "skylos 4.18.0\nAnalyzing pi/\n{\"key\": \"value\"}"
        assert strip_banner(text) == '{"key": "value"}'

    def test_no_open_brace(self):
        with pytest.raises(SkylosError):
            strip_banner("no json here")


class TestParseSkylosJson:
    def test_empty_payload(self):
        findings = parse_skylos_json({})
        assert findings == []

    def test_quality_finding_shape(self):
        findings = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        quality = [f for f in findings if f.tool == "skylos" and f.rule_id == "SKY-Q301"]
        assert len(quality) == 1
        f = quality[0]
        assert f.category == "quality"
        assert f.severity == "HIGH"
        assert f.line == 35
        assert "Cyclomatic complexity" in f.message
        # Absolute paths should be unchanged at parse time; normalization is the caller's job
        assert f.file.endswith("foo.py")

    def test_danger_finding_shape(self):
        findings = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        danger = [f for f in findings if f.rule_id == "SKY-D324"]
        assert len(danger) == 1
        assert danger[0].category == "security"
        assert danger[0].severity == "HIGH"

    def test_unused_function_synthetic_rule_id(self):
        findings = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        dead = [f for f in findings if f.category == "dead-code"]
        assert len(dead) == 1
        # No native rule_id from skylos for unused_*; we synthesize one
        assert dead[0].rule_id.startswith("SKY-DEAD")
        assert dead[0].file.endswith("dead.py")
        # Skylos reports confidence as 0-100; QualityFinding normalizes to 0.0-1.0
        assert dead[0].confidence == 0.95

    def test_empty_arrays_skipped(self):
        # `secrets: []` should not produce a finding
        findings = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        assert not any(f.category == "secrets" for f in findings)

    def test_fingerprints_are_stable_and_unique(self):
        # Re-parse the same payload; fingerprints should match across runs
        a = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        b = parse_skylos_json(SAMPLE_SKYLOS_JSON)
        assert [f.fingerprint for f in a] == [f.fingerprint for f in b]
        # And distinct findings have distinct fingerprints
        fps = [f.fingerprint for f in a]
        assert len(fps) == len(set(fps))

    def test_fingerprint_includes_rule_file_line(self):
        """Two findings with the same rule_id but different files must have different fingerprints."""
        payload = {
            "quality": [
                {"rule_id": "SKY-Q301", "severity": "HIGH", "message": "complexity", "file": "/a/x.py", "line": 10},
                {"rule_id": "SKY-Q301", "severity": "HIGH", "message": "complexity", "file": "/b/x.py", "line": 10},
            ],
        }
        findings = parse_skylos_json(payload)
        assert len(findings) == 2
        assert findings[0].fingerprint != findings[1].fingerprint


class TestSuppressionDetection:
    """Skylos reports suppressed findings in its JSON with a `reason` field.

    Discovered 2026-05-22 dogfooding now-playing: of 180 raw findings, 54 were
    already suppressed at the source (`# skylos: ignore — <rationale>`); only
    126 were genuinely active. Before this fix, the adapter counted all 180 as
    active, inflating snapshots and triggering false alarms.
    """

    def test_inline_ignore_marks_suppressed(self):
        payload = {
            "quality": [
                {
                    "rule_id": "SKY-D211",
                    "severity": "CRITICAL",
                    "message": "Possible SQL injection",
                    "file": "/abs/path/pi/queries.py",
                    "line": 75,
                    "reason": "inline ignore comment",
                },
            ],
        }
        findings = parse_skylos_json(payload)
        assert len(findings) == 1
        assert findings[0].suppressed is True
        assert findings[0].suppression_reason == "inline ignore comment"

    def test_no_reason_means_active(self):
        # Same payload, no `reason` → active finding
        payload = {
            "quality": [
                {
                    "rule_id": "SKY-D211",
                    "severity": "CRITICAL",
                    "message": "Possible SQL injection",
                    "file": "/abs/path/pi/queries.py",
                    "line": 75,
                },
            ],
        }
        findings = parse_skylos_json(payload)
        assert len(findings) == 1
        assert findings[0].suppressed is False
        assert findings[0].suppression_reason is None

    def test_empty_reason_treated_as_active(self):
        # Defensive: empty-string reason isn't a suppression
        payload = {
            "quality": [
                {
                    "rule_id": "SKY-D211",
                    "severity": "CRITICAL",
                    "message": "Possible SQL injection",
                    "file": "/abs/path/pi/queries.py",
                    "line": 75,
                    "reason": "",
                },
            ],
        }
        findings = parse_skylos_json(payload)
        assert findings[0].suppressed is False
        assert findings[0].suppression_reason is None

    def test_mixed_active_and_suppressed(self):
        # Two findings of the same rule_id, one suppressed, one not — fingerprints
        # share the rule/file/line key, so they collide on identity; pick the
        # active one as canonical. (This shape comes from skylos when a suppression
        # comment covers one occurrence but not another at the same line; in
        # practice they differ in `symbol` so fingerprints diverge.)
        payload = {
            "danger": [
                {
                    "rule_id": "SKY-D324",
                    "severity": "HIGH",
                    "message": "symlink follow",
                    "file": "/a/x.py",
                    "line": 50,
                    "symbol": "_write_one",
                    "reason": "inline ignore comment",
                },
                {
                    "rule_id": "SKY-D324",
                    "severity": "HIGH",
                    "message": "symlink follow",
                    "file": "/a/x.py",
                    "line": 60,
                    "symbol": "_write_two",
                },
            ],
        }
        findings = parse_skylos_json(payload)
        assert len(findings) == 2
        by_symbol = {f.message: f for f in findings}
        suppressed = [f for f in findings if f.suppressed]
        active = [f for f in findings if not f.suppressed]
        assert len(suppressed) == 1
        assert len(active) == 1
        assert suppressed[0].line == 50
        assert active[0].line == 60
