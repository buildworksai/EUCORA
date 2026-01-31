# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SRE Agent models for E18 enhancement.

Implements monitoring integration, health checks, SLO tracking,
self-healing automation, and runbook execution.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class MonitoringPlatform(TimeStampedModel):
    """Configured monitoring platform."""

    class PlatformType(models.TextChoices):
        PROMETHEUS = "prometheus", "Prometheus"
        DATADOG = "datadog", "Datadog"
        AZURE_MONITOR = "azure_monitor", "Azure Monitor"
        NEWRELIC = "newrelic", "New Relic"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    platform_type = models.CharField(max_length=50, choices=PlatformType.choices, db_index=True)
    connection_config = models.JSONField(default=dict, help_text="Platform connection configuration")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Monitoring Platform"
        verbose_name_plural = "Monitoring Platforms"
        indexes = [
            models.Index(fields=["platform_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.platform_type})"


class HealthEndpoint(TimeStampedModel):
    """Application health check endpoint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    application = models.ForeignKey(
        "application_portfolio.Application", null=True, blank=True, on_delete=models.SET_NULL
    )
    url = models.URLField()
    method = models.CharField(max_length=10, default="GET")
    expected_status = models.IntegerField(default=200)
    timeout_seconds = models.IntegerField(default=30)
    check_interval_minutes = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Health Endpoint"
        verbose_name_plural = "Health Endpoints"
        indexes = [
            models.Index(fields=["is_active", "application"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.url})"


class HealthCheckResult(TimeStampedModel):
    """Health check result."""

    class Status(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        UNHEALTHY = "unhealthy", "Unhealthy"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(HealthEndpoint, on_delete=models.CASCADE, related_name="check_results")
    check_time = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Health Check Result"
        verbose_name_plural = "Health Check Results"
        ordering = ["-check_time"]
        indexes = [
            models.Index(fields=["endpoint", "check_time"]),
            models.Index(fields=["status", "check_time"]),
        ]

    def __str__(self):
        return f"{self.endpoint.name} - {self.status} ({self.check_time})"


class SLODefinition(TimeStampedModel):
    """Service Level Objective definition."""

    class SLOType(models.TextChoices):
        AVAILABILITY = "availability", "Availability"
        LATENCY = "latency", "Latency"
        ERROR_RATE = "error_rate", "Error Rate"
        THROUGHPUT = "throughput", "Throughput"

    class MeasurementWindow(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    service_name = models.CharField(max_length=255, db_index=True)
    slo_type = models.CharField(max_length=50, choices=SLOType.choices)
    target_value = models.FloatField(help_text="Target value (e.g., 99.9 for availability %)")
    target_unit = models.CharField(max_length=20, help_text="Unit (percent, ms, per_second)")
    measurement_window = models.CharField(max_length=20, choices=MeasurementWindow.choices)
    error_budget_policy = models.JSONField(null=True, blank=True, help_text="Error budget policy configuration")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "SLO Definition"
        verbose_name_plural = "SLO Definitions"
        indexes = [
            models.Index(fields=["service_name", "is_active"]),
            models.Index(fields=["slo_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.service_name})"


class SLOMetric(TimeStampedModel):
    """SLO measurement."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slo = models.ForeignKey(SLODefinition, on_delete=models.CASCADE, related_name="metrics")
    measurement_time = models.DateTimeField(default=timezone.now, db_index=True)
    actual_value = models.FloatField()
    target_met = models.BooleanField()
    error_budget_remaining = models.FloatField(null=True, blank=True)
    burn_rate = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "SLO Metric"
        verbose_name_plural = "SLO Metrics"
        ordering = ["-measurement_time"]
        indexes = [
            models.Index(fields=["slo", "measurement_time"]),
            models.Index(fields=["target_met", "measurement_time"]),
        ]

    def __str__(self):
        return f"{self.slo.name} - {self.actual_value} ({self.measurement_time})"


class SelfHealingRule(TimeStampedModel):
    """Self-healing automation rule."""

    class TriggerType(models.TextChoices):
        THRESHOLD = "threshold", "Threshold"
        PATTERN = "pattern", "Pattern"
        SCHEDULE = "schedule", "Schedule"
        ALERT = "alert", "Alert"

    class TargetType(models.TextChoices):
        SERVICE = "service", "Service"
        PROCESS = "process", "Process"
        DISK = "disk", "Disk"
        CONNECTION = "connection", "Connection"

    class ScriptType(models.TextChoices):
        POWERSHELL = "powershell", "PowerShell"
        BASH = "bash", "Bash"
        PYTHON = "python", "Python"

    class RiskLevel(models.TextChoices):
        R1 = "R1", "R1 - Low (Auto-execute allowed)"
        R2 = "R2", "R2 - Medium (Policy-dependent approval)"
        R3 = "R3", "R3 - High (Mandatory human approval)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    trigger_type = models.CharField(max_length=50, choices=TriggerType.choices)
    trigger_config = models.JSONField(default=dict, help_text="Trigger configuration")
    target_type = models.CharField(max_length=50, choices=TargetType.choices)
    target_config = models.JSONField(default=dict, help_text="Target configuration")
    remediation_script = models.TextField(help_text="Remediation script content")
    script_type = models.CharField(max_length=20, choices=ScriptType.choices, default=ScriptType.POWERSHELL)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.R2)
    requires_approval = models.BooleanField(default=False)
    max_executions_per_hour = models.IntegerField(default=3)
    cooldown_minutes = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Self-Healing Rule"
        verbose_name_plural = "Self-Healing Rules"
        indexes = [
            models.Index(fields=["is_active", "trigger_type"]),
            models.Index(fields=["risk_level", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class SelfHealingExecution(TimeStampedModel, CorrelationIdModel):
    """Self-healing execution record."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        EXECUTING = "executing", "Executing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(SelfHealingRule, on_delete=models.CASCADE, related_name="executions")
    trigger_event = models.JSONField(default=dict, help_text="Event that triggered execution")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_healing_executions",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    metrics_before = models.JSONField(null=True, blank=True, help_text="Metrics before remediation")
    metrics_after = models.JSONField(null=True, blank=True, help_text="Metrics after remediation")

    class Meta:
        verbose_name = "Self-Healing Execution"
        verbose_name_plural = "Self-Healing Executions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rule", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.rule.name} - {self.status} ({self.created_at})"


class Runbook(TimeStampedModel):
    """Operational runbook."""

    class AutomationLevel(models.TextChoices):
        MANUAL = "manual", "Manual"
        SEMI_AUTO = "semi_auto", "Semi-Automated"
        FULL_AUTO = "full_auto", "Fully Automated"

    class RiskLevel(models.TextChoices):
        R1 = "R1", "R1 - Low (Auto-execute allowed)"
        R2 = "R2", "R2 - Medium (Policy-dependent approval)"
        R3 = "R3", "R3 - High (Mandatory human approval)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, db_index=True)
    steps = models.JSONField(default=list, help_text="List of runbook steps")
    automation_level = models.CharField(max_length=20, choices=AutomationLevel.choices)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.R2)
    estimated_duration_minutes = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Runbook"
        verbose_name_plural = "Runbooks"
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["risk_level", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"


class RunbookExecution(TimeStampedModel, CorrelationIdModel):
    """Runbook execution record."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    runbook = models.ForeignKey(Runbook, on_delete=models.CASCADE, related_name="executions")
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="runbook_executions"
    )
    trigger_reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    current_step = models.IntegerField(default=0)
    step_results = models.JSONField(default=list, help_text="Results for each step")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    evidence = models.JSONField(default=list, help_text="Evidence collected during execution")

    class Meta:
        verbose_name = "Runbook Execution"
        verbose_name_plural = "Runbook Executions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["runbook", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.runbook.name} - {self.status} ({self.created_at})"
