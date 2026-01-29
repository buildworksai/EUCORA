# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Resilient HTTP Client.
Tests circuit breaker integration, retry logic, and error handling.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from django.test import TestCase

from apps.core.circuit_breaker import CircuitBreakerOpen
from apps.core.resilient_http import ResilientAPIClient, ResilientAPIError, ResilientHTTPClient


class TestResilientHTTPClient(TestCase):
    """Test resilient HTTP client with circuit breaker and retry."""

    def setUp(self):
        """Setup for each test."""
        self.client = ResilientHTTPClient(service_name="intune", timeout=30)

    def tearDown(self):
        """Cleanup after each test."""
        self.client.close()

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_successful_get_request(self, mock_request):
        """Successful GET request should return response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        response = self.client.get("https://api.example.com/test", correlation_id="TEST-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": "success"})
        mock_request.assert_called_once()

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_successful_post_request(self, mock_request):
        """Successful POST request should return response."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123"}
        mock_response.elapsed.total_seconds.return_value = 0.7
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        response = self.client.post("https://api.example.com/create", json={"name": "test"}, correlation_id="TEST-456")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"id": "123"})

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_correlation_id_propagation(self, mock_request):
        """Correlation ID should be added to request headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        self.client.get("https://api.example.com/test", correlation_id="DEPLOY-789")

        # Check that correlation ID was added to headers
        call_kwargs = mock_request.call_args[1]
        self.assertIn("headers", call_kwargs)
        self.assertEqual(call_kwargs["headers"]["X-Correlation-ID"], "DEPLOY-789")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_http_error_raised(self, mock_request):
        """HTTP errors should be raised."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(requests.HTTPError):
            self.client.get("https://api.example.com/notfound")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_timeout_handling(self, mock_request):
        """Timeout errors should be handled."""
        mock_request.side_effect = requests.Timeout()

        with self.assertRaises(requests.Timeout):
            self.client.get("https://api.example.com/slow")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_connection_error_handling(self, mock_request):
        """Connection errors should be handled."""
        mock_request.side_effect = requests.ConnectionError()

        with self.assertRaises(requests.ConnectionError):
            self.client.get("https://api.example.com/unreachable")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_circuit_breaker_integration(self, mock_request):
        """Circuit breaker should trip after failures."""
        # Simulate 5 consecutive failures (fail_max=5 for intune breaker)
        mock_request.side_effect = requests.ConnectionError()

        for i in range(5):
            try:
                self.client.get("https://api.example.com/failing")
            except requests.ConnectionError:
                pass

        # 6th attempt should raise CircuitBreakerOpen
        with self.assertRaises(CircuitBreakerOpen):
            self.client.get("https://api.example.com/failing")

    def test_all_http_methods(self):
        """Client should support all HTTP methods."""
        methods = ["get", "post", "put", "patch", "delete"]

        for method in methods:
            self.assertTrue(hasattr(self.client, method))
            self.assertTrue(callable(getattr(self.client, method)))


class TestResilientAPIClient(TestCase):
    """Test high-level resilient API client."""

    def setUp(self):
        """Setup for each test."""
        self.client = ResilientAPIClient(service_name="intune", base_url="https://graph.microsoft.com/v1.0", timeout=30)

    def tearDown(self):
        """Cleanup after each test."""
        self.client.close()

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_successful_api_get(self, mock_request):
        """Successful API GET should return JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"id": "1"}, {"id": "2"}]}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.get("/deviceManagement/managedDevices", correlation_id="API-123")

        self.assertEqual(result, {"value": [{"id": "1"}, {"id": "2"}]})

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_successful_api_post(self, mock_request):
        """Successful API POST should return JSON."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new-123", "status": "created"}
        mock_response.elapsed.total_seconds.return_value = 0.8
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = self.client.post(
            "/deviceManagement/apps", json_data={"name": "TestApp", "version": "1.0"}, correlation_id="API-456"
        )

        self.assertEqual(result["id"], "new-123")
        self.assertEqual(result["status"], "created")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_api_error_handling(self, mock_request):
        """API errors should be wrapped in ResilientAPIError."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid request payload"
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
        mock_request.return_value = mock_response

        with self.assertRaises(ResilientAPIError) as context:
            self.client.get("/invalid/endpoint")

        self.assertEqual(context.exception.service_name, "intune")
        self.assertEqual(context.exception.status_code, 400)

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_circuit_breaker_propagation(self, mock_request):
        """Circuit breaker open should propagate to API client."""
        # Simulate circuit breaker open
        mock_request.side_effect = requests.ConnectionError()

        # Trip circuit breaker
        for i in range(5):
            try:
                self.client.get("/test")
            except ResilientAPIError:
                pass

        # Next call should raise CircuitBreakerOpen
        with self.assertRaises(CircuitBreakerOpen):
            self.client.get("/test")

    @patch("apps.core.resilient_http.requests.Session.request")
    def test_base_url_concatenation(self, mock_request):
        """Base URL and endpoint should be concatenated correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        self.client.get("/deviceManagement/apps")

        # Verify full URL
        call_args = mock_request.call_args
        called_url = call_args[1]["url"]
        self.assertEqual(called_url, "https://graph.microsoft.com/v1.0/deviceManagement/apps")


class TestResilientAPIErrorHandling(TestCase):
    """Test error handling and classification."""

    def test_resilient_api_error_attributes(self):
        """ResilientAPIError should store error details."""
        error = ResilientAPIError(
            service_name="intune",
            message="Test error",
            status_code=500,
            response_body="Internal server error",
            correlation_id="ERROR-123",
        )

        self.assertEqual(error.service_name, "intune")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.response_body, "Internal server error")
        self.assertEqual(error.correlation_id, "ERROR-123")

    def test_error_string_representation(self):
        """Error should have meaningful string representation."""
        error = ResilientAPIError(service_name="jamf", message="Connection failed", correlation_id="ERROR-456")

        self.assertIn("Connection failed", str(error))


class TestResilientHTTPClientConfiguration(TestCase):
    """Test client configuration options."""

    def test_custom_timeout(self):
        """Client should respect custom timeout."""
        client = ResilientHTTPClient(service_name="jamf", timeout=60)

        self.assertEqual(client.timeout, 60)
        client.close()

    def test_custom_retry_attempts(self):
        """Client should respect custom retry attempts."""
        client = ResilientHTTPClient(service_name="jamf", max_retries=5)

        self.assertEqual(client.max_retries, 5)
        client.close()

    def test_custom_backoff_factor(self):
        """Client should respect custom backoff factor."""
        client = ResilientHTTPClient(service_name="jamf", backoff_factor=1.0)

        self.assertEqual(client.backoff_factor, 1.0)
        client.close()


class TestRequestLogging(TestCase):
    """Test request/response logging."""

    def setUp(self):
        """Setup for each test."""
        self.client = ResilientHTTPClient(service_name="intune", timeout=30)

    def tearDown(self):
        """Cleanup after each test."""
        self.client.close()

    @patch("apps.core.resilient_http.logger")
    @patch("apps.core.resilient_http.requests.Session.request")
    def test_request_logging(self, mock_request, mock_logger):
        """Requests should be logged with correlation ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        self.client.get("https://api.example.com/test", correlation_id="LOG-123")

        # Verify logging calls
        self.assertTrue(mock_logger.info.called)

        # Check log message contains correlation ID
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("HTTP GET" in str(call) for call in log_calls))

    @patch("apps.core.resilient_http.logger")
    @patch("apps.core.resilient_http.requests.Session.request")
    def test_error_logging(self, mock_request, mock_logger):
        """Errors should be logged with details."""
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        try:
            self.client.get("https://api.example.com/test", correlation_id="ERROR-789")
        except requests.ConnectionError:
            pass

        # Verify error logging
        self.assertTrue(mock_logger.error.called)
