# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Planning Agent models for E20 enhancement.

Implements deployment planning, ring assignment, blast radius analysis,
and rollback planning with schedule optimization.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class DeploymentPlan(TimeStampedModel, CorrelationIdModel):
    """AI-generated deployment plan."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        EXECUTING = "executing", "Executing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    application = models.ForeignKey(
        "application_portfolio.Application", on_delete=models.CASCADE, related_name="deployment_plans"
    )
    version = models.CharField(max_length=100)
    target_scope = models.JSONField(default=dict, help_text="Departments, regions, groups")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    # AI Generation
    input_request = models.TextField(help_text="Original natural language request")
    reasoning = models.TextField(help_text="AI reasoning for plan decisions")

    # Risk Assessment
    overall_risk_score = models.FloatField(help_text="Overall risk score (0-100)")
    risk_factors = models.JSONField(default=dict, help_text="Risk factor breakdown")

    # Approval
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_plans"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_plans"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Deployment Plan"
        verbose_name_plural = "Deployment Plans"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.application.name}"


class RingAssignment(TimeStampedModel):
    """Device assignment to deployment ring."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PAUSED = "paused", "Paused"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(DeploymentPlan, on_delete=models.CASCADE, related_name="rings")
    ring_number = models.IntegerField(db_index=True, help_text="Ring number (0-4)")
    ring_name = models.CharField(max_length=50, help_text="Ring name (e.g., 'Ring 1 - IT Canary')")
    device_count = models.IntegerField(default=0)
    device_criteria = models.JSONField(default=dict, help_text="How devices were selected")
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    success_threshold = models.FloatField(default=98.0, help_text="Required % for promotion")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        verbose_name = "Ring Assignment"
        verbose_name_plural = "Ring Assignments"
        ordering = ["plan", "ring_number"]
        indexes = [
            models.Index(fields=["plan", "ring_number"]),
            models.Index(fields=["status", "scheduled_start"]),
        ]

    def __str__(self):
        return f"{self.plan.name} - {self.ring_name}"


class RingDevice(TimeStampedModel):
    """Device in a ring."""

    class Criticality(models.TextChoices):
        VIP = "vip", "VIP"
        STANDARD = "standard", "Standard"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ring = models.ForeignKey(RingAssignment, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=255)
    user_principal = models.CharField(max_length=255, null=True, blank=True)
    selection_reason = models.CharField(max_length=255, help_text="Why this device was selected")
    health_score = models.FloatField(null=True, blank=True, help_text="Device health score (0-100)")
    criticality = models.CharField(max_length=20, choices=Criticality.choices, default=Criticality.STANDARD)

    class Meta:
        verbose_name = "Ring Device"
        verbose_name_plural = "Ring Devices"
        ordering = ["ring", "device_name"]
        indexes = [
            models.Index(fields=["ring", "device_id"]),
            models.Index(fields=["criticality"]),
        ]

    def __str__(self):
        return f"{self.ring.ring_name} - {self.device_name}"


class DeploymentWindow(TimeStampedModel):
    """Allowed deployment windows."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    day_of_week = models.JSONField(default=list, help_text="[0,1,2,3,4] for Mon-Fri")
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, default="UTC")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Deployment Window"
        verbose_name_plural = "Deployment Windows"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class ChangeFreezePeriod(TimeStampedModel):
    """Change freeze periods."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    reason = models.TextField()
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    scope = models.JSONField(default=dict, help_text="Affected departments, regions")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Change Freeze Period"
        verbose_name_plural = "Change Freeze Periods"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class BlastRadiusAnalysis(TimeStampedModel, CorrelationIdModel):
    """Blast radius analysis for a deployment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(DeploymentPlan, on_delete=models.CASCADE, related_name="blast_radius_analyses")
    total_users_affected = models.IntegerField(default=0)
    vip_users_affected = models.IntegerField(default=0)
    departments_affected = models.JSONField(default=list)
    regions_affected = models.JSONField(default=list)
    critical_systems_affected = models.JSONField(default=list)
    productivity_impact_score = models.FloatField(help_text="Impact score (0-100)")
    recommendations = models.JSONField(default=list)

    class Meta:
        verbose_name = "Blast Radius Analysis"
        verbose_name_plural = "Blast Radius Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["plan"]),
        ]

    def __str__(self):
        return f"{self.plan.name} - Blast Radius"


class RollbackPlan(TimeStampedModel):
    """Rollback plan for deployment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment_plan = models.OneToOneField(DeploymentPlan, on_delete=models.CASCADE, related_name="rollback_plan")
    trigger_conditions = models.JSONField(default=list, help_text="Conditions that trigger rollback")
    rollback_steps = models.JSONField(default=list, help_text="Steps to execute rollback")
    estimated_duration_minutes = models.IntegerField(help_text="Estimated rollback duration")
    requires_cab_approval = models.BooleanField(default=False)
    tested = models.BooleanField(default=False)
    tested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Rollback Plan"
        verbose_name_plural = "Rollback Plans"

    def __str__(self):
        return f"Rollback Plan for {self.deployment_plan.name}"
