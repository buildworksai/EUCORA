# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Intune authentication.
Tests OAuth 2.0 flow, token caching, and error handling.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase

from apps.connectors.intune.auth import IntuneAuth, IntuneAuthError


class TestIntuneAuthConfiguration(TestCase):
    """Test Intune authentication configuration."""

    @patch("apps.connectors.intune.auth.config")
    def test_missing_configuration_raises_error(self, mock_config):
        """Missing required configuration should raise IntuneAuthError."""
        mock_config.side_effect = lambda key, default=None: None

        with self.assertRaises(IntuneAuthError) as context:
            IntuneAuth()

        self.assertIn("configuration incomplete", str(context.exception).lower())

    @patch("apps.connectors.intune.auth.config")
    def test_valid_configuration(self, mock_config):
        """Valid configuration should initialize successfully."""
        mock_config.side_effect = lambda key, default=None: {
            "INTUNE_TENANT_ID": "tenant-123",
            "INTUNE_CLIENT_ID": "client-456",
            "INTUNE_CLIENT_SECRET": "secret-789",
        }.get(key, default)

        auth = IntuneAuth()

        self.assertEqual(auth.tenant_id, "tenant-123")
        self.assertEqual(auth.client_id, "client-456")
        self.assertEqual(auth.client_secret, "secret-789")


class TestIntuneTokenAcquisition(TestCase):
    """Test OAuth 2.0 token acquisition."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

        # Mock configuration
        self.config_patcher = patch("apps.connectors.intune.auth.config")
        mock_config = self.config_patcher.start()
        mock_config.side_effect = lambda key, default=None: {
            "INTUNE_TENANT_ID": "tenant-123",
            "INTUNE_CLIENT_ID": "client-456",
            "INTUNE_CLIENT_SECRET": "secret-789",
        }.get(key, default)

    def tearDown(self):
        """Cleanup after each test."""
        self.config_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_successful_token_acquisition(self, mock_http_client_class):
        """Successful token acquisition should return access token."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()
        token = auth.get_access_token(correlation_id="TEST-123")

        self.assertEqual(token, "token_abc123")
        self.assertTrue(mock_client.post.called)

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_token_caching(self, mock_http_client_class):
        """Acquired tokens should be cached."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()

        # First call - should acquire token
        token1 = auth.get_access_token()

        # Second call - should use cache
        token2 = auth.get_access_token()

        self.assertEqual(token1, token2)
        # HTTP client should only be called once
        self.assertEqual(mock_client.post.call_count, 1)

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_force_refresh_bypasses_cache(self, mock_http_client_class):
        """Force refresh should bypass cache."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_new",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()

        # First call
        auth.get_access_token()

        # Force refresh
        auth.get_access_token(force_refresh=True)

        # HTTP client should be called twice
        self.assertEqual(mock_client.post.call_count, 2)

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_invalid_token_response(self, mock_http_client_class):
        """Invalid token response should raise IntuneAuthError."""
        # Mock HTTP response without access_token
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials",
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()

        with self.assertRaises(IntuneAuthError) as context:
            auth.get_access_token()

        self.assertIn("missing access_token", str(context.exception).lower())


class TestIntuneTokenCaching(TestCase):
    """Test token caching behavior."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

        # Mock configuration
        self.config_patcher = patch("apps.connectors.intune.auth.config")
        mock_config = self.config_patcher.start()
        mock_config.side_effect = lambda key, default=None: {
            "INTUNE_TENANT_ID": "tenant-123",
            "INTUNE_CLIENT_ID": "client-456",
            "INTUNE_CLIENT_SECRET": "secret-789",
        }.get(key, default)

    def tearDown(self):
        """Cleanup after each test."""
        self.config_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_cache_key_includes_tenant_id(self, mock_http_client_class):
        """Cache key should include tenant ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "expires_in": 3600,
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()
        auth.get_access_token()

        # Check cache key
        cache_key = f"intune_access_token:{auth.tenant_id}"
        cached_data = cache.get(cache_key)

        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["access_token"], "token_abc123")

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_clear_cached_token(self, mock_http_client_class):
        """clear_cached_token should remove token from cache."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token_abc123",
            "expires_in": 3600,
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()
        auth.get_access_token()

        # Clear cache
        auth.clear_cached_token()

        # Cache should be empty
        cache_key = f"intune_access_token:{auth.tenant_id}"
        cached_data = cache.get(cache_key)
        self.assertIsNone(cached_data)


class TestIntuneTokenValidation(TestCase):
    """Test token validation."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()

        # Mock configuration
        self.config_patcher = patch("apps.connectors.intune.auth.config")
        mock_config = self.config_patcher.start()
        mock_config.side_effect = lambda key, default=None: {
            "INTUNE_TENANT_ID": "tenant-123",
            "INTUNE_CLIENT_ID": "client-456",
            "INTUNE_CLIENT_SECRET": "secret-789",
        }.get(key, default)

    def tearDown(self):
        """Cleanup after each test."""
        self.config_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_validate_valid_token(self, mock_http_client_class):
        """Valid token should pass validation."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()
        is_valid = auth.validate_token("token_abc123")

        self.assertTrue(is_valid)

    @patch("apps.connectors.intune.auth.ResilientHTTPClient")
    def test_validate_invalid_token(self, mock_http_client_class):
        """Invalid token should fail validation."""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Unauthorized")
        mock_http_client_class.return_value = mock_client

        auth = IntuneAuth()
        is_valid = auth.validate_token("invalid_token")

        self.assertFalse(is_valid)
