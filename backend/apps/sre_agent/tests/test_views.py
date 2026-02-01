# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SRE Agent views.
"""
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.sre_agent.models import HealthCheckResult, HealthEndpoint, MonitoringPlatform, Runbook, SelfHealingRule

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Create authenticated API client."""
    user = User.objects.create_user(username="testuser", password="testpass")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestMonitoringPlatformViewSet:
    """Test MonitoringPlatformViewSet."""

    def test_list_platforms(self, authenticated_client):
        """Test listing monitoring platforms."""
        MonitoringPlatform.objects.create(
            name="Test Prometheus",
            platform_type=MonitoringPlatform.PlatformType.PROMETHEUS,
            connection_config={"api_url": "https://prometheus.example.com"},
        )

        response = authenticated_client.get("/api/sre/monitoring-platforms/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_filter_by_platform_type(self, authenticated_client):
        """Test filtering platforms by type."""
        MonitoringPlatform.objects.create(
            name="Test Prometheus",
            platform_type=MonitoringPlatform.PlatformType.PROMETHEUS,
            connection_config={},
        )
        MonitoringPlatform.objects.create(
            name="Test Datadog",
            platform_type=MonitoringPlatform.PlatformType.DATADOG,
            connection_config={},
        )

        response = authenticated_client.get("/api/sre/monitoring-platforms/?platform_type=prometheus")
        assert response.status_code == 200
        assert all(p["platform_type"] == "prometheus" for p in response.data["results"])

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    def test_test_connection_prometheus_success(self, mock_http_client_class, authenticated_client):
        """Test Prometheus connection test succeeds."""
        platform = MonitoringPlatform.objects.create(
            name="Test Prometheus",
            platform_type=MonitoringPlatform.PlatformType.PROMETHEUS,
            connection_config={"api_url": "https://prometheus.example.com"},
        )

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        response = authenticated_client.post(f"/api/sre/monitoring-platforms/{platform.id}/test/")
        assert response.status_code == 200
        assert response.data["success"] is True

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    def test_test_connection_datadog_success(self, mock_http_client_class, authenticated_client):
        """Test Datadog connection test succeeds."""
        platform = MonitoringPlatform.objects.create(
            name="Test Datadog",
            platform_type=MonitoringPlatform.PlatformType.DATADOG,
            connection_config={
                "api_url": "https://api.datadoghq.com",
                "api_key": "test-key",  # pragma: allowlist secret
            },
        )

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        response = authenticated_client.post(f"/api/sre/monitoring-platforms/{platform.id}/test/")
        assert response.status_code == 200
        assert response.data["success"] is True

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    def test_test_connection_azure_monitor(self, mock_http_client_class, authenticated_client):
        """Test Azure Monitor connection test."""
        platform = MonitoringPlatform.objects.create(
            name="Test Azure Monitor",
            platform_type=MonitoringPlatform.PlatformType.AZURE_MONITOR,
            connection_config={
                "api_url": "https://management.azure.com",
                "api_key": "test-token",  # pragma: allowlist secret
            },
        )

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        response = authenticated_client.post(f"/api/sre/monitoring-platforms/{platform.id}/test/")
        assert response.status_code == 200

    def test_test_connection_no_api_url(self, authenticated_client):
        """Test connection test fails when API URL missing."""
        platform = MonitoringPlatform.objects.create(
            name="Test Platform",
            platform_type=MonitoringPlatform.PlatformType.PROMETHEUS,
            connection_config={},
        )

        response = authenticated_client.post(f"/api/sre/monitoring-platforms/{platform.id}/test/")
        assert response.status_code == 400
        assert "API URL not configured" in response.data["error"]


@pytest.mark.django_db
class TestHealthEndpointViewSet:
    """Test HealthEndpointViewSet."""

    def test_list_endpoints(self, authenticated_client):
        """Test listing health endpoints."""
        HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
        )

        response = authenticated_client.get("/api/sre/health-endpoints/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    @patch("apps.sre_agent.views.time")
    def test_check_endpoint_success(self, mock_time_module, mock_http_client_class, authenticated_client):
        """Test health endpoint check succeeds."""
        endpoint = HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
        )

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        # Mock time.time() to simulate response time
        mock_time_module.time.side_effect = [1000.0, 1000.1]  # 0.1 second difference

        response = authenticated_client.post(f"/api/sre/health-endpoints/{endpoint.id}/check/")
        assert response.status_code == 200
        assert response.data["status"] == "healthy"
        assert response.data["response_time_ms"] > 0

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    def test_check_endpoint_failure(self, mock_http_client_class, authenticated_client):
        """Test health endpoint check fails."""
        endpoint = HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
        )

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        response = authenticated_client.post(f"/api/sre/health-endpoints/{endpoint.id}/check/")
        assert response.status_code == 200
        assert response.data["status"] == "unhealthy"

    @patch("apps.sre_agent.views.ResilientHTTPClient")
    def test_check_endpoint_timeout(self, mock_http_client_class, authenticated_client):
        """Test health endpoint check handles timeout."""
        import requests

        endpoint = HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
        )

        mock_client = Mock()
        mock_client.get.side_effect = requests.exceptions.Timeout("Connection timeout")
        mock_http_client_class.return_value = mock_client

        response = authenticated_client.post(f"/api/sre/health-endpoints/{endpoint.id}/check/")
        # Timeout should return 500 status with unhealthy result
        assert response.status_code in [200, 500]
        assert response.data["status"] == "unhealthy"

    def test_history(self, authenticated_client):
        """Test getting health check history."""
        endpoint = HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://api.example.com/health",
        )

        HealthCheckResult.objects.create(
            endpoint=endpoint,
            status=HealthCheckResult.Status.HEALTHY,
            response_time_ms=100,
        )

        response = authenticated_client.get(f"/api/sre/health-endpoints/{endpoint.id}/history/")
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestRunbookViewSet:
    """Test RunbookViewSet."""

    def test_list_runbooks(self, authenticated_client):
        """Test listing runbooks."""
        Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="incident_response",
            estimated_duration_minutes=30,
        )

        response = authenticated_client.get("/api/sre/runbooks/")
        assert response.status_code == 200
        # Handle paginated or non-paginated responses
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    @patch("subprocess.run")
    def test_execute_runbook_automated(self, mock_subprocess_run, authenticated_client):
        """Test executing automated runbook."""
        runbook = Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="incident_response",
            estimated_duration_minutes=30,
            steps=[
                {
                    "type": "automated",
                    "command": "echo 'test'",
                    "name": "Test step",
                }
            ],
        )

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "test output"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        response = authenticated_client.post(f"/api/sre/runbooks/{runbook.id}/execute/")
        assert response.status_code == 200
        assert response.data["status"] in ["completed", "in_progress"]

    def test_execute_runbook_manual(self, authenticated_client):
        """Test executing runbook with manual steps."""
        runbook = Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="incident_response",
            estimated_duration_minutes=30,
            steps=[
                {
                    "type": "manual",
                    "name": "Manual step",
                    "description": "Do something",
                }
            ],
        )

        response = authenticated_client.post(f"/api/sre/runbooks/{runbook.id}/execute/")
        assert response.status_code == 200
        # Manual steps should be marked as pending or in_progress
        assert response.data["status"] in ["in_progress", "completed", "pending"]

    @patch("subprocess.run")
    def test_execute_runbook_failure(self, mock_subprocess_run, authenticated_client):
        """Test runbook execution failure."""
        runbook = Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="incident_response",
            estimated_duration_minutes=30,
            steps=[
                {
                    "type": "automated",
                    "command": "exit 1",
                    "name": "Failing step",
                }
            ],
        )

        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_process

        response = authenticated_client.post(f"/api/sre/runbooks/{runbook.id}/execute/")
        # Should handle failure gracefully
        assert response.status_code == 200
        assert response.data["status"] in ["failed", "completed", "in_progress"]


@pytest.mark.django_db
class TestSelfHealingRuleViewSet:
    """Test SelfHealingRuleViewSet."""

    def test_list_rules(self, authenticated_client):
        """Test listing self-healing rules."""
        SelfHealingRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test.ps1",
            script_type=SelfHealingRule.ScriptType.POWERSHELL,
        )

        response = authenticated_client.get("/api/sre/self-healing-rules/")
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_filter_by_risk_level(self, authenticated_client):
        """Test filtering rules by risk level."""
        SelfHealingRule.objects.create(
            name="Low Risk Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test.ps1",
            risk_level="low",
        )
        SelfHealingRule.objects.create(
            name="High Risk Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test.ps1",
            risk_level="high",
        )

        response = authenticated_client.get("/api/sre/self-healing-rules/?risk_level=high")
        assert response.status_code == 200
        # Handle paginated or non-paginated responses
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert all(r["risk_level"] == "high" for r in data)
