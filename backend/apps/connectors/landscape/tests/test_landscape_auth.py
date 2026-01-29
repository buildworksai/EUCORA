# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Landscape authentication."""
from unittest.mock import Mock, patch

import pytest
import requests

from apps.connectors.landscape.auth import LandscapeAuth, LandscapeAuthError


class TestLandscapeAuthInit:
    """Tests for LandscapeAuth initialization."""

    def test_init_missing_server_url_raises_error(self):
        """Test that missing server URL raises error."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:
            mock_config.return_value = None
            with pytest.raises(LandscapeAuthError) as exc_info:
                LandscapeAuth()
            assert "LANDSCAPE_SERVER_URL" in str(exc_info.value)

    def test_init_api_key_missing_credentials(self):
        """Test API key auth without credentials raises error."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": None,
                    "LANDSCAPE_SECRET_KEY": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(LandscapeAuthError) as exc_info:
                LandscapeAuth()
            assert "LANDSCAPE_ACCESS_KEY" in str(exc_info.value)

    def test_init_oauth_missing_credentials(self):
        """Test OAuth auth without credentials raises error."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "oauth",
                    "LANDSCAPE_CLIENT_ID": None,
                    "LANDSCAPE_CLIENT_SECRET": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(LandscapeAuthError) as exc_info:
                LandscapeAuth()
            assert "LANDSCAPE_CLIENT_ID" in str(exc_info.value)

    def test_init_certificate_missing_cert_path(self):
        """Test certificate auth without cert path raises error."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "certificate",
                    "LANDSCAPE_CERT_PATH": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(LandscapeAuthError) as exc_info:
                LandscapeAuth()
            assert "LANDSCAPE_CERT_PATH" in str(exc_info.value)

    def test_init_invalid_auth_method(self):
        """Test invalid auth method raises error."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "invalid_method",
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(LandscapeAuthError) as exc_info:
                LandscapeAuth()
            assert "invalid_method" in str(exc_info.value)

    def test_init_success_api_key_auth(self):
        """Test successful initialization with API key auth."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com/",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": "test_access_key",
                    "LANDSCAPE_SECRET_KEY": "test_secret_key",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = LandscapeAuth()
            assert auth.server_url == "https://landscape.example.com"
            assert auth.auth_method == "api_key"
            assert auth.access_key == "test_access_key"

    def test_init_normalizes_server_url(self):
        """Test that trailing slashes are removed from server URL."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com///",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": "test_key",
                    "LANDSCAPE_SECRET_KEY": "test_secret",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = LandscapeAuth()
            assert not auth.server_url.endswith("/")


class TestLandscapeAuthSignature:
    """Tests for HMAC signature generation."""

    @pytest.fixture
    def auth(self):
        """Create LandscapeAuth instance with mocked config."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": "test_access_key",
                    "LANDSCAPE_SECRET_KEY": "test_secret_key",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return LandscapeAuth()

    def test_generate_signature_consistent(self, auth):
        """Test that same inputs produce same signature."""
        sig1 = auth._generate_signature("GET", "/api/v2/computers", "1234567890")
        sig2 = auth._generate_signature("GET", "/api/v2/computers", "1234567890")
        assert sig1 == sig2

    def test_generate_signature_different_for_different_methods(self, auth):
        """Test that different methods produce different signatures."""
        sig1 = auth._generate_signature("GET", "/api/v2/computers", "1234567890")
        sig2 = auth._generate_signature("POST", "/api/v2/computers", "1234567890")
        assert sig1 != sig2

    def test_generate_signature_different_for_different_paths(self, auth):
        """Test that different paths produce different signatures."""
        sig1 = auth._generate_signature("GET", "/api/v2/computers", "1234567890")
        sig2 = auth._generate_signature("GET", "/api/v2/packages", "1234567890")
        assert sig1 != sig2

    def test_sign_request_adds_headers(self, auth):
        """Test that sign_request adds required headers."""
        headers = {}
        signed = auth.sign_request(
            "GET",
            "https://landscape.example.com/api/v2/computers",
            headers,
        )

        assert "X-LDS-Access-Key" in signed
        assert "X-LDS-Timestamp" in signed
        assert "X-LDS-Signature" in signed
        assert signed["X-LDS-Access-Key"] == "test_access_key"


class TestLandscapeAuthSession:
    """Tests for session management."""

    @pytest.fixture
    def auth(self):
        """Create LandscapeAuth instance."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": "test_key",
                    "LANDSCAPE_SECRET_KEY": "test_secret",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return LandscapeAuth()

    def test_get_session_creates_session(self, auth):
        """Test that get_session creates a new session."""
        session = auth.get_session()
        assert session is not None
        assert isinstance(session, requests.Session)

    def test_get_session_reuses_session(self, auth):
        """Test that get_session reuses existing session."""
        session1 = auth.get_session()
        session2 = auth.get_session()
        assert session1 is session2

    def test_clear_session(self, auth):
        """Test that clear_session removes session."""
        session1 = auth.get_session()
        auth.clear_session()
        session2 = auth.get_session()
        assert session1 is not session2


class TestLandscapeAuthConnection:
    """Tests for connection testing."""

    @pytest.fixture
    def auth(self):
        """Create LandscapeAuth instance."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "api_key",
                    "LANDSCAPE_ACCESS_KEY": "test_key",
                    "LANDSCAPE_SECRET_KEY": "test_secret",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return LandscapeAuth()

    def test_test_connection_success(self, auth):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.json.return_value = {"version": "23.10"}
        mock_response.raise_for_status = Mock()

        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is True
            assert "23.10" in message

    def test_test_connection_http_error(self, auth):
        """Test connection test with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is False
            assert "401" in message

    def test_test_connection_connection_error(self, auth):
        """Test connection test with connection error."""
        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection refused")
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is False
            assert "Connection failed" in message


class TestLandscapeAuthOAuth:
    """Tests for OAuth authentication."""

    @pytest.fixture
    def oauth_auth(self):
        """Create LandscapeAuth instance with OAuth."""
        with patch("apps.connectors.landscape.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "LANDSCAPE_SERVER_URL": "https://landscape.example.com",
                    "LANDSCAPE_AUTH_METHOD": "oauth",
                    "LANDSCAPE_CLIENT_ID": "test_client_id",
                    "LANDSCAPE_CLIENT_SECRET": "test_client_secret",
                    "LANDSCAPE_TOKEN_URL": "https://landscape.example.com/oauth2/token",
                    "LANDSCAPE_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return LandscapeAuth()

    def test_get_oauth_token_success(self, oauth_auth):
        """Test successful OAuth token acquisition."""
        with patch("apps.connectors.landscape.auth.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "expires_in": 3600,
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            token = oauth_auth._get_oauth_token()

            assert token == "test_token_123"
            assert oauth_auth._access_token == "test_token_123"

    def test_get_oauth_token_reuses_valid_token(self, oauth_auth):
        """Test that valid token is reused."""
        import time

        oauth_auth._access_token = "existing_token"
        oauth_auth._token_expires_at = time.time() + 3600

        token = oauth_auth._get_oauth_token()

        assert token == "existing_token"

    def test_sign_request_oauth_adds_bearer_token(self, oauth_auth):
        """Test that OAuth sign_request adds Bearer token."""
        with patch.object(oauth_auth, "_get_oauth_token", return_value="oauth_token"):
            headers = {}
            signed = oauth_auth.sign_request(
                "GET",
                "https://landscape.example.com/api/v2/computers",
                headers,
            )

            assert "Authorization" in signed
            assert signed["Authorization"] == "Bearer oauth_token"
