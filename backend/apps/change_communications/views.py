# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Change Communications.
"""
import asyncio
import logging

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    ChangeAuditEvent,
    ChangeRecord,
    Communication,
    CommunicationTemplate,
    KBArticleLink,
    StakeholderGroup,
)
from .serializers import (
    ChangeAuditEventSerializer,
    ChangeRecordCloseSerializer,
    ChangeRecordCreateSerializer,
    ChangeRecordSerializer,
    CommunicationSerializer,
    CommunicationTemplatePreviewSerializer,
    CommunicationTemplateSerializer,
    GenerateKBArticleSerializer,
    KBArticleLinkSerializer,
    SendCommunicationSerializer,
    StakeholderGroupSerializer,
)
from .services import NotificationService, TemplateRenderer

logger = logging.getLogger(__name__)


class ChangeRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for change record management.

    Provides CRUD operations and lifecycle actions.
    """

    queryset = ChangeRecord.objects.all()
    serializer_class = ChangeRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use appropriate serializer for action."""
        if self.action in ["create"]:
            return ChangeRecordCreateSerializer
        return ChangeRecordSerializer

    def get_queryset(self):
        """Filter by correlation_id and other params."""
        queryset = ChangeRecord.objects.select_related("requested_by", "assigned_to", "deployment_intent")

        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        state = self.request.query_params.get("state")
        if state:
            queryset = queryset.filter(state=state)

        change_type = self.request.query_params.get("change_type")
        if change_type:
            queryset = queryset.filter(change_type=change_type)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        """Set requested_by to current user."""
        change_record = serializer.save(requested_by=self.request.user)

        # Create audit event
        ChangeAuditEvent.objects.create(
            change_record=change_record,
            event_type=ChangeAuditEvent.EventType.CREATED,
            description=f"Change record created: {change_record.servicenow_number}",
            performed_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk=None) -> Response:
        """Sync change record with ServiceNow."""
        change_record = self.get_object()
        # In production, this would call ServiceNow API
        return Response({"message": "Sync initiated", "change_id": str(change_record.id)})

    @action(detail=True, methods=["post"])
    def close(self, request: Request, pk=None) -> Response:
        """Close the change record."""
        change_record = self.get_object()

        serializer = ChangeRecordCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_state = change_record.state
        change_record.state = ChangeRecord.State.CLOSED
        change_record.close_code = serializer.validated_data["close_code"]
        change_record.close_notes = serializer.validated_data["close_notes"]
        change_record.success = serializer.validated_data["success"]
        change_record.actual_end = timezone.now()
        change_record.save()

        # Create audit event
        ChangeAuditEvent.objects.create(
            change_record=change_record,
            event_type=ChangeAuditEvent.EventType.CLOSED,
            description=f"Change closed with code: {change_record.close_code}",
            old_value=old_state,
            new_value=change_record.state,
            performed_by=request.user,
        )

        return Response(ChangeRecordSerializer(change_record).data)

    @action(detail=True, methods=["get"])
    def timeline(self, request: Request, pk=None) -> Response:
        """Get change timeline (audit events)."""
        change_record = self.get_object()
        events = change_record.audit_events.order_by("created_at")
        serializer = ChangeAuditEventSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def communications(self, request: Request, pk=None) -> Response:
        """Get communications for change record."""
        change_record = self.get_object()
        communications = change_record.communications.order_by("-created_at")
        serializer = CommunicationSerializer(communications, many=True)
        return Response(serializer.data)


class StakeholderGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for stakeholder groups."""

    queryset = StakeholderGroup.objects.all()
    serializer_class = StakeholderGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by channel if provided."""
        queryset = StakeholderGroup.objects.all()
        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(notification_channel=channel)
        return queryset.order_by("name")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Send test notification to stakeholder group."""
        group = self.get_object()
        # In production, send a test message
        return Response(
            {
                "message": f"Test notification sent to {group.name}",
                "channel": group.notification_channel,
            }
        )


class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for communication templates."""

    queryset = CommunicationTemplate.objects.all()
    serializer_class = CommunicationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by event_type and channel."""
        queryset = CommunicationTemplate.objects.all()

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        return queryset.order_by("event_type", "channel")

    @action(detail=True, methods=["post"])
    def preview(self, request: Request, pk=None) -> Response:
        """Preview template with sample data."""
        template = self.get_object()

        serializer = CommunicationTemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        renderer = TemplateRenderer()
        context = serializer.validated_data.get("context", {})
        rendered = renderer.preview(template, context if context else None)

        return Response(
            {
                "subject": rendered.subject,
                "body": rendered.body,
                "variables_used": rendered.variables_used,
            }
        )

    @action(detail=False, methods=["get"])
    def variables(self, request: Request) -> Response:
        """Get available template variables."""
        return Response(TemplateRenderer.get_available_variables())


class CommunicationViewSet(viewsets.ModelViewSet):
    """ViewSet for communications."""

    queryset = Communication.objects.all()
    serializer_class = CommunicationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Filter communications."""
        queryset = Communication.objects.select_related("change_record", "template", "stakeholder_group")

        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["post"])
    def send(self, request: Request) -> Response:
        """Send a communication."""
        serializer = SendCommunicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_record_id = serializer.validated_data["change_record_id"]
        event_type = serializer.validated_data["event_type"]

        try:
            change_record = ChangeRecord.objects.get(id=change_record_id)
        except ChangeRecord.DoesNotExist:
            return Response(
                {"error": "Change record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get stakeholder groups
        group_ids = serializer.validated_data.get("stakeholder_group_ids", [])
        if group_ids:
            groups = list(StakeholderGroup.objects.filter(id__in=group_ids))
        else:
            groups = list(StakeholderGroup.objects.filter(is_active=True))

        # Send notifications
        service = NotificationService()
        extra_context = {}
        if serializer.validated_data.get("custom_message"):
            extra_context["custom_message"] = serializer.validated_data["custom_message"]

        async def send():
            return await service.send_notification(change_record, event_type, groups, extra_context)

        results = asyncio.run(send())

        return Response(
            {
                "sent": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "results": [
                    {
                        "success": r.success,
                        "communication_id": r.communication_id,
                        "channel": r.channel,
                        "error": r.error_message,
                    }
                    for r in results
                ],
            }
        )

    @action(detail=True, methods=["post"])
    def retry(self, request: Request, pk=None) -> Response:
        """Retry a failed communication."""
        communication = self.get_object()

        if communication.status != Communication.Status.FAILED:
            return Response(
                {"error": "Communication is not in failed state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = NotificationService()

        async def retry():
            return await service.retry_failed(str(communication.id))

        result = asyncio.run(retry())

        return Response(
            {
                "success": result.success,
                "error": result.error_message,
            }
        )


class KBArticleLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for KB article links."""

    queryset = KBArticleLink.objects.all()
    serializer_class = KBArticleLinkSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        """Filter by change record."""
        queryset = KBArticleLink.objects.select_related("change_record")

        change_record_id = self.request.query_params.get("change_record_id")
        if change_record_id:
            queryset = queryset.filter(change_record_id=change_record_id)

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["post"])
    def generate(self, request: Request) -> Response:
        """Generate KB article for change record."""
        serializer = GenerateKBArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_record_id = serializer.validated_data["change_record_id"]

        try:
            change_record = ChangeRecord.objects.get(id=change_record_id)
        except ChangeRecord.DoesNotExist:
            return Response(
                {"error": "Change record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # In production, this would call an AI service to generate KB content
        # For now, create a placeholder
        import uuid

        kb_number = f"KB{uuid.uuid4().hex[:8].upper()}"
        kb_sys_id = str(uuid.uuid4())

        link = KBArticleLink.objects.create(
            change_record=change_record,
            kb_article_number=kb_number,
            kb_article_sys_id=kb_sys_id,
            kb_article_title=serializer.validated_data.get("title", f"KB for {change_record.servicenow_number}"),
            link_type=KBArticleLink.LinkType.CREATED,
            created_by_agent=True,
        )

        # Create audit event
        ChangeAuditEvent.objects.create(
            change_record=change_record,
            event_type=ChangeAuditEvent.EventType.KB_LINKED,
            description=f"KB article generated: {kb_number}",
            performed_by=request.user,
        )

        return Response(KBArticleLinkSerializer(link).data, status=status.HTTP_201_CREATED)


class ChangeDashboardViewSet(viewsets.ViewSet):
    """ViewSet for change dashboard data."""

    permission_classes = [IsAuthenticated]

    def list(self, request: Request) -> Response:
        """Get dashboard data."""
        today = timezone.now().date()

        # Active changes
        active_changes = ChangeRecord.objects.exclude(
            state__in=[ChangeRecord.State.CLOSED, ChangeRecord.State.CANCELLED]
        ).count()

        # Pending notifications
        pending_notifications = Communication.objects.filter(status=Communication.Status.PENDING).count()

        # Communications today
        communications_today = Communication.objects.filter(
            sent_at__date=today,
            status=Communication.Status.SENT,
        ).count()

        # KB articles created this month
        month_start = today.replace(day=1)
        kb_articles_created = KBArticleLink.objects.filter(
            created_at__date__gte=month_start,
            created_by_agent=True,
        ).count()

        # Changes by state
        changes_by_state = dict(
            ChangeRecord.objects.values("state").annotate(count=Count("id")).values_list("state", "count")
        )

        # Recent communications
        recent = Communication.objects.select_related("change_record").order_by("-created_at")[:10]

        return Response(
            {
                "active_changes": active_changes,
                "pending_notifications": pending_notifications,
                "communications_today": communications_today,
                "kb_articles_created": kb_articles_created,
                "changes_by_state": changes_by_state,
                "recent_communications": CommunicationSerializer(recent, many=True).data,
            }
        )
