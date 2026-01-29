# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Structured logging utilities for EUCORA Control Plane.

Provides standardized logging patterns with correlation IDs, security event logging,
audit trail generation, and PII sanitization.

Usage:
    from apps.core.structured_logging import get_logger, log_security_event, log_audit_event

    logger = get_logger(__name__)
    logger.info('Operation completed', extra={
        'correlation_id': 'DEPLOY-123',
        'user': 'admin',
        'action': 'create_deployment'
    })
"""
import logging
import re
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings

# Sensitive field patterns to sanitize
SENSITIVE_PATTERNS = [
    r"password",
    r"passwd",
    r"token",
    r"secret",
    r"api[_-]?key",
    r"auth[_-]?key",
    r"private[_-]?key",
    r"credential",
    r"authorization",
]

# Compile regex patterns for performance
SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def sanitize_sensitive_data(data: Any) -> Any:
    """
    Recursively sanitize sensitive data in dictionaries, lists, and strings.

    Args:
        data: Data to sanitize (dict, list, str, or primitive)

    Returns:
        Sanitized data with sensitive values masked

    Example:
        >>> sanitize_sensitive_data({'password': 'secret123', 'username': 'admin'})
        {'password': '***REDACTED***', 'username': 'admin'}
    """
    if isinstance(data, dict):
        return {
            key: "***REDACTED***" if SENSITIVE_REGEX.search(key) else sanitize_sensitive_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Mask potential secrets in strings (e.g., Bearer tokens)
        if "bearer " in data.lower():
            return "Bearer ***REDACTED***"
        return data
    elif isinstance(data, Decimal):
        return float(data)  # Convert Decimal to float for JSON serialization
    else:
        return data


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standardized configuration.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info('Processing deployment', extra={'correlation_id': 'DEPLOY-123'})
    """
    return logging.getLogger(name)


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    severity: str,
    message: str,
    correlation_id: Optional[str] = None,
    user: Optional[str] = None,
    source_ip: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log security-related events with standardized format.

    Security events include:
    - Authentication attempts (success/failure)
    - Authorization failures
    - Security validation failures (artifact tampering, hash mismatch)
    - Circuit breaker state changes
    - Exception approvals/denials

    Args:
        logger: Logger instance
        event_type: Type of security event (e.g., 'AUTH_FAILURE', 'ARTIFACT_TAMPERED')
        severity: Severity level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        message: Human-readable message
        correlation_id: Correlation ID for tracing
        user: Username (if applicable)
        source_ip: Source IP address (if applicable)
        details: Additional event details (will be sanitized)

    Example:
        log_security_event(
            logger=logger,
            event_type='ARTIFACT_TAMPERED',
            severity='CRITICAL',
            message='Artifact hash mismatch detected',
            correlation_id='DEPLOY-123',
            user='deployer',
            details={'expected_hash': 'abc123', 'actual_hash': 'def456'}
        )
    """
    # Sanitize details to prevent PII/secret leakage
    safe_details = sanitize_sensitive_data(details) if details else {}

    log_level = {
        "LOW": logging.INFO,
        "MEDIUM": logging.WARNING,
        "HIGH": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(severity.upper(), logging.WARNING)

    logger.log(
        log_level,
        f"SECURITY_EVENT: {message}",
        extra={
            "event_category": "SECURITY",
            "event_type": event_type,
            "severity": severity,
            "correlation_id": correlation_id,
            "user": user,
            "source_ip": source_ip,
            **safe_details,
        },
    )


def log_audit_event(
    logger: logging.Logger,
    action: str,
    resource_type: str,
    resource_id: str,
    user: str,
    correlation_id: Optional[str] = None,
    outcome: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log audit trail events for compliance and forensics.

    Audit events include:
    - CAB approval/rejection decisions
    - Risk model version activations
    - Exception approvals
    - Deployment intent submissions
    - Evidence package uploads

    Args:
        logger: Logger instance
        action: Action performed (e.g., 'CAB_APPROVE', 'RISK_MODEL_ACTIVATE')
        resource_type: Type of resource (e.g., 'CABApprovalRequest', 'RiskModelVersion')
        resource_id: Resource identifier (UUID)
        user: Username performing action
        correlation_id: Correlation ID for tracing
        outcome: Outcome ('SUCCESS', 'FAILURE', 'DENIED')
        details: Additional audit details (will be sanitized)

    Example:
        log_audit_event(
            logger=logger,
            action='CAB_APPROVE',
            resource_type='CABApprovalRequest',
            resource_id='550e8400-e29b-41d4-a716-446655440000',
            user='cab_member_1',
            correlation_id='CAB-456',
            outcome='SUCCESS',
            details={'risk_score': 45, 'blast_radius': 'BUSINESS_CRITICAL'}
        )
    """
    # Sanitize details
    safe_details = sanitize_sensitive_data(details) if details else {}

    log_level = logging.INFO if outcome == "SUCCESS" else logging.WARNING

    logger.log(
        log_level,
        f"AUDIT: {action} on {resource_type} {resource_id}",
        extra={
            "event_category": "AUDIT",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user": user,
            "correlation_id": correlation_id,
            "outcome": outcome,
            **safe_details,
        },
    )


def log_deployment_event(
    logger: logging.Logger,
    event_type: str,
    deployment_id: str,
    correlation_id: str,
    ring: str,
    outcome: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log deployment pipeline events.

    Deployment events include:
    - Evidence generation
    - Blast radius classification
    - Security validation (pass/fail)
    - CAB submission
    - Connector publish (success/failure)
    - Ring promotion

    Args:
        logger: Logger instance
        event_type: Event type (e.g., 'EVIDENCE_GENERATED', 'SECURITY_VALIDATED', 'CONNECTOR_PUBLISHED')
        deployment_id: Deployment intent ID
        correlation_id: Correlation ID for end-to-end tracing
        ring: Target ring (e.g., 'CANARY', 'PILOT')
        outcome: Outcome ('SUCCESS', 'FAILURE')
        details: Additional event details (will be sanitized)

    Example:
        log_deployment_event(
            logger=logger,
            event_type='SECURITY_VALIDATED',
            deployment_id='550e8400-e29b-41d4-a716-446655440000',
            correlation_id='DEPLOY-789',
            ring='CANARY',
            outcome='SUCCESS',
            details={'artifact_hash_valid': True, 'sbom_integrity_valid': True}
        )
    """
    safe_details = sanitize_sensitive_data(details) if details else {}

    log_level = logging.INFO if outcome == "SUCCESS" else logging.ERROR

    logger.log(
        log_level,
        f"DEPLOYMENT: {event_type} for {deployment_id} (ring={ring})",
        extra={
            "event_category": "DEPLOYMENT",
            "event_type": event_type,
            "deployment_id": deployment_id,
            "correlation_id": correlation_id,
            "ring": ring,
            "outcome": outcome,
            **safe_details,
        },
    )


def log_connector_event(
    logger: logging.Logger,
    connector_type: str,
    operation: str,
    correlation_id: str,
    outcome: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log execution plane connector events.

    Connector events include:
    - API calls to Intune/Jamf/SCCM/Landscape/Ansible
    - Circuit breaker state changes
    - Retry attempts
    - Idempotent operation detection

    Args:
        logger: Logger instance
        connector_type: Connector type (e.g., 'intune', 'jamf', 'sccm')
        operation: Operation performed (e.g., 'CREATE_APP', 'ASSIGN_POLICY', 'QUERY_DEVICES')
        correlation_id: Correlation ID for tracing
        outcome: Outcome ('SUCCESS', 'FAILURE', 'RETRY', 'CIRCUIT_OPEN')
        details: Additional event details (will be sanitized)

    Example:
        log_connector_event(
            logger=logger,
            connector_type='intune',
            operation='CREATE_APP',
            correlation_id='DEPLOY-123',
            outcome='SUCCESS',
            details={'app_id': 'abc-123', 'elapsed_ms': 523}
        )
    """
    safe_details = sanitize_sensitive_data(details) if details else {}

    log_level = {
        "SUCCESS": logging.INFO,
        "RETRY": logging.WARNING,
        "CIRCUIT_OPEN": logging.ERROR,
        "FAILURE": logging.ERROR,
    }.get(outcome, logging.INFO)

    logger.log(
        log_level,
        f"CONNECTOR: {connector_type} {operation}",
        extra={
            "event_category": "CONNECTOR",
            "connector_type": connector_type,
            "operation": operation,
            "correlation_id": correlation_id,
            "outcome": outcome,
            **safe_details,
        },
    )


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str,
    correlation_id: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Log performance metrics for monitoring and alerting.

    Performance metrics include:
    - API response times
    - Database query durations
    - Evidence generation time
    - Risk score calculation time

    Args:
        logger: Logger instance
        metric_name: Metric name (e.g., 'api.response_time', 'evidence.generation.duration')
        value: Metric value
        unit: Unit of measurement (e.g., 'ms', 'seconds', 'count')
        correlation_id: Correlation ID for tracing
        tags: Additional metric tags (e.g., {'endpoint': '/api/v1/cab/submit/'})

    Example:
        log_performance_metric(
            logger=logger,
            metric_name='api.response_time',
            value=123.4,
            unit='ms',
            correlation_id='API-123',
            tags={'endpoint': '/api/v1/cab/submit/', 'method': 'POST'}
        )
    """
    logger.info(
        f"METRIC: {metric_name} = {value} {unit}",
        extra={
            "event_category": "METRIC",
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            "correlation_id": correlation_id,
            **(tags or {}),
        },
    )


class StructuredLogger:
    """
    Context-aware structured logger with automatic correlation ID injection.

    Simplifies structured logging by automatically including correlation ID
    and other context in all log messages.

    Usage:
        logger = StructuredLogger(__name__, correlation_id='DEPLOY-123')
        logger.info('Deployment started', extra={'ring': 'CANARY'})
        logger.security_event('ARTIFACT_VALIDATED', 'LOW', 'Artifact hash verified')
    """

    def __init__(self, name: str, correlation_id: Optional[str] = None, user: Optional[str] = None):
        """
        Initialize structured logger with context.

        Args:
            name: Logger name (typically __name__)
            correlation_id: Correlation ID for all log messages
            user: Username for all log messages
        """
        self.logger = logging.getLogger(name)
        self.correlation_id = correlation_id
        self.user = user

    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add correlation ID and user to extra fields."""
        context = extra or {}
        if self.correlation_id:
            context["correlation_id"] = self.correlation_id
        if self.user:
            context["user"] = self.user
        return sanitize_sensitive_data(context)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log DEBUG message with context."""
        self.logger.debug(message, extra=self._add_context(extra))

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log INFO message with context."""
        self.logger.info(message, extra=self._add_context(extra))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log WARNING message with context."""
        self.logger.warning(message, extra=self._add_context(extra))

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log ERROR message with context."""
        self.logger.error(message, extra=self._add_context(extra))

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log CRITICAL message with context."""
        self.logger.critical(message, extra=self._add_context(extra))

    def security_event(
        self, event_type: str, severity: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security event with context."""
        log_security_event(
            logger=self.logger,
            event_type=event_type,
            severity=severity,
            message=message,
            correlation_id=self.correlation_id,
            user=self.user,
            details=details,
        )

    def audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log audit event with context."""
        log_audit_event(
            logger=self.logger,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user=self.user or "system",
            correlation_id=self.correlation_id,
            outcome=outcome,
            details=details,
        )

    def deployment_event(
        self, event_type: str, deployment_id: str, ring: str, outcome: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log deployment event with context."""
        log_deployment_event(
            logger=self.logger,
            event_type=event_type,
            deployment_id=deployment_id,
            correlation_id=self.correlation_id or "UNKNOWN",
            ring=ring,
            outcome=outcome,
            details=details,
        )

    def connector_event(
        self, connector_type: str, operation: str, outcome: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log connector event with context."""
        log_connector_event(
            logger=self.logger,
            connector_type=connector_type,
            operation=operation,
            correlation_id=self.correlation_id or "UNKNOWN",
            outcome=outcome,
            details=details,
        )
