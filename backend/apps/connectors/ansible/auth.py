# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Authentication module for AWX/Ansible Tower API.

Supports:
- Personal Access Token (PAT) authentication
- OAuth 2.0 token authentication
- Basic authentication (username/password)
"""
import logging
import time
from typing import Optional

import requests
from decouple import config

logger = logging.getLogger(__name__)


class AnsibleAuthError(Exception):
    """Exception raised for Ansible/AWX authentication errors."""

    def __init__(self, message: str, is_transient: bool = False):
        """
        Initialize AnsibleAuthError.

        Args:
            message: Error description
            is_transient: Whether the error is transient and retryable
        """
        super().__init__(message)
        self.is_transient = is_transient


class AnsibleAuth:
    """
    Authentication handler for AWX/Ansible Tower API.

    Supports multiple authentication methods:
    - token: Personal Access Token (recommended)
    - oauth: OAuth 2.0 application token
    - basic: Username/password (not recommended for production)
    """

    SUPPORTED_AUTH_METHODS = ("token", "oauth", "basic")

    def __init__(
        self,
        server_url: Optional[str] = None,
        auth_method: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        """
        Initialize AWX/Ansible Tower authentication.

        Args:
            server_url: AWX/Tower server URL
            auth_method: Authentication method (token, oauth, basic)
            token: Personal Access Token for token auth
            username: Username for basic/oauth auth
            password: Password for basic/oauth auth
            client_id: OAuth client ID
            client_secret: OAuth client secret
            verify_ssl: Whether to verify SSL certificates

        Raises:
            AnsibleAuthError: If required configuration is missing
        """
        self.server_url = server_url or config("AWX_SERVER_URL", default=None)
        if not self.server_url:
            raise AnsibleAuthError("AWX_SERVER_URL is required")

        # Normalize server URL
        self.server_url = self.server_url.rstrip("/")

        self.auth_method = auth_method or config("AWX_AUTH_METHOD", default="token")
        if self.auth_method not in self.SUPPORTED_AUTH_METHODS:
            raise AnsibleAuthError(
                f"Unsupported auth method: {self.auth_method}. " f"Supported: {self.SUPPORTED_AUTH_METHODS}"
            )

        self.verify_ssl = verify_ssl if verify_ssl is not None else config("AWX_VERIFY_SSL", default=True, cast=bool)

        # Token authentication (recommended)
        if self.auth_method == "token":
            self.token = token or config("AWX_TOKEN", default=None)
            if not self.token:
                raise AnsibleAuthError("AWX_TOKEN is required for token auth")

        # Basic authentication
        elif self.auth_method == "basic":
            self.username = username or config("AWX_USERNAME", default=None)
            self.password = password or config("AWX_PASSWORD", default=None)
            if not self.username or not self.password:
                raise AnsibleAuthError("AWX_USERNAME and AWX_PASSWORD are required for basic auth")

        # OAuth 2.0 authentication
        elif self.auth_method == "oauth":
            self.client_id = client_id or config("AWX_CLIENT_ID", default=None)
            self.client_secret = client_secret or config("AWX_CLIENT_SECRET", default=None)
            self.username = username or config("AWX_USERNAME", default=None)
            self.password = password or config("AWX_PASSWORD", default=None)

            if not self.client_id or not self.client_secret:
                raise AnsibleAuthError("AWX_CLIENT_ID and AWX_CLIENT_SECRET are required for oauth auth")

            self._access_token: Optional[str] = None
            self._refresh_token: Optional[str] = None
            self._token_expires_at: float = 0

        self._session: Optional[requests.Session] = None

    def _get_oauth_token(self) -> str:
        """
        Get OAuth 2.0 access token, refreshing if expired.

        Returns:
            Valid access token

        Raises:
            AnsibleAuthError: If token acquisition fails
        """
        # Check if we have a valid token
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        try:
            token_url = f"{self.server_url}/api/o/token/"

            # If we have a refresh token, use it
            if self._refresh_token:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            # Otherwise use password grant
            elif self.username and self.password:
                data = {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            # Or client credentials
            else:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }

            response = requests.post(
                token_url,
                data=data,
                verify=self.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in

            logger.info("Successfully acquired OAuth token for AWX")
            return self._access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to acquire OAuth token: {e}")
            raise AnsibleAuthError(
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
            if self.auth_method == "token":
                self._session.headers["Authorization"] = f"Bearer {self.token}"

            elif self.auth_method == "basic":
                self._session.auth = (self.username, self.password)

            # OAuth is handled per-request since tokens expire

        return self._session

    def sign_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
    ) -> dict[str, str]:
        """
        Add authentication to request headers.

        Args:
            method: HTTP method
            url: Request URL
            headers: Existing headers

        Returns:
            Updated headers with authentication
        """
        if self.auth_method == "oauth":
            token = self._get_oauth_token()
            headers["Authorization"] = f"Bearer {token}"

        # Token and basic auth are handled at session level

        return headers

    def clear_session(self) -> None:
        """Clear the current session, forcing re-authentication."""
        if self._session:
            self._session.close()
            self._session = None

        if self.auth_method == "oauth":
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = 0

    def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to AWX/Tower server.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            session = self.get_session()
            url = f"{self.server_url}/api/v2/ping/"

            headers = self.sign_request("GET", url, {})
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            version = data.get("version", "unknown")
            active_node = data.get("active_node", "unknown")

            logger.info(f"Successfully connected to AWX v{version} (node: {active_node})")
            return True, f"Connected to AWX v{version} (node: {active_node})"

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            logger.error(f"AWX connection failed: HTTP {status_code}")
            return False, f"HTTP error {status_code}: {e}"

        except requests.exceptions.ConnectionError as e:
            logger.error(f"AWX connection failed: {e}")
            return False, f"Connection failed: {e}"

        except Exception as e:
            logger.error(f"AWX connection test failed: {e}")
            return False, f"Connection test failed: {e}"

    def get_api_version(self) -> dict:
        """
        Get API version information.

        Returns:
            API version details
        """
        try:
            session = self.get_session()
            url = f"{self.server_url}/api/v2/"

            headers = self.sign_request("GET", url, {})
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get API version: {e}")
            raise AnsibleAuthError(f"Failed to get API version: {e}")
