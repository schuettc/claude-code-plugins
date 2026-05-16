"""Data models for feature-workflow plugin."""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import date

# Handle both package and standalone imports
try:
    from .effective_review import resolve_review, ReviewMode
except ImportError:
    from effective_review import resolve_review, ReviewMode


class FeatureStatus(Enum):
    """Feature lifecycle status determined by file presence."""

    BACKLOG = "backlog"  # idea.md only
    IN_PROGRESS = "in_progress"  # idea.md + plan.md
    COMPLETED = "completed"  # idea.md + plan.md + shipped.md


class FeatureState(Enum):
    """Orthogonal state overlay on lifecycle. Source: idea.md frontmatter `state:`."""

    ACTIVE = "active"
    PAUSED = "paused"
    REPLACED = "replaced"
    ABANDONED = "abandoned"

    @classmethod
    def default(cls) -> "FeatureState":
        return cls.ACTIVE

    @classmethod
    def parse(cls, value: Optional[str]) -> "FeatureState":
        """Parse a frontmatter value into a FeatureState. Unknown values default to ACTIVE with a warning."""
        if not value:
            return cls.ACTIVE
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            print(f"[models] Unknown state value '{value}', defaulting to active", file=sys.stderr)
            return cls.ACTIVE

    def is_tombstone(self) -> bool:
        """Tombstones are excluded from active backlog views."""
        return self in (FeatureState.REPLACED, FeatureState.ABANDONED)


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
    category: str = "general"
    created: Optional[date] = None
    depends_on: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)

    # Ownership (idea.md frontmatter)
    assignees: list[str] = field(default_factory=list)

    # Grouping and relations (idea.md frontmatter)
    epic: str = ""
    children: list[str] = field(default_factory=list)
    related_to: list[str] = field(default_factory=list)
    parallel_safe: bool = True
    review: str = ""  # "external" | "internal" | "skip" | "" (defer to project)

    # State overlay (idea.md frontmatter)
    state: FeatureState = FeatureState.ACTIVE
    paused_reason: str = ""
    replaced_by: str = ""
    abandoned_reason: str = ""

    # Forward-direction replacement (idea.md frontmatter): "this feature replaces these"
    # Writing `replaces: [a, b]` triggers the hook to mark a/b as state=replaced and replaced_by=<self>.
    replaces: list[str] = field(default_factory=list)

    # From plan.md frontmatter
    started: Optional[date] = None

    # From shipped.md frontmatter
    shipped: Optional[date] = None

    def is_active(self) -> bool:
        """Active = state==ACTIVE. Used to decide active backlog membership."""
        return self.state == FeatureState.ACTIVE

    def is_tombstone(self) -> bool:
        """Tombstones (replaced/abandoned) belong in the archive."""
        return self.state.is_tombstone()

    def is_paused(self) -> bool:
        """Paused = state==PAUSED. Surfaces in the dashboard Paused section."""
        return self.state == FeatureState.PAUSED

    def is_epic(self) -> bool:
        """Epic features have type='Epic' and coordinate other features via children list."""
        return self.type.lower() == "epic"

    def effective_review(self, project_reviewer: str) -> "ReviewMode":
        """Compute the effective review mode for this feature.

        Combines the per-feature `review:` override with the project's `reviewer:`
        config to decide which review path runs.
        """
        return resolve_review(self.review, project_reviewer)

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

        # Parse assignee (handle both string and list)
        assignee_raw = idea_fm.get("assignee", [])
        if isinstance(assignee_raw, str):
            assignees = [assignee_raw] if assignee_raw else []
        elif isinstance(assignee_raw, list):
            assignees = [str(a).strip() for a in assignee_raw if str(a).strip()]
        else:
            assignees = []

        # Parse epic relations and review override
        epic = str(idea_fm.get("epic", "") or "")

        children_raw = idea_fm.get("children", [])
        if isinstance(children_raw, str):
            children = [children_raw] if children_raw else []
        elif isinstance(children_raw, list):
            children = [str(c).strip() for c in children_raw if str(c).strip()]
        else:
            children = []

        related_raw = idea_fm.get("relatedTo", [])
        if isinstance(related_raw, str):
            related_to = [related_raw] if related_raw else []
        elif isinstance(related_raw, list):
            related_to = [str(r).strip() for r in related_raw if str(r).strip()]
        else:
            related_to = []

        parallel_safe = _parse_bool(idea_fm.get("parallelSafe"), default=True)
        review = str(idea_fm.get("review", "") or "").strip().lower()

        # Parse state and companion fields
        state = FeatureState.parse(idea_fm.get("state"))
        paused_reason = str(idea_fm.get("pausedReason", "") or "")
        replaced_by = str(idea_fm.get("replacedBy", "") or "")
        abandoned_reason = str(idea_fm.get("abandonedReason", "") or "")

        # Parse forward-direction `replaces:` (this feature replaces these)
        replaces_raw = idea_fm.get("replaces", [])
        if isinstance(replaces_raw, str):
            replaces = [replaces_raw] if replaces_raw else []
        elif isinstance(replaces_raw, list):
            replaces = [str(r).strip() for r in replaces_raw if str(r).strip()]
        else:
            replaces = []

        return cls(
            feature_id=feature_dir.name,
            feature_dir=feature_dir,
            status=status,
            name=idea_fm.get("name", feature_dir.name),
            type=idea_fm.get("type", ""),
            priority=idea_fm.get("priority", ""),
            effort=idea_fm.get("effort", ""),
            impact=idea_fm.get("impact", ""),
            category=idea_fm.get("category", "general") or "general",
            created=created,
            started=started,
            shipped=shipped,
            depends_on=depends_on,
            blocked_by=blocked_by,
            assignees=assignees,
            epic=epic,
            children=children,
            related_to=related_to,
            parallel_safe=parallel_safe,
            review=review,
            state=state,
            paused_reason=paused_reason,
            replaced_by=replaced_by,
            abandoned_reason=abandoned_reason,
            replaces=replaces,
        )


def _parse_bool(value: object, default: bool) -> bool:
    """Parse a frontmatter value into a bool. Frontmatter parser returns strings, so we accept both."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "yes", "1"):
        return True
    if s in ("false", "no", "0"):
        return False
    return default


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
