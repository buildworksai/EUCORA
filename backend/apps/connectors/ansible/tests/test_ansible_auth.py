# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Ansible/AWX authentication."""
from unittest.mock import Mock, patch

import pytest
import requests

from apps.connectors.ansible.auth import AnsibleAuth, AnsibleAuthError


class TestAnsibleAuthInit:
    """Tests for AnsibleAuth initialization."""

    def test_init_missing_server_url_raises_error(self):
        """Test that missing server URL raises error."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:
            mock_config.return_value = None
            with pytest.raises(AnsibleAuthError) as exc_info:
                AnsibleAuth()
            assert "AWX_SERVER_URL" in str(exc_info.value)

    def test_init_token_auth_missing_token(self):
        """Test token auth without token raises error."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "token",
                    "AWX_TOKEN": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(AnsibleAuthError) as exc_info:
                AnsibleAuth()
            assert "AWX_TOKEN" in str(exc_info.value)

    def test_init_basic_auth_missing_credentials(self):
        """Test basic auth without credentials raises error."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "basic",
                    "AWX_USERNAME": None,
                    "AWX_PASSWORD": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(AnsibleAuthError) as exc_info:
                AnsibleAuth()
            assert "AWX_USERNAME" in str(exc_info.value)

    def test_init_oauth_missing_client_credentials(self):
        """Test OAuth auth without client credentials raises error."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "oauth",
                    "AWX_CLIENT_ID": None,
                    "AWX_CLIENT_SECRET": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(AnsibleAuthError) as exc_info:
                AnsibleAuth()
            assert "AWX_CLIENT_ID" in str(exc_info.value)

    def test_init_invalid_auth_method(self):
        """Test invalid auth method raises error."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "invalid_method",
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(AnsibleAuthError) as exc_info:
                AnsibleAuth()
            assert "invalid_method" in str(exc_info.value)

    def test_init_success_token_auth(self):
        """Test successful initialization with token auth."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com/",
                    "AWX_AUTH_METHOD": "token",
                    "AWX_TOKEN": "test_token_123",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = AnsibleAuth()
            assert auth.server_url == "https://awx.example.com"
            assert auth.auth_method == "token"
            assert auth.token == "test_token_123"

    def test_init_normalizes_server_url(self):
        """Test that trailing slashes are removed from server URL."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com///",
                    "AWX_AUTH_METHOD": "token",
                    "AWX_TOKEN": "test_token",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = AnsibleAuth()
            assert not auth.server_url.endswith("/")


class TestAnsibleAuthSession:
    """Tests for session management."""

    @pytest.fixture
    def token_auth(self):
        """Create AnsibleAuth instance with token auth."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "token",
                    "AWX_TOKEN": "test_token",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return AnsibleAuth()

    def test_get_session_creates_session(self, token_auth):
        """Test that get_session creates a new session."""
        session = token_auth.get_session()
        assert session is not None
        assert isinstance(session, requests.Session)

    def test_get_session_sets_token_header(self, token_auth):
        """Test that token auth sets Authorization header."""
        session = token_auth.get_session()
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer test_token"

    def test_get_session_reuses_session(self, token_auth):
        """Test that get_session reuses existing session."""
        session1 = token_auth.get_session()
        session2 = token_auth.get_session()
        assert session1 is session2

    def test_clear_session(self, token_auth):
        """Test that clear_session removes session."""
        session1 = token_auth.get_session()
        token_auth.clear_session()
        session2 = token_auth.get_session()
        assert session1 is not session2


class TestAnsibleAuthBasic:
    """Tests for basic authentication."""

    @pytest.fixture
    def basic_auth(self):
        """Create AnsibleAuth instance with basic auth."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "basic",
                    "AWX_USERNAME": "admin",
                    "AWX_PASSWORD": "password123",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return AnsibleAuth()

    def test_get_session_sets_basic_auth(self, basic_auth):
        """Test that basic auth sets session auth."""
        session = basic_auth.get_session()
        assert session.auth == ("admin", "password123")


class TestAnsibleAuthOAuth:
    """Tests for OAuth authentication."""

    @pytest.fixture
    def oauth_auth(self):
        """Create AnsibleAuth instance with OAuth."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "oauth",
                    "AWX_CLIENT_ID": "test_client_id",
                    "AWX_CLIENT_SECRET": "test_client_secret",
                    "AWX_USERNAME": "admin",
                    "AWX_PASSWORD": "password123",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return AnsibleAuth()

    def test_get_oauth_token_success(self, oauth_auth):
        """Test successful OAuth token acquisition."""
        with patch("apps.connectors.ansible.auth.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "oauth_token_123",
                "refresh_token": "refresh_token_456",
                "expires_in": 3600,
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            token = oauth_auth._get_oauth_token()

            assert token == "oauth_token_123"
            assert oauth_auth._access_token == "oauth_token_123"
            assert oauth_auth._refresh_token == "refresh_token_456"

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
                "https://awx.example.com/api/v2/ping/",
                headers,
            )

            assert "Authorization" in signed
            assert signed["Authorization"] == "Bearer oauth_token"


class TestAnsibleAuthConnection:
    """Tests for connection testing."""

    @pytest.fixture
    def auth(self):
        """Create AnsibleAuth instance."""
        with patch("apps.connectors.ansible.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "AWX_SERVER_URL": "https://awx.example.com",
                    "AWX_AUTH_METHOD": "token",
                    "AWX_TOKEN": "test_token",
                    "AWX_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return AnsibleAuth()

    def test_test_connection_success(self, auth):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "version": "21.0.0",
            "active_node": "awx-node-1",
        }
        mock_response.raise_for_status = Mock()

        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is True
            assert "21.0.0" in message

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
