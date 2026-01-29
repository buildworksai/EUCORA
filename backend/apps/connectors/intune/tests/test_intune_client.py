# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for Intune connector client.
Tests device management, app deployment, and assignment operations.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.cache import cache
from django.test import TestCase

from apps.connectors.intune.client import IntuneConnector, IntuneConnectorError
from apps.core.circuit_breaker import CircuitBreakerOpen
from apps.core.resilient_http import ResilientAPIError


class TestIntuneConnectorConfiguration(TestCase):
    """Test connector initialization and configuration."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    @patch("apps.connectors.intune.client.IntuneAuth")
    def test_connector_initialization(self, mock_auth_class):
        """Connector should initialize with auth and API client."""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        connector = IntuneConnector()

        self.assertIsNotNone(connector.auth)
        self.assertIsNotNone(connector.client)
        self.assertEqual(connector.client.base_url, "https://graph.microsoft.com/v1.0")


class TestIntuneDeviceManagement(TestCase):
    """Test device management operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = IntuneConnector()

        # Mock auth to return valid token
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_list_managed_devices_success(self, mock_api_client_class):
        """Should successfully list managed devices."""
        # Mock API response
        mock_client = Mock()
        mock_client.get.return_value = {
            "value": [
                {"id": "device-1", "deviceName": "WIN-001", "operatingSystem": "Windows"},
                {"id": "device-2", "deviceName": "WIN-002", "operatingSystem": "Windows"},
            ],
            "@odata.nextLink": None,
        }
        self.connector.client = mock_client

        devices = self.connector.list_managed_devices(top=100, correlation_id="TEST-123")

        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["deviceName"], "WIN-001")
        self.assertEqual(devices[1]["deviceName"], "WIN-002")

        # Verify API call
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["$top"], "100")
        self.assertEqual(call_kwargs["correlation_id"], "TEST-123")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_list_managed_devices_with_filter(self, mock_api_client_class):
        """Should apply OData filter when listing devices."""
        mock_client = Mock()
        mock_client.get.return_value = {"value": [{"id": "device-1"}]}
        self.connector.client = mock_client

        filter_query = "operatingSystem eq 'Windows' and complianceState eq 'compliant'"
        devices = self.connector.list_managed_devices(top=50, filter_query=filter_query, correlation_id="TEST-456")

        # Verify filter parameter
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["$filter"], filter_query)
        self.assertEqual(call_kwargs["params"]["$top"], "50")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_list_managed_devices_circuit_breaker_open(self, mock_api_client_class):
        """Should propagate CircuitBreakerOpen exception."""
        mock_client = Mock()
        mock_client.get.side_effect = CircuitBreakerOpen()
        self.connector.client = mock_client

        with self.assertRaises(CircuitBreakerOpen):
            self.connector.list_managed_devices(correlation_id="TEST-789")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_list_managed_devices_api_error(self, mock_api_client_class):
        """Should raise IntuneConnectorError on API failure."""
        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="intune", message="API error", status_code=500, correlation_id="TEST-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(IntuneConnectorError) as context:
            self.connector.list_managed_devices(correlation_id="TEST-ERROR")

        self.assertIn("Failed to list managed devices", str(context.exception))

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_list_managed_devices_top_limit(self, mock_api_client_class):
        """Should enforce maximum top limit of 999."""
        mock_client = Mock()
        mock_client.get.return_value = {"value": []}
        self.connector.client = mock_client

        self.connector.list_managed_devices(top=2000, correlation_id="TEST-LIMIT")

        # Verify top is clamped to 999
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["$top"], "999")


class TestIntuneAppDeployment(TestCase):
    """Test Win32 application deployment operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = IntuneConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_create_win32_app_success(self, mock_api_client_class):
        """Should successfully create Win32 application."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "id": "app-123",
            "@odata.type": "#microsoft.graph.win32LobApp",
            "displayName": "TestApp",
            "publisher": "Test Publisher",
        }
        self.connector.client = mock_client

        detection_rules = [
            {
                "@odata.type": "#microsoft.graph.win32LobAppFileSystemDetection",
                "path": "C:\\Program Files\\TestApp",
                "fileOrFolderName": "testapp.exe",
                "check32BitOn64System": False,
                "detectionType": "exists",
            }
        ]

        app = self.connector.create_win32_app(
            display_name="TestApp",
            description="Test application",
            publisher="Test Publisher",
            file_name="testapp.intunewin",
            setup_file_path="setup.exe",
            install_command="setup.exe /silent",
            uninstall_command="setup.exe /uninstall /silent",
            detection_rules=detection_rules,
            correlation_id="APP-CREATE-123",
        )

        self.assertEqual(app["id"], "app-123")
        self.assertEqual(app["displayName"], "TestApp")

        # Verify payload structure
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json_data"]
        self.assertEqual(payload["@odata.type"], "#microsoft.graph.win32LobApp")
        self.assertEqual(payload["displayName"], "TestApp")
        self.assertEqual(payload["installCommandLine"], "setup.exe /silent")
        self.assertEqual(payload["uninstallCommandLine"], "setup.exe /uninstall /silent")
        self.assertEqual(len(payload["detectionRules"]), 1)
        self.assertIn("returnCodes", payload)

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_create_win32_app_idempotent_conflict(self, mock_api_client_class):
        """Should handle 409 conflict by finding existing app."""
        mock_client = Mock()

        # First call raises 409 conflict
        conflict_error = ResilientAPIError(
            service_name="intune", message="Conflict", status_code=409, correlation_id="APP-CONFLICT"
        )
        mock_client.post.side_effect = conflict_error

        # Mock finding existing app
        mock_client.get.return_value = {
            "value": [
                {
                    "id": "existing-app-123",
                    "displayName": "ExistingApp",
                    "publisher": "Test Publisher",
                }
            ]
        }
        self.connector.client = mock_client

        detection_rules = [{"@odata.type": "#microsoft.graph.win32LobAppFileSystemDetection"}]

        app = self.connector.create_win32_app(
            display_name="ExistingApp",
            description="Test",
            publisher="Test Publisher",
            file_name="app.intunewin",
            setup_file_path="setup.exe",
            install_command="setup.exe /s",
            uninstall_command="setup.exe /u",
            detection_rules=detection_rules,
            correlation_id="APP-CONFLICT",
        )

        # Should return existing app
        self.assertEqual(app["id"], "existing-app-123")
        self.assertEqual(app["displayName"], "ExistingApp")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_create_win32_app_validation_error(self, mock_api_client_class):
        """Should raise IntuneConnectorError on validation failure."""
        mock_client = Mock()
        mock_client.post.side_effect = ResilientAPIError(
            service_name="intune", message="Invalid detection rules", status_code=400, correlation_id="APP-INVALID"
        )
        self.connector.client = mock_client

        detection_rules = [{"invalid": "rule"}]

        with self.assertRaises(IntuneConnectorError) as context:
            self.connector.create_win32_app(
                display_name="InvalidApp",
                description="Test",
                publisher="Test",
                file_name="app.intunewin",
                setup_file_path="setup.exe",
                install_command="setup.exe /s",
                uninstall_command="setup.exe /u",
                detection_rules=detection_rules,
                correlation_id="APP-INVALID",
            )

        self.assertIn("Failed to create Win32 app", str(context.exception))


class TestIntuneAppAssignment(TestCase):
    """Test application assignment operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = IntuneConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_assign_app_to_group_required_intent(self, mock_api_client_class):
        """Should assign app with 'required' intent."""
        mock_client = Mock()
        mock_client.post.return_value = {"status": "success"}
        self.connector.client = mock_client

        result = self.connector.assign_app_to_group(
            app_id="app-123", group_id="group-456", intent="required", correlation_id="ASSIGN-123"
        )

        self.assertEqual(result["status"], "success")

        # Verify payload
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json_data"]
        self.assertEqual(len(payload["mobileAppAssignments"]), 1)
        assignment = payload["mobileAppAssignments"][0]
        self.assertEqual(assignment["intent"], "required")
        self.assertEqual(assignment["target"]["groupId"], "group-456")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_assign_app_to_group_available_intent(self, mock_api_client_class):
        """Should assign app with 'available' intent."""
        mock_client = Mock()
        mock_client.post.return_value = {"status": "success"}
        self.connector.client = mock_client

        self.connector.assign_app_to_group(
            app_id="app-789", group_id="group-012", intent="available", correlation_id="ASSIGN-456"
        )

        # Verify intent
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json_data"]
        self.assertEqual(payload["mobileAppAssignments"][0]["intent"], "available")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_assign_app_to_group_uninstall_intent(self, mock_api_client_class):
        """Should assign app with 'uninstall' intent."""
        mock_client = Mock()
        mock_client.post.return_value = {"status": "success"}
        self.connector.client = mock_client

        self.connector.assign_app_to_group(
            app_id="app-999", group_id="group-888", intent="uninstall", correlation_id="UNINSTALL-789"
        )

        # Verify uninstall intent
        call_kwargs = mock_client.post.call_args[1]
        payload = call_kwargs["json_data"]
        self.assertEqual(payload["mobileAppAssignments"][0]["intent"], "uninstall")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_assign_app_error_handling(self, mock_api_client_class):
        """Should raise IntuneConnectorError on assignment failure."""
        mock_client = Mock()
        mock_client.post.side_effect = ResilientAPIError(
            service_name="intune", message="Invalid group ID", status_code=404, correlation_id="ASSIGN-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(IntuneConnectorError) as context:
            self.connector.assign_app_to_group(
                app_id="app-123", group_id="invalid-group", intent="required", correlation_id="ASSIGN-ERROR"
            )

        self.assertIn("Failed to assign app", str(context.exception))


class TestIntuneAppStatus(TestCase):
    """Test application installation status operations."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = IntuneConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_get_app_install_status_success(self, mock_api_client_class):
        """Should retrieve app installation status."""
        mock_client = Mock()
        mock_client.get.return_value = {
            "value": [
                {
                    "id": "status-1",
                    "deviceName": "WIN-001",
                    "installState": "installed",
                    "installStateDetail": "completed",
                },
                {
                    "id": "status-2",
                    "deviceName": "WIN-002",
                    "installState": "failed",
                    "installStateDetail": "diskSpaceInsufficient",
                },
            ]
        }
        self.connector.client = mock_client

        statuses = self.connector.get_app_install_status(app_id="app-123", top=100, correlation_id="STATUS-123")

        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0]["installState"], "installed")
        self.assertEqual(statuses[1]["installState"], "failed")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_get_app_install_status_pagination(self, mock_api_client_class):
        """Should respect pagination limit."""
        mock_client = Mock()
        mock_client.get.return_value = {"value": []}
        self.connector.client = mock_client

        self.connector.get_app_install_status(app_id="app-456", top=50, correlation_id="STATUS-PAGINATE")

        # Verify top parameter
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["$top"], "50")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_get_app_install_status_max_limit(self, mock_api_client_class):
        """Should enforce maximum limit of 999."""
        mock_client = Mock()
        mock_client.get.return_value = {"value": []}
        self.connector.client = mock_client

        self.connector.get_app_install_status(app_id="app-789", top=5000, correlation_id="STATUS-LIMIT")

        # Verify limit is clamped to 999
        call_kwargs = mock_client.get.call_args[1]
        self.assertEqual(call_kwargs["params"]["$top"], "999")

    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_get_app_install_status_error(self, mock_api_client_class):
        """Should raise IntuneConnectorError on API failure."""
        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="intune", message="App not found", status_code=404, correlation_id="STATUS-ERROR"
        )
        self.connector.client = mock_client

        with self.assertRaises(IntuneConnectorError) as context:
            self.connector.get_app_install_status(app_id="nonexistent-app", correlation_id="STATUS-ERROR")

        self.assertIn("Failed to get app install status", str(context.exception))


class TestIntuneStructuredLogging(TestCase):
    """Test structured logging integration."""

    def setUp(self):
        """Setup for each test."""
        cache.clear()
        self.connector = IntuneConnector()

        # Mock auth
        self.mock_auth_patcher = patch.object(self.connector.auth, "get_access_token")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_auth.return_value = "mock_access_token"

    def tearDown(self):
        """Cleanup after each test."""
        self.mock_auth_patcher.stop()
        cache.clear()

    @patch("apps.connectors.intune.client.StructuredLogger")
    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_connector_events_logged(self, mock_api_client_class, mock_logger_class):
        """Should log connector events for operations."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.get.return_value = {"value": []}

        connector = IntuneConnector()
        connector.client = mock_client

        connector.list_managed_devices(correlation_id="LOG-TEST")

        # Verify connector events logged
        self.assertTrue(mock_logger.connector_event.called)

        # Check for STARTED and SUCCESS events
        calls = mock_logger.connector_event.call_args_list
        self.assertTrue(any("STARTED" in str(call) for call in calls))
        self.assertTrue(any("SUCCESS" in str(call) for call in calls))

    @patch("apps.connectors.intune.client.StructuredLogger")
    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_audit_events_logged_for_assignments(self, mock_api_client_class, mock_logger_class):
        """Should log audit events for app assignments."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.post.return_value = {"status": "success"}

        connector = IntuneConnector()
        connector.client = mock_client

        connector.assign_app_to_group(
            app_id="app-123", group_id="group-456", intent="required", correlation_id="AUDIT-TEST"
        )

        # Verify audit event logged
        self.assertTrue(mock_logger.audit_event.called)

        call_kwargs = mock_logger.audit_event.call_args[1]
        self.assertEqual(call_kwargs["action"], "INTUNE_APP_ASSIGNED")
        self.assertEqual(call_kwargs["resource_id"], "app-123")
        self.assertEqual(call_kwargs["outcome"], "SUCCESS")

    @patch("apps.connectors.intune.client.StructuredLogger")
    @patch("apps.connectors.intune.client.ResilientAPIClient")
    def test_failure_events_logged(self, mock_api_client_class, mock_logger_class):
        """Should log FAILURE connector events on errors."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger

        mock_client = Mock()
        mock_client.get.side_effect = ResilientAPIError(
            service_name="intune", message="API error", status_code=500, correlation_id="FAILURE-TEST"
        )

        connector = IntuneConnector()
        connector.client = mock_client

        try:
            connector.list_managed_devices(correlation_id="FAILURE-TEST")
        except IntuneConnectorError:
            pass

        # Verify FAILURE event logged
        calls = mock_logger.connector_event.call_args_list
        self.assertTrue(any("FAILURE" in str(call) for call in calls))
