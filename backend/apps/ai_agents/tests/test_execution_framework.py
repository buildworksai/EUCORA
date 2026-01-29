# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Agent Execution Framework (D7.1)."""
from unittest.mock import patch

import pytest

from apps.ai_agents.agents.execution_framework import (
    AgentExecutionFramework,
    ApprovalRequiredError,
    ExecutionInput,
    ExecutionResult,
    ExecutionStatus,
    GuardrailViolation,
    get_execution_framework,
    set_execution_framework,
)
from apps.ai_agents.guardrails import AGENT_GUARDRAILS, AgentGuardrail, RiskLevel


class TestAgentExecutionFrameworkInit:
    """Tests for AgentExecutionFramework initialization."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        framework = AgentExecutionFramework()
        assert framework._default_timeout == 60
        assert framework._enable_audit is True

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        framework = AgentExecutionFramework(
            default_timeout=120,
            enable_audit=False,
            evidence_storage_path="/custom/path",
        )
        assert framework._default_timeout == 120
        assert framework._enable_audit is False
        assert framework._evidence_storage_path == "/custom/path"


class TestAgentExecutionFrameworkGetGuardrail:
    """Tests for get_guardrail method."""

    def test_get_guardrail_existing(self):
        """Test getting an existing guardrail."""
        framework = AgentExecutionFramework()
        guardrail = framework.get_guardrail("incident_classifier")
        assert guardrail is not None
        assert guardrail.agent_type == "incident_classifier"

    def test_get_guardrail_missing(self):
        """Test getting a non-existent guardrail raises error."""
        framework = AgentExecutionFramework()
        with pytest.raises(ValueError, match="No guardrail registered"):
            framework.get_guardrail("nonexistent_agent")


class TestAgentExecutionFrameworkValidateGuardrails:
    """Tests for validate_guardrails method."""

    def test_validate_allowed_action(self):
        """Test validation passes for allowed actions."""
        framework = AgentExecutionFramework()
        # incident_classifier allows "classify" action
        framework.validate_guardrails(
            agent_type="incident_classifier",
            proposed_actions=["classify"],
            scope_size=1,
        )
        # No exception = success

    def test_validate_forbidden_action(self):
        """Test validation fails for forbidden actions."""
        framework = AgentExecutionFramework()
        # incident_classifier forbids "modify_incident"
        with pytest.raises(GuardrailViolation, match="Forbidden action"):
            framework.validate_guardrails(
                agent_type="incident_classifier",
                proposed_actions=["modify_incident"],
                scope_size=1,
            )

    def test_validate_unknown_action(self):
        """Test validation fails for actions not in allowed list."""
        framework = AgentExecutionFramework()
        with pytest.raises(GuardrailViolation, match="Action not in allowed list"):
            framework.validate_guardrails(
                agent_type="incident_classifier",
                proposed_actions=["unknown_action"],
                scope_size=1,
            )

    def test_validate_scope_exceeded(self):
        """Test validation fails when scope size exceeds limit."""
        framework = AgentExecutionFramework()
        # incident_classifier has max_scope_size=1
        with pytest.raises(GuardrailViolation, match="Scope size"):
            framework.validate_guardrails(
                agent_type="incident_classifier",
                proposed_actions=["classify"],
                scope_size=100,
            )


class TestAgentExecutionFrameworkInputHash:
    """Tests for input hash computation."""

    def test_compute_input_hash_consistent(self):
        """Test hash is consistent for same input."""
        framework = AgentExecutionFramework()
        data = {"key": "value", "nested": {"a": 1}}
        hash1 = framework._compute_input_hash(data)
        hash2 = framework._compute_input_hash(data)
        assert hash1 == hash2

    def test_compute_input_hash_different(self):
        """Test hash is different for different input."""
        framework = AgentExecutionFramework()
        hash1 = framework._compute_input_hash({"key": "value1"})
        hash2 = framework._compute_input_hash({"key": "value2"})
        assert hash1 != hash2


class TestAgentExecutionFrameworkExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_r1_auto(self):
        """Test R1 (low risk) agent executes automatically."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {"result": "classified", "confidence": 0.95}

        execution_input = ExecutionInput(
            agent_type="incident_classifier",
            input_data={"incident_text": "Test incident"},
            scope_size=1,
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
            proposed_actions=["classify"],
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == {"result": "classified", "confidence": 0.95}
        assert result.confidence == 0.95
        assert result.risk_level == RiskLevel.R1_LOW

    @pytest.mark.asyncio
    async def test_execute_r3_requires_approval(self):
        """Test R3 (high risk) agent requires approval."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {"result": "executed"}

        execution_input = ExecutionInput(
            agent_type="auto_remediator",
            input_data={"script_id": "test-script"},
            scope_size=1,
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
            proposed_actions=["execute_approved_script"],
        )

        assert result.status == ExecutionStatus.AWAITING_APPROVAL
        assert result.requires_approval is True
        assert result.risk_level == RiskLevel.R3_HIGH

    @pytest.mark.asyncio
    async def test_execute_missing_guardrail(self):
        """Test execution blocked for unknown agent type."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {}

        execution_input = ExecutionInput(
            agent_type="unknown_agent",
            input_data={},
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
        )

        assert result.status == ExecutionStatus.BLOCKED
        assert len(result.errors) > 0
        assert "guardrail" in result.errors[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_execute_guardrail_violation(self):
        """Test execution blocked on guardrail violation."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {}

        execution_input = ExecutionInput(
            agent_type="incident_classifier",
            input_data={},
            scope_size=100,  # Exceeds max_scope_size of 1
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
            proposed_actions=["classify"],
        )

        assert result.status == ExecutionStatus.BLOCKED
        assert "guardrail_violation" in result.errors[0]["type"]

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execution timeout handling."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def slow_executor(input_data, context):
            import asyncio

            await asyncio.sleep(100)  # Very slow
            return {}

        # Create a custom guardrail with short timeout
        with patch.dict(
            AGENT_GUARDRAILS,
            {
                "test_agent": AgentGuardrail(
                    agent_type="test_agent",
                    risk_level=RiskLevel.R1_LOW,
                    requires_approval=False,
                    requires_evidence_pack=False,
                    allowed_actions=["test"],
                    forbidden_actions=[],
                    max_scope_size=100,
                    timeout_seconds=1,  # 1 second timeout
                )
            },
        ):
            execution_input = ExecutionInput(
                agent_type="test_agent",
                input_data={},
            )

            result = await framework.execute(
                execution_input=execution_input,
                executor=slow_executor,
                proposed_actions=["test"],
            )

            assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execution handles exceptions gracefully."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def failing_executor(input_data, context):
            raise ValueError("Test error")

        execution_input = ExecutionInput(
            agent_type="incident_classifier",
            input_data={},
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=failing_executor,
            proposed_actions=["classify"],
        )

        assert result.status == ExecutionStatus.FAILED
        assert len(result.errors) > 0
        assert "Test error" in result.errors[0]["message"]


class TestAgentExecutionFrameworkApproval:
    """Tests for approval workflow."""

    @pytest.mark.asyncio
    async def test_approve_execution(self):
        """Test approving a pending execution."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {"result": "executed"}

        execution_input = ExecutionInput(
            agent_type="auto_remediator",
            input_data={},
        )

        # Execute - should be pending approval
        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
            proposed_actions=["execute_approved_script"],
        )

        assert result.status == ExecutionStatus.AWAITING_APPROVAL

        # Approve
        approved = await framework.approve_execution(
            execution_id=result.execution_id,
            approver_id=1,
            notes="Approved for testing",
        )

        assert approved.status == ExecutionStatus.APPROVED

    @pytest.mark.asyncio
    async def test_reject_execution(self):
        """Test rejecting a pending execution."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {}

        execution_input = ExecutionInput(
            agent_type="auto_remediator",
            input_data={},
        )

        result = await framework.execute(
            execution_input=execution_input,
            executor=executor,
            proposed_actions=["execute_approved_script"],
        )

        # Reject
        rejected = await framework.reject_execution(
            execution_id=result.execution_id,
            rejector_id=1,
            reason="Not approved",
        )

        assert rejected.status == ExecutionStatus.REJECTED
        assert any("Not approved" in e.get("message", "") for e in rejected.errors)

    @pytest.mark.asyncio
    async def test_approve_nonexistent(self):
        """Test approving non-existent execution raises error."""
        framework = AgentExecutionFramework(enable_audit=False)

        with pytest.raises(ValueError, match="No pending approval"):
            await framework.approve_execution(
                execution_id="nonexistent",
                approver_id=1,
            )


class TestAgentExecutionFrameworkPendingApprovals:
    """Tests for pending approvals tracking."""

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self):
        """Test getting pending approvals list."""
        framework = AgentExecutionFramework(enable_audit=False)

        async def executor(input_data, context):
            return {}

        # Create two pending executions
        for i in range(2):
            execution_input = ExecutionInput(
                agent_type="auto_remediator",
                input_data={"id": i},
            )
            await framework.execute(
                execution_input=execution_input,
                executor=executor,
                proposed_actions=["execute_approved_script"],
            )

        pending = framework.get_pending_approvals()
        assert len(pending) == 2


class TestGlobalFramework:
    """Tests for global framework singleton."""

    def test_get_execution_framework(self):
        """Test getting global framework instance."""
        framework = get_execution_framework()
        assert framework is not None
        assert isinstance(framework, AgentExecutionFramework)

    def test_set_execution_framework(self):
        """Test setting global framework instance."""
        custom = AgentExecutionFramework(default_timeout=999)
        set_execution_framework(custom)

        retrieved = get_execution_framework()
        assert retrieved._default_timeout == 999

        # Reset to default
        set_execution_framework(AgentExecutionFramework())


class TestGuardrailViolation:
    """Tests for GuardrailViolation exception."""

    def test_guardrail_violation_message(self):
        """Test exception message formatting."""
        guardrail = AGENT_GUARDRAILS["incident_classifier"]
        violation = GuardrailViolation(
            agent_type="incident_classifier",
            violation="Test violation",
            guardrail=guardrail,
        )
        assert "incident_classifier" in str(violation)
        assert "Test violation" in str(violation)


class TestApprovalRequiredError:
    """Tests for ApprovalRequiredError exception."""

    def test_approval_required_message(self):
        """Test exception message formatting."""
        error = ApprovalRequiredError(
            execution_id="exec-123",
            risk_level=RiskLevel.R3_HIGH,
        )
        assert "exec-123" in str(error)
        assert "R3" in str(error)


class TestExecutionInput:
    """Tests for ExecutionInput dataclass."""

    def test_execution_input_defaults(self):
        """Test ExecutionInput default values."""
        input_data = ExecutionInput(
            agent_type="test",
            input_data={"key": "value"},
        )
        assert input_data.context == {}
        assert input_data.correlation_id is None
        assert input_data.scope_size == 1
        assert input_data.force_approval is False


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_defaults(self):
        """Test ExecutionResult default values."""
        result = ExecutionResult(
            execution_id="test-id",
            status=ExecutionStatus.PENDING,
        )
        assert result.output is None
        assert result.confidence is None
        assert result.errors == []
        assert result.risk_level == RiskLevel.R1_LOW
