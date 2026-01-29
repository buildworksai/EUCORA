# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Jamf Pro authentication.
Tests OAuth 2.0 and Basic authentication methods, token caching, and validation.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase

from apps.connectors.jamf.auth import JamfAuth, JamfAuthError


class TestJamfAuthConfiguration(TestCase):
    """Test configuration validation."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.config")
    def test_missing_server_url_raises_error(self, mock_config):
        """Should raise error if JAMF_SERVER_URL is missing."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": None,
        }.get(key, default)

        with self.assertRaises(JamfAuthError) as context:
            JamfAuth()

        self.assertIn("JAMF_SERVER_URL is required", str(context.exception))

    @patch("apps.connectors.jamf.auth.config")
    def test_missing_credentials_raises_error(self, mock_config):
        """Should raise error if neither OAuth nor Basic auth configured."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": None,
            "JAMF_CLIENT_SECRET": None,
            "JAMF_USERNAME": None,
            "JAMF_PASSWORD": None,
        }.get(key, default)

        with self.assertRaises(JamfAuthError) as context:
            JamfAuth()

        self.assertIn("Either JAMF_CLIENT_ID + JAMF_CLIENT_SECRET", str(context.exception))

    @patch("apps.connectors.jamf.auth.config")
    def test_oauth_configuration(self, mock_config):
        """Should initialize with OAuth configuration."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        auth = JamfAuth()

        self.assertEqual(auth.auth_method, "oauth")
        self.assertEqual(auth.server_url, "https://test.jamfcloud.com")
        self.assertEqual(auth.client_id, "test_client_id")
        self.assertEqual(auth.client_secret, "test_client_secret")

    @patch("apps.connectors.jamf.auth.config")
    def test_basic_auth_configuration(self, mock_config):
        """Should initialize with Basic auth configuration."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_USERNAME": "test_user",
            "JAMF_PASSWORD": "test_password",
        }.get(key, default)

        auth = JamfAuth()

        self.assertEqual(auth.auth_method, "basic")
        self.assertEqual(auth.username, "test_user")
        self.assertEqual(auth.password, "test_password")

    @patch("apps.connectors.jamf.auth.config")
    def test_server_url_trailing_slash_removed(self, mock_config):
        """Should remove trailing slash from server URL."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com/",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        auth = JamfAuth()

        self.assertEqual(auth.server_url, "https://test.jamfcloud.com")


class TestJamfOAuthTokenAcquisition(TestCase):
    """Test OAuth 2.0 token acquisition."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_successful_oauth_token_acquisition(self, mock_config, mock_http_client_class):
        """Should successfully acquire OAuth 2.0 token."""
        # Mock configuration
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        # Mock HTTP response
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_oauth_token_12345",
            "expires_in": 1800,
            "token_type": "Bearer",
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        # Test token acquisition
        auth = JamfAuth()
        token = auth.get_access_token(correlation_id="TEST-123")

        self.assertEqual(token, "test_oauth_token_12345")
        self.assertTrue(mock_http_client.post.called)

        # Verify request payload
        call_kwargs = mock_http_client.post.call_args[1]
        self.assertIn("data", call_kwargs)
        self.assertEqual(call_kwargs["data"]["grant_type"], "client_credentials")
        self.assertEqual(call_kwargs["data"]["client_id"], "test_client_id")
        self.assertEqual(call_kwargs["data"]["client_secret"], "test_client_secret")

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_oauth_token_caching(self, mock_config, mock_http_client_class):
        """Should cache OAuth token and reuse it."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "cached_token_12345",
            "expires_in": 1800,
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()

        # First call - should acquire token
        token1 = auth.get_access_token()
        self.assertEqual(token1, "cached_token_12345")
        self.assertEqual(mock_http_client.post.call_count, 1)

        # Second call - should use cached token
        token2 = auth.get_access_token()
        self.assertEqual(token2, "cached_token_12345")
        self.assertEqual(mock_http_client.post.call_count, 1)  # No additional call

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_oauth_force_refresh_bypasses_cache(self, mock_config, mock_http_client_class):
        """Should bypass cache when force_refresh=True."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token_12345",
            "expires_in": 1800,
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()

        # First call
        token1 = auth.get_access_token()
        self.assertEqual(mock_http_client.post.call_count, 1)

        # Force refresh
        token2 = auth.get_access_token(force_refresh=True)
        self.assertEqual(mock_http_client.post.call_count, 2)

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_oauth_invalid_token_response(self, mock_config, mock_http_client_class):
        """Should raise error if token response is invalid."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()

        with self.assertRaises(JamfAuthError) as context:
            auth.get_access_token()

        self.assertIn("missing 'access_token'", str(context.exception))


class TestJamfBasicAuthTokenAcquisition(TestCase):
    """Test Basic authentication token acquisition."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_successful_basic_token_acquisition(self, mock_config, mock_http_client_class):
        """Should successfully acquire Basic auth token."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_USERNAME": "test_user",
            "JAMF_PASSWORD": "test_password",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "basic_auth_token_12345",
            "expires": 1800,
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()
        token = auth.get_access_token(correlation_id="BASIC-123")

        self.assertEqual(token, "basic_auth_token_12345")
        self.assertTrue(mock_http_client.post.called)

        # Verify Authorization header has Basic auth
        call_kwargs = mock_http_client.post.call_args[1]
        self.assertIn("headers", call_kwargs)
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertTrue(call_kwargs["headers"]["Authorization"].startswith("Basic "))

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_basic_token_caching(self, mock_config, mock_http_client_class):
        """Should cache Basic auth token."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_USERNAME": "test_user",
            "JAMF_PASSWORD": "test_password",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "cached_basic_token",
            "expires": 1800,
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()

        # First call
        token1 = auth.get_access_token()
        self.assertEqual(mock_http_client.post.call_count, 1)

        # Second call - should use cache
        token2 = auth.get_access_token()
        self.assertEqual(token2, token1)
        self.assertEqual(mock_http_client.post.call_count, 1)


class TestJamfTokenCaching(TestCase):
    """Test token caching behavior."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_cache_key_includes_server_and_identifier(self, mock_config, mock_http_client_class):
        """Cache key should include server URL and client_id/username."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client_class.return_value = Mock()

        auth = JamfAuth()
        cache_key = auth._get_cache_key()

        self.assertIn("https://test.jamfcloud.com", cache_key)
        self.assertIn("test_client_id", cache_key)

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_clear_cached_token(self, mock_config, mock_http_client_class):
        """Should clear cached token."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_to_clear",
            "expires_in": 1800,
        }
        mock_http_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()

        # Acquire and cache token
        token1 = auth.get_access_token()
        self.assertEqual(mock_http_client.post.call_count, 1)

        # Clear cache
        auth.clear_cached_token()

        # Next call should acquire new token
        token2 = auth.get_access_token()
        self.assertEqual(mock_http_client.post.call_count, 2)


class TestJamfTokenValidation(TestCase):
    """Test token validation."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

    def tearDown(self):
        """Cleanup after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_validate_valid_token(self, mock_config, mock_http_client_class):
        """Should return True for valid token."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()
        is_valid = auth.validate_token("valid_token", correlation_id="VALIDATE-123")

        self.assertTrue(is_valid)

    @patch("apps.connectors.jamf.auth.ResilientHTTPClient")
    @patch("apps.connectors.jamf.auth.config")
    def test_validate_invalid_token(self, mock_config, mock_http_client_class):
        """Should return False for invalid token."""
        mock_config.side_effect = lambda key, default=None: {
            "JAMF_SERVER_URL": "https://test.jamfcloud.com",
            "JAMF_CLIENT_ID": "test_client_id",
            "JAMF_CLIENT_SECRET": "test_client_secret",
        }.get(key, default)

        mock_http_client = Mock()
        mock_http_client.get.side_effect = Exception("Unauthorized")
        mock_http_client_class.return_value = mock_http_client

        auth = JamfAuth()
        is_valid = auth.validate_token("invalid_token", correlation_id="VALIDATE-456")

        self.assertFalse(is_valid)
