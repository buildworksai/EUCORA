# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for Ansible/AWX connector client."""
from unittest.mock import Mock

import pytest
import requests

from apps.connectors.ansible.client import AnsibleConnector, AnsibleConnectorError


@pytest.fixture
def mock_auth():
    """Create mock AnsibleAuth."""
    auth = Mock()
    auth.server_url = "https://awx.example.com"
    auth.test_connection.return_value = (True, "Connected to AWX v21.0.0")
    auth.get_session.return_value = Mock(spec=requests.Session)
    auth.sign_request.return_value = {"Authorization": "Bearer test"}
    return auth


@pytest.fixture
def connector(mock_auth):
    """Create AnsibleConnector with mock auth."""
    return AnsibleConnector(auth=mock_auth)


class TestAnsibleConnectorInit:
    """Tests for AnsibleConnector initialization."""

    def test_init_with_auth(self, mock_auth):
        """Test initialization with provided auth."""
        connector = AnsibleConnector(auth=mock_auth)
        assert connector.auth is mock_auth
        assert connector.server_url == "https://awx.example.com"

    def test_init_sets_api_base(self, mock_auth):
        """Test that api_base is set correctly."""
        connector = AnsibleConnector(auth=mock_auth)
        assert connector.api_base == "https://awx.example.com/api/v2"


class TestAnsibleConnectorInventory:
    """Tests for inventory management."""

    @pytest.mark.asyncio
    async def test_list_inventories(self, connector, mock_auth):
        """Test listing inventories."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "name": "Production"},
                {"id": 2, "name": "Staging"},
            ],
            "count": 2,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_inventories()

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_get_inventory(self, connector, mock_auth):
        """Test getting inventory details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Production",
            "description": "Production inventory",
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_inventory(inventory_id=1)

        assert result["success"] is True
        assert result["inventory"]["name"] == "Production"

    @pytest.mark.asyncio
    async def test_get_inventory_hosts(self, connector, mock_auth):
        """Test getting hosts in inventory."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "name": "server1.example.com"},
                {"id": 2, "name": "server2.example.com"},
            ],
            "count": 2,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_inventory_hosts(inventory_id=1)

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_create_host_success(self, connector, mock_auth):
        """Test creating a host."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 3,
            "name": "newserver.example.com",
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.create_host(
            inventory_id=1,
            name="newserver.example.com",
        )

        assert result["success"] is True
        assert result["created"] is True


class TestAnsibleConnectorJobTemplates:
    """Tests for job template management."""

    @pytest.mark.asyncio
    async def test_list_job_templates(self, connector, mock_auth):
        """Test listing job templates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "name": "Deploy Packages"},
                {"id": 2, "name": "Security Updates"},
            ],
            "count": 2,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_job_templates()

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_get_job_template(self, connector, mock_auth):
        """Test getting job template details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Deploy Packages",
            "playbook": "deploy.yml",
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_job_template(template_id=1)

        assert result["success"] is True
        assert result["job_template"]["name"] == "Deploy Packages"

    @pytest.mark.asyncio
    async def test_launch_job_template(self, connector, mock_auth):
        """Test launching a job template."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 100,
            "job": 100,
            "status": "pending",
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.launch_job_template(
            template_id=1,
            extra_vars={"packages": ["vim", "curl"]},
            limit="webservers",
        )

        assert result["success"] is True
        assert result["job_id"] == 100

    @pytest.mark.asyncio
    async def test_launch_job_template_with_tags(self, connector, mock_auth):
        """Test launching job template with tags."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 101, "status": "pending"}
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.launch_job_template(
            template_id=1,
            tags="install,configure",
            skip_tags="notify",
        )

        assert result["success"] is True


class TestAnsibleConnectorJobs:
    """Tests for job management."""

    @pytest.mark.asyncio
    async def test_get_job(self, connector, mock_auth):
        """Test getting job details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 100,
            "status": "running",
            "job_template": 1,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_job(job_id=100)

        assert result["success"] is True
        assert result["job"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_cancel_job(self, connector, mock_auth):
        """Test cancelling a job."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_response.text = ""

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.cancel_job(job_id=100)

        assert result["success"] is True
        assert result["cancelled"] is True

    @pytest.mark.asyncio
    async def test_list_jobs(self, connector, mock_auth):
        """Test listing jobs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 100, "status": "successful"},
                {"id": 101, "status": "failed"},
            ],
            "count": 2,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_jobs()

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_get_job_host_summaries(self, connector, mock_auth):
        """Test getting job host summaries."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"host_name": "server1", "failed": False},
                {"host_name": "server2", "failed": True},
            ],
            "count": 2,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.get_job_host_summaries(job_id=100)

        assert result["success"] is True
        assert result["successful_hosts"] == 1
        assert result["failed_hosts"] == 1
        assert result["success_rate"] == 50.0


class TestAnsibleConnectorWorkflows:
    """Tests for workflow job templates."""

    @pytest.mark.asyncio
    async def test_list_workflow_templates(self, connector, mock_auth):
        """Test listing workflow templates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "name": "Full Deployment"},
            ],
            "count": 1,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_workflow_templates()

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_launch_workflow(self, connector, mock_auth):
        """Test launching a workflow."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 200,
            "status": "pending",
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.launch_workflow(
            workflow_id=1,
            extra_vars={"environment": "production"},
        )

        assert result["success"] is True
        assert result["job_id"] == 200


class TestAnsibleConnectorProjects:
    """Tests for project management."""

    @pytest.mark.asyncio
    async def test_list_projects(self, connector, mock_auth):
        """Test listing projects."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "name": "Ansible Playbooks"},
            ],
            "count": 1,
            "next": None,
        }
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.list_projects()

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_sync_project(self, connector, mock_auth):
        """Test syncing a project."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {"id": 300}
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_project(project_id=1)

        assert result["success"] is True
        assert result["job_id"] == 300


class TestAnsibleConnectorPackageDeployment:
    """Tests for EUCORA-specific package deployment."""

    @pytest.mark.asyncio
    async def test_deploy_packages_install(self, connector, mock_auth):
        """Test package installation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 400, "status": "pending"}
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.deploy_packages(
            template_id=1,
            hosts=["server1", "server2"],
            packages=["vim", "curl"],
            action="install",
        )

        assert result["success"] is True
        assert result["action"] == "install"
        assert result["packages"] == ["vim", "curl"]

    @pytest.mark.asyncio
    async def test_deploy_packages_idempotent(self, connector, mock_auth):
        """Test that deploy_packages is idempotent for install/remove."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 401, "status": "pending"}
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        # Clear cache
        connector._idempotency_cache.clear()

        # First call
        result1 = await connector.deploy_packages(
            template_id=1,
            hosts=["server1"],
            packages=["vim"],
            action="install",
        )

        # Second call with same params
        result2 = await connector.deploy_packages(
            template_id=1,
            hosts=["server1"],
            packages=["vim"],
            action="install",
        )

        # Should only make one API call
        assert mock_session.request.call_count == 1
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_run_remediation(self, connector, mock_auth):
        """Test running remediation playbook."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 500, "status": "pending"}
        mock_response.raise_for_status = Mock()
        mock_response.text = "{}"

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        result = await connector.run_remediation(
            template_id=2,
            hosts=["server1"],
            remediation_type="security_patch",
            parameters={"patch_level": "critical"},
        )

        assert result["success"] is True
        assert result["remediation_type"] == "security_patch"


class TestAnsibleConnectorInventorySync:
    """Tests for inventory synchronization."""

    @pytest.mark.asyncio
    async def test_sync_inventory(self, connector, mock_auth):
        """Test full inventory sync."""
        # Mock inventory response
        inventory_response = Mock()
        inventory_response.status_code = 200
        inventory_response.json.return_value = {
            "id": 1,
            "name": "Production",
        }
        inventory_response.raise_for_status = Mock()
        inventory_response.text = "{}"

        # Mock hosts response
        hosts_response = Mock()
        hosts_response.status_code = 200
        hosts_response.json.return_value = {
            "results": [
                {"id": 1, "name": "server1"},
                {"id": 2, "name": "server2"},
            ],
            "count": 2,
            "next": None,
        }
        hosts_response.raise_for_status = Mock()
        hosts_response.text = "{}"

        mock_session = Mock()
        mock_session.request.side_effect = [inventory_response, hosts_response]
        mock_auth.get_session.return_value = mock_session

        result = await connector.sync_inventory(inventory_id=1)

        assert result["success"] is True
        assert result["host_count"] == 2
        assert "synced_at" in result


class TestAnsibleConnectorErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, connector, mock_auth):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(AnsibleConnectorError) as exc_info:
            await connector.list_inventories()

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

        with pytest.raises(AnsibleConnectorError) as exc_info:
            await connector.list_inventories()

        assert exc_info.value.is_transient is True
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_error(self, connector, mock_auth):
        """Test timeout error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.Timeout()
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(AnsibleConnectorError) as exc_info:
            await connector.list_inventories()

        assert exc_info.value.is_transient is True

    @pytest.mark.asyncio
    async def test_connection_error(self, connector, mock_auth):
        """Test connection error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = requests.exceptions.ConnectionError()
        mock_auth.get_session.return_value = mock_session

        with pytest.raises(AnsibleConnectorError) as exc_info:
            await connector.list_inventories()

        assert exc_info.value.is_transient is True


class TestAnsibleConnectorIdempotency:
    """Tests for idempotency."""

    def test_get_idempotency_key_consistent(self, connector):
        """Test that same params produce same key."""
        params = {"template_id": 1, "hosts": ["a", "b"]}
        key1 = connector.get_idempotency_key("deploy", params)
        key2 = connector.get_idempotency_key("deploy", params)
        assert key1 == key2

    def test_get_idempotency_key_different_for_different_params(self, connector):
        """Test that different params produce different keys."""
        key1 = connector.get_idempotency_key("deploy", {"hosts": ["a"]})
        key2 = connector.get_idempotency_key("deploy", {"hosts": ["b"]})
        assert key1 != key2
