"""Playbook loader: rule_id → list[Action].

A playbook is a YAML file describing how to respond to each static-analysis
rule_id. Day-1 ships `skylos.yaml` and `fallow.yaml` at `quality-workflow/
playbooks/`. Each rule maps to a list of actions (fix / suppress / defer).

Actions are evaluated by `quality-unblock` when a hook fails — the user
picks one per finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


class PlaybookError(RuntimeError):
    """Raised when a playbook file is missing or malformed."""


@dataclass
class Action:
    """One way to respond to a finding."""

    kind: str  # "fix" | "suppress" | "defer"
    suggestion: Optional[str] = None
    agent_prompt: Optional[str] = None
    require_why: bool = False
    require_severity_ack: bool = False
    why_template: Optional[str] = None
    epic_title_template: Optional[str] = None


@dataclass
class Playbook:
    """A loaded playbook for one tool."""

    tool: str  # "skylos" | "fallow"
    rules: dict[str, list[Action]] = field(default_factory=dict)
    fallback: list[Action] = field(default_factory=list)


def load_playbook(path: Path) -> Playbook:
    """Load a YAML playbook file."""
    if not path.exists():
        raise FileNotFoundError(f"Playbook not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PlaybookError(f"Playbook root must be a mapping: {path}")

    tool = str(raw.get("tool", "")).strip()
    if not tool:
        raise PlaybookError(f"Playbook missing `tool:` field: {path}")

    rules_raw = raw.get("rules", {}) or {}
    rules: dict[str, list[Action]] = {}
    for rule_id, body in rules_raw.items():
        if not isinstance(body, dict):
            continue
        actions_raw = body.get("actions", []) or []
        rules[str(rule_id)] = [_parse_action(a) for a in actions_raw]

    fallback_raw = raw.get("fallback", {}) or {}
    fallback_actions_raw = fallback_raw.get("actions", []) or []
    fallback = [_parse_action(a) for a in fallback_actions_raw]

    return Playbook(tool=tool, rules=rules, fallback=fallback)


def resolve_actions(playbook: Playbook, rule_id: str) -> list[Action]:
    """Return the list of actions for `rule_id`, falling back if not registered."""
    if rule_id in playbook.rules:
        return playbook.rules[rule_id]
    return list(playbook.fallback)


def _parse_action(d: dict[str, Any]) -> Action:
    """Map a YAML action dict to an Action dataclass."""
    return Action(
        kind=str(d.get("kind", "fix")),
        suggestion=d.get("suggestion"),
        agent_prompt=d.get("agent_prompt"),
        require_why=bool(d.get("require_why", False)),
        require_severity_ack=bool(d.get("require_severity_ack", False)),
        why_template=d.get("why_template"),
        epic_title_template=d.get("epic_title_template"),
    )


def load_default_playbooks(plugin_root: Path) -> dict[str, Playbook]:
    """Load the day-1 playbooks bundled with the plugin.

    Returns a dict keyed by tool name: {"skylos": Playbook, "fallow": Playbook}.
    """
    pb_dir = plugin_root / "playbooks"
    return {
        "skylos": load_playbook(pb_dir / "skylos.yaml"),
        "fallow": load_playbook(pb_dir / "fallow.yaml"),
    }
