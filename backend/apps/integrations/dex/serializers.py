# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for DEX integration API endpoints.
"""
from rest_framework import serializers

from apps.integrations.dex.models import DEXAggregateMetrics, DEXDeviceMetrics, DEXProvider


class DEXProviderSerializer(serializers.ModelSerializer):
    """Serializer for DEX provider configuration."""

    class Meta:
        model = DEXProvider
        fields = [
            "id",
            "correlation_id",
            "name",
            "provider_type",
            "is_enabled",
            "server_url",
            "auth_method",
            "sync_interval_minutes",
            "last_sync_at",
            "last_sync_status",
            "last_sync_error",
            "retention_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "last_sync_at",
            "last_sync_status",
            "last_sync_error",
            "created_at",
            "updated_at",
        ]


class DEXDeviceMetricsSerializer(serializers.ModelSerializer):
    """Serializer for device DEX metrics."""

    class Meta:
        model = DEXDeviceMetrics
        fields = [
            "id",
            "correlation_id",
            "device_id",
            "device_name",
            "asset",
            "dex_score",
            "performance_score",
            "stability_score",
            "responsiveness_score",
            "boot_time_seconds",
            "login_time_seconds",
            "user_sentiment",
            "sentiment_score",
            "carbon_footprint_kg",
            "power_consumption_kwh",
            "collected_at",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class DEXAggregateMetricsSerializer(serializers.ModelSerializer):
    """Serializer for aggregated DEX metrics."""

    class Meta:
        model = DEXAggregateMetrics
        fields = [
            "id",
            "correlation_id",
            "period_start",
            "period_end",
            "aggregation_type",
            "total_devices",
            "devices_with_dex",
            "avg_dex_score",
            "min_dex_score",
            "max_dex_score",
            "dex_score_std_dev",
            "avg_boot_time",
            "p50_boot_time",
            "p95_boot_time",
            "positive_sentiment_count",
            "neutral_sentiment_count",
            "negative_sentiment_count",
            "total_carbon_kg",
            "total_power_kwh",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class DEXDashboardSerializer(serializers.Serializer):
    """Serializer for dashboard summary data."""

    avg_dex_score = serializers.FloatField()
    total_devices = serializers.IntegerField()
    devices_with_dex = serializers.IntegerField()
    avg_boot_time = serializers.IntegerField(allow_null=True)
    total_carbon_kg = serializers.FloatField(allow_null=True)
    total_power_kwh = serializers.FloatField(allow_null=True)
    positive_sentiment_pct = serializers.FloatField()
    neutral_sentiment_pct = serializers.FloatField()
    negative_sentiment_pct = serializers.FloatField()


class GreenITSummarySerializer(serializers.Serializer):
    """Serializer for Green IT summary data."""

    total_carbon_kg = serializers.FloatField()
    total_power_kwh = serializers.FloatField()
    avg_carbon_per_device = serializers.FloatField()
    avg_power_per_device = serializers.FloatField()
    device_count = serializers.IntegerField()
