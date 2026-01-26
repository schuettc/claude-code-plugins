"""Data models for feature-workflow plugin."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import date


class FeatureStatus(Enum):
    """Feature lifecycle status determined by file presence."""

    BACKLOG = "backlog"  # idea.md only
    IN_PROGRESS = "in_progress"  # idea.md + plan.md
    COMPLETED = "completed"  # idea.md + plan.md + shipped.md


@dataclass
class FeatureContext:
    """Context for a feature, derived from its directory and files."""

    feature_id: str
    feature_dir: Path
    status: FeatureStatus

    # From idea.md frontmatter
    name: str = ""
    type: str = ""
    priority: str = ""
    effort: str = ""
    impact: str = ""
    created: Optional[date] = None
    depends_on: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)

    # From plan.md frontmatter
    started: Optional[date] = None

    # From shipped.md frontmatter
    shipped: Optional[date] = None

    def has_unmet_dependencies(self, all_features: dict[str, "FeatureContext"]) -> list[str]:
        """Return list of dependency IDs that are not yet completed."""
        return [
            dep_id for dep_id in self.depends_on
            if all_features.get(dep_id) is None
            or all_features[dep_id].status != FeatureStatus.COMPLETED
        ]

    @classmethod
    def from_directory(cls, feature_dir: Path) -> Optional["FeatureContext"]:
        """Create FeatureContext from a feature directory.

        Returns None if the directory is not a valid feature (no idea.md).
        """
        # Handle both package and standalone imports
        try:
            from .frontmatter import parse_frontmatter
        except ImportError:
            from frontmatter import parse_frontmatter

        idea_file = feature_dir / "idea.md"
        plan_file = feature_dir / "plan.md"
        shipped_file = feature_dir / "shipped.md"

        # Not a valid feature without idea.md
        if not idea_file.exists():
            return None

        # Determine status based on file presence
        if shipped_file.exists():
            status = FeatureStatus.COMPLETED
        elif plan_file.exists():
            status = FeatureStatus.IN_PROGRESS
        else:
            status = FeatureStatus.BACKLOG

        # Parse idea.md frontmatter
        idea_fm = parse_frontmatter(idea_file)

        # Parse plan.md frontmatter if exists
        plan_fm = parse_frontmatter(plan_file) if plan_file.exists() else {}

        # Parse shipped.md frontmatter if exists
        shipped_fm = parse_frontmatter(shipped_file) if shipped_file.exists() else {}

        # Parse dates
        created = _parse_date(idea_fm.get("created"))
        started = _parse_date(plan_fm.get("started"))
        shipped = _parse_date(shipped_fm.get("shipped"))

        # Parse dependency fields (handle both string and list)
        depends_on = idea_fm.get("dependsOn", [])
        if isinstance(depends_on, str):
            depends_on = [depends_on] if depends_on else []
        blocked_by = idea_fm.get("blockedBy", [])
        if isinstance(blocked_by, str):
            blocked_by = [blocked_by] if blocked_by else []

        return cls(
            feature_id=feature_dir.name,
            feature_dir=feature_dir,
            status=status,
            name=idea_fm.get("name", feature_dir.name),
            type=idea_fm.get("type", ""),
            priority=idea_fm.get("priority", ""),
            effort=idea_fm.get("effort", ""),
            impact=idea_fm.get("impact", ""),
            created=created,
            started=started,
            shipped=shipped,
            depends_on=depends_on,
            blocked_by=blocked_by,
        )


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse a date string (YYYY-MM-DD) into a date object."""
    if not value:
        return None
    try:
        # Handle both string and date objects
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None
