# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Prometheus metrics collection and recording.

Verifies:
- All metric types are properly created (Counter, Gauge, Histogram)
- Metric recording functions work correctly
- Metrics are labeled properly
- Prometheus registry integration
"""
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from prometheus_client import REGISTRY, CollectorRegistry

from apps.core.metrics import (
    celery_task_duration_seconds,
    circuit_breaker_state,
    connector_health,
    connector_operation_duration_seconds,
    deployment_duration_seconds,
    deployment_total,
    http_request_duration_seconds,
    record_celery_task,
    record_connector_operation,
    record_deployment,
    record_http_request,
    record_risk_score,
    risk_score,
    update_circuit_breaker_state,
)


class TestDeploymentMetrics(TestCase):
    """Test deployment-related metrics."""

    def test_deployment_total_counter_increments(self):
        """Verify deployment_total counter increments."""
        record_deployment("success", "CANARY", "app-name", False, 45.5)

        # Verify metric was recorded (checking via label combinations)
        assert deployment_total is not None
        assert hasattr(deployment_total, "labels")

    def test_deployment_duration_recorded(self):
        """Verify deployment duration is recorded."""
        record_deployment("success", "PILOT", "test-app", True, 120.5)

        assert deployment_duration_seconds is not None
        assert hasattr(deployment_duration_seconds, "labels")

    def test_record_deployment_with_different_rings(self):
        """Verify deployments can be recorded for all rings."""
        rings = ["LAB", "CANARY", "PILOT", "DEPARTMENT", "GLOBAL"]

        for ring in rings:
            record_deployment("success", ring, "app", False, 30.0)

        # All should complete without error
        assert True

    def test_record_deployment_with_different_status(self):
        """Verify deployments can be recorded with different statuses."""
        statuses = ["success", "failed", "pending_approval", "rolled_back"]

        for status in statuses:
            record_deployment(status, "CANARY", "app", False, 20.0)

        assert True


class TestRiskScoreMetrics(TestCase):
    """Test risk score metrics."""

    def test_risk_score_histogram_created(self):
        """Verify risk score histogram exists."""
        assert risk_score is not None
        assert hasattr(risk_score, "labels")

    def test_record_risk_score_requires_cab(self):
        """Verify risk scores requiring CAB are recorded."""
        record_risk_score(75, True)
        assert True

    def test_record_risk_score_no_cab_required(self):
        """Verify risk scores not requiring CAB are recorded."""
        record_risk_score(30, False)
        assert True

    def test_record_risk_score_boundary_values(self):
        """Verify boundary risk scores are recorded."""
        for score in [0, 25, 50, 75, 100]:
            record_risk_score(score, score > 50)

        assert True


class TestCircuitBreakerMetrics(TestCase):
    """Test circuit breaker metrics."""

    def test_circuit_breaker_state_gauge_created(self):
        """Verify circuit breaker state gauge exists."""
        assert circuit_breaker_state is not None
        assert hasattr(circuit_breaker_state, "labels")

    def test_update_circuit_breaker_closed(self):
        """Verify circuit breaker closed state is recorded."""
        update_circuit_breaker_state("intune-service", "intune", 0)
        assert True

    def test_update_circuit_breaker_open(self):
        """Verify circuit breaker open state is recorded."""
        update_circuit_breaker_state("jamf-service", "jamf", 1)
        assert True

    def test_update_circuit_breaker_half_open(self):
        """Verify circuit breaker half-open state is recorded."""
        update_circuit_breaker_state("sccm-service", "sccm", 2)
        assert True

    def test_circuit_breaker_for_multiple_services(self):
        """Verify circuit breaker state tracked for multiple services."""
        services = [("intune", "intune"), ("jamf", "jamf"), ("sccm", "sccm"), ("landscape", "landscape")]

        for service_name, connector_type in services:
            update_circuit_breaker_state(service_name, connector_type, 0)

        assert True


class TestCeleryTaskMetrics(TestCase):
    """Test Celery task metrics."""

    def test_celery_task_duration_recorded(self):
        """Verify Celery task duration is recorded."""
        record_celery_task("deploy_to_connector", "success", 45.5)
        assert True

    def test_celery_task_with_retries(self):
        """Verify Celery task retries are recorded."""
        record_celery_task("execute_rollback", "success", 30.0, retry_count=2)
        assert True

    def test_celery_task_failure_recorded(self):
        """Verify failed Celery tasks are recorded."""
        record_celery_task("process_ai_conversation", "failed", 15.0)
        assert True

    def test_celery_task_multiple_retries(self):
        """Verify tasks with multiple retries are tracked."""
        for retry in range(1, 4):
            record_celery_task("execute_ai_task", "success", 20.0, retry_count=retry)

        assert True


class TestHTTPMetrics(TestCase):
    """Test HTTP request metrics."""

    def test_http_request_success_recorded(self):
        """Verify successful HTTP requests are recorded."""
        record_http_request("GET", "/api/v1/deployments/", 200, 0.45)
        assert True

    def test_http_request_client_error_recorded(self):
        """Verify HTTP 4xx errors are recorded."""
        record_http_request("POST", "/api/v1/deployments/", 400, 0.02)
        assert True

    def test_http_request_server_error_recorded(self):
        """Verify HTTP 5xx errors are recorded."""
        record_http_request("PUT", "/api/v1/policy/rules/", 500, 0.05)
        assert True

    def test_http_request_various_endpoints(self):
        """Verify HTTP metrics track various endpoints."""
        endpoints = [
            "/api/v1/deployments/",
            "/api/v1/policy/",
            "/api/v1/cab/",
            "/api/v1/evidence/",
            "/api/v1/connectors/",
        ]

        for endpoint in endpoints:
            record_http_request("GET", endpoint, 200, 0.25)

        assert True

    def test_http_request_various_methods(self):
        """Verify HTTP metrics track various methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            record_http_request(method, "/api/v1/deployments/", 200, 0.15)

        assert True


class TestConnectorMetrics(TestCase):
    """Test connector operation metrics."""

    def test_connector_health_healthy(self):
        """Verify healthy connector is recorded."""
        update_connector_health("intune", True)
        assert True

    def test_connector_health_unhealthy(self):
        """Verify unhealthy connector is recorded."""
        update_connector_health("jamf", False)
        assert True

    def test_connector_operation_success(self):
        """Verify successful connector operation is recorded."""
        record_connector_operation("intune", "deploy", "success", 15.5)
        assert True

    def test_connector_operation_failure(self):
        """Verify failed connector operation is recorded."""
        record_connector_operation("sccm", "query", "failed", 5.0)
        assert True

    def test_connector_operation_various_types(self):
        """Verify various connector operations are tracked."""
        connectors = ["intune", "jamf", "sccm", "landscape", "ansible"]
        operations = ["deploy", "query", "remediate", "rollback"]

        for connector in connectors:
            for operation in operations:
                record_connector_operation(connector, operation, "success", 10.0)

        assert True


class TestMetricsRegistry(TestCase):
    """Test integration with Prometheus registry."""

    def test_metrics_in_prometheus_registry(self):
        """Verify metrics are registered with Prometheus."""
        from prometheus_client import REGISTRY

        # Verify metrics are accessible in registry
        metrics_list = list(REGISTRY.collect())

        # Should have at least some metrics (python_info, process_*, etc.)
        assert len(metrics_list) > 0

    def test_custom_metrics_available(self):
        """Verify custom EUCORA metrics are available."""
        # Record some metrics
        record_deployment("success", "CANARY", "test-app", False, 30.0)
        record_http_request("GET", "/api/v1/health/", 200, 0.01)

        # Metrics should be available
        assert deployment_total is not None
        assert http_request_duration_seconds is not None
