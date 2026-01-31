# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SLA Governance Agent models for E19 enhancement.

Implements SLA definition, KPI tracking, compliance monitoring,
and breach detection with ServiceNow integration.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class ServiceCatalogItem(TimeStampedModel):
    """Service catalog item for SLA attachment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, db_index=True)
    owner = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default="active", db_index=True)
    servicenow_sys_id = models.CharField(max_length=100, null=True, blank=True, unique=True)

    class Meta:
        verbose_name = "Service Catalog Item"
        verbose_name_plural = "Service Catalog Items"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self):
        return self.name


class SLADefinition(TimeStampedModel, CorrelationIdModel):
    """Service Level Agreement definition."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    service = models.ForeignKey(ServiceCatalogItem, on_delete=models.CASCADE, related_name="slas")
    version = models.CharField(max_length=50)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    # Natural language source
    original_request = models.TextField(null=True, blank=True)

    # Approval
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_slas"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_slas"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "SLA Definition"
        verbose_name_plural = "SLA Definitions"
        ordering = ["-effective_from", "name"]
        indexes = [
            models.Index(fields=["service", "status"]),
            models.Index(fields=["status", "effective_from"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class SLATarget(TimeStampedModel):
    """SLA target/objective."""

    class MetricType(models.TextChoices):
        AVAILABILITY = "availability", "Availability"
        RESPONSE_TIME = "response_time", "Response Time"
        RESOLUTION_TIME = "resolution_time", "Resolution Time"
        QUALITY = "quality", "Quality"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE, related_name="targets")
    name = models.CharField(max_length=255)
    metric_type = models.CharField(max_length=50, choices=MetricType.choices, db_index=True)
    target_value = models.FloatField()
    target_unit = models.CharField(max_length=20)  # percent, hours, minutes, score
    measurement_period = models.CharField(max_length=20, default="monthly")  # daily, weekly, monthly
    applies_to = models.JSONField(null=True, blank=True, help_text="Time windows, customer segments, etc.")

    class Meta:
        verbose_name = "SLA Target"
        verbose_name_plural = "SLA Targets"
        ordering = ["sla", "metric_type"]

    def __str__(self):
        return f"{self.sla.name} - {self.name}"


class KPIDefinition(TimeStampedModel):
    """Key Performance Indicator definition."""

    class Direction(models.TextChoices):
        HIGHER_BETTER = "higher_better", "Higher is Better"
        LOWER_BETTER = "lower_better", "Lower is Better"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    formula = models.TextField(help_text="Formula or calculation method")
    data_sources = models.JSONField(default=list, help_text="List of data sources")
    unit = models.CharField(max_length=50)
    direction = models.CharField(max_length=20, choices=Direction.choices, default=Direction.HIGHER_BETTER)
    thresholds = models.JSONField(default=dict, help_text="Warning and critical thresholds")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "KPI Definition"
        verbose_name_plural = "KPI Definitions"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class SLAKPILink(TimeStampedModel):
    """Link between SLA target and KPI."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sla_target = models.ForeignKey(SLATarget, on_delete=models.CASCADE, related_name="kpi_links")
    kpi = models.ForeignKey(KPIDefinition, on_delete=models.CASCADE, related_name="sla_links")
    weight = models.FloatField(default=1.0, help_text="Weight for composite calculations")

    class Meta:
        verbose_name = "SLA-KPI Link"
        verbose_name_plural = "SLA-KPI Links"
        unique_together = [["sla_target", "kpi"]]

    def __str__(self):
        return f"{self.sla_target.name} -> {self.kpi.name}"


class KPIMeasurement(TimeStampedModel):
    """KPI measurement value."""

    class Status(models.TextChoices):
        GREEN = "green", "Green"
        YELLOW = "yellow", "Yellow"
        RED = "red", "Red"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kpi = models.ForeignKey(KPIDefinition, on_delete=models.CASCADE, related_name="measurements")
    measurement_time = models.DateTimeField(db_index=True)
    value = models.FloatField()
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    data_points = models.JSONField(null=True, blank=True, help_text="Raw data points used in calculation")

    class Meta:
        verbose_name = "KPI Measurement"
        verbose_name_plural = "KPI Measurements"
        ordering = ["-measurement_time"]
        indexes = [
            models.Index(fields=["kpi", "measurement_time"]),
            models.Index(fields=["status", "measurement_time"]),
        ]

    def __str__(self):
        return f"{self.kpi.name} @ {self.measurement_time}"


class SLACompliance(TimeStampedModel, CorrelationIdModel):
    """SLA compliance record."""

    class Status(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        AT_RISK = "at_risk", "At Risk"
        BREACHED = "breached", "Breached"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE, related_name="compliance_records")
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    overall_compliance = models.FloatField(help_text="Overall compliance percentage")
    target_compliances = models.JSONField(default=dict, help_text="Per-target compliance percentages")
    breach_count = models.IntegerField(default=0)
    near_miss_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)

    class Meta:
        verbose_name = "SLA Compliance"
        verbose_name_plural = "SLA Compliance Records"
        ordering = ["-period_end", "-period_start"]
        indexes = [
            models.Index(fields=["sla", "period_start", "period_end"]),
            models.Index(fields=["status", "period_end"]),
        ]

    def __str__(self):
        return f"{self.sla.name} - {self.period_start} to {self.period_end}"


class SLABreach(TimeStampedModel, CorrelationIdModel):
    """SLA breach incident."""

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE, related_name="breaches")
    target = models.ForeignKey(SLATarget, on_delete=models.CASCADE, related_name="breaches")
    breach_time = models.DateTimeField(db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
    target_value = models.FloatField()
    actual_value = models.FloatField()
    root_cause = models.TextField(null=True, blank=True)
    remediation = models.TextField(null=True, blank=True)
    servicenow_incident = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "SLA Breach"
        verbose_name_plural = "SLA Breaches"
        ordering = ["-breach_time"]
        indexes = [
            models.Index(fields=["sla", "breach_time"]),
            models.Index(fields=["severity", "breach_time"]),
        ]

    def __str__(self):
        return f"{self.sla.name} breach @ {self.breach_time}"


class SLATemplate(TimeStampedModel):
    """SLA template for quick creation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, db_index=True)
    default_targets = models.JSONField(default=list, help_text="Default SLA targets")
    variables = models.JSONField(default=dict, help_text="Placeholders to fill")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "SLA Template"
        verbose_name_plural = "SLA Templates"
        ordering = ["category", "name"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.name
