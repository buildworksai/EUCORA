# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for telemetry app.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestHealthCheck:
    """Test health check endpoints."""

    def test_health_check_endpoint(self, api_client):
        """Test health check endpoint returns correct structure."""
        url = reverse("telemetry:health")
        response = api_client.get(url)

        assert response.status_code in [200, 503]
        assert "status" in response.data
        assert "checks" in response.data
        assert "database" in response.data["checks"]
        assert "cache" in response.data["checks"]
        assert "application" in response.data["checks"]

    def test_liveness_check(self, api_client):
        """Test liveness check always returns 200."""
        url = reverse("telemetry:liveness")
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["status"] == "alive"

    def test_readiness_check(self, api_client):
        """Test readiness check."""
        url = reverse("telemetry:readiness")
        response = api_client.get(url)

        # Readiness check should return same structure as health check
        assert response.status_code in [200, 503]
        assert "status" in response.data
        assert "checks" in response.data
