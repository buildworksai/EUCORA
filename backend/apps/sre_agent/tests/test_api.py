# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for SRE Agent.
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.sre_agent.models import HealthEndpoint, SelfHealingRule, SLODefinition


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, django_user_model):
    """Create authenticated API client."""
    user = django_user_model.objects.create_user(username="testuser", password="testpass")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestHealthEndpointAPI:
    """Test HealthEndpoint API endpoints."""

    def test_list_endpoints(self, authenticated_client):
        """Test listing health endpoints."""
        HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://example.com/health",
        )
        response = authenticated_client.get("/api/sre/health-endpoints/")
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestSLODefinitionAPI:
    """Test SLODefinition API endpoints."""

    def test_list_slos(self, authenticated_client):
        """Test listing SLO definitions."""
        SLODefinition.objects.create(
            name="Test SLO",
            service_name="test-service",
            slo_type=SLODefinition.SLOType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
            measurement_window=SLODefinition.MeasurementWindow.DAILY,
        )
        response = authenticated_client.get("/api/sre/slos/")
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestSelfHealingRuleAPI:
    """Test SelfHealingRule API endpoints."""

    def test_list_rules(self, authenticated_client):
        """Test listing self-healing rules."""
        SelfHealingRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test",
        )
        response = authenticated_client.get("/api/sre/self-healing-rules/")
        assert response.status_code == 200
        assert len(response.data) >= 1
