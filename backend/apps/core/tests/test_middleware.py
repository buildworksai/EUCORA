# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for CorrelationIdMiddleware.
"""
import pytest
from django.test import RequestFactory

from apps.core.middleware import CorrelationIdMiddleware


@pytest.mark.django_db
class TestCorrelationIdMiddleware:
    """Test CorrelationIdMiddleware functionality."""

    def test_generates_correlation_id_when_missing(self):
        """Test that middleware generates correlation ID when not in headers."""
        middleware = CorrelationIdMiddleware(lambda request: None)
        factory = RequestFactory()
        request = factory.get("/test")

        middleware.process_request(request)

        assert hasattr(request, "correlation_id")
        assert request.correlation_id is not None
        assert len(request.correlation_id) == 36  # UUID format

    def test_uses_existing_correlation_id_from_header(self):
        """Test that middleware uses correlation ID from X-Correlation-ID header."""
        middleware = CorrelationIdMiddleware(lambda request: None)
        factory = RequestFactory()
        existing_id = "123e4567-e89b-12d3-a456-426614174000"
        request = factory.get("/test", HTTP_X_CORRELATION_ID=existing_id)

        middleware.process_request(request)

        assert request.correlation_id == existing_id

    def test_adds_correlation_id_to_response(self):
        """Test that middleware adds correlation ID to response headers."""
        middleware = CorrelationIdMiddleware(lambda request: None)
        factory = RequestFactory()
        request = factory.get("/test")

        middleware.process_request(request)

        from django.http import HttpResponse

        response = HttpResponse()
        response = middleware.process_response(request, response)

        assert "X-Correlation-ID" in response
        assert response["X-Correlation-ID"] == request.correlation_id

    def test_creates_logger_adapter(self):
        """Test that middleware creates logger adapter with correlation ID."""
        middleware = CorrelationIdMiddleware(lambda request: None)
        factory = RequestFactory()
        request = factory.get("/test")

        middleware.process_request(request)

        assert hasattr(request, "logger")
        assert request.logger.extra["correlation_id"] == request.correlation_id
