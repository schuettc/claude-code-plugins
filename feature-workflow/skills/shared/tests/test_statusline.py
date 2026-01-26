"""Tests for statusline management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from statusline import (
    get_sessions_dir,
    get_session_id,
    set_context,
    clear_context,
    get_context,
)


class TestGetSessionsDir:
    """Tests for get_sessions_dir function."""

    def test_creates_directory(self, tmp_path: Path):
        """Test that sessions directory is created if it doesn't exist."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            sessions_dir = get_sessions_dir()
            assert sessions_dir.exists()
            assert sessions_dir == tmp_path / ".claude" / "sessions"


class TestGetSessionId:
    """Tests for get_session_id function."""

    def test_from_session_id_env(self):
        """Test getting session ID from SESSION_ID environment variable."""
        with patch.dict(os.environ, {"SESSION_ID": "test-session-123"}, clear=False):
            session_id = get_session_id()
            assert session_id == "test-session-123"

    def test_from_iterm_mapping(self, tmp_path: Path):
        """Test getting session ID from iTerm session mapping."""
        # Set up environment and session file
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_file = sessions_dir / "iterm-abc123.session"
        session_file.write_text("mapped-session-456")

        with patch.dict(
            os.environ,
            {"HOME": str(tmp_path), "ITERM_SESSION_ID": "abc123"},
            clear=True,
        ):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                session_id = get_session_id()
                assert session_id == "mapped-session-456"

    def test_returns_none_when_no_session(self):
        """Test that None is returned when no session ID can be determined."""
        with patch.dict(os.environ, {}, clear=True):
            session_id = get_session_id()
            assert session_id is None


class TestSetContext:
    """Tests for set_context function."""

    def test_sets_context_with_session_id(self, tmp_path: Path):
        """Test setting context when SESSION_ID is available."""
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"SESSION_ID": "test-session"}, clear=False):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                result = set_context("my-feature")
                assert result is True

                feature_file = sessions_dir / "test-session.feature"
                assert feature_file.exists()
                assert feature_file.read_text() == "my-feature"

    def test_returns_false_when_no_session(self):
        """Test that False is returned when no session ID."""
        with patch.dict(os.environ, {}, clear=True):
            result = set_context("my-feature")
            assert result is False


class TestClearContext:
    """Tests for clear_context function."""

    def test_clears_existing_context(self, tmp_path: Path):
        """Test clearing an existing feature context."""
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)
        feature_file = sessions_dir / "test-session.feature"
        feature_file.write_text("my-feature")

        with patch.dict(os.environ, {"SESSION_ID": "test-session"}, clear=False):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                result = clear_context()
                assert result is True
                assert not feature_file.exists()

    def test_returns_false_when_no_context(self, tmp_path: Path):
        """Test clearing when no context exists."""
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"SESSION_ID": "test-session"}, clear=False):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                result = clear_context()
                assert result is False


class TestGetContext:
    """Tests for get_context function."""

    def test_gets_existing_context(self, tmp_path: Path):
        """Test getting an existing feature context."""
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)
        feature_file = sessions_dir / "test-session.feature"
        feature_file.write_text("my-feature")

        with patch.dict(os.environ, {"SESSION_ID": "test-session"}, clear=False):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                context = get_context()
                assert context == "my-feature"

    def test_returns_none_when_no_context(self, tmp_path: Path):
        """Test getting context when none exists."""
        sessions_dir = tmp_path / ".claude" / "sessions"
        sessions_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"SESSION_ID": "test-session"}, clear=False):
            with patch("statusline.get_sessions_dir", return_value=sessions_dir):
                context = get_context()
                assert context is None

    def test_returns_none_when_no_session(self):
        """Test getting context when no session ID."""
        with patch.dict(os.environ, {}, clear=True):
            context = get_context()
            assert context is None
