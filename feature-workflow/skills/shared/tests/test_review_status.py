"""Tests for review_status module."""

from datetime import datetime
from pathlib import Path

import pytest

from review_status import (
    VALID_PHASES,
    VALID_VERDICTS,
    compute_verdict,
    get_blocking_issues,
    get_reviews_dir,
    read_review_status,
    write_review,
    write_review_request,
    write_review_status,
)


class TestGetReviewsDir:
    """Tests for get_reviews_dir."""

    def test_creates_reviews_dir(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()
        reviews_dir = get_reviews_dir(feature_dir)
        assert reviews_dir.exists()
        assert reviews_dir == feature_dir / "reviews"

    def test_returns_existing_dir(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        reviews_dir = feature_dir / "reviews"
        reviews_dir.mkdir(parents=True)
        result = get_reviews_dir(feature_dir)
        assert result == reviews_dir

    def test_creates_nested_parents(self, tmp_path: Path):
        feature_dir = tmp_path / "docs" / "features" / "my-feature"
        reviews_dir = get_reviews_dir(feature_dir)
        assert reviews_dir.exists()


class TestReadReviewStatus:
    """Tests for read_review_status."""

    def test_returns_none_when_no_file(self, tmp_path: Path):
        result = read_review_status(tmp_path)
        assert result is None

    def test_returns_none_when_no_reviews_dir(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()
        result = read_review_status(feature_dir)
        assert result is None

    def test_parses_review_status(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        reviews_dir = feature_dir / "reviews"
        reviews_dir.mkdir(parents=True)

        status_content = """---
phase: plan
verdict: pass
updated: 2024-01-20 14:30:00
blocking-issues: 0
---

## Verdict: PASS

### Blocking Issues
(none)

### Recommendations
- Consider adding more edge case tests
"""
        (reviews_dir / "review-status.md").write_text(status_content)

        result = read_review_status(feature_dir)
        assert result is not None
        assert result["phase"] == "plan"
        assert result["verdict"] == "pass"
        assert result["blocking-issues"] == "0"

    def test_parses_fail_verdict(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        reviews_dir = feature_dir / "reviews"
        reviews_dir.mkdir(parents=True)

        status_content = """---
phase: implementation
verdict: fail
updated: 2024-01-20 14:30:00
blocking-issues: 2
---

## Verdict: FAIL
"""
        (reviews_dir / "review-status.md").write_text(status_content)

        result = read_review_status(feature_dir)
        assert result["verdict"] == "fail"
        assert result["blocking-issues"] == "2"


class TestWriteReviewStatus:
    """Tests for write_review_status."""

    def test_writes_pass_verdict(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_status(feature_dir, "plan", "pass")
        assert path.exists()
        content = path.read_text()
        assert "verdict: pass" in content
        assert "phase: plan" in content
        assert "blocking-issues: 0" in content
        assert "## Verdict: PASS" in content

    def test_writes_fail_with_blocking_issues(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_status(
            feature_dir,
            "implementation",
            "fail",
            blocking_issues=2,
            blocking_details=["Missing tests for auth flow", "SQL injection risk in query builder"],
        )
        content = path.read_text()
        assert "verdict: fail" in content
        assert "blocking-issues: 2" in content
        assert "Missing tests for auth flow" in content
        assert "SQL injection risk in query builder" in content

    def test_writes_conditional_pass_with_recommendations(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_status(
            feature_dir,
            "pre-ship",
            "conditional-pass",
            recommendations=["Add integration tests", "Update README"],
        )
        content = path.read_text()
        assert "verdict: conditional-pass" in content
        assert "Add integration tests" in content
        assert "Update README" in content

    def test_creates_reviews_dir(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        write_review_status(feature_dir, "plan", "pass")
        assert (feature_dir / "reviews").exists()

    def test_invalid_phase_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Invalid phase"):
            write_review_status(tmp_path, "invalid", "pass")

    def test_invalid_verdict_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Invalid verdict"):
            write_review_status(tmp_path, "plan", "invalid")

    def test_includes_timestamp(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_status(feature_dir, "plan", "pass")
        content = path.read_text()
        # Check that a timestamp-like string is present
        assert "updated:" in content
        # Should have current year
        assert str(datetime.now().year) in content


class TestWriteReviewRequest:
    """Tests for write_review_request."""

    def test_writes_plan_request(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_request(feature_dir, "plan")
        assert path.name == "request-plan.md"
        assert path.exists()
        content = path.read_text()
        assert "phase: plan" in content

    def test_writes_impl_request(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_request(feature_dir, "implementation")
        assert path.name == "request-impl.md"

    def test_writes_preship_request(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        path = write_review_request(feature_dir, "pre-ship")
        assert path.name == "request-preship.md"

    def test_invalid_phase_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Invalid phase"):
            write_review_request(tmp_path, "invalid")

    def test_creates_reviews_dir(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        write_review_request(feature_dir, "plan")
        assert (feature_dir / "reviews").exists()


class TestWriteReview:
    """Tests for write_review."""

    def test_writes_plan_review(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        scores = {
            "Problem-Solution Alignment": (4, "Good alignment"),
            "Step Testability": (5, "All steps verifiable"),
        }
        path = write_review(
            feature_dir,
            "plan",
            "My Feature",
            scores,
            "pass",
            4.5,
            "Overall solid plan.",
            ["Consider edge cases"],
        )
        assert path.name == "plan-review.md"
        content = path.read_text()
        assert "phase: plan" in content
        assert "criteria-version: 1.0" in content
        assert "Problem-Solution Alignment" in content
        assert "Average: 4.5" in content
        assert "Consider edge cases" in content

    def test_writes_numbered_impl_reviews(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        scores = {"Plan Adherence": (4, "Good")}

        path1 = write_review(feature_dir, "implementation", "My Feature", scores, "pass", 4.0, "First review.")
        assert path1.name == "impl-review-1.md"

        path2 = write_review(feature_dir, "implementation", "My Feature", scores, "pass", 4.0, "Second review.")
        assert path2.name == "impl-review-2.md"

    def test_writes_preship_review(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        scores = {"Shipping Readiness": (5, "Ready")}
        path = write_review(feature_dir, "pre-ship", "My Feature", scores, "pass", 5.0, "Ship it.")
        assert path.name == "pre-ship-review.md"

    def test_no_recommendations(self, tmp_path: Path):
        feature_dir = tmp_path / "my-feature"
        feature_dir.mkdir()

        scores = {"Quality": (5, "Excellent")}
        path = write_review(feature_dir, "plan", "My Feature", scores, "pass", 5.0, "Perfect.")
        content = path.read_text()
        assert "(none)" in content


class TestComputeVerdict:
    """Tests for compute_verdict."""

    def test_pass_high_scores(self):
        scores = {
            "A": (5, ""),
            "B": (4, ""),
            "C": (4, ""),
        }
        verdict, avg = compute_verdict(scores)
        assert verdict == "pass"
        assert avg == pytest.approx(4.333, abs=0.01)

    def test_pass_exactly_4(self):
        scores = {"A": (4, ""), "B": (4, "")}
        verdict, avg = compute_verdict(scores)
        assert verdict == "pass"
        assert avg == 4.0

    def test_conditional_pass(self):
        scores = {
            "A": (3, ""),
            "B": (4, ""),
            "C": (3, ""),
        }
        verdict, avg = compute_verdict(scores)
        assert verdict == "conditional-pass"
        assert avg == pytest.approx(3.333, abs=0.01)

    def test_fail_low_average(self):
        scores = {
            "A": (2, ""),
            "B": (3, ""),
            "C": (2, ""),
        }
        verdict, avg = compute_verdict(scores)
        assert verdict == "fail"
        assert avg == pytest.approx(2.333, abs=0.01)

    def test_fail_any_criterion_at_1(self):
        scores = {
            "A": (1, "Critical issue"),
            "B": (5, ""),
            "C": (5, ""),
        }
        verdict, avg = compute_verdict(scores)
        assert verdict == "fail"

    def test_conditional_pass_boundary(self):
        # Average exactly 3.0, no score below 2
        scores = {"A": (3, ""), "B": (3, "")}
        verdict, avg = compute_verdict(scores)
        assert verdict == "conditional-pass"
        assert avg == 3.0

    def test_fail_score_of_2_with_low_average(self):
        # Score of 2 is ok if average >= 3.0
        scores = {"A": (2, ""), "B": (4, "")}
        verdict, avg = compute_verdict(scores)
        assert verdict == "conditional-pass"
        assert avg == 3.0

    def test_empty_scores(self):
        verdict, avg = compute_verdict({})
        assert verdict == "pending"
        assert avg == 0.0


class TestGetBlockingIssues:
    """Tests for get_blocking_issues."""

    def test_no_blocking_issues(self):
        scores = {"A": (4, "Good"), "B": (5, "Great")}
        issues = get_blocking_issues(scores)
        assert issues == []

    def test_score_of_1_is_blocking(self):
        scores = {"A": (1, "Critical problem")}
        issues = get_blocking_issues(scores)
        assert len(issues) == 1
        assert "Critical problem" in issues[0]
        assert "scored 1/5" in issues[0]

    def test_score_of_2_is_blocking(self):
        scores = {"A": (2, "Needs work")}
        issues = get_blocking_issues(scores)
        assert len(issues) == 1
        assert "scored 2/5" in issues[0]

    def test_score_of_3_is_not_blocking(self):
        scores = {"A": (3, "Acceptable")}
        issues = get_blocking_issues(scores)
        assert issues == []

    def test_multiple_blocking_issues(self):
        scores = {
            "A": (1, "Bad"),
            "B": (5, "Good"),
            "C": (2, "Poor"),
        }
        issues = get_blocking_issues(scores)
        assert len(issues) == 2


class TestValidConstants:
    """Tests for module constants."""

    def test_valid_phases(self):
        assert "plan" in VALID_PHASES
        assert "implementation" in VALID_PHASES
        assert "pre-ship" in VALID_PHASES

    def test_valid_verdicts(self):
        assert "pass" in VALID_VERDICTS
        assert "conditional-pass" in VALID_VERDICTS
        assert "fail" in VALID_VERDICTS
        assert "pending" in VALID_VERDICTS
