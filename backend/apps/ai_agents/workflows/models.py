# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Workflow models for AI Agent multi-step execution.

Implements E8: AI Agent Workflows specification.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models

from apps.ai_agents.models import AIAgentType
from apps.core.models import CorrelationIdModel, TimeStampedModel


class WorkflowDefinition(TimeStampedModel):
    """
    Defines a multi-step workflow template for an agent.

    Workflows consist of sequential steps that can be:
    - ai_action: LLM-powered step with policy context
    - approval_gate: Requires human approval before proceeding
    - user_input: Requires user input before proceeding
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices, db_index=True)
    name = models.CharField(max_length=128)
    description = models.TextField()

    # Steps as JSON schema
    # Each step: {name, type, description, instructions, task, output_schema, policy_tags, risk_level}
    steps = models.JSONField(default=list, help_text="List of step definitions")

    # Policy requirements - categories to retrieve for this workflow
    required_policies = models.JSONField(
        default=list, help_text="Policy categories to retrieve (e.g., ['application', 'security'])"
    )

    # Overall workflow risk level (R1, R2, R3)
    risk_level = models.CharField(
        max_length=4,
        choices=[
            ("R1", "R1 - Low Risk (Autonomous)"),
            ("R2", "R2 - Medium Risk (Policy-Dependent)"),
            ("R3", "R3 - High Risk (Mandatory Approval)"),
        ],
        default="R2",
        db_index=True,
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Workflow Definition"
        verbose_name_plural = "Workflow Definitions"
        indexes = [
            models.Index(fields=["agent_type", "is_active"]),
            models.Index(fields=["risk_level", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.agent_type})"


class WorkflowExecution(TimeStampedModel, CorrelationIdModel):
    """
    Instance of a workflow being executed.

    Tracks the execution state, current step, and policy context
    used throughout the workflow.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="executions")

    # Execution context
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workflow_executions")
    input_data = models.JSONField(default=dict, help_text="Input data for workflow execution")
    output_data = models.JSONField(default=dict, help_text="Final output data from workflow")

    # Status tracking
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    current_step_index = models.IntegerField(default=0, help_text="Index of current step being executed")

    # Policy context used throughout workflow
    policy_context = models.JSONField(default=list, help_text="Retrieved policy chunks used in workflow execution")

    # Approval tracking
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_workflow_executions",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Workflow Execution"
        verbose_name_plural = "Workflow Executions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["initiated_by", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["workflow", "status"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.status} ({self.initiated_by.username})"


class WorkflowStep(TimeStampedModel):
    """
    Individual step execution within a workflow.

    Each step tracks its execution state, LLM interactions,
    policy context used, and output data.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        AWAITING_INPUT = "awaiting_input", "Awaiting User Input"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Approval"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name="steps")
    step_index = models.IntegerField(help_text="Index of this step in workflow definition")

    # Step definition (cached from workflow definition)
    name = models.CharField(max_length=128)
    description = models.TextField()
    step_type = models.CharField(
        max_length=32,
        choices=[
            ("ai_action", "AI Action"),
            ("approval_gate", "Approval Gate"),
            ("user_input", "User Input"),
        ],
    )

    # Input/Output
    input_data = models.JSONField(default=dict, help_text="Input data for this step")
    output_data = models.JSONField(default=dict, help_text="Output data from this step")

    # Policy context for this step
    policies_considered = models.JSONField(default=list, help_text="Policy chunks considered for this step")

    # LLM interaction details
    prompt_used = models.TextField(blank=True, help_text="Prompt sent to LLM")
    llm_response = models.TextField(blank=True, help_text="Response from LLM")
    tokens_used = models.IntegerField(default=0, help_text="Tokens consumed")

    # Status
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    error_message = models.TextField(blank=True, help_text="Error message if step failed")

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Workflow Step"
        verbose_name_plural = "Workflow Steps"
        ordering = ["step_index"]
        indexes = [
            models.Index(fields=["execution", "step_index"]),
            models.Index(fields=["status", "created_at"]),
        ]
        unique_together = [["execution", "step_index"]]

    def __str__(self):
        return f"{self.execution.workflow.name} - Step {self.step_index}: {self.name} ({self.status})"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate step duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
