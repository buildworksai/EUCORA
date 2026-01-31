# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for SRE Agent.
"""
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    HealthCheckResult,
    HealthEndpoint,
    MonitoringPlatform,
    Runbook,
    RunbookExecution,
    SelfHealingExecution,
    SelfHealingRule,
    SLODefinition,
    SLOMetric,
)
from .serializers import (
    HealthCheckResultSerializer,
    HealthEndpointSerializer,
    MonitoringPlatformSerializer,
    RunbookExecutionSerializer,
    RunbookSerializer,
    SelfHealingExecutionSerializer,
    SelfHealingRuleSerializer,
    SLODefinitionSerializer,
    SLOMetricSerializer,
)
from .services import SelfHealingService

logger = logging.getLogger(__name__)


class MonitoringPlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for monitoring platforms."""

    queryset = MonitoringPlatform.objects.all()
    serializer_class = MonitoringPlatformSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by platform_type and is_active."""
        queryset = MonitoringPlatform.objects.all()
        platform_type = self.request.query_params.get("platform_type")
        if platform_type:
            queryset = queryset.filter(platform_type=platform_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test platform connection."""
        # TODO: Implement connection test
        return Response({"success": True})


class HealthEndpointViewSet(viewsets.ModelViewSet):
    """ViewSet for health endpoints."""

    queryset = HealthEndpoint.objects.select_related("application")
    serializer_class = HealthEndpointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by is_active and application."""
        queryset = HealthEndpoint.objects.select_related("application")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        application_id = self.request.query_params.get("application_id")
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def check(self, request: Request, pk=None) -> Response:
        """Perform health check."""
        endpoint = self.get_object()
        # TODO: Implement actual health check
        result = HealthCheckResult.objects.create(
            endpoint=endpoint,
            status=HealthCheckResult.Status.HEALTHY,
            response_time_ms=100,
            status_code=200,
        )
        serializer = HealthCheckResultSerializer(result)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def history(self, request: Request, pk=None) -> Response:
        """Get health check history."""
        endpoint = self.get_object()
        limit = int(request.query_params.get("limit", 50))
        results = endpoint.check_results.order_by("-check_time")[:limit]
        serializer = HealthCheckResultSerializer(results, many=True)
        return Response(serializer.data)


class HealthCheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for health check results."""

    queryset = HealthCheckResult.objects.select_related("endpoint")
    serializer_class = HealthCheckResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by endpoint and status."""
        queryset = HealthCheckResult.objects.select_related("endpoint")
        endpoint_id = self.request.query_params.get("endpoint_id")
        if endpoint_id:
            queryset = queryset.filter(endpoint_id=endpoint_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-check_time")


class SLODefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for SLO definitions."""

    queryset = SLODefinition.objects.all()
    serializer_class = SLODefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by service_name, slo_type, and is_active."""
        queryset = SLODefinition.objects.all()
        service_name = self.request.query_params.get("service_name")
        if service_name:
            queryset = queryset.filter(service_name=service_name)
        slo_type = self.request.query_params.get("slo_type")
        if slo_type:
            queryset = queryset.filter(slo_type=slo_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["get"])
    def metrics(self, request: Request, pk=None) -> Response:
        """Get SLO metrics."""
        slo = self.get_object()
        limit = int(request.query_params.get("limit", 100))
        metrics = slo.metrics.order_by("-measurement_time")[:limit]
        serializer = SLOMetricSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def error_budget(self, request: Request, pk=None) -> Response:
        """Get error budget status."""
        slo = self.get_object()
        recent_metric = slo.metrics.order_by("-measurement_time").first()
        if recent_metric:
            return Response(
                {
                    "error_budget_remaining": recent_metric.error_budget_remaining,
                    "burn_rate": recent_metric.burn_rate,
                    "target_met": recent_metric.target_met,
                }
            )
        return Response({"error_budget_remaining": None, "burn_rate": None, "target_met": None})


class SLOMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SLO metrics."""

    queryset = SLOMetric.objects.select_related("slo")
    serializer_class = SLOMetricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by slo."""
        queryset = SLOMetric.objects.select_related("slo")
        slo_id = self.request.query_params.get("slo_id")
        if slo_id:
            queryset = queryset.filter(slo_id=slo_id)
        return queryset.order_by("-measurement_time")


class SelfHealingRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for self-healing rules."""

    queryset = SelfHealingRule.objects.all()
    serializer_class = SelfHealingRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by is_active, trigger_type, and risk_level."""
        queryset = SelfHealingRule.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        trigger_type = self.request.query_params.get("trigger_type")
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test self-healing rule."""
        # TODO: Implement rule test
        return Response({"success": True})

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk=None) -> Response:
        """Execute self-healing rule."""
        rule = self.get_object()
        trigger_event = request.data.get("trigger_event", {})

        execution = SelfHealingExecution.objects.create(
            rule=rule,
            trigger_event=trigger_event,
            status=SelfHealingExecution.Status.PENDING,
        )

        if rule.requires_approval:
            execution.status = SelfHealingExecution.Status.PENDING
        else:
            execution.status = SelfHealingExecution.Status.APPROVED
            execution.save()
            # Execute remediation script
            service = SelfHealingService()
            execution = service.execute(execution)

        execution.save()
        serializer = SelfHealingExecutionSerializer(execution)
        return Response(serializer.data)


class SelfHealingExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for self-healing executions."""

    queryset = SelfHealingExecution.objects.select_related("rule", "approved_by")
    serializer_class = SelfHealingExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, and rule."""
        queryset = SelfHealingExecution.objects.select_related("rule", "approved_by")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        rule_id = self.request.query_params.get("rule_id")
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve execution and trigger script execution."""
        execution = self.get_object()
        execution.status = SelfHealingExecution.Status.APPROVED
        execution.approved_by = request.user
        execution.save()
        # Execute remediation script after approval
        service = SelfHealingService()
        execution = service.execute(execution)
        serializer = self.get_serializer(execution)
        return Response(serializer.data)


class RunbookViewSet(viewsets.ModelViewSet):
    """ViewSet for runbooks."""

    queryset = Runbook.objects.all()
    serializer_class = RunbookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by category, risk_level, and is_active."""
        queryset = Runbook.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk=None) -> Response:
        """Execute runbook."""
        runbook = self.get_object()
        trigger_reason = request.data.get("trigger_reason", "")

        execution = RunbookExecution.objects.create(
            runbook=runbook,
            executed_by=request.user,
            trigger_reason=trigger_reason,
            status=RunbookExecution.Status.PENDING,
        )

        # TODO: Execute runbook steps
        execution.status = RunbookExecution.Status.IN_PROGRESS
        execution.started_at = timezone.now()
        execution.save()

        serializer = RunbookExecutionSerializer(execution)
        return Response(serializer.data)


class RunbookExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for runbook executions."""

    queryset = RunbookExecution.objects.select_related("runbook", "executed_by")
    serializer_class = RunbookExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, status, and runbook."""
        queryset = RunbookExecution.objects.select_related("runbook", "executed_by")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        runbook_id = self.request.query_params.get("runbook_id")
        if runbook_id:
            queryset = queryset.filter(runbook_id=runbook_id)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def step_complete(self, request: Request, pk=None) -> Response:
        """Mark step as complete."""
        execution = self.get_object()
        step_number = request.data.get("step_number")
        notes = request.data.get("notes", "")

        step_results = execution.step_results or []
        step_results.append({"step": step_number, "completed_at": timezone.now().isoformat(), "notes": notes})
        execution.step_results = step_results
        execution.current_step = step_number + 1

        if execution.current_step >= len(execution.runbook.steps):
            execution.status = RunbookExecution.Status.COMPLETED
            execution.completed_at = timezone.now()

        execution.save()
        serializer = self.get_serializer(execution)
        return Response(serializer.data)


class SREReportsViewSet(viewsets.ViewSet):
    """ViewSet for SRE reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def overview(self, request: Request) -> Response:
        """Get SRE overview statistics."""
        healthy_endpoints = HealthCheckResult.objects.filter(status=HealthCheckResult.Status.HEALTHY).count()
        unhealthy_endpoints = HealthCheckResult.objects.filter(status=HealthCheckResult.Status.UNHEALTHY).count()

        active_slos = SLODefinition.objects.filter(is_active=True).count()
        compliant_slos = SLOMetric.objects.filter(target_met=True).values("slo").distinct().count()

        active_rules = SelfHealingRule.objects.filter(is_active=True).count()
        recent_executions = SelfHealingExecution.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        return Response(
            {
                "healthy_endpoints": healthy_endpoints,
                "unhealthy_endpoints": unhealthy_endpoints,
                "active_slos": active_slos,
                "compliant_slos": compliant_slos,
                "active_healing_rules": active_rules,
                "recent_executions": recent_executions,
            }
        )

    @action(detail=False, methods=["get"])
    def slo_status(self, request: Request) -> Response:
        """Get SLO status summary."""
        slos = SLODefinition.objects.filter(is_active=True)
        status_data = []

        for slo in slos:
            recent_metric = slo.metrics.order_by("-measurement_time").first()
            status_data.append(
                {
                    "slo_id": str(slo.id),
                    "name": slo.name,
                    "service_name": slo.service_name,
                    "slo_type": slo.slo_type,
                    "target_value": slo.target_value,
                    "current_value": recent_metric.actual_value if recent_metric else None,
                    "target_met": recent_metric.target_met if recent_metric else None,
                    "error_budget_remaining": recent_metric.error_budget_remaining if recent_metric else None,
                }
            )

        return Response({"slo_status": status_data})

    @action(detail=False, methods=["get"])
    def healing_activity(self, request: Request) -> Response:
        """Get self-healing activity summary."""
        days = int(request.query_params.get("days", 7))
        since = timezone.now() - timedelta(days=days)

        executions = SelfHealingExecution.objects.filter(created_at__gte=since)

        success_count = executions.filter(status=SelfHealingExecution.Status.COMPLETED).count()
        failed_count = executions.filter(status=SelfHealingExecution.Status.FAILED).count()
        pending_count = executions.filter(status=SelfHealingExecution.Status.PENDING).count()

        return Response(
            {
                "total_executions": executions.count(),
                "successful": success_count,
                "failed": failed_count,
                "pending": pending_count,
                "success_rate": (success_count / executions.count() * 100) if executions.count() > 0 else 0,
            }
        )
