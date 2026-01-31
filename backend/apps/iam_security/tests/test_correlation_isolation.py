# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for IAM Security.
"""
import pytest
from django.utils import timezone

from apps.iam_security.models import AnomalyDetection, IdentityProvider, SecurityAlert


@pytest.fixture
def provider():
    """Create a test identity provider."""
    return IdentityProvider.objects.create(
        name="Test Provider",
        provider_type=IdentityProvider.ProviderType.ENTRA_ID,
        connection_config={},
    )


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation."""

    def test_anomaly_correlation_id_generated(self, provider):
        """Verify correlation_id is auto-generated."""
        anomaly = AnomalyDetection.objects.create(
            provider=provider,
            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
            severity=AnomalyDetection.Severity.HIGH,
            user_principal="user@example.com",
            description="Test",
            evidence={},
            detection_rule="test",
        )
        assert anomaly.correlation_id is not None

    def test_alert_correlation_id_generated(self, provider):
        """Verify correlation_id is auto-generated."""
        anomaly = AnomalyDetection.objects.create(
            provider=provider,
            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
            severity=AnomalyDetection.Severity.CRITICAL,
            user_principal="user@example.com",
            description="Test",
            evidence={},
            detection_rule="test",
        )
        alert = SecurityAlert.objects.create(
            anomaly=anomaly,
            channel=SecurityAlert.Channel.EMAIL,
            recipients=["admin@example.com"],
            subject="Test",
            body="Test",
            sent_at=timezone.now(),
        )
        assert alert.correlation_id is not None

    def test_correlation_id_filtering(self, provider):
        """Verify filtering by correlation_id works."""
        anomaly1 = AnomalyDetection.objects.create(
            provider=provider,
            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
            severity=AnomalyDetection.Severity.HIGH,
            user_principal="user1@example.com",
            description="Test 1",
            evidence={},
            detection_rule="test",
        )
        anomaly2 = AnomalyDetection.objects.create(  # noqa: F841
            provider=provider,
            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
            severity=AnomalyDetection.Severity.HIGH,
            user_principal="user2@example.com",
            description="Test 2",
            evidence={},
            detection_rule="test",
        )

        filtered = AnomalyDetection.objects.filter(correlation_id=anomaly1.correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == anomaly1
