"""Tests for hook_verify — uses mocks since we can't run real hooks in CI.

Covers both managers: lefthook (the default) and the pre-commit framework.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from hook_verify import VerifyResult, verify_hook, detect_manager


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
    """A directory that pretends to be a git repo, wired with lefthook (default)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "lefthook.yml").write_text("pre-commit:\n  commands: {}\n")
    return repo


# The CLI a given manager invokes for running a hook.
HOOK_CLI = {"lefthook": "lefthook", "pre-commit": "pre-commit"}


def _make_fake_run(call_log, hook_cli, bad_rc, good_rc):
    """Build a subprocess.run stand-in: hook invocations return bad_rc then
    good_rc in order; everything else (git) returns 0."""
    def fake_run(cmd, *args, **kwargs):
        call_log.append(cmd)
        mock = MagicMock()
        mock.stdout = "captured stdout"
        mock.stderr = ""
        if cmd[0] == hook_cli:
            n = sum(1 for c in call_log if c[0] == hook_cli)
            mock.returncode = bad_rc if n == 1 else good_rc
        else:
            mock.returncode = 0
        return mock
    return fake_run


class TestVerifyResult:
    def test_ok_requires_both_phases(self):
        assert VerifyResult(hook_id="h", bad_passed=True, good_passed=True).ok
        assert not VerifyResult(hook_id="h", bad_passed=False, good_passed=True).ok
        assert not VerifyResult(hook_id="h", bad_passed=True, good_passed=False).ok
        assert not VerifyResult(hook_id="h", bad_passed=True, good_passed=True, error="boom").ok


class TestDetectManager:
    def test_prefers_lefthook(self, tmp_path: Path):
        (tmp_path / "lefthook.yml").write_text("")
        (tmp_path / ".pre-commit-config.yaml").write_text("")
        assert detect_manager(tmp_path) == "lefthook"

    def test_falls_back_to_pre_commit(self, tmp_path: Path):
        (tmp_path / ".pre-commit-config.yaml").write_text("")
        assert detect_manager(tmp_path) == "pre-commit"

    def test_override_wins(self, tmp_path: Path):
        (tmp_path / "lefthook.yml").write_text("")
        assert detect_manager(tmp_path, "pre-commit") == "pre-commit"

    def test_raises_when_none(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            detect_manager(tmp_path)


class TestVerifyHookWithMockedSubprocess:
    def test_lefthook_happy_path(self, bad_fixture, good_fixture, fake_repo):
        """Default manager (lefthook): bad → non-zero, good → 0."""
        call_log: list[list[str]] = []
        with patch(
            "hook_verify.subprocess.run",
            side_effect=_make_fake_run(call_log, "lefthook", bad_rc=1, good_rc=0),
        ):
            result = verify_hook("py-scan", fake_repo, bad_fixture, good_fixture)

        assert result.ok
        assert result.manager == "lefthook"
        assert result.bad_exit_code == 1 and result.good_exit_code == 0
        hook_calls = [c for c in call_log if c[0] == "lefthook"]
        assert len(hook_calls) == 2
        assert all(c == ["lefthook", "run", "pre-commit", "--commands", "py-scan"] for c in hook_calls)

    def test_pre_commit_path(self, bad_fixture, good_fixture, tmp_path):
        """Explicit pre-commit manager still works and uses `pre-commit run <id>`."""
        repo = tmp_path / "pcrepo"
        repo.mkdir()
        (repo / ".pre-commit-config.yaml").write_text("")
        call_log: list[list[str]] = []
        with patch(
            "hook_verify.subprocess.run",
            side_effect=_make_fake_run(call_log, "pre-commit", bad_rc=1, good_rc=0),
        ):
            result = verify_hook("skylos-agent", repo, bad_fixture, good_fixture)

        assert result.ok
        assert result.manager == "pre-commit"
        hook_calls = [c for c in call_log if c[0] == "pre-commit"]
        assert len(hook_calls) == 2
        assert all(c == ["pre-commit", "run", "skylos-agent"] for c in hook_calls)

    def test_silently_passing_bad_fixture_caught(self, bad_fixture, good_fixture, fake_repo):
        """The failure case the plugin exists for: hook returns 0 on bad input."""
        call_log: list[list[str]] = []
        with patch(
            "hook_verify.subprocess.run",
            side_effect=_make_fake_run(call_log, "lefthook", bad_rc=0, good_rc=0),
        ):
            result = verify_hook("broken-hook", fake_repo, bad_fixture, good_fixture)

        assert not result.ok
        assert not result.bad_passed  # ← the key signal: should have fired, didn't
        assert result.good_passed
        assert result.bad_exit_code == 0

    def test_false_positive_on_good_caught(self, bad_fixture, good_fixture, fake_repo):
        """The reverse problem: hook fires on a good fixture."""
        call_log: list[list[str]] = []
        with patch(
            "hook_verify.subprocess.run",
            side_effect=_make_fake_run(call_log, "lefthook", bad_rc=1, good_rc=1),
        ):
            result = verify_hook("overzealous-hook", fake_repo, bad_fixture, good_fixture)

        assert not result.ok
        assert result.bad_passed
        assert not result.good_passed

    def test_subprocess_timeout(self, bad_fixture, good_fixture, fake_repo):
        """If the hook hangs, surface a clean error rather than blocking forever."""
        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "lefthook":
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

    def test_missing_manager_surfaces_error(self, bad_fixture, good_fixture, tmp_path):
        """No lefthook.yml / .pre-commit-config.yaml → clean error, not a crash."""
        repo = tmp_path / "bare"
        repo.mkdir()
        result = verify_hook("py-scan", repo, bad_fixture, good_fixture)
        assert not result.ok
        assert result.error is not None
        assert "hook manager" in result.error.lower()
