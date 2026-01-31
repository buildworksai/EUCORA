# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for SLA Governance Agent.
"""
import logging
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    KPIDefinition,
    KPIMeasurement,
    ServiceCatalogItem,
    SLABreach,
    SLACompliance,
    SLADefinition,
    SLAKPILink,
    SLATarget,
    SLATemplate,
)
from .serializers import (
    KPIDefinitionSerializer,
    KPIMeasurementSerializer,
    ServiceCatalogItemSerializer,
    SLABreachSerializer,
    SLAComplianceSerializer,
    SLADefinitionSerializer,
    SLAKPILinkSerializer,
    SLATargetSerializer,
    SLATemplateSerializer,
)

logger = logging.getLogger(__name__)


class ServiceCatalogItemViewSet(viewsets.ModelViewSet):
    """ViewSet for service catalog items."""

    queryset = ServiceCatalogItem.objects.all()
    serializer_class = ServiceCatalogItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by category and status."""
        queryset = ServiceCatalogItem.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("name")


class SLADefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for SLA definitions."""

    queryset = SLADefinition.objects.select_related("service", "created_by", "approved_by").all()
    serializer_class = SLADefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, service, and status."""
        queryset = SLADefinition.objects.select_related("service", "created_by", "approved_by").all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        service_id = self.request.query_params.get("service")
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-effective_from", "name")

    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk=None) -> Response:
        """Approve SLA definition."""
        sla = self.get_object()
        if sla.status != SLADefinition.Status.PENDING_APPROVAL:
            return Response({"error": "SLA is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)
        sla.status = SLADefinition.Status.ACTIVE
        sla.approved_by = request.user
        sla.approved_at = timezone.now()
        sla.save()
        serializer = self.get_serializer(sla)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def activate(self, request: Request, pk=None) -> Response:
        """Activate SLA definition."""
        sla = self.get_object()
        if sla.status != SLADefinition.Status.DRAFT:
            return Response({"error": "SLA must be in draft status"}, status=status.HTTP_400_BAD_REQUEST)
        sla.status = SLADefinition.Status.ACTIVE
        sla.approved_by = request.user
        sla.approved_at = timezone.now()
        sla.save()
        serializer = self.get_serializer(sla)
        return Response(serializer.data)


class SLATargetViewSet(viewsets.ModelViewSet):
    """ViewSet for SLA targets."""

    queryset = SLATarget.objects.select_related("sla").all()
    serializer_class = SLATargetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by SLA."""
        queryset = SLATarget.objects.select_related("sla").all()
        sla_id = self.request.query_params.get("sla")
        if sla_id:
            queryset = queryset.filter(sla_id=sla_id)
        return queryset.order_by("sla", "metric_type")


class KPIDefinitionViewSet(viewsets.ModelViewSet):
    """ViewSet for KPI definitions."""

    queryset = KPIDefinition.objects.all()
    serializer_class = KPIDefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by is_active."""
        queryset = KPIDefinition.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("name")


class SLAKPILinkViewSet(viewsets.ModelViewSet):
    """ViewSet for SLA-KPI links."""

    queryset = SLAKPILink.objects.select_related("sla_target", "kpi").all()
    serializer_class = SLAKPILinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by SLA target or KPI."""
        queryset = SLAKPILink.objects.select_related("sla_target", "kpi").all()
        sla_target_id = self.request.query_params.get("sla_target")
        if sla_target_id:
            queryset = queryset.filter(sla_target_id=sla_target_id)
        kpi_id = self.request.query_params.get("kpi")
        if kpi_id:
            queryset = queryset.filter(kpi_id=kpi_id)
        return queryset.order_by("sla_target", "kpi")


class KPIMeasurementViewSet(viewsets.ModelViewSet):
    """ViewSet for KPI measurements."""

    queryset = KPIMeasurement.objects.select_related("kpi").all()
    serializer_class = KPIMeasurementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by KPI, status, and date range."""
        queryset = KPIMeasurement.objects.select_related("kpi").all()
        kpi_id = self.request.query_params.get("kpi")
        if kpi_id:
            queryset = queryset.filter(kpi_id=kpi_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(measurement_time__gte=start_date)
        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(measurement_time__lte=end_date)
        return queryset.order_by("-measurement_time")


class SLAComplianceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SLA compliance records."""

    queryset = SLACompliance.objects.select_related("sla").all()
    serializer_class = SLAComplianceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, SLA, status, and date range."""
        queryset = SLACompliance.objects.select_related("sla").all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        sla_id = self.request.query_params.get("sla")
        if sla_id:
            queryset = queryset.filter(sla_id=sla_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)
        return queryset.order_by("-period_end", "-period_start")

    @action(detail=False, methods=["get"])
    def at_risk(self, request: Request) -> Response:
        """Get SLAs at risk."""
        queryset = self.get_queryset().filter(status=SLACompliance.Status.AT_RISK)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SLABreachViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SLA breaches."""

    queryset = SLABreach.objects.select_related("sla", "target").all()
    serializer_class = SLABreachSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, SLA, severity, and date range."""
        queryset = SLABreach.objects.select_related("sla", "target").all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        sla_id = self.request.query_params.get("sla")
        if sla_id:
            queryset = queryset.filter(sla_id=sla_id)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(breach_time__gte=start_date)
        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(breach_time__lte=end_date)
        return queryset.order_by("-breach_time")


class SLATemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for SLA templates."""

    queryset = SLATemplate.objects.all()
    serializer_class = SLATemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by category and is_active."""
        queryset = SLATemplate.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("category", "name")


class SLAReportsViewSet(viewsets.ViewSet):
    """ViewSet for SLA reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request: Request) -> Response:
        """Get SLA summary report."""
        total_slas = SLADefinition.objects.count()
        active_slas = SLADefinition.objects.filter(status=SLADefinition.Status.ACTIVE).count()
        at_risk_count = SLACompliance.objects.filter(status=SLACompliance.Status.AT_RISK).count()
        breach_count = SLABreach.objects.count()

        return Response(
            {
                "total_slas": total_slas,
                "active_slas": active_slas,
                "at_risk_count": at_risk_count,
                "breach_count": breach_count,
            }
        )

    @action(detail=False, methods=["get"])
    def trends(self, request: Request) -> Response:
        """Get SLA compliance trends."""
        # Get compliance records for last 12 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)

        compliance_records = SLACompliance.objects.filter(
            period_start__gte=start_date, period_end__lte=end_date
        ).order_by("period_end")

        trends = []
        for record in compliance_records:
            trends.append(
                {
                    "date": record.period_end.isoformat(),
                    "compliance": record.overall_compliance,
                    "status": record.status,
                }
            )

        return Response({"trends": trends})


class SLAParseRequestViewSet(viewsets.ViewSet):
    """ViewSet for natural language SLA parsing."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def parse(self, request: Request) -> Response:
        """Parse natural language SLA request."""
        # TODO: Implement NL parsing with LLM
        request_text = request.data.get("request", "")
        return Response(
            {
                "parsed": True,
                "request": request_text,
                "message": "NL parsing will be implemented with LLM integration",
            }
        )
