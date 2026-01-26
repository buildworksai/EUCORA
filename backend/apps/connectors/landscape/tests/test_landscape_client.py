# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Landscape connector client."""
from unittest.mock import Mock, patch

import pytest
import requests

from apps.connectors.landscape.client import LandscapeConnector, LandscapeConnectorError


@pytest.fixture
def mock_auth():
    """Create mock LandscapeAuth."""
    auth = Mock()
    auth.server_url = "https://landscape.example.com"
    auth.test_connection.return_value = (True, "Connected to Landscape v23.10")
    auth.get_session.return_value = Mock(spec=requests.Session)
    auth.sign_request.return_value = {"X-LDS-Access-Key": "test"}
    return auth


@pytest.fixture
def connector(mock_auth):
    """Create LandscapeConnector with mock auth."""
    return LandscapeConnector(auth=mock_auth)


class TestLandscapeConnectorInit:
    """Tests for LandscapeConnector initialization."""

    def test_init_with_auth(self, mock_auth):
        """Test initialization with provided auth."""
        connector = LandscapeConnector(auth=mock_auth)
        assert connector.auth is mock_auth
        assert connector.server_url == "https://landscape.example.com"

    def test_init_without_auth_creates_auth(self):
        """Test initialization creates auth when not provided."""
        with patch("apps.connectors.landscape.client.LandscapeAuth") as mock_auth_class:
            mock_auth_class.return_value.server_url = "https://landscape.test"
            LandscapeConnector()
            mock_auth_class.assert_called_once()


class TestLandscapeConnectorIdempotency:
    """Tests for idempotency key generation."""

    def test_get_idempotency_key_consistent(self, connector):
        """Test that same params produce same key."""
        params = {"packages": ["vim", "curl"], "computer_ids": ["1", "2"]}
        key1 = connector.get_idempotency_key("install_packages", params)
        key2 = connector.get_idempotency_key("install_packages", params)
        assert key1 == key2

    def test_get_idempotency_key_different_for_different_params(self, connector):
        """Test that different params produce different keys."""
        key1 = connector.get_idempotency_key("install_packages", {"packages": ["vim"]})
        key2 = connector.get_idempotency_key("install_packages", {"packages": ["curl"]})
        assert key1 != key2

    def test_get_idempotency_key_different_for_different_operations(self, connector):
        """Test that different operations produce different keys."""
        params = {"packages": ["vim"]}
        key1 = connector.get_idempotency_key("install_packages", params)
        key2 = connector.get_idempotency_key("remove_packages", params)
        assert key1 != key2


class TestLandscapeConnectorTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    async def test_test_connection_delegates_to_auth(self, connector, mock_auth):
        """Test that test_connection delegates to auth."""
        mock_auth.test_connection.return_value = (True, "Connected to Landscape v23.10")
        success, message = await connector.test_connection()
        assert success is True
        assert "23.10" in message


class TestLandscapeConnectorListComputers:
    """Tests for list_computers method."""

    @pytest.mark.asyncio
    async def test_list_computers_success(self, connector, mock_auth):
        """Test successful computer listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "computers": [
                {"id": "1", "hostname": "server1.example.com"},
                {"id": "2", "hostname": "server2.example.com"},
            ],
            "total": 2,
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_computers(correlation_id="test-123")

        assert result["success"] is True
        assert result["total"] == 2
        assert len(result["computers"]) == 2

    @pytest.mark.asyncio
    async def test_list_computers_with_query(self, connector, mock_auth):
        """Test computer listing with query filter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"computers": [], "total": 0}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_computers(query="web-server")

        assert result["success"] is True
        # Verify query param was passed
        call_args = mock_session.request.call_args
        assert call_args[1]["params"]["query"] == "web-server"

    @pytest.mark.asyncio
    async def test_list_computers_with_tags(self, connector, mock_auth):
        """Test computer listing with tag filter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"computers": [], "total": 0}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_computers(tags=["production", "web"])

        assert result["success"] is True


class TestLandscapeConnectorInstallPackages:
    """Tests for install_packages method."""

    @pytest.mark.asyncio
    async def test_install_packages_success(self, connector, mock_auth):
        """Test successful package installation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "act-123"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.install_packages(
            computer_ids=["1", "2"],
            packages=["vim", "curl"],
            correlation_id="test-123",
        )

        assert result["success"] is True
        assert result["activity_id"] == "act-123"
        assert result["packages"] == ["vim", "curl"]

    @pytest.mark.asyncio
    async def test_install_packages_idempotent(self, connector, mock_auth):
        """Test that install_packages is idempotent."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "act-123"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        # First call
        result1 = await connector.install_packages(
            computer_ids=["1"],
            packages=["vim"],
        )

        # Second call with same params should return cached result
        result2 = await connector.install_packages(
            computer_ids=["1"],
            packages=["vim"],
        )

        # Session.request should only be called once
        assert mock_session.request.call_count == 1
        assert result1 == result2


class TestLandscapeConnectorRemovePackages:
    """Tests for remove_packages method."""

    @pytest.mark.asyncio
    async def test_remove_packages_success(self, connector, mock_auth):
        """Test successful package removal."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "act-456"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.remove_packages(
            computer_ids=["1"],
            packages=["vim"],
        )

        assert result["success"] is True
        assert result["activity_id"] == "act-456"


class TestLandscapeConnectorUpgradePackages:
    """Tests for upgrade_packages method."""

    @pytest.mark.asyncio
    async def test_upgrade_packages_all(self, connector, mock_auth):
        """Test upgrading all packages."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "act-789"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.upgrade_packages(computer_ids=["1", "2"])

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_upgrade_packages_security_only(self, connector, mock_auth):
        """Test security-only upgrades."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "act-sec"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.upgrade_packages(
            computer_ids=["1"],
            security_only=True,
        )

        assert result["success"] is True
        assert result["security_only"] is True


class TestLandscapeConnectorRepositories:
    """Tests for repository management."""

    @pytest.mark.asyncio
    async def test_list_repositories(self, connector, mock_auth):
        """Test listing repositories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "repositories": [
                {"id": "repo-1", "name": "Ubuntu Main"},
                {"id": "repo-2", "name": "Internal Repo"},
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_repositories()

        assert result["success"] is True
        assert len(result["repositories"]) == 2

    @pytest.mark.asyncio
    async def test_create_repository_success(self, connector, mock_auth):
        """Test successful repository creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "repo-new", "name": "Custom Repo"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.create_repository(
            name="Custom Repo",
            uri="http://repo.example.com/ubuntu",
            distribution="jammy",
            components=["main"],
            architectures=["amd64"],
        )

        assert result["success"] is True
        assert result["created"] is True

    @pytest.mark.asyncio
    async def test_create_repository_already_exists(self, connector, mock_auth):
        """Test repository creation when already exists."""
        mock_response = Mock()
        mock_response.status_code = 409

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        # Clear cache to ensure fresh call
        connector._idempotency_cache.clear()

        with patch.object(connector, "_make_request") as mock_make_request:
            mock_make_request.side_effect = LandscapeConnectorError("Conflict", status_code=409)

            result = await connector.create_repository(
                name="Existing Repo",
                uri="http://repo.example.com/ubuntu",
                distribution="jammy",
                components=["main"],
                architectures=["amd64"],
            )

            assert result["success"] is True
            assert result["created"] is False

    @pytest.mark.asyncio
    async def test_sync_repository(self, connector, mock_auth):
        """Test repository sync."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {"activity_id": "sync-123"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_repository(repository_id="repo-1")

        assert result["success"] is True
        assert result["activity_id"] == "sync-123"


class TestLandscapeConnectorScriptExecution:
    """Tests for script execution."""

    @pytest.mark.asyncio
    async def test_run_script_success(self, connector, mock_auth):
        """Test successful script execution."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "script-123"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.run_script(
            computer_ids=["1", "2"],
            script="#!/bin/bash\necho 'Hello World'",
        )

        assert result["success"] is True
        assert result["activity_id"] == "script-123"


class TestLandscapeConnectorActivities:
    """Tests for activity tracking."""

    @pytest.mark.asyncio
    async def test_get_activity(self, connector, mock_auth):
        """Test getting activity details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "act-123",
            "status": "completed",
            "type": "install-packages",
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_activity(activity_id="act-123")

        assert result["success"] is True
        assert result["activity"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_activities(self, connector, mock_auth):
        """Test listing activities."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "activities": [
                {"id": "act-1", "status": "completed"},
                {"id": "act-2", "status": "running"},
            ],
            "total": 2,
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_activities()

        assert result["success"] is True
        assert len(result["activities"]) == 2

    @pytest.mark.asyncio
    async def test_cancel_activity(self, connector, mock_auth):
        """Test cancelling an activity."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.cancel_activity(activity_id="act-123")

        assert result["success"] is True
        assert result["cancelled"] is True


class TestLandscapeConnectorCompliance:
    """Tests for compliance reporting."""

    @pytest.mark.asyncio
    async def test_get_compliance_status(self, connector, mock_auth):
        """Test getting compliance status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_computers": 100,
            "compliant_computers": 95,
            "pending_updates": 50,
            "security_updates": 10,
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_compliance_status()

        assert result["success"] is True
        assert result["compliance_rate"] == 95.0
        assert result["non_compliant_computers"] == 5

    @pytest.mark.asyncio
    async def test_get_security_updates(self, connector, mock_auth):
        """Test getting security updates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "updates": [
                {"package": "openssl", "severity": "critical"},
                {"package": "curl", "severity": "high"},
            ],
            "total": 2,
            "by_severity": {"critical": 1, "high": 1},
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_security_updates()

        assert result["success"] is True
        assert result["total"] == 2


class TestLandscapeConnectorRollback:
    """Tests for rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_packages(self, connector, mock_auth):
        """Test package rollback."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"activity_id": "rollback-123"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.rollback_packages(
            computer_ids=["1"],
            packages=[
                {"name": "vim", "version": "8.0.0"},
                {"name": "curl", "version": "7.68.0"},
            ],
        )

        assert result["success"] is True
        assert result["rollback"] is True


class TestLandscapeConnectorInventorySync:
    """Tests for inventory synchronization."""

    @pytest.mark.asyncio
    async def test_sync_inventory(self, connector, mock_auth):
        """Test full inventory sync."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "computers": [
                {"id": "1", "hostname": "server1"},
                {"id": "2", "hostname": "server2"},
            ],
            "total": 2,
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_inventory(correlation_id="sync-123")

        assert result["success"] is True
        assert result["count"] == 2
        assert "synced_at" in result


class TestLandscapeConnectorErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, connector, mock_auth):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(LandscapeConnectorError) as exc_info:
            await connector.list_computers()

        assert exc_info.value.is_transient is True
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_server_error(self, connector, mock_auth):
        """Test server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(LandscapeConnectorError) as exc_info:
            await connector.list_computers()

        assert exc_info.value.is_transient is True
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_error(self, connector, mock_auth):
        """Test timeout error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.Timeout()
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(LandscapeConnectorError) as exc_info:
            await connector.list_computers()

        assert exc_info.value.is_transient is True

    @pytest.mark.asyncio
    async def test_connection_error(self, connector, mock_auth):
        """Test connection error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.ConnectionError()
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(LandscapeConnectorError) as exc_info:
            await connector.list_computers()

        assert exc_info.value.is_transient is True
