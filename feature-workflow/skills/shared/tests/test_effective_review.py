"""Tests for effective_review resolution."""

import sys
from pathlib import Path

# Path setup
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import pytest
from effective_review import resolve_review, ReviewMode


class TestResolveReview:
    """Per-feature override beats project default; if both absent, return SKIP."""

    def test_feature_external_wins(self):
        assert resolve_review(feature_review="external", project_reviewer="none") == ReviewMode.EXTERNAL_DEFAULT
        # With project reviewer=none and feature override=external, we still
        # try external — though it has no concrete reviewer to dispatch to,
        # so the caller surfaces a usage error. The mode is EXTERNAL.

    def test_feature_internal_wins(self):
        assert resolve_review(feature_review="internal", project_reviewer="gemini") == ReviewMode.INTERNAL

    def test_feature_skip_wins(self):
        assert resolve_review(feature_review="skip", project_reviewer="gemini") == ReviewMode.SKIP

    def test_empty_feature_falls_back_to_project_gemini(self):
        assert resolve_review(feature_review="", project_reviewer="gemini") == ReviewMode.EXTERNAL_GEMINI

    def test_empty_feature_falls_back_to_project_codex(self):
        assert resolve_review(feature_review="", project_reviewer="codex") == ReviewMode.EXTERNAL_CODEX

    def test_both_absent_means_skip(self):
        assert resolve_review(feature_review="", project_reviewer="none") == ReviewMode.SKIP
        assert resolve_review(feature_review="", project_reviewer="") == ReviewMode.SKIP

    def test_unknown_feature_value_falls_back_with_warning(self, capsys):
        result = resolve_review(feature_review="garbled", project_reviewer="gemini")
        assert result == ReviewMode.EXTERNAL_GEMINI
        captured = capsys.readouterr()
        assert "garbled" in captured.err

    def test_external_mode_value(self):
        """The EXTERNAL_DEFAULT mode encodes 'use whatever project says (or refuse if project=none)'."""
        # Just verify the enum has the values we depend on:
        assert ReviewMode.INTERNAL.value == "internal"
        assert ReviewMode.SKIP.value == "skip"
        assert ReviewMode.EXTERNAL_GEMINI.value == "external_gemini"
        assert ReviewMode.EXTERNAL_CODEX.value == "external_codex"
        assert ReviewMode.EXTERNAL_DEFAULT.value == "external_default"
