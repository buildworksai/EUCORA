# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for DEX models.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.integrations.dex.models import DEXAggregateMetrics, DEXDeviceMetrics, DEXProvider


@pytest.mark.django_db
class TestDEXProvider:
    """Tests for DEXProvider model."""

    def test_create_provider(self):
        """Test creating a DEX provider."""
        provider = DEXProvider.objects.create(
            name="Test Provider",
            provider_type=DEXProvider.ProviderType.MOCK,
            is_enabled=True,
        )
        assert provider.id is not None
        assert provider.correlation_id is not None
        assert provider.provider_type == DEXProvider.ProviderType.MOCK

    def test_provider_str(self):
        """Test provider string representation."""
        provider = DEXProvider.objects.create(
            name="Test Provider",
            provider_type=DEXProvider.ProviderType.ONE_E,
        )
        assert "Test Provider" in str(provider)
        assert "1E DEX Platform" in str(provider)


@pytest.mark.django_db
class TestDEXDeviceMetrics:
    """Tests for DEXDeviceMetrics model."""

    def test_create_device_metrics(self):
        """Test creating device metrics."""
        metrics = DEXDeviceMetrics.objects.create(
            device_id="TEST-DEV-001",
            device_name="Test Device",
            dex_score=8.5,
            boot_time_seconds=30,
            collected_at=timezone.now(),
        )
        assert metrics.id is not None
        assert metrics.correlation_id is not None
        assert metrics.dex_score == 8.5

    def test_device_metrics_str(self):
        """Test device metrics string representation."""
        metrics = DEXDeviceMetrics.objects.create(
            device_id="TEST-DEV-001",
            device_name="Test Device",
            dex_score=8.5,
            collected_at=timezone.now(),
        )
        assert "Test Device" in str(metrics)
        assert "TEST-DEV-001" in str(metrics)


@pytest.mark.django_db
class TestDEXAggregateMetrics:
    """Tests for DEXAggregateMetrics model."""

    def test_create_aggregate_metrics(self):
        """Test creating aggregate metrics."""
        period_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)

        aggregate = DEXAggregateMetrics.objects.create(
            period_start=period_start,
            period_end=period_end,
            aggregation_type="daily",
            total_devices=100,
            devices_with_dex=95,
            avg_dex_score=7.5,
        )
        assert aggregate.id is not None
        assert aggregate.correlation_id is not None
        assert aggregate.total_devices == 100
