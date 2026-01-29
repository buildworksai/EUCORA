# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Integration tests for connector services.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from apps.connectors.services import PowerShellConnectorService, get_connector_service


@pytest.mark.django_db
class TestPowerShellConnectorService:
    """Integration tests for PowerShell connector service."""

    @patch("subprocess.run")
    def test_health_check_healthy(self, mock_subprocess):
        """Test health check returns healthy status."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "healthy"}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = PowerShellConnectorService()
        result = service.health_check("intune")

        assert result["status"] == "healthy"
        assert "intune".upper() in result["message"].upper()

    @patch("subprocess.run")
    def test_health_check_unhealthy(self, mock_subprocess):
        """Test health check returns unhealthy status on failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Connection failed"
        mock_subprocess.return_value = mock_result

        service = PowerShellConnectorService()
        result = service.health_check("intune")

        assert result["status"] == "unhealthy"
        assert "failed" in result["message"].lower()

    @patch("subprocess.run")
    def test_health_check_timeout(self, mock_subprocess):
        """Test health check handles timeout."""
        import subprocess

        mock_subprocess.side_effect = subprocess.TimeoutExpired("pwsh", 30)

        service = PowerShellConnectorService()
        result = service.health_check("intune")

        assert result["status"] == "unhealthy"
        assert "timeout" in result["message"].lower()

    @patch("subprocess.run")
    def test_deploy_success(self, mock_subprocess):
        """Test deploy returns success status."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"object_id": "test-id-123"}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = PowerShellConnectorService()
        result = service.deploy(
            "intune",
            {
                "deployment_intent_id": "test-intent",
                "artifact_path": "/path/to/artifact",
                "target_ring": "canary",
                "app_name": "TestApp",
                "version": "1.0.0",
            },
        )

        assert result["status"] == "success"
        assert result["connector_object_id"] == "test-id-123"

    @patch("subprocess.run")
    def test_deploy_failure(self, mock_subprocess):
        """Test deploy returns failure status on error."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Deployment failed"
        mock_subprocess.return_value = mock_result

        service = PowerShellConnectorService()
        result = service.deploy(
            "intune",
            {
                "deployment_intent_id": "test-intent",
                "artifact_path": "/path/to/artifact",
                "target_ring": "canary",
                "app_name": "TestApp",
                "version": "1.0.0",
            },
        )

        assert result["status"] == "failed"
        assert result["connector_object_id"] is None

    def test_health_check_unknown_connector(self):
        """Test health check returns unhealthy for unknown connector."""
        service = PowerShellConnectorService()
        result = service.health_check("unknown")

        assert result["status"] == "unhealthy"
        assert "unknown" in result["message"].lower()

    def test_deploy_unknown_connector(self):
        """Test deploy returns failure for unknown connector."""
        service = PowerShellConnectorService()
        result = service.deploy(
            "unknown",
            {
                "deployment_intent_id": "test-intent",
                "artifact_path": "/path/to/artifact",
                "target_ring": "canary",
                "app_name": "TestApp",
                "version": "1.0.0",
            },
        )

        assert result["status"] == "failed"
        assert result["connector_object_id"] is None


@pytest.mark.django_db
class TestConnectorServiceSingleton:
    """Test connector service singleton pattern."""

    def test_get_connector_service_returns_singleton(self):
        """Test that get_connector_service returns singleton instance."""
        service1 = get_connector_service()
        service2 = get_connector_service()

        assert service1 is service2
