# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for IAM Security.
"""
import pytest
from django.utils import timezone

from apps.iam_security.models import AnomalyDetection, IdentityProvider, SecurityAlert, SignInEvent


@pytest.fixture
def provider():
    """Create a test identity provider."""
    return IdentityProvider.objects.create(
        name="Test Entra ID",
        provider_type=IdentityProvider.ProviderType.ENTRA_ID,
        tenant_id="test-tenant-id",
        connection_config={"client_id": "test", "client_secret": "test"},
    )


@pytest.mark.django_db
class TestIdentityProvider:
    """Test IdentityProvider model."""

    def test_create_provider(self):
        """Test provider creation."""
        provider = IdentityProvider.objects.create(
            name="Test Provider",
            provider_type=IdentityProvider.ProviderType.OKTA,
            connection_config={},
        )
        assert provider.name == "Test Provider"
        assert provider.provider_type == IdentityProvider.ProviderType.OKTA
        assert provider.is_active is True


@pytest.mark.django_db
class TestSignInEvent:
    """Test SignInEvent model."""

    def test_create_sign_in_event(self, provider):
        """Test sign-in event creation."""
        event = SignInEvent.objects.create(
            provider=provider,
            event_id="test-event-123",
            user_principal="user@example.com",
            user_display_name="Test User",
            status=SignInEvent.Status.SUCCESS,
            event_time=timezone.now(),
        )
        assert event.provider == provider
        assert event.user_principal == "user@example.com"
        assert event.status == SignInEvent.Status.SUCCESS


@pytest.mark.django_db
class TestAnomalyDetection:
    """Test AnomalyDetection model."""

    def test_create_anomaly(self, provider):
        """Test anomaly creation."""
        anomaly = AnomalyDetection.objects.create(
            provider=provider,
            anomaly_type=AnomalyDetection.AnomalyType.SUSPICIOUS_LOGIN,
            severity=AnomalyDetection.Severity.HIGH,
            user_principal="user@example.com",
            description="Test anomaly",
            evidence={},
            detection_rule="test_rule",
        )
        assert anomaly.provider == provider
        assert anomaly.severity == AnomalyDetection.Severity.HIGH
        assert anomaly.correlation_id is not None
        assert anomaly.status == AnomalyDetection.Status.NEW


@pytest.mark.django_db
class TestSecurityAlert:
    """Test SecurityAlert model."""

    def test_create_alert(self, provider):
        """Test alert creation."""
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
            subject="Test Alert",
            body="Test body",
            sent_at=timezone.now(),
        )
        assert alert.anomaly == anomaly
        assert alert.channel == SecurityAlert.Channel.EMAIL
        assert alert.correlation_id is not None
