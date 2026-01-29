# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
HTTP utilities with circuit breakers, timeouts, and retries.

Provides resilient HTTP client that all external service calls should use.

Usage:
    from apps.core.http import ResilientHTTPClient

    # Create client for a specific service
    client = ResilientHTTPClient(service_name='servicenow')

    # Make resilient HTTP calls
    response = client.get('https://api.servicenow.com/...')
    response = client.post('https://api.servicenow.com/...', json=data)
"""
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.core.circuit_breaker import CircuitBreakerOpen, get_breaker
from apps.core.retry import DEFAULT_RETRY

logger = logging.getLogger(__name__)


def create_resilient_session(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 30,
    status_forcelist: Optional[List[int]] = None,
) -> requests.Session:
    """
    Create requests session with automatic retries and timeouts.

    Args:
        max_retries: Number of retries for failed requests
        backoff_factor: Exponential backoff factor (e.g., 0.5s, 1s, 2s, 4s)
        timeout: Request timeout in seconds
        status_forcelist: HTTP status codes to retry on (default: 429, 500, 502, 503, 504)

    Returns:
        requests.Session with retry strategy configured
    """
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]

    session = requests.Session()

    # Configure retry strategy for transient failures
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default timeout
    session._timeout = timeout

    # Wrap make_request to apply timeout
    original_request = session.request

    def request_with_timeout(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return original_request(*args, **kwargs)

    session.request = request_with_timeout

    return session


# Singleton instance for reuse
_default_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """Get or create default resilient session (singleton)."""
    global _default_session
    if _default_session is None:
        _default_session = create_resilient_session(
            max_retries=3,
            backoff_factor=0.5,
            timeout=30,
        )
    return _default_session


class ResilientHTTPClient:
    """
    HTTP client with circuit breaker, retries, and timeouts.

    This is the recommended way to make external HTTP calls in the application.

    Features:
    - Circuit breaker protection (fails fast when service is down)
    - Automatic retries with exponential backoff for transient errors
    - Configurable timeouts
    - Request/response logging for debugging
    - Correlation ID tracking for audit trail

    Usage:
        client = ResilientHTTPClient(service_name='servicenow')

        # Simple GET
        response = client.get('https://api.servicenow.com/table/incident')

        # POST with data
        response = client.post(
            'https://api.servicenow.com/table/incident',
            json={'short_description': 'Test'},
            headers={'Authorization': 'Bearer token'}
        )

        # With correlation ID for audit trail
        response = client.get(url, correlation_id='abc-123')
    """

    def __init__(
        self,
        service_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        """
        Initialize resilient HTTP client.

        Args:
            service_name: Name of the external service (for circuit breaker)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Number of retries for transient errors (default: 3)
            backoff_factor: Exponential backoff factor (default: 0.5)
        """
        self.service_name = service_name
        self.timeout = timeout
        self.breaker = get_breaker(service_name)
        self.session = create_resilient_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            timeout=timeout,
        )

    def request(
        self,
        method: str,
        url: str,
        correlation_id: Optional[str] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Make HTTP request with circuit breaker protection.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            correlation_id: Optional correlation ID for audit trail
            **kwargs: Additional arguments passed to requests

        Returns:
            requests.Response

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            requests.exceptions.RequestException: For request errors
        """
        # Check circuit breaker before making request
        if self.breaker.state.name == "open":
            logger.warning(
                f"Circuit breaker OPEN for {self.service_name}, rejecting request",
                extra={
                    "service": self.service_name,
                    "url": url,
                    "correlation_id": correlation_id,
                },
            )
            raise CircuitBreakerOpen(self.service_name)

        # Ensure timeout is set
        kwargs.setdefault("timeout", self.timeout)

        # Add correlation ID to headers if provided
        if correlation_id:
            headers = kwargs.get("headers", {})
            headers["X-Correlation-ID"] = correlation_id
            kwargs["headers"] = headers

        try:
            # Make request within circuit breaker
            def make_request():
                response = self.session.request(method, url, **kwargs)
                # Raise for error status codes (will trigger circuit breaker)
                response.raise_for_status()
                return response

            response = self.breaker.call(make_request)

            logger.debug(
                f"HTTP {method} {url} -> {response.status_code}",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "correlation_id": correlation_id,
                },
            )

            return response

        except requests.exceptions.RequestException as e:
            logger.error(
                f"HTTP request failed: {self.service_name}",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
                exc_info=True,
            )
            raise

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """Make PUT request."""
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        """Make PATCH request."""
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """Make DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs) -> requests.Response:
        """Make HEAD request."""
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs) -> requests.Response:
        """Make OPTIONS request."""
        return self.request("OPTIONS", url, **kwargs)


# Factory function for getting clients
_client_cache: Dict[str, ResilientHTTPClient] = {}


def get_http_client(
    service_name: str,
    timeout: int = 30,
    max_retries: int = 3,
) -> ResilientHTTPClient:
    """
    Get or create HTTP client for a service (cached).

    Args:
        service_name: Name of the external service
        timeout: Request timeout in seconds
        max_retries: Number of retries

    Returns:
        ResilientHTTPClient instance

    Usage:
        client = get_http_client('servicenow')
        response = client.get(url)
    """
    cache_key = f"{service_name}:{timeout}:{max_retries}"
    if cache_key not in _client_cache:
        _client_cache[cache_key] = ResilientHTTPClient(
            service_name=service_name,
            timeout=timeout,
            max_retries=max_retries,
        )
    return _client_cache[cache_key]
