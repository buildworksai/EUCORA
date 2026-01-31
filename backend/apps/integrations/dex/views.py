# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for DEX integration.

Provides endpoints for provider configuration, metrics, dashboard, and Green IT data.
"""
import logging
from datetime import timedelta

from apps.core.async_utils import run_async
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.dex.models import DEXAggregateMetrics, DEXDeviceMetrics, DEXProvider
from apps.integrations.dex.serializers import (
    DEXAggregateMetricsSerializer,
    DEXDashboardSerializer,
    DEXDeviceMetricsSerializer,
    DEXProviderSerializer,
    GreenITSummarySerializer,
)
from apps.integrations.dex.services.sync import DEXSyncService

logger = logging.getLogger(__name__)


class DEXProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DEX provider configuration.

    Provides CRUD operations and actions:
    - test: Test connection to 1E API
    - sync: Manually trigger sync
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DEXProviderSerializer
    queryset = DEXProvider.objects.all()

    def get_queryset(self):
        """Return single provider (only one provider supported)."""
        return DEXProvider.objects.all()

    def get_object(self):
        """Get or create single provider instance."""
        provider, _ = DEXProvider.objects.get_or_create(
            defaults={"name": "1E DEX Platform", "provider_type": DEXProvider.ProviderType.MOCK}
        )
        return provider

    @action(detail=False, methods=["post"])
    def test(self, request):
        """
        Test connection to 1E API.

        POST /api/v1/dex/provider/test/
        """
        provider = self.get_object()

        try:
            service = DEXSyncService(provider)
            is_healthy = run_async(service.client.health_check())

            if is_healthy:
                return Response({"status": "success", "message": "Connection successful"}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"status": "failed", "message": "Connection failed"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        except Exception as e:
            logger.error(f"DEX connection test failed: {e}")
            return Response({"status": "failed", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def sync(self, request):
        """
        Manually trigger DEX data sync.

        POST /api/v1/dex/provider/sync/
        """
        provider = self.get_object()

        try:
            service = DEXSyncService(provider)
            result = run_async(service.sync())

            return Response(
                {
                    "status": "success",
                    "metrics_synced": result.metrics_synced,
                    "duration_seconds": result.duration.total_seconds(),
                    "errors": result.errors,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"DEX sync failed: {e}")
            return Response({"status": "failed", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DEXDeviceMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading device DEX metrics.

    Read-only endpoint for querying device metrics.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DEXDeviceMetricsSerializer
    queryset = DEXDeviceMetrics.objects.all()

    def get_queryset(self):
        """Filter metrics by device_id, asset, or date range."""
        queryset = super().get_queryset()

        device_id = self.request.query_params.get("device_id")
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)

        # Date range filtering
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(collected_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(collected_at__lte=end_date)

        return queryset.order_by("-collected_at")


class DEXAggregateMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading aggregated DEX metrics.

    Read-only endpoint for dashboard queries.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DEXAggregateMetricsSerializer
    queryset = DEXAggregateMetrics.objects.all()

    def get_queryset(self):
        """Filter by aggregation type and date range."""
        queryset = super().get_queryset()

        aggregation_type = self.request.query_params.get("aggregation_type")
        if aggregation_type:
            queryset = queryset.filter(aggregation_type=aggregation_type)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)

        return queryset.order_by("-period_start")


class DEXDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard summary data.

    Provides aggregated metrics for DEX dashboard.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get dashboard summary data.

        GET /api/v1/dex/dashboard/summary/
        """
        # Get latest aggregate or calculate from device metrics
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Try to get today's aggregate
        aggregate = DEXAggregateMetrics.objects.filter(period_start=today_start, aggregation_type="daily").first()

        if aggregate:
            # Use pre-computed aggregate
            total_devices = aggregate.total_devices
            devices_with_dex = aggregate.devices_with_dex
            positive_count = aggregate.positive_sentiment_count
            neutral_count = aggregate.neutral_sentiment_count
            negative_count = aggregate.negative_sentiment_count
            total_sentiment = positive_count + neutral_count + negative_count

            data = {
                "avg_dex_score": aggregate.avg_dex_score or 0.0,
                "total_devices": total_devices,
                "devices_with_dex": devices_with_dex,
                "avg_boot_time": aggregate.avg_boot_time,
                "total_carbon_kg": aggregate.total_carbon_kg,
                "total_power_kwh": aggregate.total_power_kwh,
                "positive_sentiment_pct": (positive_count / total_sentiment * 100) if total_sentiment > 0 else 0.0,
                "neutral_sentiment_pct": (neutral_count / total_sentiment * 100) if total_sentiment > 0 else 0.0,
                "negative_sentiment_pct": (negative_count / total_sentiment * 100) if total_sentiment > 0 else 0.0,
            }
        else:
            # Calculate from device metrics
            metrics = DEXDeviceMetrics.objects.filter(collected_at__gte=today_start)

            agg = metrics.aggregate(
                total_devices=Count("id"),
                devices_with_dex=Count("id", filter=Q(dex_score__isnull=False)),
                avg_dex_score=Avg("dex_score"),
                avg_boot_time=Avg("boot_time_seconds"),
                total_carbon_kg=Sum("carbon_footprint_kg"),
                total_power_kwh=Sum("power_consumption_kwh"),
            )

            sentiment_counts = {
                "positive": metrics.filter(user_sentiment="Positive").count(),
                "neutral": metrics.filter(user_sentiment="Neutral").count(),
                "negative": metrics.filter(user_sentiment="Negative").count(),
            }
            total_sentiment = sum(sentiment_counts.values())

            data = {
                "avg_dex_score": agg["avg_dex_score"] or 0.0,
                "total_devices": agg["total_devices"] or 0,
                "devices_with_dex": agg["devices_with_dex"] or 0,
                "avg_boot_time": int(agg["avg_boot_time"]) if agg["avg_boot_time"] else None,
                "total_carbon_kg": agg["total_carbon_kg"],
                "total_power_kwh": agg["total_power_kwh"],
                "positive_sentiment_pct": (
                    (sentiment_counts["positive"] / total_sentiment * 100) if total_sentiment > 0 else 0.0
                ),
                "neutral_sentiment_pct": (
                    (sentiment_counts["neutral"] / total_sentiment * 100) if total_sentiment > 0 else 0.0
                ),
                "negative_sentiment_pct": (
                    (sentiment_counts["negative"] / total_sentiment * 100) if total_sentiment > 0 else 0.0
                ),
            }

        serializer = DEXDashboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GreenITViewSet(viewsets.ViewSet):
    """
    ViewSet for Green IT metrics.

    Provides sustainability and carbon footprint data.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get Green IT summary data.

        GET /api/v1/dex/green-it/summary/
        """
        # Get metrics from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        metrics = DEXDeviceMetrics.objects.filter(collected_at__gte=thirty_days_ago)

        agg = metrics.aggregate(
            device_count=Count("device_id", distinct=True),
            total_carbon_kg=Sum("carbon_footprint_kg"),
            total_power_kwh=Sum("power_consumption_kwh"),
        )

        device_count = agg["device_count"] or 0
        total_carbon = agg["total_carbon_kg"] or 0.0
        total_power = agg["total_power_kwh"] or 0.0

        data = {
            "total_carbon_kg": total_carbon,
            "total_power_kwh": total_power,
            "avg_carbon_per_device": total_carbon / device_count if device_count > 0 else 0.0,
            "avg_power_per_device": total_power / device_count if device_count > 0 else 0.0,
            "device_count": device_count,
        }

        serializer = GreenITSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
