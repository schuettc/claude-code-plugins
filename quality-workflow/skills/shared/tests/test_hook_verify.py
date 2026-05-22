"""Tests for hook_verify — uses mocks since we can't run pre-commit in CI without a fixture repo."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from hook_verify import VerifyResult, verify_hook


@pytest.fixture
def bad_fixture(tmp_path: Path) -> Path:
    p = tmp_path / "bad.py"
    p.write_text("def really_bad():\n    pass\n")
    return p


@pytest.fixture
def good_fixture(tmp_path: Path) -> Path:
    p = tmp_path / "good.py"
    p.write_text("def good():\n    pass\n")
    return p


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A directory that pretends to be a git repo for path-relative ops."""
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


class TestVerifyResult:
    def test_ok_requires_both_phases(self):
        # Both correct
        r = VerifyResult(hook_id="h", bad_passed=True, good_passed=True)
        assert r.ok

        # Bad fixture didn't trigger failure
        r = VerifyResult(hook_id="h", bad_passed=False, good_passed=True)
        assert not r.ok

        # Good fixture incorrectly fired
        r = VerifyResult(hook_id="h", bad_passed=True, good_passed=False)
        assert not r.ok

        # Verification error
        r = VerifyResult(hook_id="h", bad_passed=True, good_passed=True, error="boom")
        assert not r.ok


class TestVerifyHookWithMockedSubprocess:
    def test_hook_correctly_fails_on_bad_and_passes_on_good(
        self, bad_fixture: Path, good_fixture: Path, fake_repo: Path
    ):
        """The happy path: bad fixture → exit 1, good fixture → exit 0."""
        # Returncode pattern across the calls:
        #   git add (bad)         → 0
        #   pre-commit run (bad)  → 1   ← hook caught the violation
        #   git reset (bad)       → 0
        #   git add (good)        → 0
        #   pre-commit run (good) → 0   ← hook passed
        #   git reset (good)      → 0
        def fake_run(cmd, *args, **kwargs):
            mock = MagicMock()
            mock.stdout = ""
            mock.stderr = ""
            if cmd[0] == "pre-commit":
                # The first pre-commit invocation is for the bad fixture, second for good
                # We track call count via a closure
                mock.returncode = fake_run._calls
                fake_run._calls += 1
                return mock
            mock.returncode = 0
            return mock

        fake_run._calls = 1  # First call returns 1 (bad failed); second returns 0 (good passed... wait that's wrong)

        # Easier: track call sequence explicitly
        call_log: list[list[str]] = []

        def fake_run_v2(cmd, *args, **kwargs):
            call_log.append(cmd)
            mock = MagicMock()
            mock.stdout = "captured stdout"
            mock.stderr = ""
            if cmd[0] == "pre-commit":
                # Count which pre-commit invocation this is
                pre_commit_calls = sum(1 for c in call_log if c[0] == "pre-commit")
                mock.returncode = 1 if pre_commit_calls == 1 else 0
            else:
                mock.returncode = 0
            return mock

        with patch("hook_verify.subprocess.run", side_effect=fake_run_v2):
            result = verify_hook("skylos-agent", fake_repo, bad_fixture, good_fixture)

        assert result.ok
        assert result.bad_passed
        assert result.good_passed
        assert result.bad_exit_code == 1
        assert result.good_exit_code == 0
        # We should have run pre-commit exactly twice
        pre_commit_invocations = [c for c in call_log if c[0] == "pre-commit"]
        assert len(pre_commit_invocations) == 2
        assert all(c[1:3] == ["run", "skylos-agent"] for c in pre_commit_invocations)

    def test_hook_silently_passes_bad_fixture_caught(
        self, bad_fixture: Path, good_fixture: Path, fake_repo: Path
    ):
        """The failure case the spec was written for: hook returns 0 on bad fixture."""
        def fake_run(cmd, *args, **kwargs):
            mock = MagicMock()
            mock.stdout = ""
            mock.stderr = ""
            mock.returncode = 0  # always passes — the broken-hook scenario
            return mock

        with patch("hook_verify.subprocess.run", side_effect=fake_run):
            result = verify_hook("broken-hook", fake_repo, bad_fixture, good_fixture)

        assert not result.ok
        assert not result.bad_passed  # ← the key signal: hook should have fired but didn't
        assert result.good_passed  # good fixture passed correctly
        assert result.bad_exit_code == 0

    def test_hook_false_positive_on_good_caught(
        self, bad_fixture: Path, good_fixture: Path, fake_repo: Path
    ):
        """The reverse problem: hook fires on a good fixture."""
        def fake_run(cmd, *args, **kwargs):
            call_log.append(cmd)
            mock = MagicMock()
            mock.stdout = ""
            mock.stderr = ""
            if cmd[0] == "pre-commit":
                pre_commit_calls = sum(1 for c in call_log if c[0] == "pre-commit")
                mock.returncode = 1  # both invocations fail
            else:
                mock.returncode = 0
            return mock

        call_log: list[list[str]] = []

        with patch("hook_verify.subprocess.run", side_effect=fake_run):
            result = verify_hook("overzealous-hook", fake_repo, bad_fixture, good_fixture)

        assert not result.ok
        assert result.bad_passed  # bad fixture correctly triggered
        assert not result.good_passed  # good fixture incorrectly triggered

    def test_subprocess_timeout(
        self, bad_fixture: Path, good_fixture: Path, fake_repo: Path
    ):
        """If pre-commit hangs, we surface a clean error rather than blocking forever."""
        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "pre-commit":
                import subprocess as sp
                raise sp.TimeoutExpired(cmd, timeout=1)
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""
            mock.stderr = ""
            return mock

        with patch("hook_verify.subprocess.run", side_effect=fake_run):
            result = verify_hook("hanging-hook", fake_repo, bad_fixture, good_fixture, timeout=1)

        assert not result.ok
        assert result.error is not None
        assert "timed out" in result.error.lower()
