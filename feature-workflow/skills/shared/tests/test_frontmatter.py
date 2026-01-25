"""Tests for frontmatter parsing utilities."""

from pathlib import Path

import pytest

from frontmatter import parse_frontmatter, parse_frontmatter_string


class TestParseFrontmatterString:
    """Tests for parse_frontmatter_string function."""

    def test_basic_frontmatter(self):
        """Test parsing basic YAML frontmatter."""
        content = """---
name: Test Feature
priority: P1
effort: Medium
---

# Content here
"""
        result = parse_frontmatter_string(content)
        assert result["name"] == "Test Feature"
        assert result["priority"] == "P1"
        assert result["effort"] == "Medium"

    def test_empty_content(self):
        """Test parsing empty content."""
        result = parse_frontmatter_string("")
        assert result == {}

    def test_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = """# Just a heading

Some content without frontmatter.
"""
        result = parse_frontmatter_string(content)
        assert result == {}

    def test_single_delimiter(self):
        """Test content with only opening delimiter."""
        content = """---
name: Test
"""
        # Should not parse - needs closing delimiter
        result = parse_frontmatter_string(content)
        assert result == {}

    def test_quoted_values(self):
        """Test parsing quoted string values."""
        content = """---
name: "Quoted Value"
other: 'Single Quoted'
---
"""
        result = parse_frontmatter_string(content)
        assert result["name"] == "Quoted Value"
        assert result["other"] == "Single Quoted"

    def test_date_values(self):
        """Test parsing date values."""
        content = """---
created: 2024-01-15
started: 2024-01-20
---
"""
        result = parse_frontmatter_string(content)
        assert result["created"] == "2024-01-15"
        assert result["started"] == "2024-01-20"

    def test_colon_in_value(self):
        """Test values containing colons."""
        content = """---
time: 12:30:00
url: https://example.com
---
"""
        result = parse_frontmatter_string(content)
        assert result["time"] == "12:30:00"
        assert result["url"] == "https://example.com"

    def test_empty_values(self):
        """Test keys with empty values."""
        content = """---
name: Test
empty:
another: value
---
"""
        result = parse_frontmatter_string(content)
        assert result["name"] == "Test"
        assert result["empty"] == ""
        assert result["another"] == "value"


class TestParseFrontmatter:
    """Tests for parse_frontmatter function (file-based)."""

    def test_nonexistent_file(self, tmp_path: Path):
        """Test parsing from nonexistent file."""
        result = parse_frontmatter(tmp_path / "nonexistent.md")
        assert result == {}

    def test_file_with_frontmatter(self, tmp_path: Path):
        """Test parsing from file with frontmatter."""
        file_path = tmp_path / "test.md"
        file_path.write_text("""---
name: Test
priority: P0
---

# Content
""")
        result = parse_frontmatter(file_path)
        assert result["name"] == "Test"
        assert result["priority"] == "P0"

    def test_file_without_frontmatter(self, tmp_path: Path):
        """Test parsing from file without frontmatter."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Just content\n\nNo frontmatter here.")
        result = parse_frontmatter(file_path)
        assert result == {}
