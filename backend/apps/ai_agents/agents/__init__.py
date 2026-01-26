# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Specialized AI agent implementations.

Includes:
- BaseAgent: Abstract base class for all agents
- AmaniAssistant: AI assistant agent
- AgentExecutionFramework: Guardrail-enforced execution framework (D7.1)
"""

from .amani_assistant import AmaniAssistant
from .base_agent import BaseAgent
from .execution_framework import (
    AgentExecutionFramework,
    ApprovalRequiredError,
    ExecutionInput,
    ExecutionResult,
    ExecutionStatus,
    GuardrailViolation,
    get_execution_framework,
    set_execution_framework,
)

__all__ = [
    "BaseAgent",
    "AmaniAssistant",
    "AgentExecutionFramework",
    "ExecutionInput",
    "ExecutionResult",
    "ExecutionStatus",
    "GuardrailViolation",
    "ApprovalRequiredError",
    "get_execution_framework",
    "set_execution_framework",
]
