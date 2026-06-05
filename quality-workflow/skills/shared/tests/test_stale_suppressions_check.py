"""Tests for stale_suppressions_check — strip logic + JSON walker.

The subprocess-running paths (check_candidates with a real skylos run) are
not unit-tested here; they're exercised by manual runs against now-playing.
The pure-Python helpers are testable.
"""

from pathlib import Path

import pytest

from stale_suppressions_check import (
    Candidate,
    StaleResult,
    issues_in_file_at_line,
    strip_suppression,
)


class TestStripSuppression:
    def test_removes_skylos_ignore(self):
        text = "x = 1  # skylos: ignore SKY-Q302\ny = 2\n"
        out = strip_suppression(text, 1)
        assert "skylos: ignore" not in out
        assert "x = 1" in out
        assert "y = 2" in out  # line 2 untouched

    def test_handles_full_line_suppression(self):
        text = "# skylos: ignore SKY-Q501\nclass Foo:\n    pass\n"
        out = strip_suppression(text, 1)
        # The suppression line becomes blank (we keep \n so line numbers don't shift)
        lines = out.splitlines(keepends=True)
        assert "skylos: ignore" not in lines[0]
        assert lines[1] == "class Foo:\n"

    def test_out_of_range_lineno_is_noop(self):
        text = "a\nb\n"
        assert strip_suppression(text, 99) == text
        assert strip_suppression(text, 0) == text

    def test_preserves_other_lines(self):
        text = "line1\nline2  # skylos: ignore SKY-Q302\nline3\n"
        out = strip_suppression(text, 2)
        # Just verify line1 and line3 are unchanged
        assert "line1" in out
        assert "line3" in out
        assert "skylos: ignore" not in out


class TestIssuesInFileAtLine:
    def test_finds_exact_match(self):
        report = {
            "issues": [
                {"location": "pi/foo.py:35", "rule": "SKY-Q302", "message": "..."},
                {"location": "pi/bar.py:10", "rule": "SKY-Q302", "message": "..."},
            ]
        }
        hits = issues_in_file_at_line(report, "pi/foo.py", 35, "SKY-Q302")
        assert len(hits) == 1
        assert "foo.py:35" in str(hits[0]["location"])

    def test_line_proximity_within_3(self):
        report = {"issues": [{"location": "pi/foo.py:37", "rule": "SKY-Q302"}]}
        # within 3 lines → match
        hits = issues_in_file_at_line(report, "pi/foo.py", 35, "SKY-Q302")
        assert len(hits) == 1
        # outside 3 lines → no match
        hits = issues_in_file_at_line(report, "pi/foo.py", 10, "SKY-Q302")
        assert hits == []

    def test_rule_mismatch_is_filtered(self):
        report = {"issues": [{"location": "pi/foo.py:35", "rule": "SKY-OTHER"}]}
        hits = issues_in_file_at_line(report, "pi/foo.py", 35, "SKY-Q302")
        assert hits == []

    def test_no_rule_matches_anything_at_location(self):
        report = {"issues": [{"location": "pi/foo.py:35", "rule": "SKY-Q302"}]}
        hits = issues_in_file_at_line(report, "pi/foo.py", 35, None)
        assert len(hits) == 1

    def test_walks_nested_structures(self):
        report = {
            "unused_functions": [
                {"file": "pi/foo.py", "line": 12, "name": "f"},
            ],
            "quality": [
                {"file": "pi/foo.py", "line": 35, "rule_id": "SKY-Q302"},
            ],
        }
        # Note: this report uses 'file' instead of 'location'. The walker
        # should pick up entries with EITHER key.
        hits = issues_in_file_at_line(report, "pi/foo.py", 35, "SKY-Q302")
        assert len(hits) >= 1
