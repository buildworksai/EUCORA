# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Storage.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rbac.permissions import RBACPermission

from .models import StorageProvider
from .serializers import (
    ConnectionTestResultSerializer,
    HealthStatusSerializer,
    StorageMetricsSerializer,
    StorageProviderCreateSerializer,
    StorageProviderDetailSerializer,
    StorageProviderSerializer,
)
from .services import StorageConnectionTester, get_storage_service


class StorageProviderViewSet(viewsets.ModelViewSet):
    """API viewset for StorageProvider."""

    permission_classes = [RBACPermission("storage_config", "read")]
    queryset = StorageProvider.objects.select_related(
        "minio_config", "s3_config", "azure_config", "configured_by"
    ).all()
    serializer_class = StorageProviderSerializer
    lookup_field = "id"

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "retrieve":
            return StorageProviderDetailSerializer
        if self.action == "create":
            return StorageProviderCreateSerializer
        return StorageProviderSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # RBACPermission returns a class, so instantiate it
            return [RBACPermission("storage_config", "create")()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="test")
    def test(self, request: Request, id=None) -> Response:
        """Test storage provider connection."""
        provider = self.get_object()

        tester = StorageConnectionTester()
        result = tester.test_connection(provider)

        # Update provider status
        provider.status = (
            StorageProvider.ProviderStatus.HEALTHY if result.success else StorageProvider.ProviderStatus.FAILED
        )
        provider.last_health_check = timezone.now()
        provider.health_check_error = result.message if not result.success else ""
        provider.save()

        serializer = ConnectionTestResultSerializer(result)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="set_primary")
    def set_primary(self, request: Request, id=None) -> Response:
        """Set provider as primary."""
        provider = self.get_object()

        with transaction.atomic():
            # Unset other primary providers
            StorageProvider.objects.filter(is_primary=True).update(is_primary=False)
            # Set this one as primary
            provider.is_primary = True
            provider.save()

        return Response({"message": f"{provider.name} set as primary provider"})

    @action(detail=True, methods=["get"], url_path="metrics")
    def metrics(self, request: Request, id=None) -> Response:
        """Get metrics for a provider."""
        provider = self.get_object()
        metrics = provider.metrics.all()[:100]  # Last 100 metrics
        serializer = StorageMetricsSerializer(metrics, many=True)
        return Response(serializer.data)


class StorageHealthView(APIView):
    """API endpoint for overall storage health."""

    permission_classes = [RBACPermission("storage_config", "read")]

    def get(self, request: Request) -> Response:
        """Get overall storage health status."""
        storage_service = get_storage_service()

        providers = StorageProvider.objects.filter(is_enabled=True)
        primary_provider = providers.filter(is_primary=True).first()

        available_count = 0
        for provider in providers:
            try:
                backend = storage_service._create_backend(provider)
                if backend:
                    health = backend.health_check()
                    if health.is_healthy:
                        available_count += 1
            except Exception:
                pass

        serializer = HealthStatusSerializer(
            {
                "is_healthy": available_count > 0,
                "primary_provider": primary_provider,  # Pass object, let serializer handle it
                "available_providers": available_count,
                "total_providers": providers.count(),
            }
        )
        return Response(serializer.data)
