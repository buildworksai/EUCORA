# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AI Agents app for EUCORA.

Provides AI-assisted workflows with mandatory human approval gates.
All AI recommendations require human review before execution.

P7 Governance Features:
- Model Registry with lineage tracking (AIModel)
- Agent Execution audit trail (AgentExecution)
- Drift detection metrics (ModelDriftMetric)
- Risk-level guardrails (R1/R2/R3)
"""
from .guardrails import (
    AGENT_GUARDRAILS,
    AgentGuardrail,
    RiskLevel,
    get_guardrail,
    requires_human_approval,
    validate_agent_action,
)

default_app_config = "apps.ai_agents.apps.AIAgentsConfig"

__all__ = [
    "RiskLevel",
    "AgentGuardrail",
    "AGENT_GUARDRAILS",
    "get_guardrail",
    "validate_agent_action",
    "requires_human_approval",
]
