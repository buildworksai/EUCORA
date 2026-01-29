# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Agent Management models for endpoint agent orchestration.

Manages agent registration, task assignment, offline queue, and telemetry.
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Agent(models.Model):
    """Endpoint agent registration and status tracking."""

    PLATFORM_CHOICES = [
        ("windows", "Windows"),
        ("macos", "macOS"),
        ("linux", "Linux"),
    ]

    STATUS_CHOICES = [
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
        ("DEGRADED", "Degraded"),
        ("UNKNOWN", "Unknown"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hostname = models.CharField(max_length=255, db_index=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_version = models.CharField(max_length=100)
    agent_version = models.CharField(max_length=50)

    # Registration
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat_at = models.DateTimeField(default=timezone.now)
    registration_key = models.CharField(max_length=255, unique=True, db_index=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UNKNOWN", db_index=True)
    last_error = models.TextField(null=True, blank=True)

    # Hardware info
    cpu_cores = models.IntegerField(default=0)
    memory_mb = models.IntegerField(default=0)
    disk_gb = models.IntegerField(default=0)

    # Network info
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17)

    # Metadata (JSON field for tags, custom attributes)
    tags = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agents"
        ordering = ["-last_heartbeat_at"]
        indexes = [
            models.Index(fields=["platform", "status"]),
            models.Index(fields=["last_heartbeat_at"]),
            models.Index(fields=["hostname"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.platform})"

    @property
    def is_online(self):
        """Check if agent is online (heartbeat within 5 minutes)."""
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(minutes=5)
        return self.last_heartbeat_at >= cutoff


class AgentTask(models.Model):
    """Tasks assigned to agents for execution."""

    TASK_TYPE_CHOICES = [
        ("DEPLOY", "Package Deployment"),
        ("REMEDIATE", "Remediation Script"),
        ("COLLECT", "Telemetry Collection"),
        ("UPDATE", "Agent Update"),
        ("HEALTHCHECK", "Health Check"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ASSIGNED", "Assigned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("TIMEOUT", "Timeout"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="tasks")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)

    # Task payload (deployment intent, script, etc.)
    payload = models.JSONField(default=dict)

    # Execution timing
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    timeout_seconds = models.IntegerField(default=3600)

    # Results
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agent", "status"]),
            models.Index(fields=["task_type", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.task_type} task for {self.agent.hostname} ({self.status})"


class AgentOfflineQueue(models.Model):
    """Offline queue for agents with intermittent connectivity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="offline_queue")
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE)

    # Queue management
    queued_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)

    class Meta:
        db_table = "agent_offline_queue"
        ordering = ["queued_at"]
        indexes = [
            models.Index(fields=["agent", "delivered_at"]),
            models.Index(fields=["delivered_at"]),
            models.Index(fields=["next_retry_at"]),
        ]

    def __str__(self):
        return f"Queue item for {self.agent.hostname} - Task {self.task.id}"


class AgentTelemetry(models.Model):
    """Telemetry data collected from agents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="telemetry")

    # Resource metrics
    cpu_usage_percent = models.FloatField()
    memory_usage_percent = models.FloatField()
    disk_usage_percent = models.FloatField()

    # Network metrics
    network_bytes_sent = models.BigIntegerField(default=0)
    network_bytes_received = models.BigIntegerField(default=0)

    # Process metrics
    process_count = models.IntegerField(default=0)

    # Software inventory (JSON list of installed packages)
    installed_software = models.JSONField(default=list, blank=True)

    # Timestamp
    collected_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)

    class Meta:
        db_table = "agent_telemetry"
        ordering = ["-collected_at"]
        indexes = [
            models.Index(fields=["agent", "collected_at"]),
            models.Index(fields=["collected_at"]),
        ]

    def __str__(self):
        return f"Telemetry for {self.agent.hostname} at {self.collected_at}"


class AgentDeploymentStatus(models.Model):
    """Track deployment status per agent."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("DOWNLOADING", "Downloading"),
        ("INSTALLING", "Installing"),
        ("INSTALLED", "Installed"),
        ("FAILED", "Failed"),
        ("ROLLED_BACK", "Rolled Back"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="deployments")
    deployment_intent_id = models.UUIDField(db_index=True)  # Reference to DeploymentIntent

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    progress_percent = models.IntegerField(default=0)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    error_message = models.TextField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    # Package info
    package_name = models.CharField(max_length=255)
    package_version = models.CharField(max_length=100)
    package_hash = models.CharField(max_length=64)

    # Audit
    correlation_id = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_deployment_status"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agent", "status"]),
            models.Index(fields=["deployment_intent_id", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.package_name} on {self.agent.hostname} ({self.status})"
