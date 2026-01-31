# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for AI Agent Workflows.
"""
import logging

from asgiref.sync import async_to_sync
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.rbac.permissions import RBACPermission

from .executor import WorkflowExecutor
from .models import WorkflowDefinition, WorkflowExecution
from .serializers import (
    ApproveWorkflowStepSerializer,
    RejectWorkflowStepSerializer,
    StartWorkflowSerializer,
    WorkflowDefinitionSerializer,
    WorkflowExecutionSerializer,
)

logger = logging.getLogger(__name__)


class WorkflowDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for workflow definitions.

    Provides read-only access to available workflow definitions.
    """

    queryset = WorkflowDefinition.objects.filter(is_active=True)
    serializer_class = WorkflowDefinitionSerializer
    permission_classes = [RBACPermission("ai_agents", "read")]

    @action(detail=True, methods=["post"], permission_classes=[RBACPermission("ai_agents", "create")])
    def start(self, request, pk=None) -> Response:
        """
        Start a workflow execution.

        POST /api/v1/ai/workflows/{id}/start/
        """
        workflow = self.get_object()
        serializer = StartWorkflowSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        input_data = serializer.validated_data["input_data"]

        try:
            # Start workflow asynchronously (using async_to_sync for compatibility with running event loops)
            executor = WorkflowExecutor()
            execution = async_to_sync(executor.start_workflow)(workflow, request.user, input_data)

            execution_serializer = WorkflowExecutionSerializer(execution)
            return Response(execution_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"Error starting workflow {workflow.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for workflow executions.

    Provides CRUD operations for workflow executions with approval actions.
    """

    serializer_class = WorkflowExecutionSerializer
    permission_classes = [RBACPermission("ai_agents", "read")]

    def get_queryset(self):
        """Filter executions by current user."""
        queryset = WorkflowExecution.objects.all()

        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(initiated_by=self.request.user)

        # Filter by correlation_id if provided
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        return queryset.select_related("workflow", "initiated_by", "approved_by").prefetch_related("steps")

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "approve", "reject", "cancel"]:
            return [RBACPermission("ai_agents", "create")()]
        return [RBACPermission("ai_agents", "read")()]

    @action(detail=True, methods=["post"], permission_classes=[RBACPermission("ai_agents", "create")])
    def approve(self, request, pk=None) -> Response:
        """
        Approve current workflow step.

        POST /api/v1/ai/executions/{id}/approve/
        """
        execution = self.get_object()

        if execution.status != WorkflowExecution.Status.AWAITING_APPROVAL:
            return Response(
                {"error": f"Cannot approve workflow in status {execution.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApproveWorkflowStepSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            executor = WorkflowExecutor()
            notes = serializer.validated_data.get("notes", "")

            with transaction.atomic():
                updated_execution = async_to_sync(executor.approve_step)(execution, request.user, notes)

            execution_serializer = WorkflowExecutionSerializer(updated_execution)
            return Response(execution_serializer.data)

        except Exception as e:
            logger.exception(f"Error approving workflow {execution.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], permission_classes=[RBACPermission("ai_agents", "create")])
    def reject(self, request, pk=None) -> Response:
        """
        Reject current workflow step.

        POST /api/v1/ai/executions/{id}/reject/
        """
        execution = self.get_object()

        if execution.status != WorkflowExecution.Status.AWAITING_APPROVAL:
            return Response(
                {"error": f"Cannot reject workflow in status {execution.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RejectWorkflowStepSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            executor = WorkflowExecutor()
            reason = serializer.validated_data["reason"]

            with transaction.atomic():
                updated_execution = async_to_sync(executor.reject_step)(execution, request.user, reason)

            execution_serializer = WorkflowExecutionSerializer(updated_execution)
            return Response(execution_serializer.data)

        except Exception as e:
            logger.exception(f"Error rejecting workflow {execution.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], permission_classes=[RBACPermission("ai_agents", "create")])
    def cancel(self, request, pk=None) -> Response:
        """
        Cancel workflow execution.

        POST /api/v1/ai/executions/{id}/cancel/
        """
        execution = self.get_object()

        if execution.status in [
            WorkflowExecution.Status.COMPLETED,
            WorkflowExecution.Status.FAILED,
            WorkflowExecution.Status.CANCELLED,
        ]:
            return Response(
                {"error": f"Cannot cancel workflow in status {execution.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            execution.status = WorkflowExecution.Status.CANCELLED
            execution.save()

            execution_serializer = WorkflowExecutionSerializer(execution)
            return Response(execution_serializer.data)

        except Exception as e:
            logger.exception(f"Error cancelling workflow {execution.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
