# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service for syncing DEX data from 1E or mock provider.

Handles device metrics upsert, aggregate calculation, and sync status tracking.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Max, Min, StdDev, Sum
from django.utils import timezone

from apps.integrations.dex.clients.mock import MockDEXClient
from apps.integrations.dex.clients.one_e import OneEAPIClient
from apps.integrations.dex.models import DEXAggregateMetrics, DEXDeviceMetrics, DEXProvider

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a DEX sync operation."""

    duration: timedelta
    metrics_synced: int
    errors: list[str]


class DEXSyncService:
    """
    Service for syncing DEX data from 1E or mock provider.

    Factory pattern selects appropriate client based on provider_type.
    """

    def __init__(self, provider: DEXProvider):
        """
        Initialize sync service.

        Args:
            provider: DEXProvider instance with connection configuration
        """
        self.provider = provider
        self.client = self._get_client()

    def _get_client(self):
        """Get appropriate client based on provider type."""
        if self.provider.provider_type == DEXProvider.ProviderType.ONE_E:
            return OneEAPIClient(self.provider)
        return MockDEXClient()

    async def sync(self) -> SyncResult:
        """
        Run full sync of DEX data.

        Returns:
            SyncResult with duration, metrics synced, and errors
        """
        start_time = timezone.now()
        metrics_synced = 0
        errors = []

        try:
            # Update sync status to running
            self.provider.last_sync_status = "running"
            self.provider.save(update_fields=["last_sync_status"])

            # Stream device data from client
            async for device_data in self.client.get_experience_scores():
                try:
                    await self._upsert_device_metrics(device_data)
                    metrics_synced += 1
                except Exception as e:
                    error_msg = f"Device {device_data.get('device_id', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Update aggregate metrics
            await self._update_aggregates()

            # Update sync status to success
            self.provider.last_sync_at = timezone.now()
            self.provider.last_sync_status = "success"
            self.provider.last_sync_error = ""
            self.provider.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_error"])

        except Exception as e:
            error_msg = str(e)
            self.provider.last_sync_status = "failed"
            self.provider.last_sync_error = error_msg
            self.provider.save(update_fields=["last_sync_status", "last_sync_error"])
            logger.error(f"DEX sync failed: {error_msg}")
            raise

        duration = timezone.now() - start_time
        return SyncResult(duration=duration, metrics_synced=metrics_synced, errors=errors)

    async def _upsert_device_metrics(self, data: dict):
        """
        Create or update device metrics.

        Args:
            data: Device metrics dictionary from client
        """
        from django.utils.dateparse import parse_datetime

        collected_at_str = data.get("collected_at")
        if isinstance(collected_at_str, str):
            collected_at = parse_datetime(collected_at_str) or timezone.now()
        else:
            collected_at = timezone.now()

        await DEXDeviceMetrics.objects.aupdate_or_create(
            device_id=data["device_id"],
            defaults={
                "device_name": data.get("device_name", ""),
                "dex_score": data.get("dex_score"),
                "performance_score": data.get("performance_score"),
                "stability_score": data.get("stability_score"),
                "responsiveness_score": data.get("responsiveness_score"),
                "boot_time_seconds": data.get("boot_time_seconds"),
                "login_time_seconds": data.get("login_time_seconds"),
                "user_sentiment": data.get("user_sentiment", ""),
                "sentiment_score": data.get("sentiment_score"),
                "carbon_footprint_kg": data.get("carbon_footprint_kg"),
                "power_consumption_kwh": data.get("power_consumption_kwh"),
                "collected_at": collected_at,
                "source": self.provider.provider_type,
            },
        )

    async def _update_aggregates(self):
        """Update aggregate metrics for dashboard queries."""
        # Calculate daily aggregates for today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Get all metrics from today
        metrics = DEXDeviceMetrics.objects.filter(collected_at__gte=today_start, collected_at__lt=today_end)

        if not await metrics.aexists():
            return

        # Calculate aggregates
        agg = await metrics.aaggregate(
            total_devices=Count("id"),
            devices_with_dex=Count("id", filter=models.Q(dex_score__isnull=False)),
            avg_dex_score=Avg("dex_score"),
            min_dex_score=Min("dex_score"),
            max_dex_score=Max("dex_score"),
            dex_score_std_dev=StdDev("dex_score"),
            avg_boot_time=Avg("boot_time_seconds"),
            total_carbon_kg=Sum("carbon_footprint_kg"),
            total_power_kwh=Sum("power_consumption_kwh"),
        )

        # Calculate percentiles for boot time
        boot_times = [
            m.boot_time_seconds
            async for m in metrics.values_list("boot_time_seconds", flat=True)
            if m.boot_time_seconds is not None
        ]
        boot_times_sorted = sorted(boot_times) if boot_times else []
        p50_boot_time = boot_times_sorted[len(boot_times_sorted) // 2] if boot_times_sorted else None
        p95_boot_time = boot_times_sorted[int(len(boot_times_sorted) * 0.95)] if boot_times_sorted else None

        # Count sentiment distribution
        sentiment_counts = {
            "positive": await metrics.filter(user_sentiment="Positive").acount(),
            "neutral": await metrics.filter(user_sentiment="Neutral").acount(),
            "negative": await metrics.filter(user_sentiment="Negative").acount(),
        }

        # Upsert aggregate record
        await DEXAggregateMetrics.objects.aupdate_or_create(
            period_start=today_start,
            aggregation_type="daily",
            defaults={
                "period_end": today_end,
                "total_devices": agg["total_devices"] or 0,
                "devices_with_dex": agg["devices_with_dex"] or 0,
                "avg_dex_score": agg["avg_dex_score"],
                "min_dex_score": agg["min_dex_score"],
                "max_dex_score": agg["max_dex_score"],
                "dex_score_std_dev": agg["dex_score_std_dev"],
                "avg_boot_time": int(agg["avg_boot_time"]) if agg["avg_boot_time"] else None,
                "p50_boot_time": p50_boot_time,
                "p95_boot_time": p95_boot_time,
                "positive_sentiment_count": sentiment_counts["positive"],
                "neutral_sentiment_count": sentiment_counts["neutral"],
                "negative_sentiment_count": sentiment_counts["negative"],
                "total_carbon_kg": agg["total_carbon_kg"],
                "total_power_kwh": agg["total_power_kwh"],
            },
        )
