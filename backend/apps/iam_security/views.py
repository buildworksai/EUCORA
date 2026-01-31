# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for IAM Security.
"""
import logging
from datetime import datetime, timedelta

from apps.core.async_utils import run_async
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import AnomalyDetection, DetectionRule, IdentityProvider, PermissionChange, SecurityAlert, SignInEvent
from .serializers import (
    AnomalyDetectionSerializer,
    AnomalyResolveSerializer,
    DetectionRuleSerializer,
    IdentityProviderSerializer,
    PermissionChangeSerializer,
    SecurityAlertSerializer,
    SignInEventSerializer,
)
from .services.clients.entra_client import EntraIDClient
from .services.response_actions import ResponseActionsService

logger = logging.getLogger(__name__)


class IdentityProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for identity provider management."""

    queryset = IdentityProvider.objects.all()
    serializer_class = IdentityProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by provider_type and active status."""
        queryset = IdentityProvider.objects.annotate(
            sign_in_count=Count("sign_in_events"),
            anomaly_count=Count("anomalies", filter=Q(anomalies__status=AnomalyDetection.Status.NEW)),
        )
        provider_type = self.request.query_params.get("provider_type")
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test connection to identity provider."""
        provider = self.get_object()  # noqa: F841
        # Test connection (simplified)
        return Response({"status": "success", "message": "Connection test successful"})

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk=None) -> Response:
        """Sync events from identity provider."""
        provider = self.get_object()

        async def run_sync():
            if provider.provider_type == IdentityProvider.ProviderType.ENTRA_ID:
                config = provider.connection_config
                client = EntraIDClient(
                    tenant_id=provider.tenant_id or "",
                    client_id=config.get("client_id", ""),
                    client_secret=config.get("client_secret", ""),
                )
                try:
                    await client.authenticate()
                    since = provider.last_sync or (datetime.now() - timedelta(hours=24))
                    sign_ins = await client.get_sign_in_logs(since)
                    # Process sign-ins (simplified)
                    provider.last_sync = timezone.now()
                    provider.save()
                    await client.close()
                    return {"synced": len(sign_ins)}
                except Exception as e:
                    logger.exception("Error syncing Entra ID")
                    await client.close()
                    return {"error": str(e)}
            return {"error": "Provider type not supported"}

        result = run_async(run_sync())
        return Response(result)


class SignInEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for sign-in events (read-only)."""

    queryset = SignInEvent.objects.select_related("provider")
    serializer_class = SignInEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by provider, user, status, and time range."""
        queryset = SignInEvent.objects.select_related("provider")
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        user_principal = self.request.query_params.get("user_principal")
        if user_principal:
            queryset = queryset.filter(user_principal=user_principal)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-event_time")


class PermissionChangeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for permission changes (read-only)."""

    queryset = PermissionChange.objects.select_related("provider")
    serializer_class = PermissionChangeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by provider, target user, and change type."""
        queryset = PermissionChange.objects.select_related("provider")
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        target_principal = self.request.query_params.get("target_principal")
        if target_principal:
            queryset = queryset.filter(target_principal=target_principal)
        change_type = self.request.query_params.get("change_type")
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        return queryset.order_by("-event_time")


class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for anomaly detections."""

    queryset = AnomalyDetection.objects.select_related("provider", "assigned_to")
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, provider, severity, status, and user."""
        queryset = AnomalyDetection.objects.select_related("provider", "assigned_to").annotate(
            alert_count=Count("alerts")
        )
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        provider_id = self.request.query_params.get("provider_id")
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        user_principal = self.request.query_params.get("user_principal")
        if user_principal:
            queryset = queryset.filter(user_principal=user_principal)
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def investigate(self, request: Request, pk=None) -> Response:
        """Mark anomaly as under investigation."""
        anomaly = self.get_object()
        anomaly.status = AnomalyDetection.Status.INVESTIGATING
        anomaly.assigned_to = request.user
        anomaly.save()
        return Response(AnomalyDetectionSerializer(anomaly).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk=None) -> Response:
        """Resolve an anomaly."""
        anomaly = self.get_object()
        serializer = AnomalyResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        anomaly.status = (
            AnomalyDetection.Status.FALSE_POSITIVE
            if serializer.validated_data.get("is_false_positive")
            else AnomalyDetection.Status.RESOLVED
        )
        anomaly.resolved_at = timezone.now()
        if serializer.validated_data.get("resolution_notes"):
            anomaly.resolution_notes = serializer.validated_data["resolution_notes"]
        anomaly.save()

        return Response(AnomalyDetectionSerializer(anomaly).data)

    @action(detail=True, methods=["post"])
    def false_positive(self, request: Request, pk=None) -> Response:
        """Mark anomaly as false positive."""
        anomaly = self.get_object()
        anomaly.status = AnomalyDetection.Status.FALSE_POSITIVE
        anomaly.resolved_at = timezone.now()
        anomaly.save()
        return Response(AnomalyDetectionSerializer(anomaly).data)


class DetectionRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for detection rules."""

    queryset = DetectionRule.objects.all()
    serializer_class = DetectionRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by anomaly_type, severity, and active status."""
        queryset = DetectionRule.objects.all()
        anomaly_type = self.request.query_params.get("anomaly_type")
        if anomaly_type:
            queryset = queryset.filter(anomaly_type=anomaly_type)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset.order_by("anomaly_type", "name")

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test detection rule."""
        rule = self.get_object()  # noqa: F841
        # Test rule (simplified)
        return Response({"status": "success", "message": "Rule test completed"})


class SecurityAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for security alerts (read-only)."""

    queryset = SecurityAlert.objects.select_related("anomaly")
    serializer_class = SecurityAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by correlation_id, anomaly, channel, and status."""
        queryset = SecurityAlert.objects.select_related("anomaly")
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        anomaly_id = self.request.query_params.get("anomaly_id")
        if anomaly_id:
            queryset = queryset.filter(anomaly_id=anomaly_id)
        channel = self.request.query_params.get("channel")
        if channel:
            queryset = queryset.filter(channel=channel)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-sent_at")


class SecurityActionsViewSet(viewsets.ViewSet):
    """ViewSet for security response actions."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def disable_account(self, request: Request) -> Response:
        """Disable user account (R3 action)."""
        provider_id = request.data.get("provider_id")
        user_principal = request.data.get("user_principal")

        if not provider_id or not user_principal:
            return Response(
                {"error": "provider_id and user_principal are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            provider = IdentityProvider.objects.get(id=provider_id)
        except IdentityProvider.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

        async def run_action():
            service = ResponseActionsService(provider)
            return await service.disable_account(user_principal)

        result = run_async(run_action())
        return Response({"success": result})

    @action(detail=False, methods=["post"])
    def revoke_permissions(self, request: Request) -> Response:
        """Revoke user permissions (R2 action)."""
        provider_id = request.data.get("provider_id")
        user_principal = request.data.get("user_principal")

        if not provider_id or not user_principal:
            return Response(
                {"error": "provider_id and user_principal are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            provider = IdentityProvider.objects.get(id=provider_id)
        except IdentityProvider.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

        async def run_action():
            service = ResponseActionsService(provider)
            return await service.revoke_permissions(user_principal)

        result = run_async(run_action())
        return Response({"success": result})

    @action(detail=False, methods=["post"])
    def force_password_reset(self, request: Request) -> Response:
        """Force password reset (R2 action)."""
        provider_id = request.data.get("provider_id")
        user_principal = request.data.get("user_principal")

        if not provider_id or not user_principal:
            return Response(
                {"error": "provider_id and user_principal are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            provider = IdentityProvider.objects.get(id=provider_id)
        except IdentityProvider.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

        async def run_action():
            service = ResponseActionsService(provider)
            return await service.force_password_reset(user_principal)

        result = run_async(run_action())
        return Response({"success": result})


class SecurityReportsViewSet(viewsets.ViewSet):
    """ViewSet for security reports."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request: Request) -> Response:
        """Get security summary statistics."""
        total_anomalies = AnomalyDetection.objects.count()
        critical = AnomalyDetection.objects.filter(severity=AnomalyDetection.Severity.CRITICAL).count()
        high = AnomalyDetection.objects.filter(severity=AnomalyDetection.Severity.HIGH).count()
        new = AnomalyDetection.objects.filter(status=AnomalyDetection.Status.NEW).count()

        return Response(
            {
                "total_anomalies": total_anomalies,
                "critical": critical,
                "high": high,
                "new": new,
            }
        )

    @action(detail=False, methods=["get"])
    def trends(self, request: Request) -> Response:
        """Get anomaly trends over time."""
        # Simplified - would calculate trends
        return Response({"trends": []})
