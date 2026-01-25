# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for resilient HTTP client.

Verifies:
- Session creation with retries and timeouts
- Circuit breaker integration
- Request/response handling
- Correlation ID tracking
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from apps.core.circuit_breaker import CircuitBreakerOpen, reset_breaker
from apps.core.http import ResilientHTTPClient, create_resilient_session, get_http_client, get_session


class TestCreateResilientSession:
    """Test resilient session creation."""

    def test_create_session_defaults(self):
        """Should create session with default settings."""
        session = create_resilient_session()

        assert session is not None
        assert session._timeout == 30  # Default timeout

    def test_create_session_custom_timeout(self):
        """Should create session with custom timeout."""
        session = create_resilient_session(timeout=60)

        assert session._timeout == 60

    def test_create_session_custom_retries(self):
        """Should create session with custom retry count."""
        session = create_resilient_session(max_retries=5)

        assert session is not None

    def test_session_has_adapters(self):
        """Should mount adapters for http and https."""
        session = create_resilient_session()

        assert "http://" in session.adapters
        assert "https://" in session.adapters


class TestGetSession:
    """Test singleton session getter."""

    def test_get_session_returns_session(self):
        """Should return a session instance."""
        session = get_session()

        assert session is not None
        assert isinstance(session, requests.Session)

    def test_get_session_singleton(self):
        """Should return same session instance."""
        session1 = get_session()
        session2 = get_session()

        assert session1 is session2


class TestResilientHTTPClient:
    """Test ResilientHTTPClient class."""

    def setup_method(self):
        """Reset breakers before each test."""
        reset_breaker("servicenow")

    def test_init_creates_session(self):
        """Should create internal session on init."""
        client = ResilientHTTPClient(service_name="servicenow")

        assert client.session is not None
        assert client.service_name == "servicenow"
        assert client.timeout == 30  # Default

    def test_init_custom_timeout(self):
        """Should accept custom timeout."""
        client = ResilientHTTPClient(service_name="servicenow", timeout=60)

        assert client.timeout == 60

    @patch.object(requests.Session, "request")
    def test_get_request(self, mock_request):
        """Should make GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = ResilientHTTPClient(service_name="servicenow")
        response = client.get("https://example.com/api")

        assert response.status_code == 200

    @patch.object(requests.Session, "request")
    def test_post_request(self, mock_request):
        """Should make POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = ResilientHTTPClient(service_name="servicenow")
        response = client.post("https://example.com/api", json={"key": "value"})

        assert response.status_code == 201

    @patch.object(requests.Session, "request")
    def test_correlation_id_added_to_headers(self, mock_request):
        """Should add correlation ID to request headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = ResilientHTTPClient(service_name="servicenow")
        client.get("https://example.com/api", correlation_id="test-correlation-123")

        # Verify correlation ID was added
        call_kwargs = mock_request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"].get("X-Correlation-ID") == "test-correlation-123"

    def test_circuit_breaker_open_raises_exception(self):
        """Should raise CircuitBreakerOpen when breaker is open."""
        client = ResilientHTTPClient(service_name="servicenow")

        # Manually open the breaker
        client.breaker._state_storage.state = "open"

        try:
            with pytest.raises(CircuitBreakerOpen):
                client.get("https://example.com/api")
        finally:
            # Reset breaker
            client.breaker.close()

    def test_all_http_methods_available(self):
        """Should have all standard HTTP methods."""
        client = ResilientHTTPClient(service_name="servicenow")

        assert callable(client.get)
        assert callable(client.post)
        assert callable(client.put)
        assert callable(client.patch)
        assert callable(client.delete)
        assert callable(client.head)
        assert callable(client.options)


class TestGetHTTPClient:
    """Test HTTP client factory."""

    def test_get_http_client_returns_client(self):
        """Should return ResilientHTTPClient instance."""
        client = get_http_client("servicenow")

        assert isinstance(client, ResilientHTTPClient)
        assert client.service_name == "servicenow"

    def test_get_http_client_caching(self):
        """Should cache clients by service name and settings."""
        client1 = get_http_client("servicenow", timeout=30)
        client2 = get_http_client("servicenow", timeout=30)

        # Same settings should return same client
        assert client1 is client2

    def test_get_http_client_different_settings(self):
        """Should return different clients for different settings."""
        client1 = get_http_client("servicenow", timeout=30)
        client2 = get_http_client("servicenow", timeout=60)

        # Different settings should return different clients
        assert client1 is not client2
