# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AI Agent Guardrails for EUCORA.

Defines execution boundaries, risk levels, and approval requirements
for all AI agents. Non-negotiable governance controls.

Risk Levels:
- R1 (Low): Auto-execute allowed, no human approval required
- R2 (Medium): Policy-dependent approval, may require human sign-off
- R3 (High): Mandatory human approval before any execution
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    """
    Risk classification for AI agent actions.

    R1: Low risk - can auto-execute without approval
    R2: Medium risk - policy-dependent, may need approval
    R3: High risk - mandatory human approval always required
    """

    R1_LOW = "R1"
    R2_MEDIUM = "R2"
    R3_HIGH = "R3"

    @property
    def requires_approval(self) -> bool:
        """Check if this risk level always requires approval."""
        return self == RiskLevel.R3_HIGH

    @property
    def can_auto_execute(self) -> bool:
        """Check if this risk level can auto-execute."""
        return self == RiskLevel.R1_LOW

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            RiskLevel.R1_LOW: "Low Risk (Auto-execute)",
            RiskLevel.R2_MEDIUM: "Medium Risk (Policy-dependent)",
            RiskLevel.R3_HIGH: "High Risk (Approval Required)",
        }
        return names.get(self, self.value)


@dataclass
class AgentGuardrail:
    """
    Defines execution boundaries for an AI agent.

    All agents must have a guardrail definition that specifies:
    - Risk level and approval requirements
    - Allowed and forbidden actions
    - Scope limits (max devices/users affected)
    - Timeout and resource limits
    """

    agent_type: str
    risk_level: RiskLevel
    requires_approval: bool
    requires_evidence_pack: bool
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    max_scope_size: int = 100  # Max devices/users affected in single action
    timeout_seconds: int = 300  # Execution timeout
    max_retries: int = 3
    require_correlation_id: bool = True
    allow_pii_in_output: bool = False
    audit_all_inputs: bool = True
    audit_all_outputs: bool = True

    def can_execute_action(self, action: str) -> tuple[bool, Optional[str]]:
        """
        Check if an action can be executed by this agent.

        Args:
            action: Action name to check

        Returns:
            Tuple of (allowed: bool, reason: str or None)
        """
        if action in self.forbidden_actions:
            return False, f"Action '{action}' is explicitly forbidden for {self.agent_type}"

        if self.allowed_actions and action not in self.allowed_actions:
            return False, f"Action '{action}' is not in the allowed actions list for {self.agent_type}"

        return True, None

    def validate_scope(self, scope_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate that scope is within limits.

        Args:
            scope_size: Number of entities affected

        Returns:
            Tuple of (valid: bool, reason: str or None)
        """
        if scope_size > self.max_scope_size:
            return False, f"Scope size {scope_size} exceeds maximum {self.max_scope_size} for {self.agent_type}"
        return True, None


# =============================================================================
# Guardrail Registry (Non-Negotiable)
# =============================================================================

AGENT_GUARDRAILS: dict[str, AgentGuardrail] = {
    # Incident Classification - Low risk, read-only analysis
    "incident_classifier": AgentGuardrail(
        agent_type="incident_classifier",
        risk_level=RiskLevel.R1_LOW,
        requires_approval=False,
        requires_evidence_pack=True,
        allowed_actions=["classify", "suggest_category", "extract_entities", "summarize"],
        forbidden_actions=["execute", "deploy", "delete", "modify_config"],
        max_scope_size=1000,
        timeout_seconds=60,
    ),
    # Remediation Advisor - Medium risk, provides recommendations
    "remediation_advisor": AgentGuardrail(
        agent_type="remediation_advisor",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,  # Recommendations require review
        requires_evidence_pack=True,
        allowed_actions=[
            "analyze",
            "recommend",
            "generate_script",
            "generate_rollback_plan",
            "estimate_impact",
        ],
        forbidden_actions=["execute", "deploy", "delete", "modify_production"],
        max_scope_size=500,
        timeout_seconds=120,
    ),
    # Risk Assessment - Low risk, read-only scoring
    "risk_assessor": AgentGuardrail(
        agent_type="risk_assessor",
        risk_level=RiskLevel.R1_LOW,
        requires_approval=False,
        requires_evidence_pack=True,
        allowed_actions=["score", "explain", "compare", "forecast"],
        forbidden_actions=["execute", "deploy", "delete", "approve"],
        max_scope_size=10000,
        timeout_seconds=60,
    ),
    # CAB Evidence Generator - Medium risk, generates artifacts
    "cab_evidence_generator": AgentGuardrail(
        agent_type="cab_evidence_generator",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,  # Generated evidence must be reviewed
        requires_evidence_pack=True,
        allowed_actions=[
            "generate_summary",
            "generate_risk_analysis",
            "generate_test_plan",
            "generate_rollback_plan",
            "compile_evidence",
        ],
        forbidden_actions=["approve", "submit", "deploy", "execute"],
        max_scope_size=100,
        timeout_seconds=300,
    ),
    # Packaging Assistant - Medium risk, generates packages
    "packaging_assistant": AgentGuardrail(
        agent_type="packaging_assistant",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,
        requires_evidence_pack=True,
        allowed_actions=[
            "analyze_installer",
            "generate_detection_rules",
            "generate_install_script",
            "generate_uninstall_script",
            "validate_package",
        ],
        forbidden_actions=["deploy", "publish", "sign", "approve"],
        max_scope_size=10,
        timeout_seconds=600,
    ),
    # Deployment Advisor - Medium risk, provides deployment recommendations
    "deployment_advisor": AgentGuardrail(
        agent_type="deployment_advisor",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,
        requires_evidence_pack=True,
        allowed_actions=[
            "recommend_ring",
            "recommend_schedule",
            "analyze_dependencies",
            "estimate_rollout_time",
            "identify_conflicts",
        ],
        forbidden_actions=["deploy", "rollback", "approve", "execute"],
        max_scope_size=10000,
        timeout_seconds=120,
    ),
    # Auto-Remediator - HIGH RISK, can execute changes
    "auto_remediator": AgentGuardrail(
        agent_type="auto_remediator",
        risk_level=RiskLevel.R3_HIGH,
        requires_approval=True,  # ALWAYS requires approval
        requires_evidence_pack=True,
        allowed_actions=[
            "execute_script",
            "restart_service",
            "clear_cache",
            "update_config",
        ],
        forbidden_actions=[
            "delete_data",
            "format_disk",
            "disable_security",
            "modify_firewall",
            "change_credentials",
        ],
        max_scope_size=50,  # Limited scope for safety
        timeout_seconds=600,
        max_retries=1,  # Minimal retries for destructive actions
    ),
    # License Optimizer - Medium risk, provides recommendations
    "license_optimizer": AgentGuardrail(
        agent_type="license_optimizer",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,
        requires_evidence_pack=True,
        allowed_actions=[
            "analyze_usage",
            "recommend_reallocation",
            "identify_waste",
            "forecast_needs",
            "generate_report",
        ],
        forbidden_actions=["revoke_license", "modify_assignment", "delete_entitlement"],
        max_scope_size=10000,
        timeout_seconds=300,
    ),
    # Compliance Analyzer - Low risk, read-only analysis
    "compliance_analyzer": AgentGuardrail(
        agent_type="compliance_analyzer",
        risk_level=RiskLevel.R1_LOW,
        requires_approval=False,
        requires_evidence_pack=True,
        allowed_actions=[
            "analyze",
            "score",
            "identify_violations",
            "generate_report",
            "recommend_remediation",
        ],
        forbidden_actions=["execute", "deploy", "modify", "approve"],
        max_scope_size=10000,
        timeout_seconds=300,
    ),
    # Ask Amani (General Assistant) - Low risk, conversational
    "amani_assistant": AgentGuardrail(
        agent_type="amani_assistant",
        risk_level=RiskLevel.R1_LOW,
        requires_approval=False,
        requires_evidence_pack=False,
        allowed_actions=[
            "answer_question",
            "explain_concept",
            "search_documentation",
            "summarize",
            "translate",
        ],
        forbidden_actions=["execute", "deploy", "delete", "modify", "approve"],
        max_scope_size=1,  # Single user context
        timeout_seconds=60,
        allow_pii_in_output=False,
    ),
}


def get_guardrail(agent_type: str) -> Optional[AgentGuardrail]:
    """
    Get guardrail for an agent type.

    Args:
        agent_type: Agent type identifier

    Returns:
        AgentGuardrail or None if not found
    """
    return AGENT_GUARDRAILS.get(agent_type)


def validate_agent_action(
    agent_type: str,
    action: str,
    scope_size: int = 1,
) -> tuple[bool, list[str]]:
    """
    Validate if an agent can perform an action.

    Args:
        agent_type: Agent type identifier
        action: Action to perform
        scope_size: Number of entities affected

    Returns:
        Tuple of (valid: bool, errors: list[str])
    """
    errors = []

    guardrail = get_guardrail(agent_type)
    if not guardrail:
        errors.append(f"No guardrail defined for agent type: {agent_type}")
        return False, errors

    # Check action
    action_allowed, action_error = guardrail.can_execute_action(action)
    if not action_allowed:
        errors.append(action_error)

    # Check scope
    scope_valid, scope_error = guardrail.validate_scope(scope_size)
    if not scope_valid:
        errors.append(scope_error)

    return len(errors) == 0, errors


def requires_human_approval(agent_type: str, action: str) -> bool:
    """
    Check if an action requires human approval.

    Args:
        agent_type: Agent type identifier
        action: Action to perform

    Returns:
        True if human approval is required
    """
    guardrail = get_guardrail(agent_type)
    if not guardrail:
        return True  # Default to requiring approval for unknown agents

    # R3 always requires approval
    if guardrail.risk_level == RiskLevel.R3_HIGH:
        return True

    # Explicit approval requirement
    if guardrail.requires_approval:
        return True

    return False
