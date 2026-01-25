# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Jamf Pro connector client.
Tests device management, package deployment, and policy operations.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase

from apps.connectors.jamf.client import JamfConnector, JamfConnectorError
from apps.core.circuit_breaker import CircuitBreakerOpen
from apps.core.resilient_http import ResilientAPIError


class TestJamfConnectorConfiguration(TestCase):
    """Test connector initialization and configuration."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    @patch("apps.connectors.jamf.client.JamfAuth")
    def test_connector_initialization(self, mock_auth_class):
        """Connector should initialize with auth and API client."""
        mock_auth = Mock()
        mock_auth.server_url = "https://test.jamfcloud.com"
        mock_auth_class.return_value = mock_auth

        connector = JamfConnector()

        self.assertIsNotNone(connector.auth)
        self.assertIsNotNone(connector.client)
        self.assertEqual(connector.client.base_url, "https://test.jamfcloud.com")


class TestJamfComputerManagement(TestCase):
    """Test computer (macOS device) management operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = JamfConnector()

        # Mock auth to return valid token
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_success(self, mock_api_client_class):
        """Should successfully list computers."""
        mock_client = Mock()
        mock_client.get.return_value = {
            "totalCount": 2,
            "results": [
                {
                    "id": "comp-1",
                    "general": {"name": "MacBook-001", "platform": "Mac"},
                    "hardware": {"model": "MacBook Pro"},
                },
                {
                    "id": "comp-2",
                    "general": {"name": "MacBook-002", "platform": "Mac"},
                    "hardware": {"model": "MacBook Air"},
                },
            ],
        }
        self.connector.client = mock_client

        result = self.connector.list_computers(page=0, page_size=100, correlation_id="TEST-123")

        self.assertEqual(result["totalCount"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["general"]["name"], "MacBook-001")

        # Verify API call
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["page"], "0")
        self.assertEqual(call_kwargs["params"]["page-size"], "100")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_with_filter(self, mock_api_client_class):
        """Should apply RSQL filter when listing computers."""
        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 1, "results": [{"id": "comp-1"}]}
        self.connector.client = mock_client

        filter_query = 'general.platform=="Mac"'
        result = self.connector.list_computers(
            page=0, page_size=50, filter_query=filter_query, correlation_id="TEST-456"
        )

        # Verify filter parameter
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["filter"], filter_query)
        self.assertEqual(call_kwargs["params"]["page-size"], "50")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_with_sort(self, mock_api_client_class):
        """Should apply sort parameter when listing computers."""
        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}
        self.connector.client = mock_client

        sort_expr = "general.name:asc"
        self.connector.list_computers(sort=sort_expr, correlation_id="TEST-SORT")

        # Verify sort parameter
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["sort"], sort_expr)

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_page_size_limit(self, mock_api_client_class):
        """Should enforce maximum page size of 2000."""
        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}
        self.connector.client = mock_client

        self.connector.list_computers(page_size=5000, correlation_id="TEST-LIMIT")

        # Verify page-size is clamped to 2000
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["page-size"], "2000")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_circuit_breaker_open(self, mock_api_client_class):
        """Should propagate CircuitBreakerOpen exception."""
        mock_client = Mock()
        mock_client.get.side_effect = CircuitBreakerOpen()
        self.connector.client = mock_client

        with self.assertRaises(CircuitBreakerOpen):
            self.connector.list_computers(correlation_id="TEST-CB")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_list_computers_api_error(self, mock_api_client_class):
        """Should raise JamfConnectorError on API failure."""
        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="jamf", message="API error", status_code=500, correlation_id="TEST-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(JamfConnectorError) as context:
            self.connector.list_computers(correlation_id="TEST-ERROR")

        self.assertIn("Failed to list computers", str(context.exception))
        self.assertEqual(context.exception.status_code, 500)

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_computer_by_id_success(self, mock_api_client_class):
        """Should retrieve computer details by ID."""
        mock_client = Mock()
        mock_client.get.return_value = {
            "id": "comp-123",
            "general": {"name": "MacBook-Test", "platform": "Mac"},
            "hardware": {"model": "MacBook Pro", "serialNumber": "ABC123"},
            "applications": [
                {"name": "Safari", "version": "16.0"},
                {"name": "Chrome", "version": "110.0"},
            ],
        }
        self.connector.client = mock_client

        computer = self.connector.get_computer_by_id("comp-123", correlation_id="GET-COMP")

        self.assertEqual(computer["id"], "comp-123")
        self.assertEqual(computer["general"]["name"], "MacBook-Test")
        self.assertEqual(len(computer["applications"]), 2)

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_computer_by_id_not_found(self, mock_api_client_class):
        """Should raise JamfConnectorError if computer not found."""
        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="jamf", message="Not found", status_code=404, correlation_id="NOT-FOUND"
        )
        self.connector.client = mock_client

        with self.assertRaises(JamfConnectorError) as context:
            self.connector.get_computer_by_id("nonexistent", correlation_id="NOT-FOUND")

        self.assertEqual(context.exception.status_code, 404)


class TestJamfPackageManagement(TestCase):
    """Test package deployment operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = JamfConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_create_package_success(self, mock_api_client_class):
        """Should successfully create package."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "id": "pkg-123",
            "packageName": "TestApp",
            "fileName": "TestApp-1.0.pkg",
        }
        self.connector.client = mock_client

        package = self.connector.create_package(
            package_name="TestApp",
            file_name="TestApp-1.0.pkg",
            category="Productivity",
            info="Test application for macOS",
            notes="Version 1.0",
            priority=10,
            correlation_id="PKG-CREATE",
        )

        self.assertEqual(package["id"], "pkg-123")
        self.assertEqual(package["packageName"], "TestApp")

        # Verify payload
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json_data"]
        self.assertEqual(payload["packageName"], "TestApp")
        self.assertEqual(payload["fileName"], "TestApp-1.0.pkg")
        self.assertEqual(payload["priority"], 10)
        self.assertFalse(payload["rebootRequired"])

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_create_package_idempotent_conflict(self, mock_api_client_class):
        """Should handle 409 conflict by finding existing package."""
        mock_client = Mock()

        # First call raises 409 conflict
        conflict_error = ResilientAPIError(
            service_name="jamf", message="Conflict", status_code=409, correlation_id="PKG-CONFLICT"
        )
        mock_client.post.side_effect = conflict_error

        # Mock finding existing package
        mock_client.get.return_value = {
            "results": [
                {
                    "id": "existing-pkg-456",
                    "packageName": "ExistingApp",
                    "fileName": "ExistingApp-1.0.pkg",
                }
            ]
        }
        self.connector.client = mock_client

        package = self.connector.create_package(
            package_name="ExistingApp", file_name="ExistingApp-1.0.pkg", correlation_id="PKG-CONFLICT"
        )

        # Should return existing package
        self.assertEqual(package["id"], "existing-pkg-456")
        self.assertEqual(package["packageName"], "ExistingApp")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_create_package_validation_error(self, mock_api_client_class):
        """Should raise JamfConnectorError on validation failure."""
        mock_client = Mock()
        mock_client.post.side_effect = ResilientAPIError(
            service_name="jamf", message="Invalid package data", status_code=400, correlation_id="PKG-INVALID"
        )
        self.connector.client = mock_client

        with self.assertRaises(JamfConnectorError) as context:
            self.connector.create_package(
                package_name="InvalidApp", file_name="", correlation_id="PKG-INVALID"  # Invalid empty filename
            )

        self.assertIn("Failed to create package", str(context.exception))
        self.assertEqual(context.exception.status_code, 400)


class TestJamfPolicyManagement(TestCase):
    """Test policy-based deployment operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = JamfConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_create_policy_success(self, mock_api_client_class):
        """Should successfully create policy."""
        mock_client = Mock()
        mock_client.post.return_value = "<policy><id>123</id><name>TestPolicy</name></policy>"
        self.connector.client = mock_client

        scope = {"computerGroups": ["Engineering"]}

        policy = self.connector.create_policy(
            policy_name="TestPolicy",
            package_id="pkg-123",
            scope=scope,
            enabled=True,
            frequency="Once per computer",
            category="Deployment",
            trigger_checkin=True,
            correlation_id="POLICY-CREATE",
        )

        self.assertEqual(policy["id"], "123")
        self.assertEqual(policy["name"], "TestPolicy")

        # Verify XML payload sent
        call_kwargs = mock_client.post.call_args[1]
        self.assertIn("data", call_kwargs)
        xml_data = call_kwargs["data"]
        self.assertIn("TestPolicy", xml_data)
        self.assertIn("pkg-123", xml_data)
        self.assertIn("Once per computer", xml_data)

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_create_policy_error(self, mock_api_client_class):
        """Should raise JamfConnectorError on policy creation failure."""
        mock_client = Mock()
        mock_client.post.side_effect = ResilientAPIError(
            service_name="jamf", message="Invalid policy data", status_code=400, correlation_id="POLICY-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(JamfConnectorError) as context:
            self.connector.create_policy(
                policy_name="InvalidPolicy", package_id="invalid-pkg", scope={}, correlation_id="POLICY-ERROR"
            )

        self.assertIn("Failed to create policy", str(context.exception))

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_policy_logs_success(self, mock_api_client_class):
        """Should retrieve policy execution logs."""
        mock_client = Mock()
        mock_client.get.return_value = {
            "totalCount": 3,
            "results": [
                {
                    "id": "log-1",
                    "computerName": "MacBook-001",
                    "status": "Completed",
                    "timestamp": "2026-01-23T10:00:00Z",
                },
                {
                    "id": "log-2",
                    "computerName": "MacBook-002",
                    "status": "Failed",
                    "timestamp": "2026-01-23T10:05:00Z",
                },
            ],
        }
        self.connector.client = mock_client

        logs = self.connector.get_policy_logs(policy_id="policy-123", page=0, page_size=100, correlation_id="LOGS-123")

        self.assertEqual(logs["totalCount"], 3)
        self.assertEqual(len(logs["results"]), 2)
        self.assertEqual(logs["results"][0]["status"], "Completed")
        self.assertEqual(logs["results"][1]["status"], "Failed")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_policy_logs_pagination(self, mock_api_client_class):
        """Should respect pagination parameters."""
        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}
        self.connector.client = mock_client

        self.connector.get_policy_logs(policy_id="policy-456", page=2, page_size=50, correlation_id="LOGS-PAGE")

        # Verify pagination params
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["page"], "2")
        self.assertEqual(call_kwargs["params"]["page-size"], "50")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_policy_logs_max_limit(self, mock_api_client_class):
        """Should enforce maximum page size of 2000."""
        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}
        self.connector.client = mock_client

        self.connector.get_policy_logs(policy_id="policy-789", page_size=5000, correlation_id="LOGS-LIMIT")

        # Verify limit is clamped to 2000
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["page-size"], "2000")


class TestJamfApplicationTracking(TestCase):
    """Test application installation tracking."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = JamfConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_computer_applications_success(self, mock_api_client_class):
        """Should retrieve installed applications for computer."""
        mock_client = Mock()
        mock_client.get.return_value = {
            "id": "comp-123",
            "applications": [
                {"name": "Safari", "version": "16.0", "bundleId": "com.apple.Safari"},
                {"name": "Chrome", "version": "110.0", "bundleId": "com.google.Chrome"},
                {"name": "TestApp", "version": "1.0", "bundleId": "com.test.TestApp"},
            ],
        }
        self.connector.client = mock_client

        applications = self.connector.get_computer_applications(computer_id="comp-123", correlation_id="APPS-123")

        self.assertEqual(len(applications), 3)
        self.assertEqual(applications[0]["name"], "Safari")
        self.assertEqual(applications[2]["name"], "TestApp")

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_computer_applications_empty(self, mock_api_client_class):
        """Should handle computer with no applications."""
        mock_client = Mock()
        mock_client.get.return_value = {"id": "comp-456", "applications": []}
        self.connector.client = mock_client

        applications = self.connector.get_computer_applications(computer_id="comp-456", correlation_id="APPS-EMPTY")

        self.assertEqual(len(applications), 0)

    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_get_computer_applications_error(self, mock_api_client_class):
        """Should raise JamfConnectorError on failure."""
        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="jamf", message="Computer not found", status_code=404, correlation_id="APPS-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(JamfConnectorError) as context:
            self.connector.get_computer_applications(computer_id="nonexistent", correlation_id="APPS-ERROR")

        self.assertIn("Failed to get computer", str(context.exception))


class TestJamfStructuredLogging(TestCase):
    """Test structured logging integration."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = JamfConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.jamf.client.StructuredLogger")
    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_connector_events_logged(self, mock_api_client_class, mock_logger_class):
        """Should log connector events for operations."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.get.return_value = {"totalCount": 0, "results": []}

        connector = JamfConnector()
        connector.client = mock_client

        connector.list_computers(correlation_id="LOG-TEST")

        # Verify connector events logged
        self.assertTrue(mock_logger.connector_event.called)

        # Check for STARTED and SUCCESS events
        calls = mock_logger.connector_event.call_args_list
        self.assertTrue(any("STARTED" in str(call) for call in calls))
        self.assertTrue(any("SUCCESS" in str(call) for call in calls))

    @patch("apps.connectors.jamf.client.StructuredLogger")
    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_audit_events_logged_for_package_creation(self, mock_api_client_class, mock_logger_class):
        """Should log audit events for package creation."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.post.return_value = {"id": "pkg-123", "packageName": "TestApp"}

        connector = JamfConnector()
        connector.client = mock_client

        connector.create_package(package_name="TestApp", file_name="TestApp.pkg", correlation_id="AUDIT-TEST")

        # Verify audit event logged
        self.assertTrue(mock_logger.audit_event.called)

        call_kwargs = mock_logger.audit_event.call_args[1]
        self.assertEqual(call_kwargs["action"], "JAMF_PACKAGE_CREATED")
        self.assertEqual(call_kwargs["resource_id"], "pkg-123")
        self.assertEqual(call_kwargs["outcome"], "SUCCESS")

    @patch("apps.connectors.jamf.client.StructuredLogger")
    @patch("apps.connectors.jamf.client.ResilientAPIClient")
    def test_failure_events_logged(self, mock_api_client_class, mock_logger_class):
        """Should log FAILURE connector events on errors."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="jamf", message="API error", status_code=500, correlation_id="FAILURE-TEST"
        )

        connector = JamfConnector()
        connector.client = mock_client

        try:
            connector.list_computers(correlation_id="FAILURE-TEST")
        except JamfConnectorError:
            pass

        # Verify FAILURE event logged
        calls = mock_logger.connector_event.call_args_list
        self.assertTrue(any("FAILURE" in str(call) for call in calls))
