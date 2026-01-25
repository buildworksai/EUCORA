# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for SCCM connector client."""
from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests

from apps.connectors.sccm.client import SCCMConnector, SCCMConnectorError


@pytest.fixture
def mock_auth():
    """Create mock SCCMAuth."""
    auth = Mock()
    auth.server_url = "https://sccm.example.com/AdminService"
    auth.site_code = "PS1"
    auth.test_connection.return_value = (True, "Connected")
    auth.get_session.return_value = Mock(spec=requests.Session)
    return auth


@pytest.fixture
def connector(mock_auth):
    """Create SCCMConnector with mock auth."""
    return SCCMConnector(auth=mock_auth)


class TestSCCMConnectorInit:
    """Tests for SCCMConnector initialization."""

    def test_init_with_auth(self, mock_auth):
        """Test initialization with provided auth."""
        connector = SCCMConnector(auth=mock_auth)
        assert connector.auth is mock_auth
        assert connector.server_url == "https://sccm.example.com/AdminService"

    def test_init_without_auth_creates_auth(self):
        """Test initialization creates auth when not provided."""
        with patch("apps.connectors.sccm.client.SCCMAuth") as mock_auth_class:
            mock_auth_class.return_value.server_url = "https://sccm.test/AdminService"
            mock_auth_class.return_value.site_code = "PS1"
            connector = SCCMConnector()
            mock_auth_class.assert_called_once()


class TestSCCMConnectorIdempotency:
    """Tests for idempotency key generation."""

    def test_get_idempotency_key_consistent(self, connector):
        """Test that same params produce same key."""
        params = {"name": "TestApp", "version": "1.0"}
        key1 = connector.get_idempotency_key("create_application", params)
        key2 = connector.get_idempotency_key("create_application", params)
        assert key1 == key2

    def test_get_idempotency_key_different_for_different_params(self, connector):
        """Test that different params produce different keys."""
        key1 = connector.get_idempotency_key("create_application", {"name": "App1", "version": "1.0"})
        key2 = connector.get_idempotency_key("create_application", {"name": "App2", "version": "1.0"})
        assert key1 != key2

    def test_get_idempotency_key_different_for_different_operations(self, connector):
        """Test that different operations produce different keys."""
        params = {"name": "TestApp", "version": "1.0"}
        key1 = connector.get_idempotency_key("create_application", params)
        key2 = connector.get_idempotency_key("delete_application", params)
        assert key1 != key2


class TestSCCMConnectorTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_test_connection_delegates_to_auth(self, connector, mock_auth):
        """Test that test_connection delegates to auth."""
        mock_auth.test_connection.return_value = (True, "Connected to SCCM site PS1")
        success, message = await connector.test_connection()
        assert success is True
        assert "PS1" in message


class TestSCCMConnectorSyncInventory:
    """Tests for sync_inventory method."""

    @pytest.mark.asyncio
    async def test_sync_inventory_success(self, connector, mock_auth):
        """Test successful inventory sync."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"CI_UniqueID": "app1", "LocalizedDisplayName": "App 1"},
                {"CI_UniqueID": "app2", "LocalizedDisplayName": "App 2"},
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_inventory(correlation_id="test-123")

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["applications"]) == 2

    @pytest.mark.asyncio
    async def test_sync_inventory_empty(self, connector, mock_auth):
        """Test inventory sync with no applications."""
        mock_response = Mock()
        mock_response.json.return_value = {"value": []}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_inventory()

        assert result["success"] is True
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_sync_inventory_http_error(self, connector, mock_auth):
        """Test inventory sync with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(SCCMConnectorError) as exc_info:
            await connector.sync_inventory()

        assert exc_info.value.is_transient is True


class TestSCCMConnectorCreateApplication:
    """Tests for create_application method."""

    @pytest.mark.asyncio
    async def test_create_application_success(self, connector, mock_auth):
        """Test successful application creation."""
        # Mock find returns None (app doesn't exist)
        mock_find_response = Mock()
        mock_find_response.json.return_value = {"value": []}
        mock_find_response.raise_for_status = Mock()

        # Mock create returns new app
        mock_create_response = Mock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = {
            "CI_UniqueID": "new-app-id",
            "LocalizedDisplayName": "TestApp",
        }
        mock_create_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_find_response
        mock_session.post.return_value = mock_create_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.create_application(
            name="TestApp",
            version="1.0.0",
            publisher="EUCORA",
            content_location="\\\\server\\share\\app",
            install_command="setup.exe /quiet",
            uninstall_command="setup.exe /uninstall /quiet",
        )

        assert result["success"] is True
        assert result["created"] is True

    @pytest.mark.asyncio
    async def test_create_application_already_exists(self, connector, mock_auth):
        """Test application creation when app already exists."""
        mock_find_response = Mock()
        mock_find_response.json.return_value = {
            "value": [{"CI_UniqueID": "existing-app", "LocalizedDisplayName": "TestApp"}]
        }
        mock_find_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_find_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.create_application(
            name="TestApp",
            version="1.0.0",
            publisher="EUCORA",
            content_location="\\\\server\\share\\app",
            install_command="setup.exe /quiet",
            uninstall_command="setup.exe /uninstall /quiet",
        )

        assert result["success"] is True
        assert result["created"] is False
        assert "already exists" in result["message"]

    @pytest.mark.asyncio
    async def test_create_application_idempotent(self, connector, mock_auth):
        """Test that create_application is idempotent."""
        mock_find_response = Mock()
        mock_find_response.json.return_value = {"value": []}
        mock_find_response.raise_for_status = Mock()

        mock_create_response = Mock()
        mock_create_response.status_code = 201
        mock_create_response.json.return_value = {"CI_UniqueID": "new-app"}
        mock_create_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_find_response
        mock_session.post.return_value = mock_create_response
        mock_auth.get_session.return_value = mock_session

        # First call
        result1 = await connector.create_application(
            name="TestApp",
            version="1.0.0",
            publisher="EUCORA",
            content_location="\\\\server\\share\\app",
            install_command="setup.exe /quiet",
            uninstall_command="setup.exe /uninstall /quiet",
        )

        # Second call with same params should return cached result
        result2 = await connector.create_application(
            name="TestApp",
            version="1.0.0",
            publisher="EUCORA",
            content_location="\\\\server\\share\\app",
            install_command="setup.exe /quiet",
            uninstall_command="setup.exe /uninstall /quiet",
        )

        # Session.post should only be called once
        assert mock_session.post.call_count == 1
        assert result1 == result2


class TestSCCMConnectorDeployToCollection:
    """Tests for deploy_to_collection method."""

    @pytest.mark.asyncio
    async def test_deploy_to_collection_success(self, connector, mock_auth):
        """Test successful deployment to collection."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "AssignmentID": "deploy-123",
            "ApplicationName": "app-id",
            "CollectionName": "collection-id",
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.deploy_to_collection(
            application_id="app-id",
            collection_id="collection-id",
            deployment_action="Install",
            deployment_purpose="Required",
        )

        assert result["success"] is True
        assert result["created"] is True

    @pytest.mark.asyncio
    async def test_deploy_to_collection_conflict(self, connector, mock_auth):
        """Test deployment when assignment already exists."""
        mock_response = Mock()
        mock_response.status_code = 409

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.deploy_to_collection(
            application_id="app-id",
            collection_id="collection-id",
        )

        assert result["success"] is True
        assert result["created"] is False


class TestSCCMConnectorGetComplianceStatus:
    """Tests for get_compliance_status method."""

    @pytest.mark.asyncio
    async def test_get_compliance_status_success(self, connector, mock_auth):
        """Test successful compliance status query."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"StatusType": 1},  # installed
                {"StatusType": 1},  # installed
                {"StatusType": 2},  # failed
                {"StatusType": 3},  # pending
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_compliance_status(
            application_id="app-id",
            collection_id="collection-id",
        )

        assert result["success"] is True
        assert result["total_devices"] == 4
        assert result["status_counts"]["installed"] == 2
        assert result["status_counts"]["failed"] == 1
        assert result["status_counts"]["pending"] == 1
        assert result["success_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_get_compliance_status_empty(self, connector, mock_auth):
        """Test compliance status with no devices."""
        mock_response = Mock()
        mock_response.json.return_value = {"value": []}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_compliance_status(application_id="app-id")

        assert result["success"] is True
        assert result["total_devices"] == 0
        assert result["success_rate"] == 0


class TestSCCMConnectorRollback:
    """Tests for rollback method."""

    @pytest.mark.asyncio
    async def test_rollback_success(self, connector, mock_auth):
        """Test successful rollback."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.delete.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.rollback(deployment_id="deploy-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rollback_not_found(self, connector, mock_auth):
        """Test rollback when deployment not found."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_session = Mock()
        mock_session.delete.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.rollback(deployment_id="deploy-123")

        assert result["success"] is True
        assert "not found" in result["message"].lower()


class TestSCCMConnectorListCollections:
    """Tests for list_collections method."""

    @pytest.mark.asyncio
    async def test_list_collections_device(self, connector, mock_auth):
        """Test listing device collections."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"CollectionID": "COL001", "Name": "All Workstations"},
                {"CollectionID": "COL002", "Name": "IT Department"},
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_collections(collection_type="Device")

        assert len(result) == 2
        # Verify filter includes CollectionType eq 2 (Device)
        call_args = mock_session.get.call_args
        assert "CollectionType eq 2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_collections_user(self, connector, mock_auth):
        """Test listing user collections."""
        mock_response = Mock()
        mock_response.json.return_value = {"value": []}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_collections(collection_type="User")

        # Verify filter includes CollectionType eq 1 (User)
        call_args = mock_session.get.call_args
        assert "CollectionType eq 1" in call_args[0][0]
