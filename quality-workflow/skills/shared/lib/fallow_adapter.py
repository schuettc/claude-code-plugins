"""fallow JSON output → list[QualityFinding].

Fallow has three relevant subcommands for the snapshot path:
- `fallow health --format json`   — complexity findings + per-file scores
- `fallow dupes --format json`    — clone groups
- `fallow dead-code --format json` — unused files/exports/types/etc.

And one for the hook path:
- `fallow audit`                  — changeset-scoped; combines all three

Unlike skylos, fallow doesn't expose a rule_id field. We synthesize stable
rule_ids per finding kind (FAL-COMPLEXITY, FAL-DUPE, FAL-DEAD-EXPORT, …).
Fingerprints follow the same {rule_id|file|line|symbol} scheme as skylos.

Suppression: fallow does not surface per-finding suppression state in its JSON —
its `// fallow-ignore-next-line` directives cause findings to be omitted from
the report rather than flagged. The adapter therefore leaves `suppressed=False`
on every fallow finding. Hygiene of `// fallow-ignore-next-line` comments is
audited separately by `audit_suppressions.py` (post-MVP `/quality-suppressions`).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

try:
    from .snapshot import QualityFinding
except ImportError:
    from snapshot import QualityFinding


class FallowError(RuntimeError):
    """Raised when fallow output is missing, malformed, or the tool isn't installed."""


# ---- Public parsers (operate on already-parsed JSON dicts) ----

def parse_health_json(payload: dict[str, Any]) -> list[QualityFinding]:
    """Map a `fallow health --format json` payload to QualityFinding list."""
    findings: list[QualityFinding] = []
    for item in payload.get("findings", []) or []:
        rule_id = "FAL-COMPLEXITY"
        severity = (item.get("severity") or "medium").upper()
        path = str(item.get("path", ""))
        line = int(item.get("line", 0) or 0)
        name = str(item.get("name", ""))
        cyc = item.get("cyclomatic")
        cog = item.get("cognitive")
        exceeded = item.get("exceeded", "complexity")
        message = (
            f"`{name}` exceeds {exceeded} threshold "
            f"(cyclomatic={cyc}, cognitive={cog})."
            if name
            else f"Complexity threshold exceeded ({exceeded})."
        )
        findings.append(
            QualityFinding(
                fingerprint=_fingerprint(rule_id, path, line, name),
                rule_id=rule_id,
                category="quality",
                severity=severity,
                file=path,
                line=line,
                message=message,
                tool="fallow",
                confidence=None,
            )
        )
    return findings


def parse_dupes_json(payload: dict[str, Any]) -> list[QualityFinding]:
    """Map a `fallow dupes --format json` payload to QualityFinding list.

    Each clone_group's instances become individual findings — one per duplicate
    location — so the fingerprint set covers each occurrence.
    """
    findings: list[QualityFinding] = []
    for group in payload.get("clone_groups", []) or []:
        group_id = str(group.get("id", ""))
        tokens = group.get("tokens", 0)
        instances = group.get("instances", []) or []
        for inst in instances:
            path = str(inst.get("path", ""))
            line = int(inst.get("start_line", 0) or 0)
            rule_id = "FAL-DUPE"
            # symbol = group id so all instances in one group share fingerprint identity
            # but each instance's (file, line) keeps fingerprints distinct per location
            symbol = group_id
            findings.append(
                QualityFinding(
                    fingerprint=_fingerprint(rule_id, path, line, symbol),
                    rule_id=rule_id,
                    category="duplication",
                    severity="MEDIUM",
                    file=path,
                    line=line,
                    message=(
                        f"Clone group {group_id} ({tokens} tokens) — duplicate code "
                        f"shared with {len(instances) - 1} other location(s)."
                    ),
                    tool="fallow",
                    confidence=None,
                )
            )
    return findings


# Each dead-code top-level key maps to a synthetic rule_id + a human kind label.
_DEAD_CODE_KEYS: dict[str, tuple[str, str]] = {
    "unused_files": ("FAL-DEAD-FILE", "file"),
    "unused_exports": ("FAL-DEAD-EXPORT", "export"),
    "unused_types": ("FAL-DEAD-TYPE", "type"),
    "unused_enum_members": ("FAL-DEAD-ENUM-MEMBER", "enum member"),
    "unused_class_members": ("FAL-DEAD-CLASS-MEMBER", "class member"),
    "unused_dependencies": ("FAL-DEAD-DEP", "dependency"),
    "unused_dev_dependencies": ("FAL-DEAD-DEV-DEP", "dev dependency"),
    "unused_optional_dependencies": ("FAL-DEAD-OPT-DEP", "optional dependency"),
    "unresolved_imports": ("FAL-UNRESOLVED-IMPORT", "import"),
    "circular_dependencies": ("FAL-CIRCULAR", "circular dependency"),
    "boundary_violations": ("FAL-BOUNDARY", "boundary violation"),
}


def parse_dead_code_json(payload: dict[str, Any]) -> list[QualityFinding]:
    """Map `fallow dead-code --format json` payload to QualityFinding list."""
    findings: list[QualityFinding] = []
    for key, (rule_id, kind_label) in _DEAD_CODE_KEYS.items():
        items = payload.get(key) or []
        for item in items:
            path = str(item.get("path", "") or item.get("file", ""))
            line = int(item.get("line", 0) or 0)
            name = str(item.get("name", "") or "")
            # Severity: dependencies are higher signal; misc dead code is LOW
            severity = (
                "MEDIUM" if rule_id in {"FAL-UNRESOLVED-IMPORT", "FAL-CIRCULAR", "FAL-BOUNDARY"} else "LOW"
            )
            message = (
                f"Unused {kind_label}: {name}"
                if name
                else f"Unused {kind_label}: {path}"
            )
            findings.append(
                QualityFinding(
                    fingerprint=_fingerprint(rule_id, path, line, name),
                    rule_id=rule_id,
                    category="dead-code",
                    severity=severity,
                    file=path,
                    line=line,
                    message=message,
                    tool="fallow",
                    confidence=None,
                )
            )
    return findings


def grade_from_health_payload(payload: dict[str, Any]) -> str:
    """Extract the health_score letter grade from a `fallow health` payload."""
    score = payload.get("health_score") or {}
    return str(score.get("grade", ""))


# ---- Subprocess wrappers (run fallow, return findings) ----

def _run_fallow(
    args: list[str],
    project_root: Path,
    *,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run `npx fallow <args> --format json` and return parsed JSON."""
    cmd = ["npx", "fallow", *args, "--format", "json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
        )
    except FileNotFoundError as e:
        raise FallowError(
            "npx not found. Install Node.js (https://nodejs.org/) so `npx fallow` is available."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise FallowError(f"fallow timed out after {timeout}s on {project_root}") from e

    if result.returncode not in (0, 1):
        # fallow returns 1 when findings are present — not an error
        raise FallowError(
            f"fallow {args[0]} exited with code {result.returncode}: "
            f"{result.stderr[:500] if result.stderr else 'no stderr'}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise FallowError(f"fallow {args[0]} output is not valid JSON: {e}") from e


def run_health(project_root: Path, *, timeout: int = 120) -> list[QualityFinding]:
    """Run `fallow health` in project_root, return findings."""
    payload = _run_fallow(["health"], project_root, timeout=timeout)
    return parse_health_json(payload)


def run_dupes(project_root: Path, *, timeout: int = 120) -> list[QualityFinding]:
    """Run `fallow dupes` in project_root, return findings."""
    payload = _run_fallow(["dupes"], project_root, timeout=timeout)
    return parse_dupes_json(payload)


def run_dead_code(project_root: Path, *, timeout: int = 120) -> list[QualityFinding]:
    """Run `fallow dead-code` in project_root, return findings."""
    payload = _run_fallow(["dead-code"], project_root, timeout=timeout)
    return parse_dead_code_json(payload)


def run_full_audit(project_root: Path, *, timeout: int = 240) -> list[QualityFinding]:
    """Run all three fallow snapshot commands and concatenate findings."""
    return [
        *run_health(project_root, timeout=timeout),
        *run_dupes(project_root, timeout=timeout),
        *run_dead_code(project_root, timeout=timeout),
    ]


def run_audit(project_root: Path, *, timeout: int = 60) -> list[QualityFinding]:
    """Run `fallow audit` (changeset-scoped) for hook-time gating.

    Fallow audit combines dead-code + complexity + duplication scoped to
    changed files. Used by the pre-commit hook path.
    """
    payload = _run_fallow(["audit"], project_root, timeout=timeout)
    findings: list[QualityFinding] = []
    # `fallow audit` returns a similar shape to its sub-commands; flatten all sources.
    findings.extend(parse_health_json(payload))
    findings.extend(parse_dupes_json(payload))
    findings.extend(parse_dead_code_json(payload))
    return findings


# ---- Helpers ----

def _fingerprint(rule_id: str, file: str, line: int, symbol: str) -> str:
    """Stable fingerprint across runs: hash of the identifying tuple."""
    key = f"{rule_id}|{file}|{line}|{symbol}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
