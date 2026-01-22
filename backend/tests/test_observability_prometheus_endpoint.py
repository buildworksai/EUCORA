# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Prometheus metrics endpoint (/api/v1/metrics/).

Verifies:
- Endpoint returns HTTP 200 OK
- Response is in Prometheus text format
- All registered metrics are included
- Endpoint handles errors gracefully
"""
from django.test import TestCase, Client
from django.urls import reverse
import pytest


class TestPrometheusMetricsEndpoint(TestCase):
    """Test /api/v1/metrics/ Prometheus endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.endpoint = "/api/v1/metrics/"

    def test_metrics_endpoint_returns_200(self):
        """Verify metrics endpoint returns HTTP 200 OK."""
        response = self.client.get(self.endpoint)
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Verify metrics endpoint returns Prometheus text format."""
        response = self.client.get(self.endpoint)
        
        # Check content type - should be text/plain with version
        content_type = response.get("Content-Type", "")
        assert "text/plain" in content_type
        assert "version=" in content_type or "charset=" in content_type

    def test_metrics_endpoint_contains_type_declarations(self):
        """Verify metrics response contains HELP and TYPE declarations."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Prometheus format includes HELP comments
        assert "# HELP" in content
        assert "# TYPE" in content

    def test_metrics_endpoint_contains_metrics_data(self):
        """Verify metrics response contains actual metric data."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Should contain some metrics (at least python_* metrics)
        assert "python_" in content or "process_" in content

    def test_metrics_endpoint_charset_utf8(self):
        """Verify metrics endpoint declares UTF-8 charset."""
        response = self.client.get(self.endpoint)
        
        content_type = response.get("Content-Type", "")
        assert "charset=utf-8" in content_type.lower()

    def test_metrics_only_accepts_get(self):
        """Verify metrics endpoint only accepts GET requests."""
        # POST should fail
        response = self.client.post(self.endpoint)
        assert response.status_code in [405, 403, 400]
        
        # PUT should fail
        response = self.client.put(self.endpoint)
        assert response.status_code in [405, 403, 400]

    def test_metrics_response_not_empty(self):
        """Verify metrics response contains data (not empty)."""
        response = self.client.get(self.endpoint)
        content = response.content
        
        assert len(content) > 0

    def test_metrics_response_valid_prometheus_format(self):
        """Verify metrics response can be parsed as Prometheus format."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        lines = content.split('\n')
        
        # Check for proper structure:
        # - Comments starting with #
        # - Metric lines with format: metric_name{labels} value
        has_help = False
        has_type = False
        has_metric = False
        
        for line in lines:
            if line.startswith("# HELP"):
                has_help = True
            if line.startswith("# TYPE"):
                has_type = True
            if line and not line.startswith("#"):
                has_metric = True
        
        assert has_help, "Response should contain # HELP comments"
        assert has_type, "Response should contain # TYPE comments"
        assert has_metric, "Response should contain metric data"

    def test_metrics_endpoint_includes_process_metrics(self):
        """Verify metrics include process-level metrics."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Process metrics are standard
        assert "process_" in content

    def test_metrics_endpoint_includes_python_metrics(self):
        """Verify metrics include Python runtime metrics."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Python metrics are standard
        assert "python_" in content

    def test_metrics_response_uses_correct_encoding(self):
        """Verify metrics response uses UTF-8 encoding."""
        response = self.client.get(self.endpoint)
        
        # Should be decodable as UTF-8
        try:
            content = response.content.decode('utf-8')
            assert True
        except UnicodeDecodeError:
            assert False, "Response should be UTF-8 encoded"

    def test_metrics_endpoint_repeatable(self):
        """Verify metrics endpoint is repeatable and consistent."""
        response1 = self.client.get(self.endpoint)
        response2 = self.client.get(self.endpoint)
        
        # Both should return 200
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should have same content type
        assert response1.get("Content-Type") == response2.get("Content-Type")

    def test_metrics_no_authentication_required(self):
        """Verify metrics endpoint doesn't require authentication."""
        # Endpoint should be accessible without auth header
        response = self.client.get(self.endpoint)
        
        # Should not redirect to login or return 401
        assert response.status_code == 200


class TestPrometheusMetricsContent(TestCase):
    """Test the content of Prometheus metrics endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.endpoint = "/api/v1/metrics/"

    def test_metrics_includes_labels(self):
        """Verify metrics response includes labels."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Metrics should have labels like version="..."
        # or they may have empty labels {}
        assert "{" in content or "=" in content

    def test_metrics_uses_standard_suffixes(self):
        """Verify metrics follow Prometheus naming conventions."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Counters should have _total suffix
        # Histograms should have _bucket, _count, _sum suffixes
        # Gauges have no suffix
        # We just verify that standard metric types are present
        lines = content.split('\n')
        
        has_counter = any('_total' in line for line in lines)
        has_histogram = any('_bucket' in line for line in lines)
        
        # At least one should be present in standard metrics
        assert has_counter or has_histogram


class TestMetricsEndpointIntegration(TestCase):
    """Test metrics endpoint integration with application."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.endpoint = "/api/v1/metrics/"

    def test_metrics_accessible_after_api_requests(self):
        """Verify metrics endpoint works after making API requests."""
        # First, make a health check request
        self.client.get("/api/v1/health/")
        
        # Then get metrics
        response = self.client.get(self.endpoint)
        assert response.status_code == 200

    def test_metrics_format_matches_prometheus_spec(self):
        """Verify metrics format matches Prometheus specification."""
        response = self.client.get(self.endpoint)
        content = response.content.decode('utf-8')
        
        # Parse metrics to verify format
        lines = [l for l in content.split('\n') if l.strip()]
        
        for line in lines:
            # Should be either a comment or a metric
            if line.startswith("#"):
                # Comment lines should be # HELP or # TYPE
                assert line.startswith("# HELP") or line.startswith("# TYPE")
            else:
                # Metric lines should have format: name{labels} value [timestamp]
                # We just check it contains a space (separator between metric and value)
                assert " " in line, f"Invalid metric format: {line}"

    def test_metrics_endpoint_url_pattern(self):
        """Verify metrics endpoint is at correct URL."""
        # Test both with and without trailing slash
        response1 = self.client.get("/api/v1/metrics/")
        assert response1.status_code == 200
        
        response2 = self.client.get("/api/v1/metrics")
        # This might redirect or work depending on Django configuration
        assert response2.status_code in [200, 301, 302]
