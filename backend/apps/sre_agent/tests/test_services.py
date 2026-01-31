# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for SRE Agent.
"""
import pytest
from django.utils import timezone

from apps.sre_agent.models import HealthEndpoint, SLODefinition


@pytest.mark.django_db
class TestHealthEndpointService:
    """Test health endpoint service."""

    def test_health_endpoint_creation(self):
        """Test creating health endpoint."""
        endpoint = HealthEndpoint.objects.create(
            name="Test API",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
        )
        assert endpoint.name == "Test API"
        assert endpoint.is_active is True


@pytest.mark.django_db
class TestSLOService:
    """Test SLO service."""

    def test_slo_creation(self):
        """Test creating SLO definition."""
        slo = SLODefinition.objects.create(
            name="API Availability",
            service_name="api-service",
            slo_type=SLODefinition.SLOType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
            measurement_window=SLODefinition.MeasurementWindow.DAILY,
        )
        assert slo.name == "API Availability"
        assert slo.target_value == 99.9
