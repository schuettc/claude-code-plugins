"""Tests for the playbook loader."""

from pathlib import Path

import pytest

from playbook import (
    Action,
    PlaybookError,
    load_playbook,
    resolve_actions,
)


PLAYBOOK_DIR = Path(__file__).parent.parent.parent.parent / "playbooks"


class TestLoadPlaybook:
    def test_load_skylos_yaml(self):
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        assert pb.tool == "skylos"
        # Known rules from day-1 playbook
        assert "SKY-Q301" in pb.rules
        assert "SKY-D216" in pb.rules
        # Fallback present
        assert pb.fallback is not None
        assert len(pb.fallback) >= 1

    def test_load_fallow_yaml(self):
        pb = load_playbook(PLAYBOOK_DIR / "fallow.yaml")
        assert pb.tool == "fallow"
        assert "FAL-COMPLEXITY" in pb.rules
        assert "FAL-DUPE" in pb.rules

    def test_load_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_playbook(tmp_path / "nope.yaml")


class TestResolveActions:
    def test_known_rule(self):
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        actions = resolve_actions(pb, "SKY-Q301")
        assert len(actions) >= 2
        kinds = [a.kind for a in actions]
        assert "fix" in kinds
        assert "suppress" in kinds

    def test_unknown_rule_returns_fallback(self):
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        actions = resolve_actions(pb, "SKY-UNKNOWN-9999")
        assert len(actions) >= 1
        kinds = [a.kind for a in actions]
        # Fallback should include at least fix + suppress with require_why
        assert "suppress" in kinds

    def test_suppress_action_requires_why(self):
        """Every suppress action in the day-1 playbook should require a justification."""
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        for rule_id, actions in pb.rules.items():
            for action in actions:
                if action.kind == "suppress":
                    assert action.require_why is True, (
                        f"Suppress action for {rule_id} should require_why"
                    )

    def test_severity_ack_for_security_rules(self):
        """Security rules' suppress actions should require_severity_ack."""
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        for rule_id in ["SKY-D211", "SKY-D215", "SKY-D216", "SKY-D324"]:
            actions = pb.rules.get(rule_id, [])
            suppress_actions = [a for a in actions if a.kind == "suppress"]
            assert suppress_actions, f"{rule_id} should have a suppress action"
            assert all(a.require_severity_ack for a in suppress_actions), (
                f"{rule_id} suppress should require severity ack"
            )

    def test_action_has_required_fields(self):
        pb = load_playbook(PLAYBOOK_DIR / "skylos.yaml")
        actions = resolve_actions(pb, "SKY-Q301")
        for a in actions:
            assert isinstance(a, Action)
            assert a.kind in {"fix", "suppress", "defer"}
            # `fix` should have a suggestion or agent_prompt; suppress should have why_template
            if a.kind == "fix":
                assert a.suggestion or a.agent_prompt
            if a.kind == "suppress":
                assert a.why_template
