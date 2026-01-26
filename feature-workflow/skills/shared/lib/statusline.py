#!/usr/bin/env python3
"""Statusline management for feature-workflow plugin.

Manages feature context for Claude Code statusline display.
Writes/clears feature ID to ~/.claude/sessions/${SESSION_ID}.feature

Usage:
    # Set context
    python3 statusline.py set <feature-id>

    # Clear context
    python3 statusline.py clear
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_sessions_dir() -> Path:
    """Get the Claude sessions directory, creating if needed."""
    sessions_dir = Path.home() / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_id() -> Optional[str]:
    """Get the current session ID from environment or iTerm mapping.

    Returns:
        Session ID string, or None if not determinable
    """
    # Primary: Check for SESSION_ID environment variable (set by hooks)
    session_id = os.environ.get("SESSION_ID")
    if session_id:
        return session_id

    # Fallback: iTerm session mapping
    iterm_session_id = os.environ.get("ITERM_SESSION_ID")
    if iterm_session_id:
        session_file = get_sessions_dir() / f"iterm-{iterm_session_id}.session"
        if session_file.exists():
            session_id = session_file.read_text().strip()
            if session_id:
                return session_id

    return None


def set_context(feature_id: str) -> bool:
    """Set the feature context for statusline display.

    Args:
        feature_id: The feature ID to set

    Returns:
        True if context was set, False if session ID not found
    """
    session_id = get_session_id()
    if not session_id:
        print("Warning: Could not determine session ID", file=sys.stderr)
        return False

    feature_file = get_sessions_dir() / f"{session_id}.feature"
    feature_file.write_text(feature_id)
    print(f"Feature context set: {feature_id}")
    return True


def clear_context() -> bool:
    """Clear the feature context from statusline display.

    Returns:
        True if context was cleared, False if no context or session ID not found
    """
    session_id = get_session_id()
    if not session_id:
        print("Warning: Could not determine session ID", file=sys.stderr)
        return False

    feature_file = get_sessions_dir() / f"{session_id}.feature"
    if feature_file.exists():
        feature_id = feature_file.read_text().strip()
        feature_file.unlink()
        print(f"Feature context cleared: {feature_id}")
        return True
    else:
        print("No feature context to clear")
        return False


def get_context() -> Optional[str]:
    """Get the current feature context.

    Returns:
        Feature ID if set, None otherwise
    """
    session_id = get_session_id()
    if not session_id:
        return None

    feature_file = get_sessions_dir() / f"{session_id}.feature"
    if feature_file.exists():
        return feature_file.read_text().strip()
    return None


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 statusline.py <set|clear|get> [feature-id]", file=sys.stderr)
        print("  set <feature-id>  - Set feature context for statusline", file=sys.stderr)
        print("  clear             - Clear feature context", file=sys.stderr)
        print("  get               - Get current feature context", file=sys.stderr)
        return 1

    command = sys.argv[1].lower()

    if command == "set":
        if len(sys.argv) < 3:
            print("Usage: python3 statusline.py set <feature-id>", file=sys.stderr)
            return 1
        feature_id = sys.argv[2]
        set_context(feature_id)
        return 0

    elif command == "clear":
        clear_context()
        return 0

    elif command == "get":
        context = get_context()
        if context:
            print(context)
        return 0

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
