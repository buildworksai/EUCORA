# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for agent management REST API.

Target: 25 tests covering all endpoints and authentication.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.agent_management.models import Agent, AgentDeploymentStatus, AgentOfflineQueue, AgentTask, AgentTelemetry

User = get_user_model()


class AgentRegistrationAPITests(TestCase):
    """Tests for agent registration API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_register_new_agent(self):
        """Test POST /api/v1/agent-management/agents/register/ creates new agent."""
        data = {
            "hostname": "test-win-001",
            "platform": "windows",
            "platform_version": "11 22H2",
            "agent_version": "1.0.0",
            "registration_key": "reg-key-001",
            "cpu_cores": 8,
            "memory_mb": 16384,
            "disk_gb": 512,
            "ip_address": "10.0.1.100",
            "mac_address": "00:15:5D:00:00:01",
        }

        response = self.client.post(
            "/api/v1/agent-management/agents/register/", data, format="json", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["hostname"], "test-win-001")
        self.assertEqual(response.data["platform"], "windows")

    def test_register_agent_requires_authentication(self):
        """Test registration requires authentication."""
        self.client.force_authenticate(user=None)

        data = {
            "hostname": "test-win-001",
            "platform": "windows",
            "platform_version": "11",
            "agent_version": "1.0.0",
            "registration_key": "reg-key-001",
            "cpu_cores": 4,
            "memory_mb": 8192,
            "disk_gb": 256,
            "ip_address": "10.0.1.1",
            "mac_address": "00:00:00:00:00:01",
        }

        response = self.client.post("/api/v1/agent-management/agents/register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_agent_validation_errors(self):
        """Test registration validates required fields."""
        data = {
            "hostname": "test-win-001",
            # Missing required fields
        }

        response = self.client.post("/api/v1/agent-management/agents/register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AgentHeartbeatAPITests(TestCase):
    """Tests for agent heartbeat API endpoint."""

    def setUp(self):
        """Set up test client, user, and agent."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
            status="OFFLINE",
        )

    def test_heartbeat_success(self):
        """Test POST /api/v1/agent-management/agents/{id}/heartbeat/ succeeds."""
        response = self.client.post(
            f"/api/v1/agent-management/agents/{self.agent.id}/heartbeat/", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

        # Agent should be marked online
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.status, "ONLINE")

    def test_heartbeat_returns_pending_tasks(self):
        """Test heartbeat returns pending tasks."""
        # Create pending tasks
        AgentTask.objects.create(
            agent=self.agent,
            task_type="DEPLOY",
            payload={"package_name": "pkg-001"},
            created_by=self.user,
            status="PENDING",
        )
        AgentTask.objects.create(
            agent=self.agent, task_type="COLLECT", payload={}, created_by=self.user, status="PENDING"
        )

        response = self.client.post(f"/api/v1/agent-management/agents/{self.agent.id}/heartbeat/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending_tasks"], 2)
        self.assertEqual(len(response.data["tasks"]), 2)

    def test_heartbeat_nonexistent_agent(self):
        """Test heartbeat with non-existent agent returns 404."""
        fake_id = uuid.uuid4()
        response = self.client.post(f"/api/v1/agent-management/agents/{fake_id}/heartbeat/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AgentTaskAPITests(TestCase):
    """Tests for agent task management API endpoints."""

    def setUp(self):
        """Set up test client, user, and agent."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
            status="ONLINE",
        )

    def test_create_task(self):
        """Test POST /api/v1/agent-management/tasks/ creates task."""
        data = {
            "agent_id": str(self.agent.id),
            "task_type": "DEPLOY",
            "payload": {"package_name": "pkg-001", "version": "1.0.0"},
            "timeout_seconds": 3600,
        }

        response = self.client.post(
            "/api/v1/agent-management/tasks/", data, format="json", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["task_type"], "DEPLOY")
        self.assertEqual(response.data["status"], "PENDING")

    def test_list_tasks_with_filters(self):
        """Test GET /api/v1/agent-management/tasks/ with query filters."""
        # Create tasks
        task1 = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user, status="PENDING"
        )
        task2 = AgentTask.objects.create(
            agent=self.agent, task_type="REMEDIATE", payload={}, created_by=self.user, status="COMPLETED"
        )

        # Filter by status
        response = self.client.get("/api/v1/agent-management/tasks/?status=PENDING")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(task1.id))

    def test_start_task(self):
        """Test POST /api/v1/agent-management/tasks/{id}/start/ marks task in progress."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user, status="PENDING"
        )

        response = self.client.post(
            f"/api/v1/agent-management/tasks/{task.id}/start/", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "IN_PROGRESS")

        task.refresh_from_db()
        self.assertEqual(task.status, "IN_PROGRESS")

    def test_complete_task(self):
        """Test POST /api/v1/agent-management/tasks/{id}/complete/ marks task completed."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user, status="IN_PROGRESS"
        )

        data = {"status": "COMPLETED", "result": {"exit_code": 0, "message": "Success"}, "exit_code": 0}

        response = self.client.post(
            f"/api/v1/agent-management/tasks/{task.id}/complete/",
            data,
            format="json",
            HTTP_X_CORRELATION_ID="test-corr-001",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "COMPLETED")

        task.refresh_from_db()
        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(task.result["exit_code"], 0)

    def test_fail_task(self):
        """Test POST /api/v1/agent-management/tasks/{id}/fail/ marks task failed."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user, status="IN_PROGRESS"
        )

        data = {"status": "FAILED", "error_message": "Package not found", "exit_code": 1}

        response = self.client.post(
            f"/api/v1/agent-management/tasks/{task.id}/fail/",
            data,
            format="json",
            HTTP_X_CORRELATION_ID="test-corr-001",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "FAILED")

        task.refresh_from_db()
        self.assertEqual(task.status, "FAILED")
        self.assertEqual(task.error_message, "Package not found")


class AgentTelemetryAPITests(TestCase):
    """Tests for agent telemetry API endpoints."""

    def setUp(self):
        """Set up test client, user, and agent."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_submit_telemetry(self):
        """Test POST /api/v1/agent-management/telemetry/ submits telemetry."""
        data = {
            "agent_id": str(self.agent.id),
            "cpu_usage_percent": 45.2,
            "memory_usage_percent": 62.8,
            "disk_usage_percent": 73.5,
            "network_bytes_sent": 512000,
            "network_bytes_received": 1024000,
            "installed_software": [{"name": "pkg1"}, {"name": "pkg2"}],
        }

        response = self.client.post(
            "/api/v1/agent-management/telemetry/", data, format="json", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cpu_usage_percent"], 45.2)

    def test_list_telemetry_for_agent(self):
        """Test GET /api/v1/agent-management/telemetry/?agent_id={id} lists telemetry."""
        # Create telemetry
        AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=40.0,
            memory_usage_percent=50.0,
            disk_usage_percent=60.0,
            collected_at=timezone.now(),
            correlation_id="test-corr-001",
        )
        AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=45.0,
            memory_usage_percent=55.0,
            disk_usage_percent=65.0,
            collected_at=timezone.now(),
            correlation_id="test-corr-002",
        )

        response = self.client.get(f"/api/v1/agent-management/telemetry/?agent_id={self.agent.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)


class AgentDeploymentStatusAPITests(TestCase):
    """Tests for agent deployment status API endpoints."""

    def setUp(self):
        """Set up test client, user, and agent."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_list_deployment_status(self):
        """Test GET /api/v1/agent-management/deployments/ lists statuses."""
        # Create deployment statuses
        AgentDeploymentStatus.objects.create(
            agent=self.agent,
            deployment_intent_id=uuid.uuid4(),
            package_name="pkg-001",
            package_version="1.0.0",
            package_hash="abc123",
            status="IN_PROGRESS",
            progress_percent=45,
            correlation_id="test-corr-001",
        )

        response = self.client.get("/api/v1/agent-management/deployments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_deployment_status_by_agent(self):
        """Test filtering deployment status by agent_id."""
        deployment = AgentDeploymentStatus.objects.create(
            agent=self.agent,
            deployment_intent_id=uuid.uuid4(),
            package_name="pkg-001",
            package_version="1.0.0",
            package_hash="abc123",
            status="INSTALLED",
            correlation_id="test-corr-001",
        )

        response = self.client.get(f"/api/v1/agent-management/deployments/?agent_id={self.agent.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["package_name"], "pkg-001")


class AgentListAPITests(TestCase):
    """Tests for agent list API endpoints."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_list_agents(self):
        """Test GET /api/v1/agent-management/agents/ lists all agents."""
        # Create agents
        Agent.objects.create(
            hostname="test-win-001",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )
        Agent.objects.create(
            hostname="test-mac-001",
            platform="macos",
            platform_version="14.0",
            agent_version="1.0.0",
            registration_key="reg-key-002",
            cpu_cores=8,
            memory_mb=16384,
            disk_gb=512,
            ip_address="10.0.1.2",
            mac_address="00:00:00:00:00:02",
        )

        response = self.client.get("/api/v1/agent-management/agents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_agents_by_platform(self):
        """Test filtering agents by platform."""
        Agent.objects.create(
            hostname="test-win-001",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )
        Agent.objects.create(
            hostname="test-mac-001",
            platform="macos",
            platform_version="14.0",
            agent_version="1.0.0",
            registration_key="reg-key-002",
            cpu_cores=8,
            memory_mb=16384,
            disk_gb=512,
            ip_address="10.0.1.2",
            mac_address="00:00:00:00:00:02",
        )

        response = self.client.get("/api/v1/agent-management/agents/?platform=windows")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["platform"], "windows")

    def test_filter_agents_by_online_status(self):
        """Test filtering agents by online/offline status."""
        online_agent = Agent.objects.create(
            hostname="test-online",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-online",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
            last_heartbeat_at=timezone.now(),
        )
        offline_agent = Agent.objects.create(
            hostname="test-offline",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-offline",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.2",
            mac_address="00:00:00:00:00:02",
            last_heartbeat_at=timezone.now() - timedelta(minutes=10),
        )

        response = self.client.get("/api/v1/agent-management/agents/?is_online=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["hostname"], "test-online")

    def test_get_agent_details(self):
        """Test GET /api/v1/agent-management/agents/{id}/ returns agent details."""
        agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

        response = self.client.get(f"/api/v1/agent-management/agents/{agent.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hostname"], "test-agent")
        self.assertEqual(response.data["platform"], "windows")

    def test_get_agent_tasks(self):
        """Test GET /api/v1/agent-management/agents/{id}/tasks/ returns agent tasks."""
        agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

        # Create tasks
        AgentTask.objects.create(agent=agent, task_type="DEPLOY", payload={}, created_by=self.user)
        AgentTask.objects.create(agent=agent, task_type="COLLECT", payload={}, created_by=self.user)

        response = self.client.get(f"/api/v1/agent-management/agents/{agent.id}/tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_agent_telemetry(self):
        """Test GET /api/v1/agent-management/agents/{id}/telemetry/ returns telemetry."""
        agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

        # Create telemetry
        AgentTelemetry.objects.create(
            agent=agent,
            cpu_usage_percent=40.0,
            memory_usage_percent=50.0,
            disk_usage_percent=60.0,
            collected_at=timezone.now(),
            correlation_id="test-corr-001",
        )

        response = self.client.get(f"/api/v1/agent-management/agents/{agent.id}/telemetry/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_agent_detail_endpoint(self):
        """Test GET /api/v1/agent-management/agents/{id}/ returns agent details."""
        agent = Agent.objects.create(
            hostname="detail-agent",
            platform="linux",
            platform_version="22.04",
            agent_version="1.0.0",
            registration_key="reg-key-detail",
            cpu_cores=8,
            memory_mb=16384,
            disk_gb=512,
            ip_address="10.0.2.1",
            mac_address="00:00:00:00:00:02",
        )

        response = self.client.get(f"/api/v1/agent-management/agents/{agent.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hostname"], "detail-agent")
        self.assertEqual(response.data["platform"], "linux")

    def test_agent_update_endpoint(self):
        """Test PATCH /api/v1/agent-management/agents/{id}/ updates agent."""
        agent = Agent.objects.create(
            hostname="update-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-update",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.3.1",
            mac_address="00:00:00:00:00:03",
        )

        response = self.client.patch(
            f"/api/v1/agent-management/agents/{agent.id}/", {"agent_version": "1.1.0"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        agent.refresh_from_db()
        self.assertEqual(agent.agent_version, "1.1.0")

    def test_task_create_for_offline_agent(self):
        """Test task creation for offline agent goes to offline queue."""
        agent = Agent.objects.create(
            hostname="offline-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="reg-key-offline",
            status="OFFLINE",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.10",
            mac_address="00:00:00:00:00:10",
            last_heartbeat_at=timezone.now() - timedelta(minutes=10),  # Offline (>5 min ago)
        )

        response = self.client.post(
            "/api/v1/agent-management/tasks/",
            {"agent_id": str(agent.id), "task_type": "DEPLOY", "payload": {"package_name": "pkg-offline-001"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check offline queue entry created
        self.assertTrue(AgentOfflineQueue.objects.filter(agent=agent).exists())

    def test_telemetry_submission_updates_agent_status(self):
        """Test telemetry submission updates agent online status."""
        agent = Agent.objects.create(
            hostname="telemetry-agent",
            platform="linux",
            platform_version="22.04",
            agent_version="1.0.0",
            registration_key="reg-key-telemetry",
            status="OFFLINE",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.11",
            mac_address="00:00:00:00:00:11",
        )

        response = self.client.post(
            "/api/v1/agent-management/telemetry/",
            {
                "agent_id": str(agent.id),
                "cpu_usage_percent": 25.0,
                "memory_usage_percent": 30.0,
                "disk_usage_percent": 40.0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        agent.refresh_from_db()
        # Telemetry submission should update heartbeat and potentially status
        self.assertIsNotNone(agent.last_heartbeat_at)
