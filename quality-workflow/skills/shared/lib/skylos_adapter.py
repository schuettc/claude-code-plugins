"""skylos JSON output → list[QualityFinding].

Skylos's JSON output has multiple top-level arrays for different finding kinds:
- `quality`     — code-quality findings with explicit rule_ids (SKY-Q*)
- `danger`      — security findings with explicit rule_ids (SKY-D*)
- `secrets`     — secret-detection findings (SKY-S* when present)
- `sca`         — software-composition findings (SKY-C*)
- `unused_functions`, `unused_imports`, `unused_classes`,
  `unused_variables`, `unused_parameters`, `unused_files`
                 — dead-code findings (no native rule_id; we synthesize)

Each shape gets normalized to a QualityFinding. Fingerprints are synthesized
from (rule_id, file, line, symbol) so the same finding produces the same
fingerprint across runs.

Suppression: skylos emits findings it knows are suppressed by inline directives
(`# skylos: ignore`) with a `reason` field — typically the string
"inline ignore comment". The adapter sets `suppressed=True` and stores the
reason verbatim. Headlines and delta tables filter these out via
`QualitySnapshot.active_findings()` / `SnapshotDiff.active_*`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

try:
    from .snapshot import QualityFinding
except ImportError:
    from snapshot import QualityFinding


class SkylosError(RuntimeError):
    """Raised when skylos output is missing, malformed, or the tool isn't installed."""


# Map skylos top-level array → QualityFinding `category` field.
# Unused-* keys all collapse to "dead-code".
_CATEGORY_BY_KEY: dict[str, str] = {
    "quality": "quality",
    "danger": "security",
    "secrets": "secrets",
    "sca": "dependency",
    "unused_functions": "dead-code",
    "unused_imports": "dead-code",
    "unused_classes": "dead-code",
    "unused_variables": "dead-code",
    "unused_parameters": "dead-code",
    "unused_files": "dead-code",
}

# Synthetic rule_ids for the unused_* categories (skylos doesn't provide one
# for these so they all flatten into a single bucket without something stable).
_SYNTHETIC_RULE_ID: dict[str, str] = {
    "unused_functions": "SKY-DEAD-FUNCTION",
    "unused_imports": "SKY-DEAD-IMPORT",
    "unused_classes": "SKY-DEAD-CLASS",
    "unused_variables": "SKY-DEAD-VARIABLE",
    "unused_parameters": "SKY-DEAD-PARAMETER",
    "unused_files": "SKY-DEAD-FILE",
}


def strip_banner(stdout: str) -> str:
    """Skylos sometimes prints a banner/progress lines before the JSON payload.

    Cut everything before the first `{` so json.loads can parse the rest.
    Raises SkylosError if no opening brace is found.
    """
    idx = stdout.find("{")
    if idx < 0:
        raise SkylosError("no JSON object found in skylos output")
    return stdout[idx:]


def parse_skylos_json(payload: dict[str, Any]) -> list[QualityFinding]:
    """Map a parsed skylos JSON payload to a list of QualityFinding records."""
    findings: list[QualityFinding] = []
    for key, category in _CATEGORY_BY_KEY.items():
        items = payload.get(key)
        if not items:
            continue
        for item in items:
            findings.append(_finding_from_item(item, key, category))
    return findings


def _finding_from_item(item: dict[str, Any], key: str, category: str) -> QualityFinding:
    """Normalize a single skylos finding (whatever its shape) to QualityFinding."""
    # Rule ID: explicit if present, otherwise synthesized for dead-code variants
    rule_id = item.get("rule_id") or _SYNTHETIC_RULE_ID.get(key, key.upper())

    # Severity: explicit if present, otherwise infer from category
    severity = (item.get("severity") or _default_severity(category)).upper()

    # File: skylos uses absolute paths; we keep them as-is (the caller can normalize)
    file_path = str(item.get("file", ""))

    # Line: most findings have it; default to 0 for file-level findings
    line = int(item.get("line", 0) or 0)

    # Message: skylos provides a message for quality/danger; for unused_* we
    # synthesize one from the name + category
    message = item.get("message") or _synthesize_message(item, key)

    # Symbol (for fingerprint uniqueness when multiple findings share file:line)
    symbol = item.get("symbol") or item.get("simple_name") or item.get("name") or ""

    # Confidence: skylos's unused_* findings expose this as 0-100; quality/danger don't
    raw_confidence = item.get("confidence")
    confidence = float(raw_confidence) if raw_confidence is not None else None
    # Normalize 0-100 → 0.0-1.0 for unused_* where it's int
    if confidence is not None and confidence > 1.0:
        confidence = confidence / 100.0

    # Suppression: skylos sets `reason` on findings it knows were suppressed by an
    # inline directive (`# skylos: ignore`). Without this branch the adapter would
    # ingest suppressed findings as active — the v0.2.0 bug that inflated counts.
    raw_reason = item.get("reason")
    reason_str = str(raw_reason).strip() if raw_reason else ""
    suppressed = bool(reason_str)
    suppression_reason = reason_str if suppressed else None

    return QualityFinding(
        fingerprint=_fingerprint(rule_id, file_path, line, str(symbol)),
        rule_id=rule_id,
        category=category,
        severity=severity,
        file=file_path,
        line=line,
        message=str(message),
        tool="skylos",
        confidence=confidence,
        suppressed=suppressed,
        suppression_reason=suppression_reason,
    )


def _default_severity(category: str) -> str:
    """Best-guess severity when skylos doesn't provide one."""
    return {
        "security": "HIGH",
        "secrets": "CRITICAL",
        "dependency": "MEDIUM",
        "dead-code": "LOW",
        "quality": "MEDIUM",
    }.get(category, "MEDIUM")


def _synthesize_message(item: dict[str, Any], key: str) -> str:
    """Build a one-line message for dead-code findings (skylos doesn't include one)."""
    if key == "unused_files":
        return f"Unused file: {item.get('file', '<unknown>')}"
    name = item.get("simple_name") or item.get("name") or "<unknown>"
    kind = {
        "unused_functions": "function",
        "unused_imports": "import",
        "unused_classes": "class",
        "unused_variables": "variable",
        "unused_parameters": "parameter",
    }.get(key, "symbol")
    return f"Unused {kind}: {name}"


def _fingerprint(rule_id: str, file: str, line: int, symbol: str) -> str:
    """Stable fingerprint across runs: hash of the identifying tuple."""
    key = f"{rule_id}|{file}|{line}|{symbol}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def run_full_audit(
    project_root: Path,
    *,
    include_quality: bool = True,
    include_danger: bool = True,
    include_secrets: bool = True,
    include_sca: bool = True,
    timeout: int = 300,
) -> list[QualityFinding]:
    """Run a full skylos audit on `project_root` and return findings.

    Equivalent to: `uvx skylos <project_root> --quality --danger --secrets --sca --format json --no-upload`
    """
    cmd = ["uvx", "skylos", str(project_root)]
    if include_quality:
        cmd.append("--quality")
    if include_danger:
        cmd.append("--danger")
    if include_secrets:
        cmd.append("--secrets")
    if include_sca:
        cmd.append("--sca")
    cmd.extend(["--format", "json", "--no-upload"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise SkylosError(
            "uvx not found. Install uv (https://docs.astral.sh/uv/) or invoke skylos directly."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise SkylosError(f"skylos timed out after {timeout}s on {project_root}") from e

    if result.returncode not in (0, 1):
        # skylos uses exit 1 to signal findings-present (not an error); other codes are real failures
        raise SkylosError(
            f"skylos exited with code {result.returncode}: {result.stderr[:500] if result.stderr else 'no stderr'}"
        )

    payload_text = strip_banner(result.stdout)
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as e:
        raise SkylosError(f"skylos output is not valid JSON: {e}") from e
    return parse_skylos_json(payload)


def run_agent_pre_commit(project_root: Path, *, timeout: int = 60) -> list[QualityFinding]:
    """Run `uvx skylos agent pre-commit --format json` for staged-file gating.

    Returns findings on staged files only; empty list if no Python files are staged.
    """
    cmd = ["uvx", "skylos", "agent", "pre-commit", str(project_root), "--format", "json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise SkylosError(
            "uvx not found. Install uv (https://docs.astral.sh/uv/) or invoke skylos directly."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise SkylosError(f"skylos agent pre-commit timed out after {timeout}s") from e

    stdout = result.stdout.strip()
    # When nothing is staged, skylos prints a single line and exits 0; no JSON to parse.
    if "No staged files to analyze" in stdout or not stdout:
        return []

    payload_text = strip_banner(stdout)
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as e:
        raise SkylosError(f"skylos agent pre-commit output is not valid JSON: {e}") from e
    return parse_skylos_json(payload)


def grade_from_payload(payload: dict[str, Any]) -> str:
    """Extract the overall grade letter from a skylos audit payload."""
    grade = payload.get("grade") or {}
    overall = grade.get("overall") or {}
    return str(overall.get("letter", ""))
