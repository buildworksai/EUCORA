# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Authentication module for Canonical Landscape API.

Supports:
- API key authentication (legacy)
- OAuth 2.0 client credentials
- Certificate-based authentication for on-premise deployments
"""
import hashlib
import hmac
import logging
import time
from typing import Optional

import requests
from decouple import config

logger = logging.getLogger(__name__)


class LandscapeAuthError(Exception):
    """Exception raised for Landscape authentication errors."""

    def __init__(self, message: str, is_transient: bool = False):
        """
        Initialize LandscapeAuthError.

        Args:
            message: Error description
            is_transient: Whether the error is transient and retryable
        """
        super().__init__(message)
        self.is_transient = is_transient


class LandscapeAuth:
    """
    Authentication handler for Canonical Landscape API.

    Landscape uses HMAC-SHA256 signed requests for API authentication.
    Each request must include:
    - X-LDS-Access-Key: The access key ID
    - X-LDS-Timestamp: Current UTC timestamp
    - X-LDS-Signature: HMAC-SHA256 signature of the request
    """

    SUPPORTED_AUTH_METHODS = ("api_key", "oauth", "certificate")

    def __init__(
        self,
        server_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        auth_method: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        """
        Initialize Landscape authentication.

        Args:
            server_url: Landscape API server URL
            access_key: API access key ID
            secret_key: API secret key for signing
            auth_method: Authentication method (api_key, oauth, certificate)
            verify_ssl: Whether to verify SSL certificates

        Raises:
            LandscapeAuthError: If required configuration is missing
        """
        self.server_url = server_url or config("LANDSCAPE_SERVER_URL", default=None)
        if not self.server_url:
            raise LandscapeAuthError("LANDSCAPE_SERVER_URL is required")

        # Normalize server URL - remove trailing slashes
        self.server_url = self.server_url.rstrip("/")

        self.auth_method = auth_method or config("LANDSCAPE_AUTH_METHOD", default="api_key")
        if self.auth_method not in self.SUPPORTED_AUTH_METHODS:
            raise LandscapeAuthError(
                f"Unsupported auth method: {self.auth_method}. " f"Supported: {self.SUPPORTED_AUTH_METHODS}"
            )

        self.verify_ssl = (
            verify_ssl if verify_ssl is not None else config("LANDSCAPE_VERIFY_SSL", default=True, cast=bool)
        )

        # API key authentication
        if self.auth_method == "api_key":
            self.access_key = access_key or config("LANDSCAPE_ACCESS_KEY", default=None)
            self.secret_key = secret_key or config("LANDSCAPE_SECRET_KEY", default=None)

            if not self.access_key or not self.secret_key:
                raise LandscapeAuthError("LANDSCAPE_ACCESS_KEY and LANDSCAPE_SECRET_KEY are required for api_key auth")

        # OAuth 2.0 authentication
        elif self.auth_method == "oauth":
            self.client_id = config("LANDSCAPE_CLIENT_ID", default=None)
            self.client_secret = config("LANDSCAPE_CLIENT_SECRET", default=None)
            self.token_url = config("LANDSCAPE_TOKEN_URL", default=f"{self.server_url}/oauth2/token")

            if not self.client_id or not self.client_secret:
                raise LandscapeAuthError("LANDSCAPE_CLIENT_ID and LANDSCAPE_CLIENT_SECRET are required for oauth auth")

            self._access_token: Optional[str] = None
            self._token_expires_at: float = 0

        # Certificate authentication
        elif self.auth_method == "certificate":
            self.cert_path = config("LANDSCAPE_CERT_PATH", default=None)
            self.key_path = config("LANDSCAPE_KEY_PATH", default=None)

            if not self.cert_path:
                raise LandscapeAuthError("LANDSCAPE_CERT_PATH is required for certificate auth")

        self._session: Optional[requests.Session] = None

    def _generate_signature(
        self,
        method: str,
        path: str,
        timestamp: str,
        body: str = "",
    ) -> str:
        """
        Generate HMAC-SHA256 signature for request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            timestamp: UTC timestamp
            body: Request body (empty for GET)

        Returns:
            Base64-encoded HMAC-SHA256 signature
        """
        # Canonical string format: METHOD\nPATH\nTIMESTAMP\nBODY_HASH
        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        canonical_string = f"{method.upper()}\n{path}\n{timestamp}\n{body_hash}"

        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            canonical_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return signature

    def _get_oauth_token(self) -> str:
        """
        Get OAuth 2.0 access token, refreshing if expired.

        Returns:
            Valid access token

        Raises:
            LandscapeAuthError: If token acquisition fails
        """
        # Check if we have a valid token
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                verify=self.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in

            logger.info("Successfully acquired OAuth token for Landscape")
            return self._access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to acquire OAuth token: {e}")
            raise LandscapeAuthError(
                f"OAuth token acquisition failed: {e}",
                is_transient=True,
            )

    def get_session(self) -> requests.Session:
        """
        Get or create authenticated session.

        Returns:
            Configured requests.Session
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.verify = self.verify_ssl

            # Set common headers
            self._session.headers.update(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "EUCORA-ControlPlane/1.0",
                }
            )

            # Configure authentication based on method
            if self.auth_method == "certificate":
                if self.key_path:
                    self._session.cert = (self.cert_path, self.key_path)
                else:
                    self._session.cert = self.cert_path

        return self._session

    def sign_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: str = "",
    ) -> dict[str, str]:
        """
        Sign a request with appropriate authentication.

        Args:
            method: HTTP method
            url: Full request URL
            headers: Existing headers
            body: Request body

        Returns:
            Updated headers with authentication
        """
        if self.auth_method == "api_key":
            # Extract path from URL
            from urllib.parse import urlparse

            parsed = urlparse(url)
            path = parsed.path

            timestamp = str(int(time.time()))
            signature = self._generate_signature(method, path, timestamp, body)

            headers.update(
                {
                    "X-LDS-Access-Key": self.access_key,
                    "X-LDS-Timestamp": timestamp,
                    "X-LDS-Signature": signature,
                }
            )

        elif self.auth_method == "oauth":
            token = self._get_oauth_token()
            headers["Authorization"] = f"Bearer {token}"

        # Certificate auth is handled at session level

        return headers

    def clear_session(self) -> None:
        """Clear the current session, forcing re-authentication."""
        if self._session:
            self._session.close()
            self._session = None

        if self.auth_method == "oauth":
            self._access_token = None
            self._token_expires_at = 0

    def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to Landscape server.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            session = self.get_session()
            url = f"{self.server_url}/api/v2/ping"

            headers = self.sign_request("GET", url, {})
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            server_version = data.get("version", "unknown")

            logger.info(f"Successfully connected to Landscape server v{server_version}")
            return True, f"Connected to Landscape server v{server_version}"

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            logger.error(f"Landscape connection failed: HTTP {status_code}")
            return False, f"HTTP error {status_code}: {e}"

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Landscape connection failed: {e}")
            return False, f"Connection failed: {e}"

        except Exception as e:
            logger.error(f"Landscape connection test failed: {e}")
            return False, f"Connection test failed: {e}"
