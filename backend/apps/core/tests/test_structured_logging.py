# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Structured Logging utilities.
Tests sanitization, context injection, and specialized logging functions.
"""
import logging
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.core.structured_logging import (
    StructuredLogger,
    get_logger,
    log_audit_event,
    log_connector_event,
    log_deployment_event,
    log_performance_metric,
    log_security_event,
    sanitize_sensitive_data,
)


class TestSanitizeSensitiveData(TestCase):
    """Test sensitive data sanitization."""

    def test_sanitize_password_in_dict(self):
        """Password fields should be redacted."""
        data = {"username": "admin", "password": "secret123"}
        result = sanitize_sensitive_data(data)

        self.assertEqual(result["username"], "admin")
        self.assertEqual(result["password"], "***REDACTED***")

    def test_sanitize_token_in_dict(self):
        """Token fields should be redacted."""
        data = {"api_token": "abc123", "api_key": "xyz789"}
        result = sanitize_sensitive_data(data)

        self.assertEqual(result["api_token"], "***REDACTED***")
        self.assertEqual(result["api_key"], "***REDACTED***")

    def test_sanitize_nested_dict(self):
        """Nested sensitive data should be redacted."""
        data = {"user": {"username": "admin", "password": "secret"}, "config": {"api_key": "token123"}}
        result = sanitize_sensitive_data(data)

        self.assertEqual(result["user"]["username"], "admin")
        self.assertEqual(result["user"]["password"], "***REDACTED***")
        self.assertEqual(result["config"]["api_key"], "***REDACTED***")

    def test_sanitize_list_of_dicts(self):
        """Lists containing sensitive dicts should be sanitized."""
        data = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "token": "token2"},
        ]
        result = sanitize_sensitive_data(data)

        self.assertEqual(result[0]["password"], "***REDACTED***")
        self.assertEqual(result[1]["token"], "***REDACTED***")

    def test_sanitize_bearer_token_in_string(self):
        """Bearer tokens in strings should be redacted."""
        data = "Bearer abc123def456"
        result = sanitize_sensitive_data(data)

        self.assertEqual(result, "Bearer ***REDACTED***")

    def test_sanitize_decimal_conversion(self):
        """Decimal values should be converted to float."""
        data = {"risk_score": Decimal("45.5")}
        result = sanitize_sensitive_data(data)

        self.assertIsInstance(result["risk_score"], float)
        self.assertEqual(result["risk_score"], 45.5)

    def test_sanitize_non_sensitive_data_unchanged(self):
        """Non-sensitive data should remain unchanged."""
        data = {"username": "admin", "email": "admin@example.com", "role": "CAB_MEMBER"}
        result = sanitize_sensitive_data(data)

        self.assertEqual(result, data)

    def test_sanitize_case_insensitive(self):
        """Sanitization should be case-insensitive."""
        data = {"PASSWORD": "secret", "Api_Key": "token", "SECRET_TOKEN": "xyz"}
        result = sanitize_sensitive_data(data)

        self.assertEqual(result["PASSWORD"], "***REDACTED***")
        self.assertEqual(result["Api_Key"], "***REDACTED***")
        self.assertEqual(result["SECRET_TOKEN"], "***REDACTED***")


class TestGetLogger(TestCase):
    """Test logger retrieval."""

    def test_get_logger_returns_logger_instance(self):
        """get_logger should return a logger instance."""
        logger = get_logger("test_module")

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_module")


class TestSecurityEventLogging(TestCase):
    """Test security event logging."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_security_event_critical_severity(self, mock_get_logger):
        """Critical security events should log at CRITICAL level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_security_event(
            logger=logger,
            event_type="ARTIFACT_TAMPERED",
            severity="CRITICAL",
            message="Artifact hash mismatch detected",
            correlation_id="DEPLOY-123",
            user="deployer",
            details={"expected": "abc", "actual": "def"},
        )

        # Verify CRITICAL level used
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.CRITICAL)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_security_event_includes_context(self, mock_get_logger):
        """Security events should include full context."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_security_event(
            logger=logger,
            event_type="AUTH_FAILURE",
            severity="HIGH",
            message="Failed login attempt",
            correlation_id="AUTH-456",
            user="attacker",
            source_ip="192.168.1.100",
            details={"attempts": 3},
        )

        call_kwargs = mock_logger.log.call_args[1]
        extra = call_kwargs["extra"]

        self.assertEqual(extra["event_category"], "SECURITY")
        self.assertEqual(extra["event_type"], "AUTH_FAILURE")
        self.assertEqual(extra["correlation_id"], "AUTH-456")
        self.assertEqual(extra["user"], "attacker")
        self.assertEqual(extra["source_ip"], "192.168.1.100")

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_security_event_sanitizes_details(self, mock_get_logger):
        """Security events should sanitize sensitive details."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_security_event(
            logger=logger,
            event_type="TEST",
            severity="LOW",
            message="Test",
            details={"password": "secret123", "username": "admin"},
        )

        call_kwargs = mock_logger.log.call_args[1]
        extra = call_kwargs["extra"]

        self.assertEqual(extra["password"], "***REDACTED***")
        self.assertEqual(extra["username"], "admin")


class TestAuditEventLogging(TestCase):
    """Test audit event logging."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_audit_event_success_logs_info(self, mock_get_logger):
        """Successful audit events should log at INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_audit_event(
            logger=logger,
            action="CAB_APPROVE",
            resource_type="CABApprovalRequest",
            resource_id="550e8400-e29b-41d4-a716-446655440000",
            user="cab_member",
            correlation_id="CAB-123",
            outcome="SUCCESS",
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.INFO)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_audit_event_failure_logs_warning(self, mock_get_logger):
        """Failed audit events should log at WARNING level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_audit_event(
            logger=logger,
            action="CAB_APPROVE",
            resource_type="CABApprovalRequest",
            resource_id="550e8400-e29b-41d4-a716-446655440000",
            user="cab_member",
            outcome="DENIED",
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.WARNING)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_audit_event_includes_resource_info(self, mock_get_logger):
        """Audit events should include resource information."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_audit_event(
            logger=logger,
            action="RISK_MODEL_ACTIVATE",
            resource_type="RiskModelVersion",
            resource_id="1.2",
            user="admin",
            details={"mode": "CAUTIOUS", "thresholds": {"NON_CRITICAL": 30}},
        )

        call_kwargs = mock_logger.log.call_args[1]
        extra = call_kwargs["extra"]

        self.assertEqual(extra["event_category"], "AUDIT")
        self.assertEqual(extra["action"], "RISK_MODEL_ACTIVATE")
        self.assertEqual(extra["resource_type"], "RiskModelVersion")
        self.assertEqual(extra["resource_id"], "1.2")


class TestDeploymentEventLogging(TestCase):
    """Test deployment event logging."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_deployment_event_success(self, mock_get_logger):
        """Successful deployment events should log at INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_deployment_event(
            logger=logger,
            event_type="SECURITY_VALIDATED",
            deployment_id="550e8400-e29b-41d4-a716-446655440000",
            correlation_id="DEPLOY-123",
            ring="CANARY",
            outcome="SUCCESS",
            details={"checks_passed": 4},
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.INFO)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_deployment_event_failure(self, mock_get_logger):
        """Failed deployment events should log at ERROR level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_deployment_event(
            logger=logger,
            event_type="SECURITY_VALIDATION_FAILED",
            deployment_id="550e8400-e29b-41d4-a716-446655440000",
            correlation_id="DEPLOY-456",
            ring="CANARY",
            outcome="FAILURE",
            details={"reason": "ARTIFACT_HASH_MISMATCH"},
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.ERROR)


class TestConnectorEventLogging(TestCase):
    """Test connector event logging."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_connector_event_success(self, mock_get_logger):
        """Successful connector events should log at INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_connector_event(
            logger=logger,
            connector_type="intune",
            operation="CREATE_APP",
            correlation_id="DEPLOY-123",
            outcome="SUCCESS",
            details={"app_id": "abc-123", "elapsed_ms": 523},
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.INFO)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_connector_event_circuit_open(self, mock_get_logger):
        """Circuit open connector events should log at ERROR level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_connector_event(
            logger=logger,
            connector_type="intune",
            operation="QUERY_DEVICES",
            correlation_id="DEPLOY-456",
            outcome="CIRCUIT_OPEN",
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.ERROR)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_connector_event_retry(self, mock_get_logger):
        """Retry connector events should log at WARNING level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_connector_event(
            logger=logger,
            connector_type="jamf",
            operation="CREATE_POLICY",
            correlation_id="DEPLOY-789",
            outcome="RETRY",
            details={"attempt": 2, "max_attempts": 3},
        )

        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.WARNING)


class TestPerformanceMetricLogging(TestCase):
    """Test performance metric logging."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_performance_metric_basic(self, mock_get_logger):
        """Performance metrics should be logged with value and unit."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_performance_metric(
            logger=logger, metric_name="api.response_time", value=123.4, unit="ms", correlation_id="API-123"
        )

        call_kwargs = mock_logger.info.call_args[1]
        extra = call_kwargs["extra"]

        self.assertEqual(extra["event_category"], "METRIC")
        self.assertEqual(extra["metric_name"], "api.response_time")
        self.assertEqual(extra["metric_value"], 123.4)
        self.assertEqual(extra["metric_unit"], "ms")

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_performance_metric_with_tags(self, mock_get_logger):
        """Performance metrics should support custom tags."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        log_performance_metric(
            logger=logger,
            metric_name="db.query_time",
            value=45.6,
            unit="ms",
            tags={"query_type": "SELECT", "table": "cab_approval_request"},
        )

        call_kwargs = mock_logger.info.call_args[1]
        extra = call_kwargs["extra"]

        self.assertEqual(extra["query_type"], "SELECT")
        self.assertEqual(extra["table"], "cab_approval_request")


class TestStructuredLogger(TestCase):
    """Test StructuredLogger context-aware wrapper."""

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_adds_correlation_id(self, mock_get_logger):
        """StructuredLogger should automatically add correlation ID."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test", correlation_id="DEPLOY-123")
        logger.info("Test message")

        call_kwargs = mock_logger.info.call_args[1]
        self.assertEqual(call_kwargs["extra"]["correlation_id"], "DEPLOY-123")

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_adds_user(self, mock_get_logger):
        """StructuredLogger should automatically add user."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test", user="admin")
        logger.info("Test message")

        call_kwargs = mock_logger.info.call_args[1]
        self.assertEqual(call_kwargs["extra"]["user"], "admin")

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_sanitizes_extra(self, mock_get_logger):
        """StructuredLogger should sanitize extra fields."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")
        logger.info("Test message", extra={"password": "secret", "username": "admin"})

        call_kwargs = mock_logger.info.call_args[1]
        self.assertEqual(call_kwargs["extra"]["password"], "***REDACTED***")
        self.assertEqual(call_kwargs["extra"]["username"], "admin")

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_security_event(self, mock_get_logger):
        """StructuredLogger should support security_event shortcut."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test", correlation_id="SEC-123", user="admin")
        logger.security_event("TEST_EVENT", "HIGH", "Test security event")

        # Verify log was called
        self.assertTrue(mock_logger.log.called)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_audit_event(self, mock_get_logger):
        """StructuredLogger should support audit_event shortcut."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test", correlation_id="AUDIT-456", user="cab_member")
        logger.audit_event(
            action="CAB_APPROVE", resource_type="CABApprovalRequest", resource_id="550e8400-e29b-41d4-a716-446655440000"
        )

        # Verify log was called
        self.assertTrue(mock_logger.log.called)

    @patch("apps.core.structured_logging.logging.getLogger")
    def test_structured_logger_all_levels(self, mock_get_logger):
        """StructuredLogger should support all log levels."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Verify all levels were called
        self.assertTrue(mock_logger.debug.called)
        self.assertTrue(mock_logger.info.called)
        self.assertTrue(mock_logger.warning.called)
        self.assertTrue(mock_logger.error.called)
        self.assertTrue(mock_logger.critical.called)
