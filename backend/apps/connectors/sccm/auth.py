# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft SCCM authentication using AdminService REST API.

Implements Windows Integrated Authentication (NTLM/Kerberos) for SCCM AdminService.

Authentication Methods:
1. Windows Integrated Authentication (default) - Uses current user context
2. Service Account - Username/password for service accounts
3. Certificate-based - Client certificate authentication

Configuration (environment variables):
- SCCM_SERVER_URL: SCCM AdminService URL (e.g., https://sccm.domain.com/AdminService)
- SCCM_SITE_CODE: SCCM site code (e.g., PS1)
- SCCM_AUTH_METHOD: Authentication method (wia, basic, certificate)
- SCCM_USERNAME: Service account username (for basic auth)
- SCCM_PASSWORD: Service account password (for basic auth)
- SCCM_CERT_PATH: Client certificate path (for cert auth)
- SCCM_CERT_PASSWORD: Certificate password (for cert auth)
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import requests
from decouple import config
from requests_ntlm import HttpNtlmAuth

from apps.core.structured_logging import StructuredLogger

logger = logging.getLogger(__name__)


class SCCMAuthError(Exception):
    """SCCM authentication error."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class SCCMAuth:
    """
    Microsoft SCCM authentication manager.

    Handles Windows Integrated Authentication (NTLM/Kerberos) for AdminService REST API.
    """

    # Cache key prefix for connection validation
    CACHE_KEY_PREFIX = "sccm_connection"

    # Connection timeout
    DEFAULT_TIMEOUT = 30

    def __init__(self):
        """Initialize SCCM authentication."""
        # Load configuration
        self.server_url = config("SCCM_SERVER_URL", default=None)
        self.site_code = config("SCCM_SITE_CODE", default=None)
        self.auth_method = config("SCCM_AUTH_METHOD", default="basic").lower()

        # Validate configuration
        if not self.server_url:
            raise SCCMAuthError("SCCM configuration incomplete. Required: SCCM_SERVER_URL")

        # Normalize server URL
        self.server_url = self.server_url.rstrip("/")

        # Initialize credentials based on auth method
        self._init_auth()

        self.structured_logger = StructuredLogger(__name__, user="system")
        self._session: Optional[requests.Session] = None

    def _init_auth(self) -> None:
        """Initialize authentication based on configured method."""
        if self.auth_method == "wia":
            # Windows Integrated Auth - uses current process credentials
            # Requires python-ntlm or requests-kerberos
            self.username = None
            self.password = None
            self.cert_path = None
        elif self.auth_method == "basic":
            # Basic auth with service account
            self.username = config("SCCM_USERNAME", default=None)
            self.password = config("SCCM_PASSWORD", default=None)
            if not self.username or not self.password:
                raise SCCMAuthError("SCCM basic auth requires SCCM_USERNAME and SCCM_PASSWORD")
            self.cert_path = None
        elif self.auth_method == "certificate":
            # Certificate-based authentication
            self.cert_path = config("SCCM_CERT_PATH", default=None)
            self.cert_password = config("SCCM_CERT_PASSWORD", default=None)
            if not self.cert_path:
                raise SCCMAuthError("SCCM certificate auth requires SCCM_CERT_PATH")
            self.username = None
            self.password = None
        else:
            raise SCCMAuthError(
                f"Invalid SCCM_AUTH_METHOD: {self.auth_method}. Must be one of: wia, basic, certificate"
            )

    def get_session(self, correlation_id: Optional[str] = None) -> requests.Session:
        """
        Get authenticated requests session.

        Args:
            correlation_id: Correlation ID for logging

        Returns:
            Authenticated requests.Session

        Raises:
            SCCMAuthError: If authentication fails
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        if self._session is None:
            self._session = self._create_session()

        return self._session

    def _create_session(self) -> requests.Session:
        """Create authenticated session based on auth method."""
        session = requests.Session()

        # Set common headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Configure authentication
        if self.auth_method == "wia":
            # Windows Integrated Authentication using NTLM
            # Uses current process credentials (requires domain-joined machine)
            session.auth = HttpNtlmAuth("", "")  # Empty = use current user
        elif self.auth_method == "basic":
            # NTLM auth with explicit credentials
            session.auth = HttpNtlmAuth(self.username, self.password)
        elif self.auth_method == "certificate":
            # Certificate-based authentication
            session.cert = (self.cert_path, self.cert_password)

        # Disable SSL verification warnings for self-signed certs (common in SCCM)
        # In production, configure proper CA bundle
        session.verify = config("SCCM_VERIFY_SSL", default=True, cast=bool)

        self.structured_logger.log_info(
            "SCCM session created",
            extra={
                "auth_method": self.auth_method,
                "server_url": self.server_url,
            },
        )

        return session

    def test_connection(self, correlation_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Test connection to SCCM AdminService.

        Args:
            correlation_id: Correlation ID for logging

        Returns:
            Tuple of (success: bool, message: str)
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        try:
            session = self.get_session(correlation_id)

            # Test endpoint - get site information
            url = f"{self.server_url}/wmi/SMS_Site"
            if self.site_code:
                url += f"?$filter=SiteCode eq '{self.site_code}'"

            response = session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            sites = data.get("value", [])

            if sites:
                site_info = sites[0]
                self.structured_logger.log_info(
                    "SCCM connection test successful",
                    extra={
                        "site_code": site_info.get("SiteCode"),
                        "site_name": site_info.get("SiteName"),
                        "version": site_info.get("Version"),
                    },
                )
                return True, f"Connected to SCCM site {site_info.get('SiteCode')}"
            else:
                return False, "Connected but no sites found"

        except requests.exceptions.ConnectionError as e:
            self.structured_logger.log_error(
                "SCCM connection failed",
                extra={"error": str(e), "server_url": self.server_url},
            )
            return False, f"Connection failed: {e}"
        except requests.exceptions.HTTPError as e:
            self.structured_logger.log_error(
                "SCCM authentication failed",
                extra={"status_code": e.response.status_code, "error": str(e)},
            )
            return False, f"Authentication failed: {e.response.status_code}"
        except Exception as e:
            self.structured_logger.log_error("SCCM connection test error", extra={"error": str(e)})
            return False, f"Error: {e}"

    def clear_session(self) -> None:
        """Clear the current session (for reconnection)."""
        if self._session:
            self._session.close()
            self._session = None
            self.structured_logger.log_info("SCCM session cleared")
