# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Agent Management service layer.

Handles agent registration, task assignment, offline queue management,
and telemetry processing.
"""
import logging
from datetime import timedelta
from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.core.structured_logging import StructuredLogger

from .models import Agent, AgentDeploymentStatus, AgentOfflineQueue, AgentTask, AgentTelemetry

logger = StructuredLogger(__name__, user="system")


class AgentManagementService:
    """Service for agent lifecycle management."""

    @transaction.atomic
    def register_agent(
        self,
        hostname: str,
        platform: str,
        platform_version: str,
        agent_version: str,
        registration_key: str,
        cpu_cores: int,
        memory_mb: int,
        disk_gb: int,
        ip_address: str,
        mac_address: str,
        tags: Optional[Dict] = None,
        correlation_id: Optional[str] = None,
    ) -> Agent:
        """
        Register a new agent or update existing agent.

        Args:
            hostname: Agent hostname
            platform: Platform type (windows/macos/linux)
            platform_version: OS version
            agent_version: Agent software version
            registration_key: Unique registration key
            cpu_cores: Number of CPU cores
            memory_mb: Memory in MB
            disk_gb: Disk space in GB
            ip_address: IP address
            mac_address: MAC address
            tags: Optional tags dict
            correlation_id: Correlation ID for tracing

        Returns:
            Agent instance

        Raises:
            ValueError: If validation fails
        """
        logger.info(
            f"Registering agent: {hostname} ({platform})",
            extra={"hostname": hostname, "platform": platform, "correlation_id": correlation_id},
        )

        # Try to find existing agent by registration key or hostname
        agent = Agent.objects.filter(registration_key=registration_key).first()

        if agent:
            # Update existing agent
            agent.platform_version = platform_version
            agent.agent_version = agent_version
            agent.cpu_cores = cpu_cores
            agent.memory_mb = memory_mb
            agent.disk_gb = disk_gb
            agent.ip_address = ip_address
            agent.mac_address = mac_address
            agent.last_heartbeat_at = timezone.now()
            agent.status = "ONLINE"
            if tags:
                agent.tags.update(tags)
            agent.save()

            logger.info(
                f"Updated existing agent: {agent.id}",
                extra={"agent_id": str(agent.id), "correlation_id": correlation_id},
            )
        else:
            # Create new agent
            agent = Agent.objects.create(
                hostname=hostname,
                platform=platform,
                platform_version=platform_version,
                agent_version=agent_version,
                registration_key=registration_key,
                cpu_cores=cpu_cores,
                memory_mb=memory_mb,
                disk_gb=disk_gb,
                ip_address=ip_address,
                mac_address=mac_address,
                last_heartbeat_at=timezone.now(),
                status="ONLINE",
                tags=tags or {},
            )

            logger.security_event(
                event_type="AGENT_REGISTERED",
                severity="LOW",
                message=f"New agent registered: {hostname}",
                details={"agent_id": str(agent.id), "hostname": hostname, "platform": platform},
            )

        return agent

    def process_heartbeat(
        self,
        agent_id: str,
        correlation_id: Optional[str] = None,
    ) -> Dict:
        """
        Process agent heartbeat and return pending tasks.

        Args:
            agent_id: Agent UUID
            correlation_id: Correlation ID for tracing

        Returns:
            Dict with pending tasks

        Raises:
            Agent.DoesNotExist: If agent not found
        """
        agent = Agent.objects.get(id=agent_id)

        # Update heartbeat
        agent.last_heartbeat_at = timezone.now()
        agent.status = "ONLINE"
        agent.save(update_fields=["last_heartbeat_at", "status", "updated_at"])

        # Get pending tasks (limit to 10)
        pending_tasks = AgentTask.objects.filter(agent=agent, status="PENDING").select_related("created_by")[:10]

        # Mark tasks as assigned
        task_ids = [task.id for task in pending_tasks]
        AgentTask.objects.filter(id__in=task_ids).update(status="ASSIGNED", assigned_at=timezone.now())

        # Replay offline queue if any
        if agent.offline_queue.filter(delivered_at__isnull=True).exists():
            self._replay_offline_queue(agent, correlation_id)

        logger.connector_event(
            "agent_management",
            "HEARTBEAT_PROCESSED",
            "SUCCESS",
            {"agent_id": str(agent.id), "pending_tasks": len(pending_tasks)},
        )

        return {
            "status": "ok",
            "pending_tasks": len(pending_tasks),
            "tasks": [self._serialize_task(task) for task in pending_tasks],
        }

    def create_task(
        self,
        agent_id: str,
        task_type: str,
        payload: Dict,
        created_by=None,
        timeout_seconds: int = 3600,
        correlation_id: Optional[str] = None,
    ) -> AgentTask:
        """
        Create a new task for an agent.

        Args:
            agent_id: Agent UUID
            task_type: Type of task (DEPLOY, REMEDIATE, COLLECT, UPDATE, HEALTHCHECK)
            payload: Task payload dict
            created_by: User who created the task
            timeout_seconds: Task timeout in seconds
            correlation_id: Correlation ID for tracing

        Returns:
            AgentTask instance

        Raises:
            Agent.DoesNotExist: If agent not found
            ValueError: If validation fails
        """
        agent = Agent.objects.get(id=agent_id)

        task = AgentTask.objects.create(
            agent=agent,
            task_type=task_type,
            payload=payload,
            timeout_seconds=timeout_seconds,
            correlation_id=correlation_id or "",
            created_by=created_by,
            status="PENDING",
        )

        # If agent is offline, queue task
        if not agent.is_online:
            self._queue_task_for_offline_agent(agent, task, correlation_id)

        logger.audit_event(
            action="AGENT_TASK_CREATED",
            resource_type="AgentTask",
            resource_id=str(task.id),
            outcome="SUCCESS",
            details={"agent_id": str(agent.id), "task_type": task_type, "correlation_id": correlation_id},
        )

        return task

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None,
        exit_code: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> AgentTask:
        """
        Update task status.

        Args:
            task_id: Task UUID
            status: New status (IN_PROGRESS, COMPLETED, FAILED)
            result: Optional result dict
            error_message: Optional error message
            exit_code: Optional exit code
            correlation_id: Correlation ID for tracing

        Returns:
            Updated AgentTask instance

        Raises:
            AgentTask.DoesNotExist: If task not found
        """
        task = AgentTask.objects.select_related("agent").get(id=task_id)

        task.status = status
        if result is not None:
            task.result = result
        if error_message is not None:
            task.error_message = error_message
        if exit_code is not None:
            task.exit_code = exit_code

        if status == "IN_PROGRESS" and not task.started_at:
            task.started_at = timezone.now()
        elif status in ["COMPLETED", "FAILED", "TIMEOUT"]:
            task.completed_at = timezone.now()

        task.save()

        logger.connector_event(
            "agent_management",
            "TASK_STATUS_UPDATED",
            "SUCCESS",
            {"task_id": str(task.id), "agent_id": str(task.agent.id), "status": status, "task_type": task.task_type},
        )

        return task

    def store_telemetry(
        self,
        agent_id: str,
        cpu_usage_percent: float,
        memory_usage_percent: float,
        disk_usage_percent: float,
        network_bytes_sent: int = 0,
        network_bytes_received: int = 0,
        process_count: int = 0,
        installed_software: Optional[List] = None,
        collected_at=None,
        correlation_id: Optional[str] = None,
    ) -> AgentTelemetry:
        """
        Store telemetry data from agent.

        Args:
            agent_id: Agent UUID
            cpu_usage_percent: CPU usage percentage
            memory_usage_percent: Memory usage percentage
            disk_usage_percent: Disk usage percentage
            network_bytes_sent: Network bytes sent
            network_bytes_received: Network bytes received
            process_count: Number of processes
            installed_software: List of installed software
            collected_at: When telemetry was collected
            correlation_id: Correlation ID for tracing

        Returns:
            AgentTelemetry instance

        Raises:
            Agent.DoesNotExist: If agent not found
        """
        agent = Agent.objects.get(id=agent_id)

        telemetry = AgentTelemetry.objects.create(
            agent=agent,
            cpu_usage_percent=cpu_usage_percent,
            memory_usage_percent=memory_usage_percent,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_received=network_bytes_received,
            process_count=process_count,
            installed_software=installed_software or [],
            collected_at=collected_at or timezone.now(),
            correlation_id=correlation_id or "",
        )

        logger.connector_event(
            "agent_management",
            "TELEMETRY_STORED",
            "SUCCESS",
            {
                "agent_id": str(agent.id),
                "cpu": cpu_usage_percent,
                "memory": memory_usage_percent,
                "disk": disk_usage_percent,
            },
        )

        return telemetry

    def _queue_task_for_offline_agent(
        self,
        agent: Agent,
        task: AgentTask,
        correlation_id: Optional[str] = None,
    ):
        """Queue task for offline agent."""
        AgentOfflineQueue.objects.create(
            agent=agent,
            task=task,
            correlation_id=correlation_id or "",
            next_retry_at=timezone.now() + timedelta(minutes=5),
        )

        logger.connector_event(
            "agent_management", "TASK_QUEUED_OFFLINE", "SUCCESS", {"agent_id": str(agent.id), "task_id": str(task.id)}
        )

    def _replay_offline_queue(
        self,
        agent: Agent,
        correlation_id: Optional[str] = None,
    ):
        """Replay offline queue when agent comes online."""
        queued_items = (
            AgentOfflineQueue.objects.filter(agent=agent, delivered_at__isnull=True)
            .select_related("task")
            .order_by("queued_at")
        )

        delivered_count = 0
        for item in queued_items:
            try:
                # Mark as delivered
                item.delivered_at = timezone.now()
                item.save()

                # Update task status to PENDING so it gets picked up
                if item.task.status == "PENDING":
                    delivered_count += 1

            except Exception as e:
                item.retry_count += 1
                if item.retry_count >= item.max_retries:
                    # Max retries exceeded, mark task as failed
                    item.task.status = "FAILED"
                    item.task.error_message = f"Max retries exceeded in offline queue: {str(e)}"
                    item.task.completed_at = timezone.now()
                    item.task.save()
                else:
                    # Schedule next retry
                    item.next_retry_at = timezone.now() + timedelta(minutes=5 * (item.retry_count + 1))
                item.save()

        if delivered_count > 0:
            logger.connector_event(
                "agent_management",
                "OFFLINE_QUEUE_REPLAYED",
                "SUCCESS",
                {"agent_id": str(agent.id), "delivered_count": delivered_count},
            )

    def _serialize_task(self, task: AgentTask) -> Dict:
        """Serialize task for API response."""
        return {
            "id": str(task.id),
            "task_type": task.task_type,
            "payload": task.payload,
            "timeout_seconds": task.timeout_seconds,
            "correlation_id": task.correlation_id,
            "created_at": task.created_at.isoformat(),
        }

    def check_agent_health(self):
        """Check agent health and mark offline agents (run via Celery)."""
        cutoff = timezone.now() - timedelta(minutes=5)

        # Mark agents offline if no heartbeat for 5 minutes
        offline_count = Agent.objects.filter(last_heartbeat_at__lt=cutoff, status="ONLINE").update(status="OFFLINE")

        if offline_count > 0:
            logger.connector_event("agent_management", "AGENTS_MARKED_OFFLINE", "SUCCESS", {"count": offline_count})

        # Alert on critical offline agents
        critical_offline = Agent.objects.filter(status="OFFLINE", tags__critical=True)

        for agent in critical_offline:
            logger.security_event(
                event_type="CRITICAL_AGENT_OFFLINE",
                severity="HIGH",
                message=f"Critical agent offline: {agent.hostname}",
                details={"agent_id": str(agent.id), "hostname": agent.hostname},
            )

        return {"marked_offline": offline_count}

    def timeout_stale_tasks(self):
        """Timeout tasks that have been running too long (run via Celery)."""
        cutoff = timezone.now() - timedelta(hours=1)

        stale_tasks = AgentTask.objects.filter(status="IN_PROGRESS", started_at__lt=cutoff).select_related("agent")

        timeout_count = 0
        for task in stale_tasks:
            task.status = "TIMEOUT"
            task.completed_at = timezone.now()
            task.error_message = "Task timeout after 1 hour"
            task.save()
            timeout_count += 1

            logger.connector_event(
                "agent_management",
                "TASK_TIMEOUT",
                "FAILURE",
                {"task_id": str(task.id), "agent_id": str(task.agent.id), "task_type": task.task_type},
            )

        if timeout_count > 0:
            logger.connector_event("agent_management", "TASKS_TIMED_OUT", "SUCCESS", {"count": timeout_count})

        return {"timed_out": timeout_count}
