# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Jamf Pro authentication manager with OAuth 2.0 support.

Handles authentication with Jamf Pro API using:
- OAuth 2.0 client credentials flow (preferred for API integrations)
- Basic authentication (fallback for legacy configurations)
- Token caching with automatic refresh

Configuration (environment variables):
- JAMF_SERVER_URL: Jamf Pro server URL (e.g., https://yourorg.jamfcloud.com)
- JAMF_CLIENT_ID: OAuth 2.0 client ID (preferred)
- JAMF_CLIENT_SECRET: OAuth 2.0 client secret (preferred)
- JAMF_USERNAME: Basic auth username (fallback)
- JAMF_PASSWORD: Basic auth password (fallback)

Example:
    auth = JamfAuth()
    token = auth.get_access_token(correlation_id='DEPLOY-123')
"""
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from decouple import config
from django.core.cache import cache

from apps.core.resilient_http import ResilientHTTPClient
from apps.core.structured_logging import StructuredLogger

logger = logging.getLogger(__name__)


class JamfAuthError(Exception):
    """Exception raised for Jamf authentication errors."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(self.message)


class JamfAuth:
    """
    Jamf Pro authentication manager.

    Supports both OAuth 2.0 (preferred) and Basic authentication (fallback).
    Implements token caching with automatic refresh.
    """

    # OAuth 2.0 endpoints
    TOKEN_ENDPOINT = "/api/oauth/token"
    TOKEN_VALIDATION_ENDPOINT = "/api/v1/auth"

    # Token expiry buffer (refresh 5 minutes before expiry)
    EXPIRY_BUFFER_SECONDS = 300

    # Cache TTL for tokens
    CACHE_TTL_SECONDS = 1800  # 30 minutes (Jamf tokens typically expire after 30 minutes)

    def __init__(self):
        """
        Initialize Jamf authentication manager.

        Loads configuration from environment variables and determines auth method.

        Raises:
            JamfAuthError: If required configuration is missing
        """
        # Load server URL (required)
        self.server_url = config("JAMF_SERVER_URL", default=None)
        if not self.server_url:
            raise JamfAuthError("JAMF_SERVER_URL is required")

        # Remove trailing slash from server URL
        self.server_url = self.server_url.rstrip("/")

        # Load OAuth 2.0 credentials (preferred)
        self.client_id = config("JAMF_CLIENT_ID", default=None)
        self.client_secret = config("JAMF_CLIENT_SECRET", default=None)

        # Load Basic auth credentials (fallback)
        self.username = config("JAMF_USERNAME", default=None)
        self.password = config("JAMF_PASSWORD", default=None)

        # Determine auth method
        if self.client_id and self.client_secret:
            self.auth_method = "oauth"
        elif self.username and self.password:
            self.auth_method = "basic"
        else:
            raise JamfAuthError(
                "Either JAMF_CLIENT_ID + JAMF_CLIENT_SECRET (OAuth) or "
                "JAMF_USERNAME + JAMF_PASSWORD (Basic) must be configured"
            )

        # Initialize HTTP client
        self.http_client = ResilientHTTPClient(service_name="jamf", timeout=30)

        # Initialize structured logger
        self.structured_logger = StructuredLogger(__name__, user="system")

        logger.info(f"Jamf authentication initialized (method={self.auth_method}, server={self.server_url})")

    def get_access_token(self, force_refresh: bool = False, correlation_id: Optional[str] = None) -> str:
        """
        Get valid access token (cached or new).

        Args:
            force_refresh: Force token refresh even if cached token is valid
            correlation_id: Correlation ID for tracing

        Returns:
            Valid access token string

        Raises:
            JamfAuthError: If token acquisition fails
        """
        # Check cache for valid token (unless force refresh)
        if not force_refresh:
            cached_token = self._get_cached_token()
            if cached_token:
                self.structured_logger.debug("Using cached Jamf access token", extra={"auth_method": self.auth_method})
                return cached_token

        # Acquire new token based on auth method
        if self.auth_method == "oauth":
            token_data = self._acquire_oauth_token(correlation_id)
        else:
            token_data = self._acquire_basic_token(correlation_id)

        # Cache token
        self._cache_token(token_data)

        return token_data["access_token"]

    def _acquire_oauth_token(self, correlation_id: Optional[str] = None) -> Dict:
        """
        Acquire access token using OAuth 2.0 client credentials flow.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Token data dict with 'access_token' and 'expires_in'

        Raises:
            JamfAuthError: If token acquisition fails
        """
        token_url = f"{self.server_url}{self.TOKEN_ENDPOINT}"

        self.structured_logger.info(
            "Acquiring Jamf OAuth 2.0 access token", extra={"server": self.server_url, "client_id": self.client_id}
        )

        # Prepare OAuth 2.0 request
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            response = self.http_client.post(
                url=token_url, data=payload, headers=headers, correlation_id=correlation_id
            )

            token_data = response.json()

            # Validate token response
            if "access_token" not in token_data:
                raise JamfAuthError("Invalid token response: missing 'access_token'", correlation_id=correlation_id)

            # Jamf returns expires_in in seconds
            if "expires_in" not in token_data:
                # Default to 30 minutes if not provided
                token_data["expires_in"] = 1800

            self.structured_logger.security_event(
                event_type="JAMF_AUTH_SUCCESS",
                severity="LOW",
                message=f'Successfully acquired Jamf OAuth 2.0 token (expires_in={token_data["expires_in"]}s)',
                details={"auth_method": "oauth", "server": self.server_url},
            )

            return token_data

        except Exception as e:
            self.structured_logger.security_event(
                event_type="JAMF_AUTH_FAILURE",
                severity="HIGH",
                message=f"Failed to acquire Jamf OAuth 2.0 token: {str(e)}",
                details={"auth_method": "oauth", "server": self.server_url, "error": str(e)},
            )
            raise JamfAuthError(
                f"Failed to acquire Jamf OAuth 2.0 token: {str(e)}", correlation_id=correlation_id
            ) from e

    def _acquire_basic_token(self, correlation_id: Optional[str] = None) -> Dict:
        """
        Acquire access token using Basic authentication.

        Jamf Pro API supports Basic auth for legacy integrations.
        This method creates a token using the /api/v1/auth/token endpoint.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Token data dict with 'access_token' and 'expires_in'

        Raises:
            JamfAuthError: If token acquisition fails
        """
        token_url = f"{self.server_url}/api/v1/auth/token"

        self.structured_logger.info(
            "Acquiring Jamf Basic auth token", extra={"server": self.server_url, "username": self.username}
        )

        # Create Basic auth header
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Accept": "application/json",
        }

        try:
            response = self.http_client.post(url=token_url, headers=headers, correlation_id=correlation_id)

            token_data = response.json()

            # Validate token response
            if "token" not in token_data:
                raise JamfAuthError("Invalid token response: missing 'token'", correlation_id=correlation_id)

            # Normalize response format (Basic auth returns 'token', OAuth returns 'access_token')
            normalized_token_data = {
                "access_token": token_data["token"],
                "expires_in": token_data.get("expires", 1800),  # Default to 30 minutes
            }

            self.structured_logger.security_event(
                event_type="JAMF_AUTH_SUCCESS",
                severity="LOW",
                message=f'Successfully acquired Jamf Basic auth token (expires_in={normalized_token_data["expires_in"]}s)',
                details={"auth_method": "basic", "server": self.server_url, "username": self.username},
            )

            return normalized_token_data

        except Exception as e:
            self.structured_logger.security_event(
                event_type="JAMF_AUTH_FAILURE",
                severity="HIGH",
                message=f"Failed to acquire Jamf Basic auth token: {str(e)}",
                details={"auth_method": "basic", "server": self.server_url, "username": self.username, "error": str(e)},
            )
            raise JamfAuthError(
                f"Failed to acquire Jamf Basic auth token: {str(e)}", correlation_id=correlation_id
            ) from e

    def _get_cached_token(self) -> Optional[str]:
        """
        Get cached access token if available and not expired.

        Returns:
            Cached token string or None if not available/expired
        """
        cache_key = self._get_cache_key()
        cached_data = cache.get(cache_key)

        if cached_data:
            token = cached_data.get("token")
            expiry = cached_data.get("expiry")

            # Check if token is still valid (with buffer)
            if expiry and datetime.utcnow() < expiry:
                return token

        return None

    def _cache_token(self, token_data: Dict) -> None:
        """
        Cache access token with expiry time.

        Args:
            token_data: Token data dict with 'access_token' and 'expires_in'
        """
        cache_key = self._get_cache_key()

        # Calculate expiry time with buffer
        expires_in_seconds = token_data.get("expires_in", self.CACHE_TTL_SECONDS)
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in_seconds - self.EXPIRY_BUFFER_SECONDS)

        cached_data = {
            "token": token_data["access_token"],
            "expiry": expiry_time,
        }

        # Cache with TTL
        cache.set(cache_key, cached_data, timeout=expires_in_seconds)

        self.structured_logger.debug(
            "Cached Jamf access token", extra={"expiry": expiry_time.isoformat(), "expires_in": expires_in_seconds}
        )

    def _get_cache_key(self) -> str:
        """
        Get cache key for token storage.

        Returns:
            Cache key string
        """
        # Include server URL and client_id/username to support multiple Jamf instances
        identifier = self.client_id if self.auth_method == "oauth" else self.username
        return f"jamf_token:{self.server_url}:{identifier}"

    def clear_cached_token(self) -> None:
        """
        Clear cached access token.

        Useful for testing or forcing token refresh.
        """
        cache_key = self._get_cache_key()
        cache.delete(cache_key)

        self.structured_logger.debug("Cleared cached Jamf access token")

    def validate_token(self, token: str, correlation_id: Optional[str] = None) -> bool:
        """
        Validate access token by making test API call.

        Args:
            token: Access token to validate
            correlation_id: Correlation ID for tracing

        Returns:
            True if token is valid, False otherwise
        """
        validation_url = f"{self.server_url}{self.TOKEN_VALIDATION_ENDPOINT}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            response = self.http_client.get(url=validation_url, headers=headers, correlation_id=correlation_id)

            # If we get 200, token is valid
            return response.status_code == 200

        except Exception as e:
            self.structured_logger.warning(f"Token validation failed: {str(e)}", extra={"error": str(e)})
            return False
