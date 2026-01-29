# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for SCCM authentication."""
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from apps.connectors.sccm.auth import SCCMAuth, SCCMAuthError


class TestSCCMAuthInit:
    """Tests for SCCMAuth initialization."""

    def test_init_missing_server_url_raises_error(self):
        """Test that missing server URL raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("apps.connectors.sccm.auth.config") as mock_config:
                mock_config.return_value = None
                with pytest.raises(SCCMAuthError) as exc_info:
                    SCCMAuth()
                assert "SCCM_SERVER_URL" in str(exc_info.value)

    def test_init_basic_auth_missing_credentials(self):
        """Test basic auth without credentials raises error."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "basic",
                    "SCCM_USERNAME": None,
                    "SCCM_PASSWORD": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(SCCMAuthError) as exc_info:
                SCCMAuth()
            assert "SCCM_USERNAME" in str(exc_info.value)

    def test_init_certificate_auth_missing_cert_path(self):
        """Test certificate auth without cert path raises error."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "certificate",
                    "SCCM_CERT_PATH": None,
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(SCCMAuthError) as exc_info:
                SCCMAuth()
            assert "SCCM_CERT_PATH" in str(exc_info.value)

    def test_init_invalid_auth_method(self):
        """Test invalid auth method raises error."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "invalid_method",
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            with pytest.raises(SCCMAuthError) as exc_info:
                SCCMAuth()
            assert "invalid_method" in str(exc_info.value)

    def test_init_success_basic_auth(self):
        """Test successful initialization with basic auth."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService/",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "basic",
                    "SCCM_USERNAME": "svc_sccm",
                    "SCCM_PASSWORD": "test_password",  # pragma: allowlist secret
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = SCCMAuth()
            assert auth.server_url == "https://sccm.example.com/AdminService"
            assert auth.site_code == "PS1"
            assert auth.auth_method == "basic"
            assert auth.username == "svc_sccm"

    def test_init_normalizes_server_url(self):
        """Test that trailing slash is removed from server URL."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService///",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "wia",
                }
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            auth = SCCMAuth()
            assert not auth.server_url.endswith("/")


class TestSCCMAuthSession:
    """Tests for SCCMAuth session management."""

    @pytest.fixture
    def auth(self):
        """Create SCCMAuth instance with mocked config."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "basic",
                    "SCCM_USERNAME": "svc_sccm",
                    "SCCM_PASSWORD": "test_password",  # pragma: allowlist secret
                    "SCCM_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return SCCMAuth()

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


class TestSCCMAuthConnection:
    """Tests for SCCM connection testing."""

    @pytest.fixture
    def auth(self):
        """Create SCCMAuth instance with mocked config."""
        with patch("apps.connectors.sccm.auth.config") as mock_config:

            def config_side_effect(key, default=None, cast=None):
                values = {
                    "SCCM_SERVER_URL": "https://sccm.example.com/AdminService",
                    "SCCM_SITE_CODE": "PS1",
                    "SCCM_AUTH_METHOD": "basic",
                    "SCCM_USERNAME": "svc_sccm",
                    "SCCM_PASSWORD": "test_password",  # pragma: allowlist secret
                    "SCCM_VERIFY_SSL": True,
                }
                if cast:
                    return cast(values.get(key, default))
                return values.get(key, default)

            mock_config.side_effect = config_side_effect
            return SCCMAuth()

    def test_test_connection_success(self, auth):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {
                    "SiteCode": "PS1",
                    "SiteName": "Primary Site",
                    "Version": "5.2207.1048.1000",
                }
            ]
        }
        mock_response.raise_for_status = Mock()

        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is True
            assert "PS1" in message

    def test_test_connection_no_sites(self, auth):
        """Test connection test with no sites found."""
        mock_response = Mock()
        mock_response.json.return_value = {"value": []}
        mock_response.raise_for_status = Mock()

        with patch.object(auth, "get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_get_session.return_value = mock_session

            success, message = auth.test_connection()

            assert success is False
            assert "no sites found" in message.lower()

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
