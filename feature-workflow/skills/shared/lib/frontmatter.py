"""YAML frontmatter parsing utilities."""

from pathlib import Path
from typing import Any


def parse_frontmatter(file_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown file.

    Extracts content between the first pair of '---' markers.

    Args:
        file_path: Path to the markdown file

    Returns:
        Dictionary of frontmatter key-value pairs, or empty dict if no frontmatter
    """
    if not file_path.exists():
        return {}

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    return parse_frontmatter_string(content)


def parse_frontmatter_string(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a string.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Dictionary of frontmatter key-value pairs
    """
    lines = content.split("\n")
    result: dict[str, Any] = {}

    in_frontmatter = False
    frontmatter_lines: list[str] = []

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                # End of frontmatter
                break

        if in_frontmatter:
            frontmatter_lines.append(line)

    # Parse simple YAML key: value pairs
    for line in frontmatter_lines:
        if ":" not in line:
            continue

        # Split on first colon only
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Skip empty keys
        if not key:
            continue

        # Handle quoted strings
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        # Handle YAML array syntax [item1, item2]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner:
                result[key] = [item.strip().strip("'\"") for item in inner.split(",")]
            else:
                result[key] = []
            continue

        result[key] = value

    return result
