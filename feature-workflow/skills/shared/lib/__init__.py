"""Shared library for feature-workflow plugin.

This module provides common utilities for:
- Dashboard generation from feature directories
- YAML frontmatter parsing
- Feature status models
"""

from .models import FeatureStatus, FeatureContext
from .frontmatter import parse_frontmatter
from .dashboard import generate_dashboard

__all__ = [
    "FeatureStatus",
    "FeatureContext",
    "parse_frontmatter",
    "generate_dashboard",
]
