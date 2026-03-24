"""Tests for statusline management."""

from pathlib import Path
from unittest.mock import patch

from statusline import (
    set_context,
    clear_context,
    get_context,
    FEATURE_CONTEXT_FILE,
)


class TestSetContext:
    """Tests for set_context function."""

    def test_sets_context(self, tmp_path: Path):
        """Test setting feature context."""
        fake_file = tmp_path / "feature-context"
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            result = set_context("my-feature")
            assert result is True
            assert fake_file.read_text() == "my-feature"

    def test_overwrites_existing(self, tmp_path: Path):
        """Test overwriting existing context."""
        fake_file = tmp_path / "feature-context"
        fake_file.write_text("old-feature")
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            set_context("new-feature")
            assert fake_file.read_text() == "new-feature"


class TestClearContext:
    """Tests for clear_context function."""

    def test_clears_existing_context(self, tmp_path: Path):
        """Test clearing an existing feature context."""
        fake_file = tmp_path / "feature-context"
        fake_file.write_text("my-feature")
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            result = clear_context()
            assert result is True
            assert not fake_file.exists()

    def test_returns_false_when_no_context(self, tmp_path: Path):
        """Test clearing when no context exists."""
        fake_file = tmp_path / "feature-context"
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            result = clear_context()
            assert result is False


class TestGetContext:
    """Tests for get_context function."""

    def test_gets_existing_context(self, tmp_path: Path):
        """Test getting an existing feature context."""
        fake_file = tmp_path / "feature-context"
        fake_file.write_text("my-feature")
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            context = get_context()
            assert context == "my-feature"

    def test_returns_none_when_no_context(self, tmp_path: Path):
        """Test getting context when file doesn't exist."""
        fake_file = tmp_path / "feature-context"
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            context = get_context()
            assert context is None

    def test_returns_none_when_empty(self, tmp_path: Path):
        """Test getting context when file is empty."""
        fake_file = tmp_path / "feature-context"
        fake_file.write_text("")
        with patch("statusline.FEATURE_CONTEXT_FILE", fake_file):
            context = get_context()
            assert context is None
