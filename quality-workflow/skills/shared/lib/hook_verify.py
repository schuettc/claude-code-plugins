"""Self-verification for git hooks — manager-agnostic.

The "hook silence ≠ hook working" lesson, codified. Given a hook ID, this
module copies a known-bad fixture into a temp staged location, runs the
project's hook (via whichever manager is wired — lefthook or the pre-commit
framework), and asserts a non-zero exit. Then a known-good fixture, asserts
exit 0. Always reverts the working tree.

A hook that doesn't fail on the bad fixture isn't a hook — it's a placebo.

Manager detection (override with `manager=`):
  lefthook.yml / lefthook.yaml present → "lefthook"  →  `lefthook run pre-commit --commands <id>`
  .pre-commit-config.yaml present      → "pre-commit" →  `pre-commit run <id>`
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VerifyResult:
    """Outcome of a hook verification round."""

    hook_id: str
    bad_passed: bool  # True if the bad fixture correctly triggered a non-zero exit
    good_passed: bool  # True if the good fixture correctly triggered exit 0
    manager: str = ""  # which hook manager was used ("lefthook" / "pre-commit")
    bad_stdout: str = ""
    bad_stderr: str = ""
    good_stdout: str = ""
    good_stderr: str = ""
    bad_exit_code: int = 0
    good_exit_code: int = 0
    error: Optional[str] = None  # non-empty if the verification itself failed

    @property
    def ok(self) -> bool:
        """True iff both phases behaved as expected."""
        return self.bad_passed and self.good_passed and self.error is None


def detect_manager(project_root: Path, override: Optional[str] = None) -> str:
    """Resolve which git-hook manager the project uses.

    Explicit `override` wins. Otherwise lefthook is preferred (the current
    standard), then the pre-commit framework. Raises FileNotFoundError if
    neither is configured.
    """
    if override:
        return override
    if (project_root / "lefthook.yml").exists() or (project_root / "lefthook.yaml").exists():
        return "lefthook"
    if (project_root / ".pre-commit-config.yaml").exists():
        return "pre-commit"
    raise FileNotFoundError(
        "no hook manager found (looked for lefthook.yml / .pre-commit-config.yaml)"
    )


def verify_hook(
    hook_id: str,
    project_root: Path,
    bad_fixture: Path,
    good_fixture: Path,
    *,
    manager: Optional[str] = None,
    staged_target: Optional[Path] = None,
    timeout: int = 60,
) -> VerifyResult:
    """Verify that `hook_id` fails on bad_fixture and passes on good_fixture.

    Args:
        hook_id: the hook/command ID to run. For lefthook this is the command
            name under `pre-commit:` (e.g. "py-scan", "ts-scan"); for the
            pre-commit framework it's the hook ID (e.g. "skylos-agent").
        project_root: the repo where the hooks are installed
        bad_fixture: path to a file with a deliberate violation
        good_fixture: path to a file with no violations
        manager: force "lefthook" or "pre-commit"; auto-detected if None
        staged_target: optional path inside project_root where the fixture
            should be staged (defaults to `<project_root>/.quality-workflow-verify/<basename>`)
        timeout: per-phase subprocess timeout

    Returns:
        VerifyResult. Caller checks `result.ok` for the overall outcome.
    """
    if staged_target is None:
        staged_target = project_root / ".quality-workflow-verify" / bad_fixture.name

    result = VerifyResult(hook_id=hook_id, bad_passed=False, good_passed=False)

    try:
        resolved_manager = detect_manager(project_root, manager)
        result.manager = resolved_manager

        # Phase 1: bad fixture should make the hook fail
        staged_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bad_fixture, staged_target)
        _stage(staged_target, project_root)
        bad_run = _run_hook(hook_id, project_root, manager=resolved_manager, timeout=timeout)
        result.bad_exit_code = bad_run.returncode
        result.bad_stdout = bad_run.stdout
        result.bad_stderr = bad_run.stderr
        result.bad_passed = bad_run.returncode != 0  # any non-zero = caught the violation
        _unstage_and_remove(staged_target, project_root)

        # Phase 2: good fixture should make the hook pass
        good_target = staged_target.parent / good_fixture.name
        shutil.copy2(good_fixture, good_target)
        _stage(good_target, project_root)
        good_run = _run_hook(hook_id, project_root, manager=resolved_manager, timeout=timeout)
        result.good_exit_code = good_run.returncode
        result.good_stdout = good_run.stdout
        result.good_stderr = good_run.stderr
        result.good_passed = good_run.returncode == 0
        _unstage_and_remove(good_target, project_root)

        # Clean up the staged dir if empty
        try:
            staged_target.parent.rmdir()
        except OSError:
            pass

    except subprocess.TimeoutExpired:
        result.error = f"hook {hook_id} timed out after {timeout}s"
    except FileNotFoundError as e:
        result.error = f"required tool missing: {e}"
    except Exception as e:  # noqa: BLE001 — surface anything else to the caller
        result.error = f"verification error: {e}"

    return result


def _stage(path: Path, project_root: Path) -> None:
    """git add <path> relative to project_root."""
    subprocess.run(
        ["git", "add", "--", str(path.relative_to(project_root))],
        cwd=project_root,
        check=False,
        capture_output=True,
    )


def _unstage_and_remove(path: Path, project_root: Path) -> None:
    """Unstage and delete the file. Best-effort; safe if file already gone."""
    try:
        subprocess.run(
            ["git", "reset", "HEAD", "--", str(path.relative_to(project_root))],
            cwd=project_root,
            check=False,
            capture_output=True,
        )
    except Exception:
        pass
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _run_hook(
    hook_id: str, project_root: Path, *, manager: str, timeout: int
) -> subprocess.CompletedProcess:
    """Run the project's hook against the currently-staged files.

    lefthook:   `lefthook run pre-commit --commands <hook_id>`
    pre-commit: `pre-commit run <hook_id>`
    """
    if manager == "lefthook":
        cmd = ["lefthook", "run", "pre-commit", "--commands", hook_id]
    elif manager == "pre-commit":
        cmd = ["pre-commit", "run", hook_id]
    else:
        raise ValueError(f"unknown hook manager: {manager!r}")
    return subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
