# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Resilient HTTP client combining circuit breakers and retry logic.

Provides unified interface for external API calls with:
- Circuit breaker protection (fail-fast for known-bad services)
- Exponential backoff with jitter (retry transient failures)
- Request timeouts (prevent hanging)
- Correlation ID propagation (audit trail)
- Structured logging (observability)

Usage:
    from apps.core.resilient_http import ResilientHTTPClient

    client = ResilientHTTPClient(service_name='intune', timeout=30)
    response = client.get(url, headers=headers, correlation_id='DEPLOY-123')
"""
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from tenacity import RetryError
from urllib3.util.retry import Retry as URLLib3Retry

from .circuit_breaker import CircuitBreakerOpen, get_breaker
from .retry import DEFAULT_RETRY

logger = logging.getLogger(__name__)


class ResilientHTTPClient:
    """
    Resilient HTTP client with circuit breaker and retry logic.

    Combines fail-fast (circuit breaker) with transient retry (exponential backoff).
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
            service_name: Service name for circuit breaker (e.g., 'intune', 'jamf')
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            backoff_factor: Exponential backoff factor (default: 0.5)
        """
        self.service_name = service_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Get circuit breaker for this service
        self.breaker = get_breaker(service_name)

        # Create requests session with connection pooling
        self.session = requests.Session()

        # Configure retry strategy (urllib3 level)
        retry_strategy = URLLib3Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _log_request(self, method: str, url: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log outbound request."""
        logger.info(
            f"HTTP {method.upper()} request",
            extra={
                "service": self.service_name,
                "method": method.upper(),
                "url": url,
                "correlation_id": correlation_id,
                "circuit_breaker_state": self.breaker.state.name,
            },
        )

    def _log_response(
        self,
        method: str,
        url: str,
        status_code: int,
        elapsed_ms: float,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log response received."""
        logger.info(
            f"HTTP {method.upper()} response",
            extra={
                "service": self.service_name,
                "method": method.upper(),
                "url": url,
                "status_code": status_code,
                "elapsed_ms": elapsed_ms,
                "correlation_id": correlation_id,
            },
        )

    def _log_error(
        self,
        method: str,
        url: str,
        error: Exception,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log request error."""
        logger.error(
            f"HTTP {method.upper()} error",
            extra={
                "service": self.service_name,
                "method": method.upper(),
                "url": url,
                "error": str(error),
                "error_type": type(error).__name__,
                "correlation_id": correlation_id,
            },
        )

    @DEFAULT_RETRY
    def _execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """
        Execute HTTP request with circuit breaker protection and retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Target URL
            headers: Request headers
            data: Request body (form data)
            json: Request body (JSON)
            params: Query parameters
            correlation_id: Correlation ID for audit trail

        Returns:
            requests.Response

        Raises:
            CircuitBreakerOpen: Circuit breaker is open (service unavailable)
            RetryError: All retry attempts exhausted
            requests.HTTPError: HTTP error response
            requests.RequestException: Network/connection error
        """
        # Add correlation ID to headers
        if headers is None:
            headers = {}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        self._log_request(method, url, correlation_id)

        try:
            # Circuit breaker protection
            with self.breaker:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    data=data,
                    json=json,
                    params=params,
                    timeout=self.timeout,
                )

                # Log response
                elapsed_ms = response.elapsed.total_seconds() * 1000
                self._log_response(method, url, response.status_code, elapsed_ms, correlation_id)

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                return response

        except requests.HTTPError as e:
            self._log_error(method, url, e, correlation_id)
            raise

        except requests.RequestException as e:
            self._log_error(method, url, e, correlation_id)
            raise

        except Exception as e:
            # Circuit breaker or other errors
            self._log_error(method, url, e, correlation_id)
            if "circuit breaker" in str(e).lower():
                raise CircuitBreakerOpen(self.service_name)
            raise

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """Execute GET request."""
        return self._execute_request("GET", url, headers=headers, params=params, correlation_id=correlation_id)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """Execute POST request."""
        return self._execute_request("POST", url, headers=headers, data=data, json=json, correlation_id=correlation_id)

    def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """Execute PUT request."""
        return self._execute_request("PUT", url, headers=headers, data=data, json=json, correlation_id=correlation_id)

    def patch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """Execute PATCH request."""
        return self._execute_request("PATCH", url, headers=headers, data=data, json=json, correlation_id=correlation_id)

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> requests.Response:
        """Execute DELETE request."""
        return self._execute_request("DELETE", url, headers=headers, correlation_id=correlation_id)

    def close(self) -> None:
        """Close session and release connections."""
        self.session.close()


class ResilientAPIError(Exception):
    """Base exception for resilient API errors."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        self.service_name = service_name
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.correlation_id = correlation_id
        super().__init__(message)


class ResilientAPIClient:
    """
    High-level API client with circuit breaker, retry, and error handling.

    Wraps ResilientHTTPClient with business logic error handling.
    """

    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        """
        Initialize resilient API client.

        Args:
            service_name: Service name for circuit breaker
            base_url: Base URL for API (e.g., 'https://graph.microsoft.com/v1.0')
            timeout: Request timeout in seconds
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.http_client = ResilientHTTPClient(service_name=service_name, timeout=timeout)

    def _handle_error(
        self,
        error: Exception,
        url: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Handle and classify API errors.

        Raises:
            CircuitBreakerOpen: Service unavailable
            ResilientAPIError: Classified API error
        """
        if isinstance(error, CircuitBreakerOpen):
            raise

        if isinstance(error, requests.HTTPError):
            response = error.response
            raise ResilientAPIError(
                service_name=self.service_name,
                message=f"HTTP {response.status_code}: {response.reason}",
                status_code=response.status_code,
                response_body=response.text[:500],  # Truncate
                correlation_id=correlation_id,
            )

        if isinstance(error, RetryError):
            raise ResilientAPIError(
                service_name=self.service_name,
                message=f"All retry attempts exhausted for {url}",
                correlation_id=correlation_id,
            )

        raise ResilientAPIError(
            service_name=self.service_name,
            message=f"Unexpected error: {str(error)}",
            correlation_id=correlation_id,
        )

    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute GET request and return JSON response.

        Args:
            endpoint: API endpoint (e.g., '/deviceManagement/managedDevices')
            headers: Request headers
            params: Query parameters
            correlation_id: Correlation ID for audit trail

        Returns:
            JSON response as dict

        Raises:
            CircuitBreakerOpen: Service unavailable
            ResilientAPIError: API error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.http_client.get(url, headers=headers, params=params, correlation_id=correlation_id)
            return response.json()
        except Exception as e:
            self._handle_error(e, url, correlation_id)

    def post(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute POST request and return JSON response."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.http_client.post(url, headers=headers, json=json_data, correlation_id=correlation_id)
            return response.json()
        except Exception as e:
            self._handle_error(e, url, correlation_id)

    def put(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute PUT request and return JSON response."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.http_client.put(url, headers=headers, json=json_data, correlation_id=correlation_id)
            return response.json()
        except Exception as e:
            self._handle_error(e, url, correlation_id)

    def patch(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute PATCH request and return JSON response."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.http_client.patch(url, headers=headers, json=json_data, correlation_id=correlation_id)
            return response.json()
        except Exception as e:
            self._handle_error(e, url, correlation_id)

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Execute DELETE request."""
        url = f"{self.base_url}{endpoint}"

        try:
            self.http_client.delete(url, headers=headers, correlation_id=correlation_id)
        except Exception as e:
            self._handle_error(e, url, correlation_id)

    def close(self) -> None:
        """Close HTTP client and release connections."""
        self.http_client.close()
