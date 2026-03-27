"""Review status management for feature-workflow plugin.

Read/write/parse review-status.md and review request/result files.
Used by both the implementer (to read verdicts and write requests)
and the reviewer (to write verdicts and reviews).
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Handle both package and standalone imports
try:
    from .frontmatter import parse_frontmatter, parse_frontmatter_string
except ImportError:
    from frontmatter import parse_frontmatter, parse_frontmatter_string


VALID_PHASES = ("plan", "implementation", "pre-ship")
VALID_VERDICTS = ("pass", "conditional-pass", "fail", "pending")


def get_reviews_dir(feature_dir: Path) -> Path:
    """Get the reviews directory for a feature, creating it if needed."""
    reviews_dir = feature_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    return reviews_dir


def read_review_status(feature_dir: Path) -> Optional[dict[str, Any]]:
    """Read and parse review-status.md for a feature.

    Returns:
        Dictionary with frontmatter fields (phase, verdict, updated,
        blocking-issues) or None if file doesn't exist.
    """
    status_file = feature_dir / "reviews" / "review-status.md"
    if not status_file.exists():
        return None

    return parse_frontmatter(status_file)


def write_review_status(
    feature_dir: Path,
    phase: str,
    verdict: str,
    blocking_issues: int = 0,
    recommendations: Optional[list[str]] = None,
    blocking_details: Optional[list[str]] = None,
) -> Path:
    """Write review-status.md for a feature.

    Args:
        feature_dir: Path to the feature directory
        phase: Review phase (plan, implementation, pre-ship)
        verdict: Review verdict (pass, conditional-pass, fail, pending)
        blocking_issues: Number of blocking issues
        recommendations: List of non-blocking recommendation strings
        blocking_details: List of blocking issue descriptions

    Returns:
        Path to the written review-status.md file
    """
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"Invalid verdict: {verdict}. Must be one of {VALID_VERDICTS}")

    reviews_dir = get_reviews_dir(feature_dir)
    status_file = reviews_dir / "review-status.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "---",
        f"phase: {phase}",
        f"verdict: {verdict}",
        f"updated: {timestamp}",
        f"blocking-issues: {blocking_issues}",
        "---",
        "",
        f"## Verdict: {verdict.upper()}",
        "",
        "### Blocking Issues",
    ]

    if blocking_details:
        for issue in blocking_details:
            lines.append(f"- {issue}")
    else:
        lines.append("(none)")

    lines.append("")
    lines.append("### Recommendations")

    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("(none)")

    lines.append("")

    status_file.write_text("\n".join(lines), encoding="utf-8")
    return status_file


def write_review_request(feature_dir: Path, phase: str) -> Path:
    """Write a review request file to signal the reviewer.

    Args:
        feature_dir: Path to the feature directory
        phase: Review phase being requested (plan, implementation, pre-ship)

    Returns:
        Path to the written request file
    """
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")

    reviews_dir = get_reviews_dir(feature_dir)

    phase_key = phase.replace("-", "")  # pre-ship -> preship
    if phase == "plan":
        request_file = reviews_dir / "request-plan.md"
    elif phase == "implementation":
        request_file = reviews_dir / "request-impl.md"
    else:
        request_file = reviews_dir / "request-preship.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""---
phase: {phase}
requested: {timestamp}
---

# Review Requested: {phase.title()}

External review requested for the **{phase}** phase.
"""

    request_file.write_text(content, encoding="utf-8")
    return request_file


def write_review(
    feature_dir: Path,
    phase: str,
    feature_name: str,
    scores: dict[str, tuple[int, str]],
    verdict: str,
    average: float,
    detailed_findings: str,
    recommendations: Optional[list[str]] = None,
) -> Path:
    """Write a review file with scores and findings.

    Args:
        feature_dir: Path to the feature directory
        phase: Review phase (plan, implementation, pre-ship)
        feature_name: Human-readable feature name
        scores: Dict of criterion -> (score, notes) tuples
        verdict: Overall verdict string
        average: Average score
        detailed_findings: Markdown text with detailed findings
        recommendations: List of recommendation strings

    Returns:
        Path to the written review file
    """
    reviews_dir = get_reviews_dir(feature_dir)

    # Determine filename based on phase
    if phase == "plan":
        review_file = reviews_dir / "plan-review.md"
    elif phase == "pre-ship":
        review_file = reviews_dir / "pre-ship-review.md"
    else:
        # Implementation reviews are numbered
        existing = list(reviews_dir.glob("impl-review-*.md"))
        next_num = len(existing) + 1
        review_file = reviews_dir / f"impl-review-{next_num}.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "---",
        f"phase: {phase}",
        f"reviewer-session: {timestamp}",
        "criteria-version: 1.0",
        "---",
        "",
        f"# {phase.title()} Review: {feature_name}",
        "",
        "## Scores",
        "",
        "| Criterion | Score (1-5) | Notes |",
        "|-----------|-------------|-------|",
    ]

    for criterion, (score, notes) in scores.items():
        lines.append(f"| {criterion} | {score} | {notes} |")

    lines.append("")
    lines.append(f"## Average: {average:.1f} | Verdict: {verdict.upper()}")
    lines.append("")
    lines.append("## Detailed Findings")
    lines.append("")
    lines.append(detailed_findings)
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")

    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("(none)")

    lines.append("")

    review_file.write_text("\n".join(lines), encoding="utf-8")
    return review_file


def compute_verdict(scores: dict[str, tuple[int, str]]) -> tuple[str, float]:
    """Compute verdict from scores using rubric rules.

    Rules:
        - Average >= 4.0: PASS
        - Average >= 3.0, no criterion below 2: CONDITIONAL PASS
        - Any criterion at 1, or average < 3.0: FAIL

    Args:
        scores: Dict of criterion -> (score, notes) tuples

    Returns:
        Tuple of (verdict string, average score)
    """
    if not scores:
        return ("pending", 0.0)

    values = [score for score, _ in scores.values()]
    average = sum(values) / len(values)

    if any(v == 1 for v in values) or average < 3.0:
        return ("fail", average)
    elif average >= 4.0:
        return ("pass", average)
    else:
        return ("conditional-pass", average)


def get_blocking_issues(scores: dict[str, tuple[int, str]]) -> list[str]:
    """Extract blocking issues from scores (criteria scored 1 or 2).

    Args:
        scores: Dict of criterion -> (score, notes) tuples

    Returns:
        List of blocking issue descriptions
    """
    issues = []
    for criterion, (score, notes) in scores.items():
        if score <= 2:
            issues.append(f"{criterion} (scored {score}/5): {notes}")
    return issues
