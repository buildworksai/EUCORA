# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Request Coordination.
"""
import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.cmdb_integration.models import CMDBConnection
from apps.core.async_utils import run_async

from .models import (
    CommunicationTemplate,
    EscalationEvent,
    EscalationRule,
    RequestCommunication,
    RequestStakeholder,
    RequestStatusUpdate,
    TrackedRequest,
)
from .serializers import (
    CommunicationTemplateSerializer,
    EscalationEventSerializer,
    EscalationRuleSerializer,
    RequestCommunicationSerializer,
    RequestStakeholderSerializer,
    RequestStatusUpdateSerializer,
    TrackedRequestSerializer,
)
from .services.notification_service import RequestNotificationService
from .services.sync_service import RequestSyncService

logger = logging.getLogger(__name__)


class TrackedRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracked requests.

    Provides CRUD operations, sync, and timeline.
    """

    queryset = TrackedRequest.objects.all()
    serializer_class = TrackedRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id and status if provided."""
        queryset = TrackedRequest.objects.all()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        priority_filter = self.request.query_params.get("priority")
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        return queryset.order_by("-created_at")

    @action(detail=False, methods=["post"])
    def sync(self, request: Request) -> Response:
        """Sync requests from ServiceNow."""
        connection_id = request.data.get("connection_id")
        if not connection_id:
            return Response({"error": "connection_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = CMDBConnection.objects.get(id=connection_id)
        except CMDBConnection.DoesNotExist:
            return Response({"error": "Connection not found"}, status=status.HTTP_404_NOT_FOUND)

        limit = request.data.get("limit", 100)

        async def run_sync():
            service = RequestSyncService(connection, use_mock=True)
            try:
                synced = await service.sync_all_requests(limit=limit)
                return [str(r.id) for r in synced]
            finally:
                await service.close()

        synced_ids = run_async(run_sync())

        return Response({"synced": len(synced_ids), "request_ids": synced_ids})

    @action(detail=True, methods=["get"])
    def timeline(self, request: Request, pk=None) -> Response:
        """Get timeline of status updates and communications."""
        tracked_request = self.get_object()

        timeline = []
        for update in RequestStatusUpdate.objects.filter(request=tracked_request).order_by("created_at"):
            timeline.append(
                {
                    "type": "status_update",
                    "timestamp": update.created_at,
                    "data": RequestStatusUpdateSerializer(update).data,
                }
            )

        for comm in RequestCommunication.objects.filter(request=tracked_request).order_by("created_at"):
            timeline.append(
                {
                    "type": "communication",
                    "timestamp": comm.created_at,
                    "data": RequestCommunicationSerializer(comm).data,
                }
            )

        timeline.sort(key=lambda x: x["timestamp"])

        return Response({"timeline": timeline})


class RequestStakeholderViewSet(viewsets.ModelViewSet):
    """ViewSet for request stakeholders."""

    queryset = RequestStakeholder.objects.all()
    serializer_class = RequestStakeholderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by request if provided."""
        queryset = RequestStakeholder.objects.select_related("request")
        request_id = self.request.query_params.get("request_id")
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        return queryset.order_by("role", "name")


class RequestCommunicationViewSet(viewsets.ModelViewSet):
    """ViewSet for request communications."""

    queryset = RequestCommunication.objects.all()
    serializer_class = RequestCommunicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id and request if provided."""
        queryset = RequestCommunication.objects.select_related("request")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        request_id = self.request.query_params.get("request_id")
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        return queryset.order_by("-created_at")

    @action(detail=False, methods=["post"])
    def send(self, request: Request) -> Response:
        """Send a communication for a request."""
        request_id = request.data.get("request_id")
        communication_type = request.data.get("communication_type")
        template_id = request.data.get("template_id")

        try:
            tracked_request = TrackedRequest.objects.get(id=request_id)
        except TrackedRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

        template = None
        if template_id:
            try:
                template = CommunicationTemplate.objects.get(id=template_id)
            except CommunicationTemplate.DoesNotExist:
                return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)

        notification_service = RequestNotificationService()
        communication = notification_service.send_notification(
            request=tracked_request,
            communication_type=communication_type,
            template=template,
        )

        return Response(RequestCommunicationSerializer(communication).data)


class EscalationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for escalation rules."""

    queryset = EscalationRule.objects.all()
    serializer_class = EscalationRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by active status if provided."""
        queryset = EscalationRule.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("name")


class EscalationEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for escalation events (read-only, resolve action)."""

    queryset = EscalationEvent.objects.all()
    serializer_class = EscalationEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id and resolved status if provided."""
        queryset = EscalationEvent.objects.select_related("request", "rule")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        resolved = self.request.query_params.get("resolved")
        if resolved is not None:
            if resolved.lower() == "true":
                queryset = queryset.exclude(resolved_at__isnull=True)
            else:
                queryset = queryset.filter(resolved_at__isnull=True)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk=None) -> Response:
        """Resolve an escalation event."""
        escalation_event = self.get_object()
        escalation_event.resolved_at = timezone.now()
        escalation_event.save()

        # Optionally un-escalate the request
        if request.data.get("un_escalate", False):
            escalation_event.request.is_escalated = False
            escalation_event.request.save()

        return Response(EscalationEventSerializer(escalation_event).data)


class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for communication templates."""

    queryset = CommunicationTemplate.objects.all()
    serializer_class = CommunicationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by communication_type and channel if provided."""
        queryset = CommunicationTemplate.objects.all()
        communication_type = self.request.query_params.get("communication_type")
        if communication_type:
            queryset = queryset.filter(communication_type=communication_type)
        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("communication_type", "channel")


class RequestCoordinationReportsViewSet(viewsets.ViewSet):
    """ViewSet for request coordination reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def sla_compliance(self, request: Request) -> Response:
        """Get SLA compliance report."""
        total = TrackedRequest.objects.filter(sla_due__isnull=False).count()
        breached = TrackedRequest.objects.filter(sla_due__lt=timezone.now(), sla_due__isnull=False).count()
        at_risk = TrackedRequest.objects.filter(
            sla_due__lte=timezone.now() + timedelta(hours=4),
            sla_due__gt=timezone.now(),
            sla_due__isnull=False,
        ).count()
        compliant = total - breached - at_risk

        compliance_rate = (compliant / total * 100) if total > 0 else 0

        return Response(
            {
                "total": total,
                "compliant": compliant,
                "at_risk": at_risk,
                "breached": breached,
                "compliance_rate": round(compliance_rate, 2),
            }
        )

    @action(detail=False, methods=["get"])
    def workload(self, request: Request) -> Response:
        """Get team workload report."""
        workload = (
            TrackedRequest.objects.filter(status__in=[TrackedRequest.Status.NEW, TrackedRequest.Status.IN_PROGRESS])
            .values("assignment_group")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response({"workload": list(workload)})

    @action(detail=False, methods=["get"])
    def trends(self, request: Request) -> Response:
        """Get escalation trends report."""
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now() - timedelta(days=days)

        trends = (
            EscalationEvent.objects.filter(created_at__gte=start_date)
            .values("created_at__date")
            .annotate(count=Count("id"))
            .order_by("created_at__date")
        )

        return Response({"trends": list(trends)})
