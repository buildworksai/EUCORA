# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for integration management.
"""
import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.models import ExternalSystem, IntegrationSyncLog
from apps.integrations.serializers import (
    ExternalSystemCreateSerializer,
    ExternalSystemSerializer,
    IntegrationSyncLogSerializer,
)
from apps.integrations.services import get_integration_service
from apps.integrations.tasks import sync_external_system

logger = logging.getLogger(__name__)


class ExternalSystemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing external system integrations.

    Provides CRUD operations and additional actions:
    - test: Test connection to external system
    - sync: Manually trigger sync
    - logs: Get sync history
    """

    permission_classes = [IsAuthenticated]
    queryset = ExternalSystem.objects.select_related("created_by").prefetch_related("sync_logs")

    def get_serializer_class(self):
        """Use different serializer for create/update."""
        if self.action in ["create", "update", "partial_update"]:
            return ExternalSystemCreateSerializer
        return ExternalSystemSerializer

    def get_queryset(self):
        """Filter by demo mode if needed."""
        queryset = super().get_queryset()

        # Filter demo data if not in demo mode
        demo_mode = self.request.query_params.get("demo_mode", "false").lower() == "true"
        if not demo_mode:
            queryset = queryset.filter(is_demo=False)

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """
        Test connection to external system.

        POST /api/v1/integrations/{id}/test/
        """
        system = self.get_object()

        try:
            service = get_integration_service(system.type)

            # Build config from system
            config = {
                "api_url": system.api_url,
                "auth_type": system.auth_type,
                "credentials": system.credentials,
                "metadata": system.metadata,
            }

            result = service.test_connection(config)

            if result["status"] == "success":
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({"status": "failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error testing connection for {system.name}: {e}", exc_info=True)
            return Response(
                {"status": "failed", "message": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """
        Manually trigger sync for an integration.

        POST /api/v1/integrations/{id}/sync/
        """
        system = self.get_object()

        if not system.is_enabled:
            return Response(
                {"status": "failed", "message": "Integration is disabled"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Queue sync task
        task = sync_external_system.delay(str(system.id))

        return Response(
            {
                "status": "queued",
                "task_id": task.id,
                "message": f"Sync queued for {system.name}",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """
        Get sync history for an integration.

        GET /api/v1/integrations/{id}/logs/
        """
        system = self.get_object()

        # Pagination
        page_size = int(request.query_params.get("page_size", 50))
        page = int(request.query_params.get("page", 1))

        logs = IntegrationSyncLog.objects.filter(system=system).order_by("-sync_started_at")

        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = logs[start:end]

        serializer = IntegrationSyncLogSerializer(paginated_logs, many=True)

        return Response(
            {
                "count": logs.count(),
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
        )


class IntegrationSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing integration sync logs.

    Read-only - logs are created by sync tasks.
    """

    permission_classes = [IsAuthenticated]
    queryset = IntegrationSyncLog.objects.select_related("integration_system")
    serializer_class = IntegrationSyncLogSerializer

    def get_queryset(self):
        """Filter by system if provided."""
        queryset = super().get_queryset()

        system_id = self.request.query_params.get("system_id")
        if system_id:
            queryset = queryset.filter(system_id=system_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-sync_started_at")
