# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Intune authentication using Microsoft Graph API.

Implements OAuth 2.0 client credentials flow with Entra ID (Azure AD).

Authentication Flow:
1. Register app in Entra ID (Azure AD)
2. Grant API permissions: DeviceManagementApps.ReadWrite.All, DeviceManagementConfiguration.ReadWrite.All
3. Create client secret
4. Use tenant ID, client ID, and client secret to obtain access token
5. Access token valid for 1 hour (cached and refreshed automatically)

Configuration (environment variables):
- INTUNE_TENANT_ID: Azure AD tenant ID
- INTUNE_CLIENT_ID: Application (client) ID
- INTUNE_CLIENT_SECRET: Client secret value
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from decouple import config
from django.conf import settings
from django.core.cache import cache

from apps.core.resilient_http import ResilientAPIError, ResilientHTTPClient
from apps.core.structured_logging import StructuredLogger

logger = logging.getLogger(__name__)


class IntuneAuthError(Exception):
    """Intune authentication error."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class IntuneAuth:
    """
    Microsoft Intune authentication manager.

    Handles OAuth 2.0 token acquisition, caching, and refresh.
    """

    # Microsoft identity platform token endpoint
    TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Required API scopes
    SCOPES = "https://graph.microsoft.com/.default"

    # Token cache key prefix
    CACHE_KEY_PREFIX = "intune_access_token"

    # Token expiry buffer (refresh 5 minutes before expiry)
    EXPIRY_BUFFER_SECONDS = 300

    def __init__(self):
        """Initialize Intune authentication."""
        # Load configuration
        self.tenant_id = config("INTUNE_TENANT_ID", default=None)
        self.client_id = config("INTUNE_CLIENT_ID", default=None)
        self.client_secret = config("INTUNE_CLIENT_SECRET", default=None)

        # Validate configuration
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise IntuneAuthError(
                "Intune configuration incomplete. Required: INTUNE_TENANT_ID, INTUNE_CLIENT_ID, INTUNE_CLIENT_SECRET"
            )

        # Initialize HTTP client for auth requests
        self.http_client = ResilientHTTPClient(
            service_name="entra_id",
            timeout=30,
            max_retries=3,
        )

        self.structured_logger = StructuredLogger(__name__, user="system")

    def get_access_token(self, force_refresh: bool = False, correlation_id: Optional[str] = None) -> str:
        """
        Get valid access token (cached or new).

        Args:
            force_refresh: Force token refresh even if cached token is valid
            correlation_id: Correlation ID for logging

        Returns:
            Valid access token

        Raises:
            IntuneAuthError: If authentication fails
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        # Check cache unless force refresh
        if not force_refresh:
            cached_token = self._get_cached_token()
            if cached_token:
                self.structured_logger.debug("Using cached Intune access token")
                return cached_token

        # Acquire new token
        self.structured_logger.info("Acquiring new Intune access token")
        token_data = self._acquire_token(correlation_id)

        # Cache token
        self._cache_token(token_data)

        return token_data["access_token"]

    def _get_cached_token(self) -> Optional[str]:
        """Get cached access token if valid."""
        cache_key = f"{self.CACHE_KEY_PREFIX}:{self.tenant_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            expiry = cached_data.get("expiry")
            if expiry and datetime.now() < expiry:
                return cached_data.get("access_token")

        return None

    def _cache_token(self, token_data: Dict) -> None:
        """Cache access token with expiry."""
        expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

        # Calculate expiry with buffer
        expiry = datetime.now() + timedelta(seconds=expires_in - self.EXPIRY_BUFFER_SECONDS)

        cache_key = f"{self.CACHE_KEY_PREFIX}:{self.tenant_id}"
        cache_data = {
            "access_token": token_data["access_token"],
            "expiry": expiry,
        }

        # Cache for token lifetime
        cache.set(cache_key, cache_data, timeout=expires_in)

        self.structured_logger.info(
            "Cached Intune access token", extra={"expires_in": expires_in, "expiry": expiry.isoformat()}
        )

    def _acquire_token(self, correlation_id: Optional[str] = None) -> Dict:
        """
        Acquire new access token from Microsoft identity platform.

        Args:
            correlation_id: Correlation ID for logging

        Returns:
            Token response data

        Raises:
            IntuneAuthError: If token acquisition fails
        """
        token_url = self.TOKEN_ENDPOINT.format(tenant_id=self.tenant_id)

        # Prepare token request
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.SCOPES,
            "grant_type": "client_credentials",
        }

        try:
            response = self.http_client.post(
                url=token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                correlation_id=correlation_id,
            )

            token_data = response.json()

            # Validate response
            if "access_token" not in token_data:
                raise IntuneAuthError("Invalid token response: missing access_token", details={"response": token_data})

            self.structured_logger.security_event(
                event_type="INTUNE_AUTH_SUCCESS",
                severity="LOW",
                message="Successfully acquired Intune access token",
                details={"tenant_id": self.tenant_id, "expires_in": token_data.get("expires_in")},
            )

            return token_data

        except Exception as e:
            self.structured_logger.security_event(
                event_type="INTUNE_AUTH_FAILURE",
                severity="HIGH",
                message="Failed to acquire Intune access token",
                details={"error": str(e), "tenant_id": self.tenant_id},
            )

            raise IntuneAuthError(
                f"Failed to acquire Intune access token: {str(e)}",
                details={"tenant_id": self.tenant_id, "error": str(e)},
            )

    def clear_cached_token(self) -> None:
        """Clear cached access token (force re-authentication on next request)."""
        cache_key = f"{self.CACHE_KEY_PREFIX}:{self.tenant_id}"
        cache.delete(cache_key)
        self.structured_logger.info("Cleared cached Intune access token")

    def validate_token(self, token: str, correlation_id: Optional[str] = None) -> bool:
        """
        Validate access token by making test API call.

        Args:
            token: Access token to validate
            correlation_id: Correlation ID for logging

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Make test call to Graph API
            test_url = "https://graph.microsoft.com/v1.0/deviceManagement"

            response = self.http_client.get(
                url=test_url,
                headers={"Authorization": f"Bearer {token}"},
                correlation_id=correlation_id,
            )

            return response.status_code == 200

        except Exception as e:
            self.structured_logger.warning("Token validation failed", extra={"error": str(e)})
            return False

    def close(self) -> None:
        """Close HTTP client and release resources."""
        self.http_client.close()
