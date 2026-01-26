# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Entra ID authentication handler."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.connectors.entra.auth import EntraAuth, EntraTokenInfo


class TestEntraAuthInit:
    """Tests for EntraAuth initialization."""

    def test_init_client_credentials(self):
        """Test initialization with client credentials."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        assert auth._tenant_id == "test-tenant"
        assert auth._client_id == "test-client"
        assert auth._auth_method == "client_credentials"

    def test_init_certificate(self):
        """Test initialization with certificate auth."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="certificate",
            certificate_thumbprint="ABC123",
            certificate_private_key="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        )
        assert auth._auth_method == "certificate"

    def test_init_managed_identity(self):
        """Test initialization with managed identity."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="managed_identity",
        )
        assert auth._auth_method == "managed_identity"

    def test_init_invalid_auth_method(self):
        """Test that invalid auth method raises error."""
        with pytest.raises(ValueError, match="Unsupported auth method"):
            EntraAuth(
                tenant_id="test-tenant",
                client_id="test-client",
                auth_method="invalid_method",
            )

    def test_init_client_credentials_missing_secret(self):
        """Test that missing secret raises error for client_credentials."""
        with pytest.raises(ValueError, match="client_secret required"):
            EntraAuth(
                tenant_id="test-tenant",
                client_id="test-client",
                auth_method="client_credentials",
            )

    def test_init_certificate_missing_thumbprint(self):
        """Test that missing thumbprint raises error for certificate auth."""
        with pytest.raises(ValueError, match="certificate_thumbprint and certificate_private_key required"):
            EntraAuth(
                tenant_id="test-tenant",
                client_id="test-client",
                auth_method="certificate",
                certificate_thumbprint="ABC123",
            )


class TestEntraAuthTokenUrl:
    """Tests for token URL generation."""

    def test_token_url(self):
        """Test token URL is correctly formatted."""
        auth = EntraAuth(
            tenant_id="my-tenant-id",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        assert auth.token_url == "https://login.microsoftonline.com/my-tenant-id/oauth2/v2.0/token"


class TestEntraAuthTokenValidity:
    """Tests for token validity checking."""

    def test_is_token_valid_no_token(self):
        """Test is_token_valid returns False when no token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        assert auth.is_token_valid is False

    def test_is_token_valid_expired_token(self):
        """Test is_token_valid returns False for expired token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        auth._token_info = EntraTokenInfo(
            access_token="test-token",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        assert auth.is_token_valid is False

    def test_is_token_valid_valid_token(self):
        """Test is_token_valid returns True for valid token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        auth._token_info = EntraTokenInfo(
            access_token="test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        assert auth.is_token_valid is True

    def test_is_token_valid_within_buffer(self):
        """Test is_token_valid returns False when within buffer period."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        # Token expires in 4 minutes (within 5 minute buffer)
        auth._token_info = EntraTokenInfo(
            access_token="test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=4),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        assert auth.is_token_valid is False


class TestEntraAuthGetAuthHeader:
    """Tests for get_auth_header method."""

    def test_get_auth_header_no_token(self):
        """Test get_auth_header raises when no token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        with pytest.raises(RuntimeError, match="No token available"):
            auth.get_auth_header()

    def test_get_auth_header_with_token(self):
        """Test get_auth_header returns correct header."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        auth._token_info = EntraTokenInfo(
            access_token="test-access-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        header = auth.get_auth_header()
        assert header == {"Authorization": "Bearer test-access-token"}


class TestEntraAuthAuthenticate:
    """Tests for authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_returns_cached_token(self):
        """Test authenticate returns cached token if valid."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        expected_token = EntraTokenInfo(
            access_token="cached-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        auth._token_info = expected_token

        result = await auth.authenticate()
        assert result == expected_token

    @pytest.mark.asyncio
    async def test_authenticate_client_credentials(self):
        """Test authenticate with client credentials."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "https://graph.microsoft.com/.default",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await auth.authenticate()

            assert result.access_token == "new-token"
            assert result.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_authenticate_managed_identity(self):
        """Test authenticate with managed identity."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="managed_identity",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "managed-identity-token",
            "expires_on": str(int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())),
            "token_type": "Bearer",
            "resource": "https://graph.microsoft.com",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await auth.authenticate()

            assert result.access_token == "managed-identity-token"


class TestEntraAuthRefreshToken:
    """Tests for refresh_token method."""

    @pytest.mark.asyncio
    async def test_refresh_token_clears_cache(self):
        """Test refresh_token clears existing token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        auth._token_info = EntraTokenInfo(
            access_token="old-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await auth.refresh_token()

            assert result.access_token == "new-token"


class TestEntraAuthTokenHash:
    """Tests for get_token_hash method."""

    def test_get_token_hash_no_token(self):
        """Test get_token_hash returns placeholder when no token."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        assert auth.get_token_hash() == "no_token"

    def test_get_token_hash_with_token(self):
        """Test get_token_hash returns truncated hash."""
        auth = EntraAuth(
            tenant_id="test-tenant",
            client_id="test-client",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        auth._token_info = EntraTokenInfo(
            access_token="test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_type="Bearer",
            scope="test",
            resource="graph",
        )
        token_hash = auth.get_token_hash()
        assert len(token_hash) == 16
        assert token_hash != "test-token"  # Should be hashed, not the actual token


class TestEntraAuthRepr:
    """Tests for __repr__ method."""

    def test_repr(self):
        """Test string representation."""
        auth = EntraAuth(
            tenant_id="test-tenant-id-12345",
            client_id="test-client-id-67890",
            auth_method="client_credentials",
            client_secret="test-secret",
        )
        repr_str = repr(auth)
        assert "tenant_id=test-ten" in repr_str
        assert "client_id=test-cli" in repr_str
        assert "auth_method=client_credentials" in repr_str
        assert "test-secret" not in repr_str  # Secret should not be in repr
