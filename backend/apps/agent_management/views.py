# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
REST API views for agent management.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import TelemetryCursorPagination

from .models import Agent, AgentDeploymentStatus, AgentTask, AgentTelemetry
from .serializers import (
    AgentDeploymentStatusSerializer,
    AgentRegistrationSerializer,
    AgentSerializer,
    AgentTaskCreateSerializer,
    AgentTaskSerializer,
    AgentTaskStatusUpdateSerializer,
    AgentTelemetrySerializer,
    AgentTelemetrySubmitSerializer,
)
from .services import AgentManagementService


class AgentViewSet(viewsets.ModelViewSet):
    """ViewSet for agent management."""

    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset by query parameters."""
        queryset = super().get_queryset()

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(platform=platform)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter online/offline
        is_online = self.request.query_params.get("is_online")
        if is_online == "true":
            from datetime import timedelta

            from django.utils import timezone

            cutoff = timezone.now() - timedelta(minutes=5)
            queryset = queryset.filter(last_heartbeat_at__gte=cutoff)
        elif is_online == "false":
            from datetime import timedelta

            from django.utils import timezone

            cutoff = timezone.now() - timedelta(minutes=5)
            queryset = queryset.filter(last_heartbeat_at__lt=cutoff)

        return queryset

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Agent registration endpoint."""
        serializer = AgentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        agent = service.register_agent(**serializer.validated_data, correlation_id=correlation_id)

        return Response(AgentSerializer(agent).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def heartbeat(self, request, pk=None):
        """Agent heartbeat endpoint."""
        correlation_id = request.headers.get("X-Correlation-ID", "")
        service = AgentManagementService()

        try:
            result = service.process_heartbeat(agent_id=str(pk), correlation_id=correlation_id)
            return Response(result)
        except Agent.DoesNotExist:
            return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def tasks(self, request, pk=None):
        """Get agent's tasks."""
        agent = self.get_object()
        tasks = agent.tasks.all()[:100]
        serializer = AgentTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def telemetry(self, request, pk=None):
        """Get agent's telemetry data."""
        agent = self.get_object()
        telemetry = agent.telemetry.all()[:100]
        serializer = AgentTelemetrySerializer(telemetry, many=True)
        return Response(serializer.data)


class AgentTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for agent task management."""

    queryset = AgentTask.objects.all()
    serializer_class = AgentTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset by query parameters."""
        queryset = super().get_queryset()

        # Filter by agent
        agent_id = self.request.query_params.get("agent_id")
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        # Filter by task type
        task_type = self.request.query_params.get("task_type")
        if task_type:
            queryset = queryset.filter(task_type=task_type)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by correlation ID
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        return queryset.select_related("agent", "created_by")

    def create(self, request):
        """Create a new agent task."""
        serializer = AgentTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        task = service.create_task(
            agent_id=str(serializer.validated_data["agent_id"]),
            task_type=serializer.validated_data["task_type"],
            payload=serializer.validated_data["payload"],
            timeout_seconds=serializer.validated_data.get("timeout_seconds", 3600),
            created_by=request.user,
            correlation_id=correlation_id,
        )

        return Response(AgentTaskSerializer(task).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Mark task as started."""
        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        task = service.update_task_status(task_id=str(pk), status="IN_PROGRESS", correlation_id=correlation_id)

        return Response(AgentTaskSerializer(task).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark task as completed with results."""
        serializer = AgentTaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        task = service.update_task_status(
            task_id=str(pk),
            status="COMPLETED",
            result=serializer.validated_data.get("result"),
            exit_code=serializer.validated_data.get("exit_code"),
            correlation_id=correlation_id,
        )

        return Response(AgentTaskSerializer(task).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        """Mark task as failed with error."""
        serializer = AgentTaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        task = service.update_task_status(
            task_id=str(pk),
            status="FAILED",
            error_message=serializer.validated_data.get("error_message"),
            exit_code=serializer.validated_data.get("exit_code"),
            correlation_id=correlation_id,
        )

        return Response(AgentTaskSerializer(task).data)


class AgentTelemetryViewSet(viewsets.ModelViewSet):
    """ViewSet for telemetry data."""

    queryset = AgentTelemetry.objects.all()
    serializer_class = AgentTelemetrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TelemetryCursorPagination

    def get_queryset(self):
        """Filter by agent."""
        queryset = super().get_queryset()

        agent_id = self.request.query_params.get("agent_id")
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        return queryset.select_related("agent")

    def create(self, request):
        """Submit telemetry data."""
        serializer = AgentTelemetrySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AgentManagementService()
        correlation_id = request.headers.get("X-Correlation-ID", "")

        telemetry = service.store_telemetry(**serializer.validated_data, correlation_id=correlation_id)

        return Response(AgentTelemetrySerializer(telemetry).data, status=status.HTTP_201_CREATED)


class AgentDeploymentStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for deployment status tracking."""

    queryset = AgentDeploymentStatus.objects.all()
    serializer_class = AgentDeploymentStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by query parameters."""
        queryset = super().get_queryset()

        agent_id = self.request.query_params.get("agent_id")
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        deployment_intent_id = self.request.query_params.get("deployment_intent_id")
        if deployment_intent_id:
            queryset = queryset.filter(deployment_intent_id=deployment_intent_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related("agent")
