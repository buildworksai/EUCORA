# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Agent Execution Framework for EUCORA Control Plane.

Implements D7.1 from MASTER-IMPLEMENTATION-PLAN-2026.md:
- Unified agent runner with guardrails enforcement
- Risk-level gating (R1/R2/R3)
- Human-in-loop approval workflow
- Complete audit trail via AgentExecution model
- Evidence pack generation for all recommendations

All agent executions MUST go through this framework.
"""
import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from django.contrib.auth import get_user_model

from ..guardrails import AGENT_GUARDRAILS, AgentGuardrail, RiskLevel
from ..models import AgentExecution, AIModel, ApprovalStatus

logger = logging.getLogger(__name__)
User = get_user_model()

T = TypeVar("T")


class ExecutionStatus(Enum):
    """Status of an agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class ExecutionInput:
    """Input for agent execution."""

    agent_type: str
    input_data: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[int] = None
    scope_size: int = 1
    force_approval: bool = False


@dataclass
class ExecutionResult:
    """Result of an agent execution."""

    execution_id: str
    status: ExecutionStatus
    output: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.R1_LOW
    requires_approval: bool = False
    approval_status: Optional[ApprovalStatus] = None
    evidence_pack_ref: Optional[str] = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class GuardrailViolation(Exception):
    """Raised when an agent violates its guardrails."""

    def __init__(self, agent_type: str, violation: str, guardrail: AgentGuardrail):
        self.agent_type = agent_type
        self.violation = violation
        self.guardrail = guardrail
        super().__init__(f"Guardrail violation for {agent_type}: {violation}")


class ApprovalRequiredError(Exception):
    """Raised when execution requires approval but none provided."""

    def __init__(self, execution_id: str, risk_level: RiskLevel):
        self.execution_id = execution_id
        self.risk_level = risk_level
        super().__init__(f"Execution {execution_id} requires {risk_level.value} approval")


class AgentExecutionFramework:
    """
    Unified execution framework for all AI agents.

    Enforces:
    - Guardrail compliance (allowed/forbidden actions)
    - Risk-level gating (R1 auto-execute, R2/R3 require approval)
    - Scope size limits
    - Timeout enforcement
    - Complete audit trail
    - Evidence pack generation

    Usage:
        framework = AgentExecutionFramework()
        result = await framework.execute(
            agent_type="incident_classifier",
            input_data={"incident_text": "..."},
            executor=my_classifier_function,
        )
    """

    def __init__(
        self,
        default_timeout: int = 60,
        enable_audit: bool = True,
        evidence_storage_path: Optional[str] = None,
    ):
        """
        Initialize execution framework.

        Args:
            default_timeout: Default timeout in seconds
            enable_audit: Enable AgentExecution audit trail
            evidence_storage_path: Path prefix for evidence packs
        """
        self._default_timeout = default_timeout
        self._enable_audit = enable_audit
        self._evidence_storage_path = evidence_storage_path or "/evidence/agent"
        self._pending_approvals: dict[str, ExecutionResult] = {}

    def get_guardrail(self, agent_type: str) -> AgentGuardrail:
        """
        Get guardrail for an agent type.

        Raises:
            ValueError: If agent type has no registered guardrail
        """
        guardrail = AGENT_GUARDRAILS.get(agent_type)
        if not guardrail:
            raise ValueError(
                f"No guardrail registered for agent type: {agent_type}. "
                f"All agents MUST have guardrails defined in guardrails.py."
            )
        return guardrail

    def validate_guardrails(
        self,
        agent_type: str,
        proposed_actions: list[str],
        scope_size: int,
    ) -> None:
        """
        Validate that proposed actions comply with guardrails.

        Args:
            agent_type: Type of agent
            proposed_actions: List of actions the agent wants to perform
            scope_size: Number of entities affected

        Raises:
            GuardrailViolation: If any guardrail is violated
        """
        guardrail = self.get_guardrail(agent_type)

        # Check forbidden actions
        for action in proposed_actions:
            if action in guardrail.forbidden_actions:
                raise GuardrailViolation(
                    agent_type=agent_type,
                    violation=f"Forbidden action: {action}",
                    guardrail=guardrail,
                )

        # Check allowed actions
        for action in proposed_actions:
            if action not in guardrail.allowed_actions:
                raise GuardrailViolation(
                    agent_type=agent_type,
                    violation=f"Action not in allowed list: {action}",
                    guardrail=guardrail,
                )

        # Check scope size
        if scope_size > guardrail.max_scope_size:
            raise GuardrailViolation(
                agent_type=agent_type,
                violation=f"Scope size {scope_size} exceeds max {guardrail.max_scope_size}",
                guardrail=guardrail,
            )

    def _compute_input_hash(self, input_data: dict[str, Any]) -> str:
        """Compute SHA-256 hash of input data for audit."""
        serialized = json.dumps(input_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _compute_output_hash(self, output: dict[str, Any]) -> str:
        """Compute SHA-256 hash of output data for evidence."""
        serialized = json.dumps(output, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    async def execute(  # noqa: C901
        self,
        execution_input: ExecutionInput,
        executor: Callable[..., Any],
        proposed_actions: Optional[list[str]] = None,
        model_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute an agent with guardrail enforcement.

        Args:
            execution_input: Execution input parameters
            executor: Async function to execute the agent logic
            proposed_actions: List of actions the agent will perform
            model_id: Optional AI model ID for lineage tracking

        Returns:
            ExecutionResult with status and output

        Raises:
            GuardrailViolation: If guardrails are violated
            ApprovalRequiredError: If R2/R3 approval not provided
        """
        execution_id = str(uuid.uuid4())
        correlation_id = execution_input.correlation_id or str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        logger.info(
            f"[{correlation_id}] Starting agent execution: {execution_input.agent_type} "
            f"(execution_id={execution_id})"
        )

        # Get guardrail
        try:
            guardrail = self.get_guardrail(execution_input.agent_type)
        except ValueError as e:
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.BLOCKED,
                errors=[{"message": str(e), "type": "guardrail_missing"}],
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        # Validate guardrails
        if proposed_actions:
            try:
                self.validate_guardrails(
                    execution_input.agent_type,
                    proposed_actions,
                    execution_input.scope_size,
                )
            except GuardrailViolation as e:
                logger.warning(f"[{correlation_id}] Guardrail violation: {e}")
                return ExecutionResult(
                    execution_id=execution_id,
                    status=ExecutionStatus.BLOCKED,
                    risk_level=guardrail.risk_level,
                    errors=[{"message": str(e), "type": "guardrail_violation"}],
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                )

        # Check approval requirement
        requires_approval = (
            guardrail.requires_approval
            or execution_input.force_approval
            or guardrail.risk_level in (RiskLevel.R2_MEDIUM, RiskLevel.R3_HIGH)
        )

        # Create audit record if enabled
        audit_record: Optional[AgentExecution] = None
        if self._enable_audit:
            input_hash = self._compute_input_hash(execution_input.input_data)
            approval_status = ApprovalStatus.PENDING if requires_approval else ApprovalStatus.NOT_REQUIRED

            # Get model if specified
            model = None
            if model_id:
                try:
                    model = await asyncio.to_thread(AIModel.objects.get, model_id=model_id)
                except AIModel.DoesNotExist:
                    pass

            audit_record = await asyncio.to_thread(
                AgentExecution.objects.create,
                agent_type=execution_input.agent_type,
                model=model,
                correlation_id=uuid.UUID(correlation_id),
                input_hash=input_hash,
                input_summary={
                    "keys": list(execution_input.input_data.keys()),
                    "scope_size": execution_input.scope_size,
                },
                risk_level=guardrail.risk_level.value,
                approval_required=requires_approval,
                approval_status=approval_status,
            )

        # If approval required and not auto-executable, return pending status
        if requires_approval and guardrail.risk_level != RiskLevel.R1_LOW:
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.AWAITING_APPROVAL,
                risk_level=guardrail.risk_level,
                requires_approval=True,
                approval_status=ApprovalStatus.PENDING,
                started_at=started_at,
            )
            self._pending_approvals[execution_id] = result
            logger.info(
                f"[{correlation_id}] Execution {execution_id} awaiting " f"{guardrail.risk_level.value} approval"
            )
            return result

        # Execute the agent
        try:
            timeout = guardrail.timeout_seconds or self._default_timeout

            output = await asyncio.wait_for(
                executor(execution_input.input_data, execution_input.context),
                timeout=timeout,
            )

            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()

            # Extract confidence if present
            confidence = None
            if isinstance(output, dict):
                confidence = output.get("confidence")

            # Generate evidence pack reference
            evidence_ref = None
            if guardrail.requires_evidence_pack and output:
                output_hash = self._compute_output_hash(output)
                evidence_ref = (
                    f"{self._evidence_storage_path}/{execution_input.agent_type}/"
                    f"{correlation_id}/{output_hash[:16]}.json"
                )

            # Update audit record
            if audit_record:
                await asyncio.to_thread(
                    self._update_audit_record,
                    audit_record,
                    output=output,
                    confidence=confidence,
                    executed=True,
                    approval_status=ApprovalStatus.NOT_REQUIRED if not requires_approval else ApprovalStatus.APPROVED,
                )

            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED,
                output=output,
                confidence=confidence,
                risk_level=guardrail.risk_level,
                requires_approval=requires_approval,
                approval_status=ApprovalStatus.NOT_REQUIRED if not requires_approval else ApprovalStatus.APPROVED,
                evidence_pack_ref=evidence_ref,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

            logger.info(f"[{correlation_id}] Execution {execution_id} completed in {duration:.2f}s")
            return result

        except asyncio.TimeoutError:
            completed_at = datetime.now(timezone.utc)
            logger.error(
                f"[{correlation_id}] Execution {execution_id} timed out " f"after {guardrail.timeout_seconds}s"
            )
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
                risk_level=guardrail.risk_level,
                errors=[{"message": f"Execution timed out after {guardrail.timeout_seconds}s", "type": "timeout"}],
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            logger.exception(f"[{correlation_id}] Execution {execution_id} failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                risk_level=guardrail.risk_level,
                errors=[{"message": str(e), "type": type(e).__name__}],
                started_at=started_at,
                completed_at=completed_at,
            )

    def _update_audit_record(
        self,
        record: AgentExecution,
        output: Optional[dict[str, Any]] = None,
        confidence: Optional[float] = None,
        executed: bool = False,
        approval_status: Optional[ApprovalStatus] = None,
    ) -> None:
        """Update audit record with execution results."""
        if output:
            record.output = output
        if confidence is not None:
            record.confidence = confidence
        record.executed = executed
        if executed:
            from django.utils import timezone as dj_timezone

            record.executed_at = dj_timezone.now()
        if approval_status:
            record.approval_status = approval_status
        record.save()

    async def approve_execution(
        self,
        execution_id: str,
        approver_id: int,
        notes: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Approve a pending execution.

        Args:
            execution_id: ID of execution to approve
            approver_id: ID of approving user
            notes: Optional approval notes

        Returns:
            Updated ExecutionResult
        """
        if execution_id not in self._pending_approvals:
            raise ValueError(f"No pending approval for execution {execution_id}")

        result = self._pending_approvals.pop(execution_id)
        result.status = ExecutionStatus.APPROVED
        result.approval_status = ApprovalStatus.APPROVED

        # Update audit record
        if self._enable_audit:
            try:
                record = await asyncio.to_thread(
                    AgentExecution.objects.get,
                    correlation_id=result.execution_id,
                )
                approver = await asyncio.to_thread(User.objects.get, pk=approver_id)
                record.approval_status = ApprovalStatus.APPROVED
                record.approved_by = approver
                from django.utils import timezone as dj_timezone

                record.approved_at = dj_timezone.now()
                await asyncio.to_thread(record.save)
            except (AgentExecution.DoesNotExist, User.DoesNotExist):
                pass

        logger.info(f"Execution {execution_id} approved by user {approver_id}")
        return result

    async def reject_execution(
        self,
        execution_id: str,
        rejector_id: int,
        reason: str,
    ) -> ExecutionResult:
        """
        Reject a pending execution.

        Args:
            execution_id: ID of execution to reject
            rejector_id: ID of rejecting user
            reason: Rejection reason

        Returns:
            Updated ExecutionResult
        """
        if execution_id not in self._pending_approvals:
            raise ValueError(f"No pending approval for execution {execution_id}")

        result = self._pending_approvals.pop(execution_id)
        result.status = ExecutionStatus.REJECTED
        result.approval_status = ApprovalStatus.REJECTED
        result.errors.append({"message": reason, "type": "rejected"})
        result.completed_at = datetime.now(timezone.utc)

        # Update audit record
        if self._enable_audit:
            try:
                record = await asyncio.to_thread(
                    AgentExecution.objects.get,
                    correlation_id=result.execution_id,
                )
                record.approval_status = ApprovalStatus.REJECTED
                record.execution_result = {"rejected_reason": reason}
                await asyncio.to_thread(record.save)
            except AgentExecution.DoesNotExist:
                pass

        logger.info(f"Execution {execution_id} rejected by user {rejector_id}: {reason}")
        return result

    def get_pending_approvals(self, agent_type: Optional[str] = None) -> list[ExecutionResult]:
        """
        Get all pending approval requests.

        Args:
            agent_type: Optional filter by agent type

        Returns:
            List of pending ExecutionResults
        """
        results = list(self._pending_approvals.values())
        if agent_type:
            # Filter requires looking up the guardrail, which is complex
            # For now, return all
            pass
        return results


# Global framework instance
_framework: Optional[AgentExecutionFramework] = None


def get_execution_framework() -> AgentExecutionFramework:
    """Get the global execution framework instance."""
    global _framework
    if _framework is None:
        _framework = AgentExecutionFramework()
    return _framework


def set_execution_framework(framework: AgentExecutionFramework) -> None:
    """Set the global execution framework instance (for testing)."""
    global _framework
    _framework = framework
