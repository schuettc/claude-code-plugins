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
