"""Resolve the effective review mode for a feature.

Pure function. No I/O. The caller is responsible for reading the project's
.feature-workflow.yml and the feature's idea.md.

Precedence:
    1. Feature's `review:` frontmatter field (if set and recognized)
    2. Project's `reviewer:` config in .feature-workflow.yml
    3. SKIP (no review at all)
"""

import sys
from enum import Enum
from typing import Optional


class ReviewMode(Enum):
    """The concrete reviewer to invoke for this feature/phase."""

    EXTERNAL_GEMINI = "external_gemini"
    EXTERNAL_CODEX = "external_codex"
    EXTERNAL_DEFAULT = "external_default"  # feature says "external" but project hasn't picked one
    INTERNAL = "internal"
    SKIP = "skip"


_RECOGNIZED_FEATURE_VALUES = {"external", "internal", "skip"}
_RECOGNIZED_PROJECT_VALUES = {"gemini", "codex", "none", ""}


def resolve_review(feature_review: Optional[str], project_reviewer: Optional[str]) -> ReviewMode:
    """Compute the effective review mode."""
    f = (feature_review or "").strip().lower()
    p = (project_reviewer or "").strip().lower()

    # Feature override path
    if f and f in _RECOGNIZED_FEATURE_VALUES:
        if f == "internal":
            return ReviewMode.INTERNAL
        if f == "skip":
            return ReviewMode.SKIP
        if f == "external":
            # Delegate to project's choice
            if p == "gemini":
                return ReviewMode.EXTERNAL_GEMINI
            if p == "codex":
                return ReviewMode.EXTERNAL_CODEX
            # Feature requested external but project has no reviewer configured —
            # signal this to the caller; they'll need to error out usefully.
            return ReviewMode.EXTERNAL_DEFAULT

    # Unknown feature value — warn and fall through to project default
    if f and f not in _RECOGNIZED_FEATURE_VALUES:
        print(f"[effective_review] Unknown feature review value '{feature_review}', falling back to project default", file=sys.stderr)

    # Project default path
    if p == "gemini":
        return ReviewMode.EXTERNAL_GEMINI
    if p == "codex":
        return ReviewMode.EXTERNAL_CODEX

    # No reviewer at any level
    return ReviewMode.SKIP
