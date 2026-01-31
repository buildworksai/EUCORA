# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CMDB Integration models for E10 enhancement.

Implements ServiceNow CMDB connection, table mappings, validation rules,
sync records, and discrepancy tracking.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class CMDBConnection(TimeStampedModel):
    """
    ServiceNow CMDB connection configuration.

    Stores connection details for ServiceNow instances including
    authentication credentials (encrypted in production).
    """

    class AuthType(models.TextChoices):
        BASIC = "basic", "Basic Authentication"
        OAUTH = "oauth", "OAuth 2.0"
        API_KEY = "api_key", "API Key"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Display name for this connection")
    instance_url = models.URLField(help_text="ServiceNow instance URL (e.g., https://instance.service-now.com)")
    auth_type = models.CharField(max_length=50, choices=AuthType.choices, default=AuthType.BASIC)
    credentials = models.JSONField(
        default=dict,
        help_text="Authentication credentials (encrypted in production)",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "CMDB Connection"
        verbose_name_plural = "CMDB Connections"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.instance_url})"


class CMDBTableMapping(TimeStampedModel):
    """
    Mapping between source systems and CMDB tables.

    Defines how data from SCCM, Intune, Discovery, or other sources
    maps to ServiceNow CMDB table fields.
    """

    class SourceType(models.TextChoices):
        SCCM = "sccm", "SCCM"
        INTUNE = "intune", "Intune"
        DISCOVERY = "discovery", "ServiceNow Discovery"
        DEPLOYMENT = "deployment", "Deployment Pipeline"
        MONITORING = "monitoring", "Monitoring System"
        MANUAL = "manual", "Manual Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(CMDBConnection, on_delete=models.CASCADE, related_name="table_mappings")
    source_type = models.CharField(max_length=50, choices=SourceType.choices, db_index=True)
    source_table = models.CharField(max_length=255, help_text="Source system table/entity name")
    cmdb_table = models.CharField(max_length=255, help_text="Target CMDB table (e.g., cmdb_ci_computer)")
    field_mappings = models.JSONField(
        default=dict,
        help_text="Field mapping configuration: {source_field: cmdb_field}",
    )
    sync_enabled = models.BooleanField(default=True, db_index=True)
    sync_direction = models.CharField(
        max_length=20,
        choices=[
            ("source_to_cmdb", "Source → CMDB"),
            ("cmdb_to_source", "CMDB → Source"),
            ("bidirectional", "Bidirectional"),
        ],
        default="source_to_cmdb",
    )
    priority = models.IntegerField(
        default=100,
        help_text="Priority for conflict resolution (lower = higher priority)",
    )

    class Meta:
        verbose_name = "CMDB Table Mapping"
        verbose_name_plural = "CMDB Table Mappings"
        ordering = ["priority", "source_type"]
        indexes = [
            models.Index(fields=["connection", "source_type"]),
            models.Index(fields=["cmdb_table"]),
            models.Index(fields=["sync_enabled"]),
        ]
        unique_together = [["connection", "source_type", "source_table", "cmdb_table"]]

    def __str__(self) -> str:
        return f"{self.source_type} → {self.cmdb_table}"


class CMDBValidationRule(TimeStampedModel):
    """
    Validation rules for CMDB data quality.

    Defines rules for field completeness, data type validation,
    referential integrity, and custom business logic.
    """

    class RuleType(models.TextChoices):
        REQUIRED = "required", "Required Field"
        FORMAT = "format", "Format Validation"
        REFERENCE = "reference", "Referential Integrity"
        RANGE = "range", "Value Range"
        REGEX = "regex", "Regular Expression"
        CUSTOM = "custom", "Custom Rule"

    class Severity(models.TextChoices):
        ERROR = "error", "Error"
        WARNING = "warning", "Warning"
        INFO = "info", "Info"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cmdb_table = models.CharField(max_length=255, db_index=True)
    field_name = models.CharField(max_length=255, blank=True, help_text="Field to validate (empty for table-level)")
    rule_type = models.CharField(max_length=50, choices=RuleType.choices)
    rule_config = models.JSONField(
        default=dict,
        help_text="Rule configuration (depends on rule_type)",
    )
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    is_active = models.BooleanField(default=True, db_index=True)
    auto_fix = models.BooleanField(
        default=False,
        help_text="Whether to automatically apply fix when possible",
    )

    class Meta:
        verbose_name = "CMDB Validation Rule"
        verbose_name_plural = "CMDB Validation Rules"
        ordering = ["cmdb_table", "field_name", "severity"]
        indexes = [
            models.Index(fields=["cmdb_table", "is_active"]),
            models.Index(fields=["rule_type"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self) -> str:
        field_str = f".{self.field_name}" if self.field_name else ""
        return f"{self.name} ({self.cmdb_table}{field_str})"


class CMDBSyncRecord(TimeStampedModel, CorrelationIdModel):
    """
    Record of CMDB synchronization operations.

    Tracks each sync run with statistics, status, and error details.
    """

    class SyncType(models.TextChoices):
        FULL = "full", "Full Sync"
        INCREMENTAL = "incremental", "Incremental Sync"
        TARGETED = "targeted", "Targeted Sync"
        VALIDATION = "validation", "Validation Only"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(CMDBConnection, on_delete=models.CASCADE, related_name="sync_records")
    sync_type = models.CharField(max_length=50, choices=SyncType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Statistics
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_skipped = models.IntegerField(default=0)
    validation_errors = models.IntegerField(default=0)

    # Error tracking
    errors = models.JSONField(default=list)

    # Quality metrics
    quality_score = models.FloatField(null=True, blank=True, help_text="Overall data quality score (0-100)")

    # Initiator
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cmdb_sync_records",
    )

    class Meta:
        verbose_name = "CMDB Sync Record"
        verbose_name_plural = "CMDB Sync Records"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["connection", "status"]),
            models.Index(fields=["sync_type", "started_at"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sync_type} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate sync duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class CMDBDiscrepancy(TimeStampedModel):
    """
    Detected discrepancies between source systems and CMDB.

    Tracks mismatches, missing data, and orphaned records
    with recommended actions and resolution status.
    """

    class DiscrepancyType(models.TextChoices):
        MISSING = "missing", "Missing in CMDB"
        MISMATCH = "mismatch", "Value Mismatch"
        ORPHAN = "orphan", "Orphan Record"
        DUPLICATE = "duplicate", "Duplicate Record"
        STALE = "stale", "Stale Data"
        INCOMPLETE = "incomplete", "Incomplete Record"

    class RecommendedAction(models.TextChoices):
        CREATE = "create", "Create CI"
        UPDATE = "update", "Update CI"
        DELETE = "delete", "Delete CI"
        MERGE = "merge", "Merge Records"
        REVIEW = "review", "Manual Review"
        IGNORE = "ignore", "Ignore"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        APPLIED = "applied", "Applied"
        IGNORED = "ignored", "Ignored"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_record = models.ForeignKey(CMDBSyncRecord, on_delete=models.CASCADE, related_name="discrepancies")

    # CI identification
    ci_sys_id = models.CharField(max_length=100, blank=True, help_text="ServiceNow CI sys_id")
    ci_name = models.CharField(max_length=255)
    ci_class = models.CharField(max_length=255, help_text="CMDB class/table")

    # Discrepancy details
    discrepancy_type = models.CharField(max_length=50, choices=DiscrepancyType.choices, db_index=True)
    field_name = models.CharField(max_length=255, blank=True)
    source_value = models.TextField(null=True, blank=True)
    cmdb_value = models.TextField(null=True, blank=True)
    source_system = models.CharField(max_length=50, blank=True)

    # Recommendation
    recommended_action = models.CharField(max_length=50, choices=RecommendedAction.choices)
    confidence_score = models.FloatField(default=0.0, help_text="Confidence in recommendation (0-1)")

    # Resolution
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_cmdb_discrepancies",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "CMDB Discrepancy"
        verbose_name_plural = "CMDB Discrepancies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sync_record", "status"]),
            models.Index(fields=["discrepancy_type", "status"]),
            models.Index(fields=["ci_sys_id"]),
            models.Index(fields=["ci_class", "status"]),
            models.Index(fields=["recommended_action"]),
        ]

    def __str__(self) -> str:
        return f"{self.ci_name} - {self.discrepancy_type} ({self.status})"


class CMDBDataQualityReport(TimeStampedModel, CorrelationIdModel):
    """
    Data quality report for CMDB.

    Aggregates quality metrics across tables and provides
    trend data for quality improvement tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(CMDBConnection, on_delete=models.CASCADE, related_name="quality_reports")
    sync_record = models.ForeignKey(
        CMDBSyncRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="quality_reports"
    )

    # Quality scores
    overall_score = models.FloatField(help_text="Overall quality score (0-100)")
    completeness_score = models.FloatField(help_text="Data completeness score (0-100)")
    accuracy_score = models.FloatField(help_text="Data accuracy score (0-100)")
    consistency_score = models.FloatField(help_text="Data consistency score (0-100)")
    timeliness_score = models.FloatField(help_text="Data timeliness score (0-100)")

    # Statistics
    total_cis = models.IntegerField(default=0)
    cis_with_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)

    # Breakdown by table
    table_scores = models.JSONField(default=dict, help_text="Quality scores per CMDB table")

    class Meta:
        verbose_name = "CMDB Data Quality Report"
        verbose_name_plural = "CMDB Data Quality Reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["connection", "created_at"]),
            models.Index(fields=["overall_score"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"Quality Report {self.overall_score:.1f}% ({self.created_at.strftime('%Y-%m-%d')})"
