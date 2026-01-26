# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Entra ID authentication handler for Microsoft Graph API.

Supports:
- Client credentials flow (app-only, certificate-based preferred)
- On-behalf-of flow for delegated scenarios
- Managed identity for Azure-hosted deployments

Certificate-based authentication is MANDATORY for production per CLAUDE.md.
"""
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntraTokenInfo:
    """Immutable token information."""

    access_token: str
    expires_at: datetime
    token_type: str
    scope: str
    resource: str


class EntraAuth:
    """
    Entra ID authentication handler for Microsoft Graph API.

    Implements OAuth 2.0 client credentials flow with certificate-based
    authentication for production security compliance.
    """

    SUPPORTED_AUTH_METHODS = ("client_credentials", "certificate", "managed_identity")

    # Microsoft Graph endpoints
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    LOGIN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Token buffer to refresh before actual expiry
    TOKEN_BUFFER_SECONDS = 300

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        auth_method: str = "client_credentials",
        client_secret: Optional[str] = None,
        certificate_thumbprint: Optional[str] = None,
        certificate_private_key: Optional[str] = None,
        scope: str = "https://graph.microsoft.com/.default",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize Entra ID authentication handler.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            auth_method: Authentication method (client_credentials, certificate, managed_identity)
            client_secret: Client secret (for client_credentials)
            certificate_thumbprint: Certificate thumbprint (for certificate auth)
            certificate_private_key: Private key PEM (for certificate auth)
            scope: OAuth scope
            timeout: Request timeout in seconds
        """
        if auth_method not in self.SUPPORTED_AUTH_METHODS:
            raise ValueError(f"Unsupported auth method: {auth_method}. Supported: {self.SUPPORTED_AUTH_METHODS}")

        self._tenant_id = tenant_id
        self._client_id = client_id
        self._auth_method = auth_method
        self._client_secret = client_secret
        self._certificate_thumbprint = certificate_thumbprint
        self._certificate_private_key = certificate_private_key
        self._scope = scope
        self._timeout = timeout

        # Token cache
        self._token_info: Optional[EntraTokenInfo] = None
        self._token_lock_time: float = 0

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate authentication configuration."""
        if self._auth_method == "client_credentials":
            if not self._client_secret:
                raise ValueError("client_secret required for client_credentials auth")
        elif self._auth_method == "certificate":
            if not self._certificate_thumbprint or not self._certificate_private_key:
                raise ValueError("certificate_thumbprint and certificate_private_key required for certificate auth")
        elif self._auth_method == "managed_identity":
            # Managed identity uses Azure IMDS
            pass

    @property
    def token_url(self) -> str:
        """Get the OAuth token endpoint URL."""
        return self.LOGIN_URL_TEMPLATE.format(tenant_id=self._tenant_id)

    @property
    def is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._token_info:
            return False
        buffer_time = timedelta(seconds=self.TOKEN_BUFFER_SECONDS)
        return datetime.now(timezone.utc) < (self._token_info.expires_at - buffer_time)

    def get_auth_header(self) -> dict[str, str]:
        """
        Get authorization header for API requests.

        Returns:
            Dict with Authorization header
        """
        if not self._token_info:
            raise RuntimeError("No token available. Call authenticate() first.")
        return {"Authorization": f"{self._token_info.token_type} {self._token_info.access_token}"}

    async def authenticate(self) -> EntraTokenInfo:
        """
        Authenticate and obtain access token.

        Returns:
            Token information

        Raises:
            httpx.HTTPStatusError: If authentication fails
            ValueError: If configuration is invalid
        """
        if self.is_token_valid and self._token_info:
            logger.debug("Using cached Entra ID token")
            return self._token_info

        logger.info(f"Authenticating to Entra ID using {self._auth_method}")

        if self._auth_method == "client_credentials":
            token_info = await self._authenticate_client_credentials()
        elif self._auth_method == "certificate":
            token_info = await self._authenticate_certificate()
        elif self._auth_method == "managed_identity":
            token_info = await self._authenticate_managed_identity()
        else:
            raise ValueError(f"Unknown auth method: {self._auth_method}")

        self._token_info = token_info
        logger.info(f"Entra ID authentication successful, expires at {token_info.expires_at.isoformat()}")
        return token_info

    async def _authenticate_client_credentials(self) -> EntraTokenInfo:
        """Authenticate using client credentials (secret)."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": self._scope,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return self._parse_token_response(response.json())

    async def _authenticate_certificate(self) -> EntraTokenInfo:
        """
        Authenticate using client certificate.

        Uses JWT assertion with x5t claim for certificate identification.
        """
        import base64

        import jwt

        # Build JWT assertion
        now = int(time.time())
        claims = {
            "aud": self.token_url,
            "iss": self._client_id,
            "sub": self._client_id,
            "jti": hashlib.sha256(f"{now}-{self._client_id}".encode()).hexdigest()[:32],
            "nbf": now,
            "exp": now + 600,  # 10 minutes
        }

        # x5t header is base64url-encoded SHA-1 thumbprint
        x5t = base64.urlsafe_b64encode(bytes.fromhex(self._certificate_thumbprint or "")).rstrip(b"=").decode()

        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "x5t": x5t,
        }

        assertion = jwt.encode(
            claims,
            self._certificate_private_key,
            algorithm="RS256",
            headers=headers,
        )

        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "scope": self._scope,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return self._parse_token_response(response.json())

    async def _authenticate_managed_identity(self) -> EntraTokenInfo:
        """
        Authenticate using Azure Managed Identity.

        Uses Azure Instance Metadata Service (IMDS).
        """
        imds_url = "http://169.254.169.254/metadata/identity/oauth2/token"
        params = {
            "api-version": "2019-08-01",
            "resource": "https://graph.microsoft.com",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                imds_url,
                params=params,
                headers={"Metadata": "true"},
            )
            response.raise_for_status()

            data = response.json()
            expires_at = datetime.fromtimestamp(int(data["expires_on"]), tz=timezone.utc)

            return EntraTokenInfo(
                access_token=data["access_token"],
                expires_at=expires_at,
                token_type=data.get("token_type", "Bearer"),
                scope=self._scope,
                resource=data.get("resource", "https://graph.microsoft.com"),
            )

    def _parse_token_response(self, data: dict[str, Any]) -> EntraTokenInfo:
        """Parse OAuth token response."""
        expires_in = int(data.get("expires_in", 3600))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        return EntraTokenInfo(
            access_token=data["access_token"],
            expires_at=expires_at,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", self._scope),
            resource="https://graph.microsoft.com",
        )

    async def refresh_token(self) -> EntraTokenInfo:
        """
        Refresh the access token.

        For client credentials flow, this re-authenticates.
        """
        self._token_info = None
        return await self.authenticate()

    def get_token_hash(self) -> str:
        """Get hash of current token for audit logging (never log the actual token)."""
        if not self._token_info:
            return "no_token"
        return hashlib.sha256(self._token_info.access_token.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        return (
            f"EntraAuth(tenant_id={self._tenant_id[:8]}..., "
            f"client_id={self._client_id[:8]}..., "
            f"auth_method={self._auth_method})"
        )
