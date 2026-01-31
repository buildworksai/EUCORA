# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Planning Agent.
"""
import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    BlastRadiusAnalysis,
    ChangeFreezePeriod,
    DeploymentPlan,
    DeploymentWindow,
    RingAssignment,
    RingDevice,
    RollbackPlan,
)
from .serializers import (
    BlastRadiusAnalysisSerializer,
    ChangeFreezePeriodSerializer,
    DeploymentPlanSerializer,
    DeploymentWindowSerializer,
    RingAssignmentSerializer,
    RingDeviceSerializer,
    RollbackPlanSerializer,
)

logger = logging.getLogger(__name__)


class DeploymentPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for deployment plans."""

    queryset = DeploymentPlan.objects.select_related("application", "created_by", "approved_by").all()
    serializer_class = DeploymentPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, application, and status."""
        queryset = DeploymentPlan.objects.select_related("application", "created_by", "approved_by").all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        application_id = self.request.query_params.get("application")
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve deployment plan."""
        plan = self.get_object()
        if plan.status != DeploymentPlan.Status.PENDING_APPROVAL:
            return Response({"error": "Plan is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)
        plan.status = DeploymentPlan.Status.APPROVED
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def execute(self, request: Request, pk=None) -> Response:
        """Execute deployment plan."""
        plan = self.get_object()
        if plan.status != DeploymentPlan.Status.APPROVED:
            return Response({"error": "Plan must be approved before execution"}, status=status.HTTP_400_BAD_REQUEST)
        plan.status = DeploymentPlan.Status.EXECUTING
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)


class RingAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for ring assignments."""

    queryset = RingAssignment.objects.select_related("plan").all()
    serializer_class = RingAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by plan and status."""
        queryset = RingAssignment.objects.select_related("plan").all()
        plan_id = self.request.query_params.get("plan")
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("plan", "ring_number")


class RingDeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for ring devices."""

    queryset = RingDevice.objects.select_related("ring").all()
    serializer_class = RingDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by ring and criticality."""
        queryset = RingDevice.objects.select_related("ring").all()
        ring_id = self.request.query_params.get("ring")
        if ring_id:
            queryset = queryset.filter(ring_id=ring_id)
        criticality = self.request.query_params.get("criticality")
        if criticality:
            queryset = queryset.filter(criticality=criticality)
        return queryset.order_by("ring", "device_name")


class DeploymentWindowViewSet(viewsets.ModelViewSet):
    """ViewSet for deployment windows."""

    queryset = DeploymentWindow.objects.all()
    serializer_class = DeploymentWindowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by is_active."""
        queryset = DeploymentWindow.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("name")


class ChangeFreezePeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for change freeze periods."""

    queryset = ChangeFreezePeriod.objects.all()
    serializer_class = ChangeFreezePeriodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by is_active and date range."""
        queryset = ChangeFreezePeriod.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        return queryset.order_by("-start_date")


class BlastRadiusAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for blast radius analysis."""

    queryset = BlastRadiusAnalysis.objects.select_related("plan").all()
    serializer_class = BlastRadiusAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id and plan."""
        queryset = BlastRadiusAnalysis.objects.select_related("plan").all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        plan_id = self.request.query_params.get("plan")
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        return queryset.order_by("-created_at")


class RollbackPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for rollback plans."""

    queryset = RollbackPlan.objects.select_related("deployment_plan").all()
    serializer_class = RollbackPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by deployment plan."""
        queryset = RollbackPlan.objects.select_related("deployment_plan").all()
        plan_id = self.request.query_params.get("plan")
        if plan_id:
            queryset = queryset.filter(deployment_plan_id=plan_id)
        return queryset.order_by("-created_at")


class PlanningReportsViewSet(viewsets.ViewSet):
    """ViewSet for planning reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request: Request) -> Response:
        """Get planning summary report."""
        total_plans = DeploymentPlan.objects.count()
        active_plans = DeploymentPlan.objects.filter(status=DeploymentPlan.Status.EXECUTING).count()
        approved_plans = DeploymentPlan.objects.filter(status=DeploymentPlan.Status.APPROVED).count()
        completed_plans = DeploymentPlan.objects.filter(status=DeploymentPlan.Status.COMPLETED).count()

        return Response(
            {
                "total_plans": total_plans,
                "active_plans": active_plans,
                "approved_plans": approved_plans,
                "completed_plans": completed_plans,
            }
        )


class PlanningGenerateViewSet(viewsets.ViewSet):
    """ViewSet for natural language plan generation."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def generate(self, request: Request) -> Response:
        """Generate deployment plan from natural language request."""
        # TODO: Implement NL plan generation with LLM
        request_text = request.data.get("request", "")
        return Response(
            {
                "generated": True,
                "request": request_text,
                "message": "NL plan generation will be implemented with LLM integration",
            }
        )
