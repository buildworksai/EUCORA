# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Models for 1E DEX Platform integration.

Provides Digital Employee Experience (DEX) telemetry and Green IT metrics.
"""
import uuid

from django.db import models

from apps.core.encryption import EncryptedCharField
from apps.core.models import CorrelationIdModel, TimeStampedModel


class DEXProvider(TimeStampedModel, CorrelationIdModel):
    """
    1E DEX Platform connection configuration.

    Supports both live 1E API and mock data provider for development/demo.
    """

    class ProviderType(models.TextChoices):
        ONE_E = "1e", "1E DEX Platform"
        MOCK = "mock", "Mock Data Provider"

    class AuthMethod(models.TextChoices):
        NTLM = "ntlm", "Windows Authentication (NTLM)"
        BASIC = "basic", "Basic Authentication"
        API_KEY = "api_key", "API Key"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128, default="1E DEX Platform")
    provider_type = models.CharField(max_length=16, choices=ProviderType.choices, default=ProviderType.MOCK)
    is_enabled = models.BooleanField(default=True)

    # 1E Connection
    server_url = models.URLField(blank=True, null=True, help_text="1E server URL (e.g., https://1e-server.example.com)")
    auth_method = models.CharField(max_length=16, choices=AuthMethod.choices, default=AuthMethod.BASIC)
    username = EncryptedCharField(max_length=256, blank=True)
    password = EncryptedCharField(max_length=256, blank=True)
    api_key = EncryptedCharField(max_length=256, blank=True)

    # Sync Configuration
    sync_interval_minutes = models.IntegerField(default=60, help_text="Sync interval in minutes")
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=32, blank=True)
    last_sync_error = models.TextField(blank=True)

    # Data Retention
    retention_days = models.IntegerField(default=90, help_text="Days to retain DEX metrics")

    class Meta:
        verbose_name = "DEX Provider"
        verbose_name_plural = "DEX Providers"
        db_table = "integrations_dex_provider"

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class DEXDeviceMetrics(TimeStampedModel, CorrelationIdModel):
    """
    Cached DEX metrics per device.

    Stores device-level DEX scores, boot times, user sentiment, and Green IT metrics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Device identification
    device_id = models.CharField(max_length=128, db_index=True, help_text="Device identifier from 1E or mock")
    device_name = models.CharField(max_length=256, help_text="Human-readable device name")

    # Link to asset (if available)
    asset = models.ForeignKey(
        "connectors.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dex_metrics",
        help_text="Linked asset record if device matches asset inventory",
    )

    # DEX Scores (0-10 scale)
    dex_score = models.FloatField(null=True, blank=True, help_text="Overall DEX score (0-10)")
    performance_score = models.FloatField(null=True, blank=True, help_text="Performance score (0-10)")
    stability_score = models.FloatField(null=True, blank=True, help_text="Stability score (0-10)")
    responsiveness_score = models.FloatField(null=True, blank=True, help_text="Responsiveness score (0-10)")

    # Boot Metrics
    boot_time_seconds = models.IntegerField(null=True, blank=True, help_text="Boot time in seconds")
    login_time_seconds = models.IntegerField(null=True, blank=True, help_text="Login time in seconds")

    # User Sentiment
    user_sentiment = models.CharField(
        max_length=32, blank=True, help_text="User sentiment: Positive, Neutral, or Negative"
    )
    sentiment_score = models.FloatField(
        null=True, blank=True, help_text="Sentiment score (-1 to 1, where 1 is most positive)"
    )

    # Green IT
    carbon_footprint_kg = models.FloatField(
        null=True, blank=True, help_text="Annual estimated carbon footprint in kg CO2"
    )
    power_consumption_kwh = models.FloatField(null=True, blank=True, help_text="Monthly power consumption in kWh")

    # Metadata
    collected_at = models.DateTimeField(help_text="When metrics were collected from source")
    source = models.CharField(max_length=16, default="1e", help_text="Source: '1e' or 'mock'")

    class Meta:
        verbose_name = "DEX Device Metrics"
        verbose_name_plural = "DEX Device Metrics"
        db_table = "integrations_dex_device_metrics"
        indexes = [
            models.Index(fields=["device_id", "collected_at"]),
            models.Index(fields=["asset", "collected_at"]),
            models.Index(fields=["collected_at"]),
        ]
        get_latest_by = "collected_at"

    def __str__(self):
        return f"{self.device_name} ({self.device_id}) - DEX: {self.dex_score or 'N/A'}"


class DEXAggregateMetrics(TimeStampedModel, CorrelationIdModel):
    """
    Aggregated DEX metrics for dashboards.

    Pre-computed aggregates for hourly, daily, or weekly periods to enable fast dashboard queries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Aggregation period
    period_start = models.DateTimeField(db_index=True, help_text="Start of aggregation period")
    period_end = models.DateTimeField(help_text="End of aggregation period")
    aggregation_type = models.CharField(max_length=16, help_text="Type: 'hourly', 'daily', or 'weekly'")

    # Device counts
    total_devices = models.IntegerField(default=0, help_text="Total devices in period")
    devices_with_dex = models.IntegerField(default=0, help_text="Devices with DEX scores")

    # DEX Scores
    avg_dex_score = models.FloatField(null=True, blank=True, help_text="Average DEX score")
    min_dex_score = models.FloatField(null=True, blank=True, help_text="Minimum DEX score")
    max_dex_score = models.FloatField(null=True, blank=True, help_text="Maximum DEX score")
    dex_score_std_dev = models.FloatField(null=True, blank=True, help_text="Standard deviation of DEX scores")

    # Boot Time
    avg_boot_time = models.IntegerField(null=True, blank=True, help_text="Average boot time in seconds")
    p50_boot_time = models.IntegerField(null=True, blank=True, help_text="50th percentile boot time")
    p95_boot_time = models.IntegerField(null=True, blank=True, help_text="95th percentile boot time")

    # Sentiment Distribution
    positive_sentiment_count = models.IntegerField(default=0, help_text="Devices with positive sentiment")
    neutral_sentiment_count = models.IntegerField(default=0, help_text="Devices with neutral sentiment")
    negative_sentiment_count = models.IntegerField(default=0, help_text="Devices with negative sentiment")

    # Green IT
    total_carbon_kg = models.FloatField(null=True, blank=True, help_text="Total carbon footprint in kg CO2")
    total_power_kwh = models.FloatField(null=True, blank=True, help_text="Total power consumption in kWh")

    class Meta:
        verbose_name = "DEX Aggregate Metrics"
        verbose_name_plural = "DEX Aggregate Metrics"
        db_table = "integrations_dex_aggregate_metrics"
        indexes = [
            models.Index(fields=["period_start", "aggregation_type"]),
        ]
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.aggregation_type} aggregate ({self.period_start} - {self.period_end})"
