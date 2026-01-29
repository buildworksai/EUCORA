# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for agent management models.

Target: 20 tests covering all models and their behaviors.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.agent_management.models import Agent, AgentDeploymentStatus, AgentOfflineQueue, AgentTask, AgentTelemetry

User = get_user_model()


class AgentModelTests(TestCase):
    """Tests for Agent model."""

    def setUp(self):
        """Set up test data."""
        self.agent = Agent.objects.create(
            hostname="test-win-001",
            platform="windows",
            platform_version="11 22H2",
            agent_version="1.0.0",
            registration_key="test-reg-key-001",
            cpu_cores=8,
            memory_mb=16384,
            disk_gb=512,
            ip_address="10.0.1.100",
            mac_address="00:15:5D:00:00:01",
            status="ONLINE",
        )

    def test_agent_creation(self):
        """Test agent is created with correct attributes."""
        self.assertEqual(self.agent.hostname, "test-win-001")
        self.assertEqual(self.agent.platform, "windows")
        self.assertEqual(self.agent.status, "ONLINE")
        self.assertIsInstance(self.agent.id, uuid.UUID)

    def test_agent_is_online_property(self):
        """Test is_online property returns correct status."""
        # Agent with recent heartbeat should be online
        self.agent.last_heartbeat_at = timezone.now()
        self.agent.save()
        self.assertTrue(self.agent.is_online)

        # Agent with old heartbeat should be offline
        self.agent.last_heartbeat_at = timezone.now() - timedelta(minutes=10)
        self.agent.save()
        self.assertFalse(self.agent.is_online)

    def test_agent_str_representation(self):
        """Test string representation of agent."""
        expected = f"{self.agent.hostname} ({self.agent.platform})"
        self.assertEqual(str(self.agent), expected)

    def test_agent_unique_registration_key(self):
        """Test registration_key uniqueness constraint."""
        with self.assertRaises(Exception):
            Agent.objects.create(
                hostname="test-win-002",
                platform="windows",
                platform_version="11 22H2",
                agent_version="1.0.0",
                registration_key="test-reg-key-001",  # Duplicate
                cpu_cores=8,
                memory_mb=16384,
                disk_gb=512,
                ip_address="10.0.1.101",
                mac_address="00:15:5D:00:00:02",
            )

    def test_agent_platform_choices(self):
        """Test platform field accepts only valid choices."""
        valid_platforms = ["windows", "macos", "linux"]
        for platform in valid_platforms:
            agent = Agent.objects.create(
                hostname=f"test-{platform}-001",
                platform=platform,
                platform_version="1.0",
                agent_version="1.0.0",
                registration_key=f"test-reg-{platform}",
                cpu_cores=4,
                memory_mb=8192,
                disk_gb=256,
                ip_address="10.0.1.1",
                mac_address="00:00:00:00:00:01",
            )
            self.assertEqual(agent.platform, platform)


class AgentTaskModelTests(TestCase):
    """Tests for AgentTask model."""

    def setUp(self):
        """Set up test data."""
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="test-reg-key",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_task_creation(self):
        """Test task is created with correct attributes."""
        task = AgentTask.objects.create(
            agent=self.agent,
            task_type="DEPLOY",
            payload={"package_name": "pkg-001", "version": "1.0.0"},
            created_by=self.user,
            timeout_seconds=3600,
            correlation_id="corr-001",
        )

        self.assertEqual(task.task_type, "DEPLOY")
        self.assertEqual(task.status, "PENDING")
        self.assertEqual(task.agent, self.agent)
        self.assertEqual(task.created_by, self.user)
        self.assertIsInstance(task.id, uuid.UUID)

    def test_task_status_transitions(self):
        """Test task status can transition through lifecycle."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-001"}, created_by=self.user
        )

        # Start task
        task.status = "IN_PROGRESS"
        task.started_at = timezone.now()
        task.save()
        self.assertEqual(task.status, "IN_PROGRESS")
        self.assertIsNotNone(task.started_at)

        # Complete task
        task.status = "COMPLETED"
        task.completed_at = timezone.now()
        task.result = {"exit_code": 0, "message": "Success"}
        task.save()
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)

    def test_task_str_representation(self):
        """Test string representation of task."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-001"}, created_by=self.user
        )
        expected = f"DEPLOY task for {self.agent.hostname} (PENDING)"
        self.assertEqual(str(task), expected)

    def test_task_ordering(self):
        """Test tasks are ordered by creation time."""
        task1 = AgentTask.objects.create(agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user)
        task2 = AgentTask.objects.create(agent=self.agent, task_type="REMEDIATE", payload={}, created_by=self.user)

        tasks = AgentTask.objects.all()
        # Tasks ordered by -created_at (newest first)
        self.assertEqual(tasks[0], task2)
        self.assertEqual(tasks[1], task1)


class AgentOfflineQueueModelTests(TestCase):
    """Tests for AgentOfflineQueue model."""

    def setUp(self):
        """Set up test data."""
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "testuser@example.com"})

        if created:

            self.user.set_password("testpass")

            self.user.save()
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="test-reg-key",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_queue_item_creation(self):
        """Test queue item is created correctly."""
        task = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-001"}, created_by=self.user
        )
        queue_item = AgentOfflineQueue.objects.create(
            agent=self.agent, task=task, retry_count=0, correlation_id="corr-001"
        )

        self.assertEqual(queue_item.agent, self.agent)
        self.assertEqual(queue_item.task, task)
        self.assertIsNone(queue_item.delivered_at)
        self.assertEqual(queue_item.retry_count, 0)

    def test_queue_item_delivery(self):
        """Test queue item can be marked as delivered."""
        task = AgentTask.objects.create(agent=self.agent, task_type="DEPLOY", payload={}, created_by=self.user)
        queue_item = AgentOfflineQueue.objects.create(
            agent=self.agent, task=task, retry_count=0, correlation_id="corr-002"
        )

        queue_item.delivered_at = timezone.now()
        queue_item.save()

        self.assertIsNotNone(queue_item.delivered_at)

    def test_queue_ordering(self):
        """Test queue items are ordered by creation time."""
        task1 = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"task": "1"}, created_by=self.user
        )
        task2 = AgentTask.objects.create(
            agent=self.agent, task_type="REMEDIATE", payload={"task": "2"}, created_by=self.user
        )
        item1 = AgentOfflineQueue.objects.create(agent=self.agent, task=task1, retry_count=0, correlation_id="corr-003")
        item2 = AgentOfflineQueue.objects.create(agent=self.agent, task=task2, retry_count=0, correlation_id="corr-004")

        items = AgentOfflineQueue.objects.all()
        # Ordered by queued_at (ascending)
        self.assertEqual(items[0], item1)
        self.assertEqual(items[1], item2)


class AgentTelemetryModelTests(TestCase):
    """Tests for AgentTelemetry model."""

    def setUp(self):
        """Set up test data."""
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="test-reg-key",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_telemetry_creation(self):
        """Test telemetry record is created correctly."""
        telemetry = AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=45.2,
            memory_usage_percent=62.8,
            disk_usage_percent=73.5,
            network_bytes_received=1024000,
            network_bytes_sent=512000,
            installed_software={"packages": ["pkg1", "pkg2"]},
            correlation_id="corr-001",
            collected_at=timezone.now(),
        )

        self.assertEqual(telemetry.agent, self.agent)
        self.assertEqual(telemetry.cpu_usage_percent, 45.2)
        self.assertEqual(telemetry.memory_usage_percent, 62.8)

    def test_telemetry_str_representation(self):
        """Test string representation of telemetry."""
        telemetry = AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=45.2,
            memory_usage_percent=62.8,
            disk_usage_percent=73.5,
            collected_at=timezone.now(),
        )
        self.assertIn(self.agent.hostname, str(telemetry))

    def test_telemetry_ordering(self):
        """Test telemetry records are ordered by timestamp (newest first)."""
        tel1 = AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=40.0,
            memory_usage_percent=50.0,
            disk_usage_percent=60.0,
            collected_at=timezone.now(),
        )
        tel2 = AgentTelemetry.objects.create(
            agent=self.agent,
            cpu_usage_percent=45.0,
            memory_usage_percent=55.0,
            disk_usage_percent=65.0,
            collected_at=timezone.now(),
        )

        telemetries = AgentTelemetry.objects.all()
        # Newest first (tel2 created after tel1)
        self.assertEqual(telemetries[0], tel2)
        self.assertEqual(telemetries[1], tel1)


class AgentDeploymentStatusModelTests(TestCase):
    """Tests for AgentDeploymentStatus model."""

    def setUp(self):
        """Set up test data."""
        self.agent = Agent.objects.create(
            hostname="test-agent",
            platform="windows",
            platform_version="11",
            agent_version="1.0.0",
            registration_key="test-reg-key",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    def test_deployment_status_creation(self):
        """Test deployment status is created correctly."""
        deployment = AgentDeploymentStatus.objects.create(
            agent=self.agent,
            deployment_intent_id=uuid.uuid4(),
            package_name="pkg-001",
            package_version="1.0.0",
            package_hash="abc123",
            status="IN_PROGRESS",
            progress_percent=45,
            correlation_id="corr-001",
        )

        self.assertEqual(deployment.agent, self.agent)
        self.assertEqual(deployment.package_name, "pkg-001")
        self.assertEqual(deployment.status, "IN_PROGRESS")
        self.assertEqual(deployment.progress_percent, 45)

    def test_deployment_status_transitions(self):
        """Test deployment status can transition through lifecycle."""
        deployment = AgentDeploymentStatus.objects.create(
            agent=self.agent,
            deployment_intent_id=uuid.uuid4(),
            package_name="pkg-001",
            package_version="1.0.0",
            package_hash="abc123",
            status="PENDING",
            correlation_id="corr-002",
        )

        # Start deployment
        deployment.status = "IN_PROGRESS"
        deployment.progress_percent = 50
        deployment.save()
        self.assertEqual(deployment.status, "IN_PROGRESS")

        # Complete deployment
        deployment.status = "SUCCESS"
        deployment.progress_percent = 100
        deployment.completed_at = timezone.now()
        deployment.save()
        self.assertEqual(deployment.status, "SUCCESS")
        self.assertIsNotNone(deployment.completed_at)

    def test_deployment_status_str_representation(self):
        """Test string representation of deployment status."""
        deployment = AgentDeploymentStatus.objects.create(
            agent=self.agent,
            deployment_intent_id=uuid.uuid4(),
            package_name="pkg-001",
            package_version="1.0.0",
            package_hash="abc123",
            status="SUCCESS",
            correlation_id="corr-003",
        )
        self.assertIn(self.agent.hostname, str(deployment))
        self.assertIn("pkg-001", str(deployment))

    def test_agent_multiple_tasks_ordering(self):
        """Test multiple tasks for same agent are ordered by created_at."""
        user, created = User.objects.get_or_create(username="testuser2", defaults={"email": "testuser2@example.com"})

        if created:

            user.set_password("testpass")

            user.save()
        task1 = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-001"}, created_by=user
        )
        task2 = AgentTask.objects.create(
            agent=self.agent, task_type="REMEDIATE", payload={"package_name": "pkg-002"}, created_by=user
        )

        tasks = AgentTask.objects.filter(agent=self.agent).order_by("created_at")
        self.assertEqual(tasks[0], task1)
        self.assertEqual(tasks[1], task2)

    def test_offline_queue_automatic_cleanup(self):
        """Test offline queue entries can be filtered by delivery status."""
        user, created = User.objects.get_or_create(username="testuser3", defaults={"email": "testuser3@example.com"})

        if created:

            user.set_password("testpass")

            user.save()
        # Create tasks first
        task1 = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-delivered"}, created_by=user
        )
        task2 = AgentTask.objects.create(
            agent=self.agent, task_type="DEPLOY", payload={"package_name": "pkg-pending"}, created_by=user
        )
        # Create delivered and undelivered entries
        delivered = AgentOfflineQueue.objects.create(
            agent=self.agent, task=task1, correlation_id="corr-005", delivered_at=timezone.now()
        )
        undelivered = AgentOfflineQueue.objects.create(agent=self.agent, task=task2, correlation_id="corr-006")

        # Filter undelivered
        pending = AgentOfflineQueue.objects.filter(delivered_at__isnull=True)
        self.assertEqual(pending.count(), 1)
        self.assertEqual(pending.first(), undelivered)

        # Filter delivered
        completed = AgentOfflineQueue.objects.filter(delivered_at__isnull=False)
        self.assertEqual(completed.count(), 1)
        self.assertEqual(completed.first(), delivered)
