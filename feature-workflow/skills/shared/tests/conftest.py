"""Pytest fixtures for feature-workflow shared library tests."""

import sys
from pathlib import Path

import pytest

# Add the lib directory to Python path for imports
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with docs/features structure."""
    features_dir = tmp_path / "docs" / "features"
    features_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def feature_in_backlog(temp_project: Path) -> Path:
    """Create a feature with only idea.md (backlog status)."""
    feature_dir = temp_project / "docs" / "features" / "test-feature"
    feature_dir.mkdir()

    idea_content = """---
id: test-feature
name: Test Feature
type: Feature
priority: P1
effort: Medium
impact: High
created: 2024-01-15
---

# Test Feature

## Problem Statement
This is a test feature for unit testing.
"""
    (feature_dir / "idea.md").write_text(idea_content)
    return feature_dir


@pytest.fixture
def feature_in_progress(feature_in_backlog: Path) -> Path:
    """Create a feature with idea.md and plan.md (in-progress status)."""
    plan_content = """---
started: 2024-01-20
---

# Implementation Plan: Test Feature

## Overview
Implementation plan for test feature.

## Implementation Steps
- [ ] Step 1
- [ ] Step 2
"""
    (feature_in_backlog / "plan.md").write_text(plan_content)
    return feature_in_backlog


@pytest.fixture
def feature_completed(feature_in_progress: Path) -> Path:
    """Create a feature with idea.md, plan.md, and shipped.md (completed status)."""
    shipped_content = """---
shipped: 2024-01-25
---

# Shipped: Test Feature

## Summary
Feature completed and delivered.
"""
    (feature_in_progress / "shipped.md").write_text(shipped_content)
    return feature_in_progress


@pytest.fixture
def multiple_features(temp_project: Path) -> Path:
    """Create multiple features in different states."""
    features_dir = temp_project / "docs" / "features"

    # Backlog feature
    backlog_dir = features_dir / "backlog-feature"
    backlog_dir.mkdir()
    (backlog_dir / "idea.md").write_text("""---
id: backlog-feature
name: Backlog Feature
type: Enhancement
priority: P2
effort: Small
impact: Medium
created: 2024-01-10
---

# Backlog Feature
A feature in backlog.
""")

    # In-progress feature
    progress_dir = features_dir / "progress-feature"
    progress_dir.mkdir()
    (progress_dir / "idea.md").write_text("""---
id: progress-feature
name: Progress Feature
type: Feature
priority: P0
effort: Large
impact: High
created: 2024-01-05
---

# Progress Feature
A feature in progress.
""")
    (progress_dir / "plan.md").write_text("""---
started: 2024-01-12
---

# Plan
Implementation plan.
""")

    # Completed feature
    done_dir = features_dir / "done-feature"
    done_dir.mkdir()
    (done_dir / "idea.md").write_text("""---
id: done-feature
name: Done Feature
type: Bug Fix
priority: P1
effort: Small
impact: High
created: 2024-01-01
---

# Done Feature
A completed feature.
""")
    (done_dir / "plan.md").write_text("""---
started: 2024-01-02
---

# Plan
Implementation plan.
""")
    (done_dir / "shipped.md").write_text("""---
shipped: 2024-01-08
---

# Shipped
Feature shipped.
""")

    return temp_project
