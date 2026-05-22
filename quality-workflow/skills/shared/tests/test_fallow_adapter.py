"""Tests for fallow_adapter — parse fallow JSON output into QualityFinding records."""

import pytest

from fallow_adapter import (
    FallowError,
    parse_health_json,
    parse_dupes_json,
    parse_dead_code_json,
)


SAMPLE_HEALTH = {
    "schema_version": 6,
    "version": "2.74.0",
    "findings": [
        {
            "path": "src/foo.ts",
            "name": "deeplyNested",
            "line": 12,
            "col": 0,
            "cyclomatic": 17,
            "cognitive": 136,
            "exceeded": "cognitive_crap",
            "severity": "critical",
            "crap": 306.0,
        },
        {
            "path": "src/bar.ts",
            "name": "simpleNest",
            "line": 5,
            "cyclomatic": 12,
            "cognitive": 18,
            "exceeded": "cyclomatic",
            "severity": "medium",
        },
    ],
    "health_score": {"score": 67.4, "grade": "C"},
}

SAMPLE_DUPES = {
    "schema_version": 1,
    "clone_groups": [
        {
            "id": "g1",
            "tokens": 80,
            "instances": [
                {"path": "src/a.ts", "start_line": 10, "end_line": 30},
                {"path": "src/b.ts", "start_line": 20, "end_line": 40},
            ],
        },
    ],
}

SAMPLE_DEAD_CODE = {
    "schema_version": 1,
    "unused_files": [{"path": "src/orphan.ts"}],
    "unused_exports": [{"path": "src/util.ts", "name": "unusedFn", "line": 22}],
    "unused_types": [{"path": "src/types.ts", "name": "Foo", "line": 5}],
    "circular_dependencies": [],
}


class TestParseHealth:
    def test_extracts_findings(self):
        findings = parse_health_json(SAMPLE_HEALTH)
        assert len(findings) == 2
        first = findings[0]
        assert first.tool == "fallow"
        assert first.category == "quality"
        assert first.rule_id == "FAL-COMPLEXITY"
        assert first.severity == "CRITICAL"  # uppercased from fallow's lowercase
        assert first.file == "src/foo.ts"
        assert first.line == 12
        assert "deeplyNested" in first.message
        assert "cyclomatic" in first.message.lower() or "cognitive" in first.message.lower()

    def test_empty(self):
        assert parse_health_json({"findings": []}) == []

    def test_fingerprints_unique(self):
        findings = parse_health_json(SAMPLE_HEALTH)
        fps = [f.fingerprint for f in findings]
        assert len(fps) == len(set(fps))


class TestParseDupes:
    def test_clone_group_to_findings(self):
        # One clone group with two instances → two findings (one per instance)
        findings = parse_dupes_json(SAMPLE_DUPES)
        assert len(findings) == 2
        assert all(f.tool == "fallow" for f in findings)
        assert all(f.category == "duplication" for f in findings)
        assert all(f.rule_id == "FAL-DUPE" for f in findings)
        assert {f.file for f in findings} == {"src/a.ts", "src/b.ts"}

    def test_clone_group_severity_inferred(self):
        findings = parse_dupes_json(SAMPLE_DUPES)
        # Duplication severity isn't given by fallow; we default
        assert findings[0].severity in {"MEDIUM", "LOW"}

    def test_empty(self):
        assert parse_dupes_json({"clone_groups": []}) == []


class TestParseDeadCode:
    def test_unused_files(self):
        findings = parse_dead_code_json(SAMPLE_DEAD_CODE)
        files = [f for f in findings if f.rule_id == "FAL-DEAD-FILE"]
        assert len(files) == 1
        assert files[0].file == "src/orphan.ts"
        assert files[0].category == "dead-code"

    def test_unused_exports(self):
        findings = parse_dead_code_json(SAMPLE_DEAD_CODE)
        exports = [f for f in findings if f.rule_id == "FAL-DEAD-EXPORT"]
        assert len(exports) == 1
        assert exports[0].file == "src/util.ts"
        assert exports[0].line == 22
        assert "unusedFn" in exports[0].message

    def test_unused_types(self):
        findings = parse_dead_code_json(SAMPLE_DEAD_CODE)
        types_ = [f for f in findings if f.rule_id == "FAL-DEAD-TYPE"]
        assert len(types_) == 1
        assert types_[0].file == "src/types.ts"

    def test_empty_arrays_skipped(self):
        findings = parse_dead_code_json(SAMPLE_DEAD_CODE)
        # circular_dependencies is empty, no findings produced
        assert not any(f.rule_id == "FAL-CIRCULAR" for f in findings)
