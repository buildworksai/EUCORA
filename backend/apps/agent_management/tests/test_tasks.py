# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for agent management Celery tasks.

Target: 5 tests covering periodic tasks.
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.agent_management.models import Agent, AgentTask
from apps.agent_management.tasks import check_agent_health, timeout_stale_tasks

User = get_user_model()


class CheckAgentHealthTaskTests(TestCase):
    """Tests for check_agent_health periodic task."""

    def setUp(self):
        """Set up test data."""
        self.online_agent = Agent.objects.create(
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
            status="ONLINE",
            last_heartbeat_at=timezone.now(),
        )
        self.offline_agent = Agent.objects.create(
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
            status="ONLINE",
            last_heartbeat_at=timezone.now() - timedelta(minutes=10),
        )

    @patch("apps.agent_management.tasks.AgentManagementService")
    def test_check_agent_health_calls_service(self, mock_service_class):
        """Test check_agent_health task calls service method."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.check_agent_health.return_value = {"marked_offline": 1}

        result = check_agent_health()

        mock_service.check_agent_health.assert_called_once()
        self.assertEqual(result["marked_offline"], 1)

    def test_check_agent_health_marks_offline_agents(self):
        """Test check_agent_health task actually marks offline agents."""
        result = check_agent_health()

        self.online_agent.refresh_from_db()
        self.offline_agent.refresh_from_db()

        # Online agent should remain online
        self.assertEqual(self.online_agent.status, "ONLINE")

        # Offline agent should be marked offline
        self.assertEqual(self.offline_agent.status, "OFFLINE")
        self.assertEqual(result["marked_offline"], 1)


class TimeoutStaleTasksTaskTests(TestCase):
    """Tests for timeout_stale_tasks periodic task."""

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
            registration_key="reg-key-001",
            cpu_cores=4,
            memory_mb=8192,
            disk_gb=256,
            ip_address="10.0.1.1",
            mac_address="00:00:00:00:00:01",
        )

    @patch("apps.agent_management.tasks.AgentManagementService")
    def test_timeout_stale_tasks_calls_service(self, mock_service_class):
        """Test timeout_stale_tasks task calls service method."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.timeout_stale_tasks.return_value = {"timed_out": 2}

        result = timeout_stale_tasks()

        mock_service.timeout_stale_tasks.assert_called_once()
        self.assertEqual(result["timed_out"], 2)

    def test_timeout_stale_tasks_marks_old_tasks(self):
        """Test timeout_stale_tasks task marks stale tasks as TIMEOUT."""
        # Create a stale task (started 2 hours ago with 1 hour timeout)
        old_time = timezone.now() - timedelta(hours=2)
        stale_task = AgentTask.objects.create(
            agent=self.agent,
            task_type="DEPLOY",
            payload={"package_name": "pkg-001"},
            created_by=self.user,
            status="IN_PROGRESS",
            started_at=old_time,
            timeout_seconds=3600,  # 1 hour
        )

        # Create a recent task that should not timeout
        recent_task = AgentTask.objects.create(
            agent=self.agent,
            task_type="COLLECT",
            payload={},
            created_by=self.user,
            status="IN_PROGRESS",
            started_at=timezone.now(),
            timeout_seconds=3600,
        )

        result = timeout_stale_tasks()

        stale_task.refresh_from_db()
        recent_task.refresh_from_db()

        # Stale task should be marked as TIMEOUT
        self.assertEqual(stale_task.status, "TIMEOUT")
        self.assertIsNotNone(stale_task.error_message)

        # Recent task should remain IN_PROGRESS
        self.assertEqual(recent_task.status, "IN_PROGRESS")

        self.assertEqual(result["timed_out"], 1)

    def test_timeout_stale_tasks_no_stale_tasks(self):
        """Test timeout_stale_tasks when no tasks are stale."""
        # Create only recent tasks
        AgentTask.objects.create(
            agent=self.agent,
            task_type="DEPLOY",
            payload={},
            created_by=self.user,
            status="IN_PROGRESS",
            started_at=timezone.now(),
            timeout_seconds=3600,
        )

        result = timeout_stale_tasks()

        self.assertEqual(result["timed_out"], 0)
