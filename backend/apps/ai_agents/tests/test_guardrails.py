# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for AI Agent guardrails."""
import pytest

from apps.ai_agents.guardrails import (
    AGENT_GUARDRAILS,
    AgentGuardrail,
    RiskLevel,
    get_guardrail,
    requires_human_approval,
    validate_agent_action,
)


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test risk level enum values."""
        assert RiskLevel.R1_LOW.value == "R1"
        assert RiskLevel.R2_MEDIUM.value == "R2"
        assert RiskLevel.R3_HIGH.value == "R3"

    def test_r1_can_auto_execute(self):
        """Test R1 can auto-execute."""
        assert RiskLevel.R1_LOW.can_auto_execute is True
        assert RiskLevel.R2_MEDIUM.can_auto_execute is False
        assert RiskLevel.R3_HIGH.can_auto_execute is False

    def test_r3_requires_approval(self):
        """Test R3 always requires approval."""
        assert RiskLevel.R1_LOW.requires_approval is False
        assert RiskLevel.R2_MEDIUM.requires_approval is False
        assert RiskLevel.R3_HIGH.requires_approval is True

    def test_display_names(self):
        """Test display names are human-readable."""
        assert "Low" in RiskLevel.R1_LOW.display_name
        assert "Medium" in RiskLevel.R2_MEDIUM.display_name
        assert "High" in RiskLevel.R3_HIGH.display_name


class TestAgentGuardrail:
    """Tests for AgentGuardrail dataclass."""

    @pytest.fixture
    def sample_guardrail(self):
        """Create sample guardrail for testing."""
        return AgentGuardrail(
            agent_type="test_agent",
            risk_level=RiskLevel.R2_MEDIUM,
            requires_approval=True,
            requires_evidence_pack=True,
            allowed_actions=["read", "analyze", "recommend"],
            forbidden_actions=["delete", "execute"],
            max_scope_size=100,
            timeout_seconds=60,
        )

    def test_can_execute_allowed_action(self, sample_guardrail):
        """Test allowed action passes validation."""
        allowed, reason = sample_guardrail.can_execute_action("read")
        assert allowed is True
        assert reason is None

    def test_cannot_execute_forbidden_action(self, sample_guardrail):
        """Test forbidden action fails validation."""
        allowed, reason = sample_guardrail.can_execute_action("delete")
        assert allowed is False
        assert "forbidden" in reason.lower()

    def test_cannot_execute_unlisted_action(self, sample_guardrail):
        """Test unlisted action fails when allowed_actions is specified."""
        allowed, reason = sample_guardrail.can_execute_action("unknown_action")
        assert allowed is False
        assert "not in the allowed actions" in reason.lower()

    def test_validate_scope_within_limits(self, sample_guardrail):
        """Test scope within limits passes."""
        valid, reason = sample_guardrail.validate_scope(50)
        assert valid is True
        assert reason is None

    def test_validate_scope_exceeds_limits(self, sample_guardrail):
        """Test scope exceeding limits fails."""
        valid, reason = sample_guardrail.validate_scope(150)
        assert valid is False
        assert "exceeds maximum" in reason.lower()

    def test_guardrail_with_no_allowed_actions(self):
        """Test guardrail with empty allowed_actions allows any non-forbidden action."""
        guardrail = AgentGuardrail(
            agent_type="permissive_agent",
            risk_level=RiskLevel.R1_LOW,
            requires_approval=False,
            requires_evidence_pack=False,
            allowed_actions=[],  # Empty = allow any
            forbidden_actions=["delete"],
        )
        allowed, _ = guardrail.can_execute_action("any_action")
        assert allowed is True


class TestAgentGuardrailsRegistry:
    """Tests for AGENT_GUARDRAILS registry."""

    def test_incident_classifier_is_r1(self):
        """Test incident classifier is low risk."""
        guardrail = AGENT_GUARDRAILS.get("incident_classifier")
        assert guardrail is not None
        assert guardrail.risk_level == RiskLevel.R1_LOW
        assert guardrail.requires_approval is False

    def test_auto_remediator_is_r3(self):
        """Test auto-remediator is high risk."""
        guardrail = AGENT_GUARDRAILS.get("auto_remediator")
        assert guardrail is not None
        assert guardrail.risk_level == RiskLevel.R3_HIGH
        assert guardrail.requires_approval is True

    def test_remediation_advisor_is_r2(self):
        """Test remediation advisor is medium risk."""
        guardrail = AGENT_GUARDRAILS.get("remediation_advisor")
        assert guardrail is not None
        assert guardrail.risk_level == RiskLevel.R2_MEDIUM
        assert guardrail.requires_approval is True

    def test_all_guardrails_have_required_fields(self):
        """Test all registered guardrails have required fields."""
        for agent_type, guardrail in AGENT_GUARDRAILS.items():
            assert guardrail.agent_type == agent_type
            assert guardrail.risk_level in RiskLevel
            assert isinstance(guardrail.requires_approval, bool)
            assert isinstance(guardrail.requires_evidence_pack, bool)
            assert isinstance(guardrail.timeout_seconds, int)
            assert guardrail.timeout_seconds > 0

    def test_auto_remediator_has_restricted_scope(self):
        """Test auto-remediator has limited scope for safety."""
        guardrail = AGENT_GUARDRAILS.get("auto_remediator")
        assert guardrail.max_scope_size <= 100  # Should be restricted

    def test_auto_remediator_forbids_dangerous_actions(self):
        """Test auto-remediator forbids dangerous actions."""
        guardrail = AGENT_GUARDRAILS.get("auto_remediator")
        dangerous_actions = ["delete_data", "format_disk", "disable_security"]
        for action in dangerous_actions:
            assert action in guardrail.forbidden_actions


class TestGetGuardrail:
    """Tests for get_guardrail function."""

    def test_get_existing_guardrail(self):
        """Test getting existing guardrail."""
        guardrail = get_guardrail("incident_classifier")
        assert guardrail is not None
        assert guardrail.agent_type == "incident_classifier"

    def test_get_nonexistent_guardrail(self):
        """Test getting nonexistent guardrail returns None."""
        guardrail = get_guardrail("nonexistent_agent")
        assert guardrail is None


class TestValidateAgentAction:
    """Tests for validate_agent_action function."""

    def test_valid_action_and_scope(self):
        """Test valid action and scope passes."""
        valid, errors = validate_agent_action(
            "incident_classifier",
            "classify",
            scope_size=10,
        )
        assert valid is True
        assert len(errors) == 0

    def test_forbidden_action_fails(self):
        """Test forbidden action fails validation."""
        valid, errors = validate_agent_action(
            "incident_classifier",
            "execute",
            scope_size=1,
        )
        assert valid is False
        assert len(errors) > 0
        assert any("forbidden" in e.lower() for e in errors)

    def test_excessive_scope_fails(self):
        """Test excessive scope fails validation."""
        valid, errors = validate_agent_action(
            "auto_remediator",
            "execute_script",
            scope_size=1000,  # Way over limit
        )
        assert valid is False
        assert any("exceeds" in e.lower() for e in errors)

    def test_unknown_agent_fails(self):
        """Test unknown agent type fails validation."""
        valid, errors = validate_agent_action(
            "unknown_agent",
            "any_action",
            scope_size=1,
        )
        assert valid is False
        assert any("no guardrail" in e.lower() for e in errors)


class TestRequiresHumanApproval:
    """Tests for requires_human_approval function."""

    def test_r3_always_requires_approval(self):
        """Test R3 agents always require approval."""
        assert requires_human_approval("auto_remediator", "any_action") is True

    def test_r1_does_not_require_approval(self):
        """Test R1 agents don't require approval."""
        assert requires_human_approval("incident_classifier", "classify") is False

    def test_r2_with_explicit_requirement(self):
        """Test R2 agents with explicit approval requirement."""
        # Remediation advisor has requires_approval=True
        assert requires_human_approval("remediation_advisor", "recommend") is True

    def test_unknown_agent_requires_approval(self):
        """Test unknown agent defaults to requiring approval."""
        assert requires_human_approval("unknown_agent", "any_action") is True


class TestGuardrailIntegration:
    """Integration tests for guardrail system."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        agent_type = "remediation_advisor"
        action = "recommend"
        scope = 50

        # Get guardrail
        guardrail = get_guardrail(agent_type)
        assert guardrail is not None

        # Validate action
        valid, errors = validate_agent_action(agent_type, action, scope)
        assert valid is True

        # Check approval requirement
        needs_approval = requires_human_approval(agent_type, action)
        assert needs_approval is True  # R2 with requires_approval=True

        # Check evidence pack requirement
        assert guardrail.requires_evidence_pack is True

    def test_blocked_dangerous_action_workflow(self):
        """Test that dangerous actions are properly blocked."""
        agent_type = "auto_remediator"
        dangerous_action = "delete_data"

        # Validation should fail
        valid, errors = validate_agent_action(agent_type, dangerous_action, scope_size=1)
        assert valid is False

        # Even if somehow bypassed, approval is required
        needs_approval = requires_human_approval(agent_type, dangerous_action)
        assert needs_approval is True
