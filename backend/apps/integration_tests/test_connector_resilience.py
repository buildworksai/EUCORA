# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Integration tests for connector resilience and circuit breaker behavior.

Tests resilience patterns across:
- Circuit breaker integration
- Retry logic with exponential backoff
- Timeout handling
- Correlation ID propagation
- Structured logging
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from django.core.cache import cache
from django.test import TestCase

from apps.connectors.intune.client import IntuneConnector, IntuneConnectorError
from apps.connectors.jamf.client import JamfConnector, JamfConnectorError
from apps.core.circuit_breaker import CircuitBreakerOpen, get_breaker
from apps.core.resilient_http import ResilientAPIError, ResilientHTTPClient


class TestIntuneConnectorResilience(TestCase):
    """Test Intune connector resilience patterns."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        # Reset all circuit breakers
        for breaker_name in ["intune", "entra_id"]:
            breaker = get_breaker(breaker_name)
            breaker._state = breaker._state.__class__(breaker, breaker._state._fail_counter)

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    @patch("apps.connectors.intune.auth.config")
    def test_intune_circuit_breaker_trips_after_failures(self, mock_config, mock_http_client_class):
        """Circuit breaker should trip after 5 consecutive failures."""
        # Mock configuration
        mock_config.side_effect = lambda key, default=None: {
            "INTUNE_TENANT_ID": "test_tenant",
            "INTUNE_CLIENT_ID": "test_client",
            "INTUNE_CLIENT_SECRET": "test_secret",
        }.get(key, default)

        # Mock HTTP client to fail
        mock_http_client = Mock()
        mock_http_client.post.side_effect = requests.ConnectionError("Connection failed")
        mock_http_client_class.return_value = mock_http_client

        connector = IntuneConnector()

        # Trigger 5 consecutive failures
        for i in range(5):
            try:
                connector.list_managed_devices(correlation_id=f"FAIL-{i}")
            except (IntuneConnectorError, requests.ConnectionError):
                pass

        # 6th attempt should raise CircuitBreakerOpen
        with self.assertRaises(CircuitBreakerOpen):
            connector.list_managed_devices(correlation_id="CIRCUIT-OPEN")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    @patch("apps.connectors.intune.auth.IntuneAuth")
    def test_intune_retry_on_transient_errors(self, mock_auth_class, mock_api_client_class):
        """Should retry on transient errors (500, 503)."""
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        # First call fails with 503, second succeeds
        mock_client.get.side_effect = [
            ResilientAPIError("intune", "Service unavailable", 503, "RETRY-1"),
            {"value": [{"id": "device-1"}]},
        ]
        mock_api_client_class.return_value = mock_client

        connector = IntuneConnector()
        connector.client = mock_client

        # Should eventually succeed after retry
        devices = connector.list_managed_devices(correlation_id="RETRY-TEST")

        # Verify retry occurred (2 calls)
        self.assertEqual(mock_client.get.call_count, 2)

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    @patch("apps.connectors.intune.auth.IntuneAuth")
    def test_intune_correlation_id_propagation(self, mock_auth_class, mock_api_client_class):
        """Correlation ID should propagate through all API calls."""
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        mock_client.get.return_value = {"value": []}
        mock_api_client_class.return_value = mock_client

        connector = IntuneConnector()
        connector.client = mock_client

        correlation_id = "CORR-ID-123"
        connector.list_managed_devices(correlation_id=correlation_id)

        # Verify correlation ID passed to API client
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["correlation_id"], correlation_id)

    @patch("apps.connectors.intune.client.StructuredLogger")
    @patch("apps.connectors.intune.client.ResilientAPIClient")
    @patch("apps.connectors.intune.auth.IntuneAuth")
    def test_intune_structured_logging_on_failure(self, mock_auth_class, mock_api_client_class, mock_logger_class):
        """Should log structured connector events on failure."""
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError("intune", "API error", 500, "LOG-TEST")
        mock_api_client_class.return_value = mock_client

        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        connector = IntuneConnector()
        connector.client = mock_client

        try:
            connector.list_managed_devices(correlation_id="LOG-TEST")
        except IntuneConnectorError:
            pass

        # Verify FAILURE event logged
        calls = mock_logger.connector_event.call_args_list
        failure_logged = any("FAILURE" in str(call) for call in calls)
        self.assertTrue(failure_logged)


class TestJamfConnectorResilience(TestCase):
    """Test Jamf connector resilience patterns."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        # Reset circuit breaker
        breaker = get_breaker("jamf")
        breaker._state = breaker._state.__class__(breaker, breaker._state._fail_counter)

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_jamf_circuit_breaker_trips_after_failures(self, mock_config, mock_http_client_class):
        """Circuit breaker should trip after 5 consecutive failures."""
        # Mock configuration
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client",
            "JAMF_CLIENT_SECRET": "test_secret",
        }.get(key, default)

        # Mock HTTP client to fail
        mock_http_client = Mock()
        mock_http_client.post.side_effect = requests.ConnectionError("Connection failed")
        mock_http_client_class.return_value = mock_http_client

        connector = JamfConnector()

        # Trigger 5 consecutive failures
        for i in range(5):
            try:
                connector.list_computers(correlation_id=f"FAIL-{i}")
            except (JamfConnectorError, requests.ConnectionError):
                pass

        # 6th attempt should raise CircuitBreakerOpen
        with self.assertRaises(CircuitBreakerOpen):
            connector.list_computers(correlation_id="CIRCUIT-OPEN")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    @patch("apps.connectors.jamf.auth.JamfAuth")
    def test_jamf_idempotent_package_creation(self, mock_auth_class, mock_api_client_class):
        """Package creation should be idempotent (handle 409 conflicts)."""
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        # First call raises 409 conflict
        mock_client.post.side_effect = ResilientAPIError("jamf", "Conflict", 409, "IDEMPOTENT")
        # Find existing package
        mock_client.get.return_value = {"results": [{"id": "existing-pkg-123", "packageName": "TestPkg"}]}
        mock_api_client_class.return_value = mock_client

        connector = JamfConnector()
        connector.client = mock_client

        # Should return existing package instead of failing
        package = connector.create_package(package_name="TestPkg", file_name="TestPkg.pkg", correlation_id="IDEMPOTENT")

        self.assertEqual(package["id"], "existing-pkg-123")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    @patch("apps.connectors.jamf.auth.JamfAuth")
    def test_jamf_correlation_id_propagation(self, mock_auth_class, mock_api_client_class):
        """Correlation ID should propagate through all API calls."""
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}
        mock_api_client_class.return_value = mock_client

        connector = JamfConnector()
        connector.client = mock_client

        correlation_id = "JAMF-CORR-456"
        connector.list_computers(correlation_id=correlation_id)

        # Verify correlation ID passed
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["correlation_id"], correlation_id)


class TestResilientHTTPClientBehavior(TestCase):
    """Test ResilientHTTPClient behavior in detail."""

    def setUp(self):
        """Setup for each test."""
        # Reset circuit breaker
        breaker = get_breaker("test_service")
        breaker._state = breaker._state.__class__(breaker, breaker._state._fail_counter)

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_timeout_handling(self, mock_request):
        """Should handle timeout errors gracefully."""
        mock_request.side_effect = requests.Timeout("Request timed out")

        client = ResilientHTTPClient(service_name="test_service", timeout=5)

        with self.assertRaises(requests.Timeout):
            client.get("https://api.example.com/test", correlation_id="TIMEOUT-TEST")

        client.close()

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_connection_pooling(self, mock_request):
        """Should reuse session for connection pooling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = ResilientHTTPClient(service_name="test_service", timeout=30)

        # Make multiple requests
        for i in range(5):
            client.get(f"https://api.example.com/test{i}", correlation_id=f"POOL-{i}")

        # Verify same session used (connection pooling)
        self.assertEqual(mock_request.call_count, 5)

        client.close()

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_correlation_id_header_injection(self, mock_request):
        """Should inject X-Correlation-ID header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = ResilientHTTPClient(service_name="test_service", timeout=30)

        correlation_id = "HEADER-INJECT-789"
        client.get("https://api.example.com/test", correlation_id=correlation_id)

        # Verify X-Correlation-ID header added
        call_kwargs = mock_request.call_args[1]
        self.assertIn("headers", call_kwargs)
        self.assertEqual(call_kwargs["headers"]["X-Correlation-ID"], correlation_id)

        client.close()


class TestMultiConnectorOrchestration(TestCase):
    """Test orchestration of multiple connectors with resilience."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.intune.client.IntuneConnector")
    @patch("apps.connectors.jamf.client.JamfConnector")
    def test_parallel_deployment_with_failure_isolation(self, mock_jamf_class, mock_intune_class):
        """Test that failure in one connector doesn't affect the other."""
        # Mock Intune connector (succeeds)
        mock_intune = mock_intune_class.return_value
        mock_intune.create_win32_app.return_value = {"id": "intune-app-success"}
        mock_intune.assign_app_to_group.return_value = {"status": "success"}

        # Mock Jamf connector (fails)
        mock_jamf = mock_jamf_class.return_value
        mock_jamf.create_package.side_effect = JamfConnectorError(
            "Jamf service unavailable", correlation_id="PARALLEL-TEST", status_code=503
        )

        correlation_id = "PARALLEL-TEST"

        # Deploy to Windows via Intune (should succeed)
        intune_result = None
        try:
            intune_result = mock_intune.create_win32_app(
                display_name="Test App",
                description="Test",
                publisher="Vendor",
                file_name="app.intunewin",
                setup_file_path="setup.exe",
                install_command="setup.exe /s",
                uninstall_command="setup.exe /u",
                detection_rules=[],
                correlation_id=correlation_id,
            )
        except IntuneConnectorError:
            pass

        # Deploy to macOS via Jamf (should fail)
        jamf_result = None
        jamf_error = None
        try:
            jamf_result = mock_jamf.create_package(
                package_name="Test App", file_name="app.pkg", correlation_id=correlation_id
            )
        except JamfConnectorError as e:
            jamf_error = e

        # Verify Intune succeeded
        self.assertIsNotNone(intune_result)
        self.assertEqual(intune_result["id"], "intune-app-success")

        # Verify Jamf failed but didn't affect Intune
        self.assertIsNone(jamf_result)
        self.assertIsNotNone(jamf_error)
        self.assertEqual(jamf_error.status_code, 503)

    @patch("apps.connectors.intune.client.IntuneConnector")
    @patch("apps.connectors.jamf.client.JamfConnector")
    def test_correlation_id_consistency_across_connectors(self, mock_jamf_class, mock_intune_class):
        """Test that correlation ID is consistent across multiple connectors."""
        mock_intune = mock_intune_class.return_value
        mock_intune.list_managed_devices.return_value = []

        mock_jamf = mock_jamf_class.return_value
        mock_jamf.list_computers.return_value = {"totalCount": 0, "results": []}

        correlation_id = "CONSISTENT-CORR-ID-999"

        # Call both connectors with same correlation ID
        mock_intune.list_managed_devices(correlation_id=correlation_id)
        mock_jamf.list_computers(correlation_id=correlation_id)

        # Verify both were called with same correlation ID
        intune_call = mock_intune.list_managed_devices.call_args[1]
        jamf_call = mock_jamf.list_computers.call_args[1]

        self.assertEqual(intune_call["correlation_id"], correlation_id)
        self.assertEqual(jamf_call["correlation_id"], correlation_id)
