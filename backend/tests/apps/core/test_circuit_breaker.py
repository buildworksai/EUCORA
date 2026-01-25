# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Unit tests for circuit breaker utilities."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from apps.core.circuit_breaker import (
    _BREAKER_REGISTRY,
    CircuitBreakerOpen,
    check_breaker_status,
    get_breaker,
    get_connector_breaker,
    reset_breaker,
    with_circuit_breaker,
)


class TestGetBreaker:
    """Test circuit breaker retrieval."""

    def test_get_breaker_intune(self):
        """Get breaker for intune service."""
        breaker = get_breaker("intune")
        assert breaker is not None
        assert "intune" in breaker.name

    def test_get_breaker_servicenow(self):
        """Get breaker for ServiceNow integration."""
        breaker = get_breaker("servicenow")
        assert breaker is not None

    def test_get_breaker_database(self):
        """Get breaker for database."""
        breaker = get_breaker("database")
        assert breaker is not None

    def test_get_breaker_case_insensitive(self):
        """Breaker lookup is case insensitive."""
        breaker_lower = get_breaker("intune")
        breaker_upper = get_breaker("INTUNE")
        assert breaker_lower == breaker_upper

    def test_get_breaker_invalid_service(self):
        """Invalid service raises ValueError."""
        with pytest.raises(ValueError, match="Unknown service"):
            get_breaker("nonexistent_service")

    def test_all_registered_services(self):
        """All expected services are registered."""
        expected = ["intune", "jamf", "sccm", "database", "ai_provider"]
        for service in expected:
            assert service in _BREAKER_REGISTRY


class TestGetConnectorBreakerAlias:
    """Test backward compatibility alias."""

    def test_connector_breaker_alias(self):
        """get_connector_breaker is alias for get_breaker."""
        intune_breaker = get_breaker("intune")
        connector_breaker = get_connector_breaker("intune")
        assert intune_breaker == connector_breaker

    def test_connector_breaker_lowercase(self):
        """Connector type lookup works with various cases."""
        breaker = get_connector_breaker("INTUNE")
        assert breaker is not None


class TestCheckBreakerStatus:
    """Test breaker status checking."""

    def test_check_breaker_closed(self):
        """Returns True when breaker is closed."""
        breaker = get_breaker("intune")
        # Mock closed state
        with patch.object(breaker, "opened", False):
            result = check_breaker_status("intune")
            assert result is True

    def test_check_breaker_open_raises(self):
        """Raises CircuitBreakerOpen when breaker is open."""
        breaker = get_breaker("intune")
        # Mock open state
        with patch.object(breaker, "opened", True):
            with pytest.raises(CircuitBreakerOpen) as exc_info:
                check_breaker_status("intune")
            assert "intune" in str(exc_info.value)

    def test_check_invalid_service(self):
        """Invalid service raises ValueError."""
        with pytest.raises(ValueError):
            check_breaker_status("invalid_service")


class TestResetBreaker:
    """Test breaker reset functionality."""

    def test_reset_breaker(self):
        """Reset breaker closes it."""
        breaker = get_breaker("intune")
        with patch.object(breaker, "close") as mock_close:
            reset_breaker("intune")
            mock_close.assert_called_once()

    def test_reset_invalid_service(self):
        """Reset on invalid service raises ValueError."""
        with pytest.raises(ValueError):
            reset_breaker("invalid_service")

    def test_reset_logs_info(self):
        """Reset logs info message."""
        with patch("apps.core.circuit_breaker.logger") as mock_logger:
            reset_breaker("intune")
            mock_logger.info.assert_called()


class TestWithCircuitBreakerDecorator:
    """Test @with_circuit_breaker decorator."""

    def test_decorator_success(self):
        """Decorator allows successful calls."""

        @with_circuit_breaker("intune")
        def api_call():
            return "success"

        result = api_call()
        assert result == "success"

    def test_decorator_with_args(self):
        """Decorator preserves function arguments."""

        @with_circuit_breaker("intune")
        def api_call(name, value):
            return f"{name}={value}"

        result = api_call("app", "v1")
        assert result == "app=v1"

    def test_decorator_with_kwargs(self):
        """Decorator preserves keyword arguments."""

        @with_circuit_breaker("intune")
        def api_call(name, version=None):
            return {"name": name, "version": version}

        result = api_call("app", version="1.0")
        assert result["name"] == "app"
        assert result["version"] == "1.0"

    def test_decorator_invalid_service(self):
        """Decorator with invalid service raises ValueError."""
        with pytest.raises(ValueError):

            @with_circuit_breaker("invalid_service")
            def api_call():
                pass


class TestCircuitBreakerException:
    """Test CircuitBreakerOpen exception."""

    def test_exception_with_service_name(self):
        """Exception stores service name."""
        exc = CircuitBreakerOpen("intune")
        assert exc.service_name == "intune"
        assert "intune" in str(exc)

    def test_exception_with_custom_message(self):
        """Exception accepts custom message."""
        exc = CircuitBreakerOpen("intune", "Custom error")
        assert "Custom error" in str(exc)

    def test_exception_is_exception_subclass(self):
        """CircuitBreakerOpen is an Exception."""
        exc = CircuitBreakerOpen("service")
        assert isinstance(exc, Exception)


class TestBreakerConfiguration:
    """Test circuit breaker configuration."""

    def test_database_breaker_exists(self):
        """Database breaker is configured."""
        breaker = get_breaker("database")
        assert breaker is not None
        assert breaker.name == "database"

    def test_ai_provider_breaker_exists(self):
        """AI provider breaker is configured."""
        breaker = get_breaker("ai_provider")
        assert breaker is not None

    def test_external_api_breaker_exists(self):
        """External API breaker is configured."""
        breaker = get_breaker("external_api")
        assert breaker is not None

    def test_all_breakers_have_names(self):
        """All breakers have names."""
        for service_name, breaker in _BREAKER_REGISTRY.items():
            assert breaker.name is not None
            assert len(breaker.name) > 0


class TestBreakerIntegration:
    """Integration tests for circuit breaker."""

    def test_multiple_services_independent(self):
        """Different services have independent breakers."""
        intune_breaker = get_breaker("intune")
        jamf_breaker = get_breaker("jamf")
        assert intune_breaker != jamf_breaker

    def test_same_service_same_breaker(self):
        """Same service returns same breaker instance."""
        breaker1 = get_breaker("intune")
        breaker2 = get_breaker("intune")
        assert breaker1 is breaker2

    @patch("apps.core.circuit_breaker.CircuitBreakerError")
    def test_decorator_handles_breaker_error(self, mock_error):
        """Decorator converts CircuitBreakerError to CircuitBreakerOpen."""

        @with_circuit_breaker("intune")
        def failing_call():
            raise mock_error("Breaker is open")

        # The decorator should handle the error
        breaker = get_breaker("intune")
        with patch.object(breaker, "call", side_effect=mock_error("error")):
            with pytest.raises(CircuitBreakerOpen):
                failing_call()
