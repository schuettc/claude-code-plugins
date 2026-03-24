#!/usr/bin/env python3
"""Statusline management for feature-workflow plugin.

Manages feature context for Claude Code statusline display.
Stores current feature ID at ~/.claude/feature-context.

Usage:
    python3 statusline.py set <feature-id>
    python3 statusline.py clear
    python3 statusline.py get
"""

import sys
from pathlib import Path


FEATURE_CONTEXT_FILE = Path.home() / ".claude" / "feature-context"


def set_context(feature_id: str) -> bool:
    """Set the feature context for statusline display."""
    FEATURE_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEATURE_CONTEXT_FILE.write_text(feature_id)
    print(f"Feature context set: {feature_id}")
    return True


def clear_context() -> bool:
    """Clear the feature context from statusline display."""
    if FEATURE_CONTEXT_FILE.exists():
        feature_id = FEATURE_CONTEXT_FILE.read_text().strip()
        FEATURE_CONTEXT_FILE.unlink()
        print(f"Feature context cleared: {feature_id}")
        return True
    else:
        print("No feature context to clear")
        return False


def get_context() -> str | None:
    """Get the current feature context."""
    if FEATURE_CONTEXT_FILE.exists():
        content = FEATURE_CONTEXT_FILE.read_text().strip()
        return content if content else None
    return None


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 statusline.py <set|clear|get> [feature-id]", file=sys.stderr)
        return 1

    command = sys.argv[1].lower()

    if command == "set":
        if len(sys.argv) < 3:
            print("Usage: python3 statusline.py set <feature-id>", file=sys.stderr)
            return 1
        set_context(sys.argv[2])
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
