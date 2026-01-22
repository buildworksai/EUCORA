# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Circuit breaker utilities for external service calls.

Implements fail-fast pattern to prevent cascading failures.
Circuit states: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing recovery)

Usage:
    from apps.core.circuit_breaker import get_breaker, CircuitBreakerOpen

    breaker = get_breaker('servicenow')
    try:
        with breaker:
            response = requests.get(url)
    except CircuitBreakerOpen:
        # Service unavailable, return cached data or error
        pass
"""
from functools import wraps
from typing import Callable, Dict, Any, Optional, List
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open - service temporarily unavailable."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        self.service_name = service_name
        self.message = message or f'Service {service_name} is currently unavailable (circuit breaker open)'
        super().__init__(self.message)


class CircuitBreakerListener:
    """Listener for circuit breaker state changes."""
    
    def __init__(self, name: str):
        self.name = name
    
    def state_change(self, cb, old_state, new_state):
        """Log state transitions."""
        logger.warning(
            f'Circuit breaker state change: {self.name}',
            extra={
                'circuit_breaker': self.name,
                'old_state': str(old_state),
                'new_state': str(new_state),
            }
        )
    
    def failure(self, cb, exc):
        """Log failures."""
        logger.error(
            f'Circuit breaker recorded failure: {self.name}',
            extra={
                'circuit_breaker': self.name,
                'error': str(exc),
                'fail_counter': cb.fail_counter,
            }
        )
    
    def success(self, cb):
        """Log successful calls after open."""
        if cb.state.name == 'half-open':
            logger.info(
                f'Circuit breaker recovery successful: {self.name}',
                extra={'circuit_breaker': self.name}
            )
    
    def before_call(self, cb, *args, **kwargs):
        """Called before breaker executes a function (pybreaker interface)."""
        pass
    
    def after_call(self, cb, *args, **kwargs):
        """Called after successful breaker execution (pybreaker interface)."""
        pass


def _create_breaker(name: str, fail_max: int = 5, reset_timeout: int = 60) -> CircuitBreaker:
    """Create a circuit breaker with standard configuration."""
    return CircuitBreaker(
        name=name,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        listeners=[CircuitBreakerListener(name)],
        exclude=[],
    )


# ==============================================================================
# Execution Plane Connectors (Intune/Jamf/SCCM/Landscape/Ansible)
# ==============================================================================
INTUNE_BREAKER = _create_breaker('intune', fail_max=5, reset_timeout=60)
JAMF_BREAKER = _create_breaker('jamf', fail_max=5, reset_timeout=60)
SCCM_BREAKER = _create_breaker('sccm', fail_max=5, reset_timeout=60)
LANDSCAPE_BREAKER = _create_breaker('landscape', fail_max=5, reset_timeout=60)
ANSIBLE_BREAKER = _create_breaker('ansible', fail_max=5, reset_timeout=60)

# ==============================================================================
# ITSM Integrations (ServiceNow/Jira/Freshservice)
# ==============================================================================
SERVICENOW_BREAKER = _create_breaker('servicenow', fail_max=5, reset_timeout=60)
JIRA_BREAKER = _create_breaker('jira', fail_max=5, reset_timeout=60)
FRESHSERVICE_BREAKER = _create_breaker('freshservice', fail_max=5, reset_timeout=60)

# ==============================================================================
# SIEM/Telemetry Integrations (Splunk/Elastic/Datadog)
# ==============================================================================
SPLUNK_BREAKER = _create_breaker('splunk', fail_max=5, reset_timeout=60)
ELASTIC_BREAKER = _create_breaker('elastic', fail_max=5, reset_timeout=60)
DATADOG_BREAKER = _create_breaker('datadog', fail_max=5, reset_timeout=60)

# ==============================================================================
# Identity Integrations (Entra ID/Active Directory)
# ==============================================================================
ENTRA_ID_BREAKER = _create_breaker('entra_id', fail_max=5, reset_timeout=60)
ACTIVE_DIRECTORY_BREAKER = _create_breaker('active_directory', fail_max=5, reset_timeout=60)

# ==============================================================================
# Security Integrations (Defender/Vulnerability Scanner)
# ==============================================================================
DEFENDER_BREAKER = _create_breaker('defender', fail_max=5, reset_timeout=60)
VULNERABILITY_SCANNER_BREAKER = _create_breaker('vulnerability_scanner', fail_max=5, reset_timeout=60)

# ==============================================================================
# AI/LLM Providers
# ==============================================================================
AI_PROVIDER_BREAKER = _create_breaker('ai_provider', fail_max=5, reset_timeout=60)

# ==============================================================================
# Database Operations (higher threshold)
# ==============================================================================
DATABASE_BREAKER = _create_breaker('database', fail_max=10, reset_timeout=30)

# ==============================================================================
# Generic External API
# ==============================================================================
EXTERNAL_API_BREAKER = _create_breaker('external_api', fail_max=5, reset_timeout=60)


# Registry of all breakers for easy lookup
_BREAKER_REGISTRY: Dict[str, CircuitBreaker] = {
    # Execution plane connectors
    'intune': INTUNE_BREAKER,
    'jamf': JAMF_BREAKER,
    'sccm': SCCM_BREAKER,
    'landscape': LANDSCAPE_BREAKER,
    'ansible': ANSIBLE_BREAKER,
    # ITSM
    'servicenow': SERVICENOW_BREAKER,
    'jira': JIRA_BREAKER,
    'freshservice': FRESHSERVICE_BREAKER,
    # SIEM/Telemetry
    'splunk': SPLUNK_BREAKER,
    'elastic': ELASTIC_BREAKER,
    'datadog': DATADOG_BREAKER,
    # Identity
    'entra_id': ENTRA_ID_BREAKER,
    'active_directory': ACTIVE_DIRECTORY_BREAKER,
    # Security
    'defender': DEFENDER_BREAKER,
    'vulnerability_scanner': VULNERABILITY_SCANNER_BREAKER,
    # AI
    'ai_provider': AI_PROVIDER_BREAKER,
    # Infrastructure
    'database': DATABASE_BREAKER,
    'external_api': EXTERNAL_API_BREAKER,
}


def get_breaker(service_name: str) -> CircuitBreaker:
    """
    Get circuit breaker for a service by name.
    
    Args:
        service_name: Name of the service (e.g., 'servicenow', 'intune')
    
    Returns:
        CircuitBreaker instance
    
    Raises:
        ValueError: If service_name is not registered
    
    Usage:
        breaker = get_breaker('servicenow')
        with breaker:
            response = requests.get(url)
    """
    breaker = _BREAKER_REGISTRY.get(service_name.lower())
    if not breaker:
        raise ValueError(
            f"Unknown service: {service_name}. "
            f"Available: {', '.join(sorted(_BREAKER_REGISTRY.keys()))}"
        )
    return breaker


# Backward compatibility alias
def get_connector_breaker(connector_type: str) -> CircuitBreaker:
    """Get circuit breaker for connector type (backward compatibility)."""
    return get_breaker(connector_type)


def check_breaker_status(service_name: str) -> bool:
    """
    Check if circuit breaker is open for a service.
    
    Args:
        service_name: Name of the service
    
    Returns:
        True if circuit is closed (service available)
    
    Raises:
        CircuitBreakerOpen: If circuit is open
    """
    breaker = get_breaker(service_name)
    if breaker.state.name == 'open':
        logger.warning(
            f'Circuit breaker OPEN for service: {service_name}',
            extra={'service': service_name, 'state': 'OPEN'}
        )
        raise CircuitBreakerOpen(service_name)
    return True


def get_all_breaker_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status of all circuit breakers.
    
    Returns:
        Dict with service name -> status info
    
    Usage:
        status = get_all_breaker_status()
        for name, info in status.items():
            print(f"{name}: {info['state']}")
    """
    result = {}
    for name, breaker in _BREAKER_REGISTRY.items():
        result[name] = {
            'state': breaker.state.name,
            'fail_counter': breaker.fail_counter,
            'fail_max': breaker.fail_max,
            'opened': breaker.state.name == 'open',
            'reset_timeout': breaker.reset_timeout,
        }
    return result


def with_circuit_breaker(service_name: str):
    """
    Decorator to wrap a function with circuit breaker protection.
    
    Args:
        service_name: Name of the service to protect
    
    Usage:
        @with_circuit_breaker('servicenow')
        def call_servicenow_api():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_breaker(service_name)
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                raise CircuitBreakerOpen(service_name)
        return wrapper
    return decorator


def reset_breaker(service_name: str) -> None:
    """
    Manually reset a circuit breaker to closed state.
    
    Use with caution - typically only for admin/debugging purposes.
    
    Args:
        service_name: Name of the service
    """
    breaker = get_breaker(service_name)
    breaker.close()
    logger.info(
        f'Circuit breaker manually reset: {service_name}',
        extra={'service': service_name}
    )
    pass
