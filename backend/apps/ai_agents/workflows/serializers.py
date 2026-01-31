# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for workflow models.
"""
from rest_framework import serializers

from .models import WorkflowDefinition, WorkflowExecution, WorkflowStep


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowStep."""

    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = WorkflowStep
        fields = [
            "id",
            "step_index",
            "name",
            "description",
            "step_type",
            "status",
            "input_data",
            "output_data",
            "policies_considered",
            "prompt_used",
            "llm_response",
            "tokens_used",
            "error_message",
            "started_at",
            "completed_at",
            "duration_seconds",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "started_at",
            "completed_at",
            "duration_seconds",
        ]


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowDefinition."""

    class Meta:
        model = WorkflowDefinition
        fields = [
            "id",
            "agent_type",
            "name",
            "description",
            "steps",
            "required_policies",
            "risk_level",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowExecution with nested steps."""

    workflow = WorkflowDefinitionSerializer(read_only=True)
    steps = WorkflowStepSerializer(many=True, read_only=True)
    initiated_by_username = serializers.CharField(source="initiated_by.username", read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "correlation_id",
            "workflow",
            "initiated_by",
            "initiated_by_username",
            "status",
            "current_step_index",
            "input_data",
            "output_data",
            "policy_context",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "rejection_reason",
            "started_at",
            "completed_at",
            "steps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
            "approved_at",
        ]


class StartWorkflowSerializer(serializers.Serializer):
    """Serializer for starting a workflow."""

    input_data = serializers.JSONField(required=True, help_text="Input data for workflow execution")


class ApproveWorkflowStepSerializer(serializers.Serializer):
    """Serializer for approving a workflow step."""

    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional approval notes")


class RejectWorkflowStepSerializer(serializers.Serializer):
    """Serializer for rejecting a workflow step."""

    reason = serializers.CharField(required=True, help_text="Rejection reason")
