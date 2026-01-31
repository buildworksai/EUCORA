# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Discovery Agent models for E14 enhancement.

Implements discovery sources, runs, discovered applications,
normalized applications, and gap analysis.
"""
import hashlib
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class DiscoverySource(TimeStampedModel):
    """
    Configured discovery data sources.

    Supports SCCM, Intune, AD, CMDB, and manual spreadsheet imports.
    """

    class SourceType(models.TextChoices):
        SCCM = "sccm", "SCCM"
        INTUNE = "intune", "Intune"
        ACTIVE_DIRECTORY = "ad", "Active Directory"
        CMDB = "cmdb", "ServiceNow CMDB"
        SPREADSHEET = "spreadsheet", "Spreadsheet Import"
        NETWORK_SCAN = "network_scan", "Network Scan"

    class SyncSchedule(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MANUAL = "manual", "Manual Only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SourceType.choices, db_index=True)
    connection_config = models.JSONField(
        default=dict,
        help_text="Connection configuration (credentials encrypted in production)",
    )
    sync_schedule = models.CharField(max_length=50, choices=SyncSchedule.choices, default=SyncSchedule.DAILY)
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Discovery configuration
    include_patterns = models.JSONField(
        default=list,
        help_text="Patterns to include in discovery (regex)",
    )
    exclude_patterns = models.JSONField(
        default=list,
        help_text="Patterns to exclude from discovery (regex)",
    )

    class Meta:
        verbose_name = "Discovery Source"
        verbose_name_plural = "Discovery Sources"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["source_type", "is_active"]),
            models.Index(fields=["sync_schedule"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.source_type})"


class DiscoveryRun(TimeStampedModel, CorrelationIdModel):
    """
    Record of discovery execution.

    Tracks each discovery run with statistics and status.
    """

    class RunType(models.TextChoices):
        FULL = "full", "Full Discovery"
        INCREMENTAL = "incremental", "Incremental"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(DiscoverySource, on_delete=models.CASCADE, related_name="runs")
    run_type = models.CharField(max_length=20, choices=RunType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Statistics
    records_discovered = models.IntegerField(default=0)
    records_new = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_normalized = models.IntegerField(default=0)
    normalization_failures = models.IntegerField(default=0)

    # Errors
    errors = models.JSONField(default=list)

    # Initiator
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovery_runs",
    )

    class Meta:
        verbose_name = "Discovery Run"
        verbose_name_plural = "Discovery Runs"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["source", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.source.name} - {self.run_type} ({self.status})"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate run duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class DiscoveredApplication(TimeStampedModel):
    """
    Raw discovered application from source.

    Stores the original data before normalization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discovery_run = models.ForeignKey(DiscoveryRun, on_delete=models.CASCADE, related_name="applications")

    # Source identification
    source_id = models.CharField(max_length=255, help_text="ID from source system")
    source_type = models.CharField(max_length=50)

    # Raw data
    raw_name = models.CharField(max_length=500, db_index=True)
    raw_publisher = models.CharField(max_length=255, blank=True)
    raw_version = models.CharField(max_length=100, blank=True)
    install_date = models.DateField(null=True, blank=True)
    install_count = models.IntegerField(default=1)
    source_metadata = models.JSONField(default=dict)

    # Normalization linkage
    normalized_app = models.ForeignKey(
        "NormalizedApplication",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discovered_instances",
    )
    normalization_confidence = models.FloatField(null=True, blank=True, help_text="Confidence score (0-1)")
    normalization_method = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Discovered Application"
        verbose_name_plural = "Discovered Applications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["discovery_run"]),
            models.Index(fields=["raw_name"]),
            models.Index(fields=["raw_publisher"]),
            models.Index(fields=["normalized_app"]),
        ]

    def __str__(self) -> str:
        return f"{self.raw_name} ({self.raw_version or 'unknown'})"


class NormalizedApplication(TimeStampedModel):
    """
    Normalized/canonical application record.

    Aggregates discovered applications into a single canonical form.
    """

    class ApplicationType(models.TextChoices):
        DESKTOP = "desktop", "Desktop Application"
        WEB = "web", "Web Application"
        MOBILE = "mobile", "Mobile Application"
        SAAS = "saas", "SaaS"
        SERVER = "server", "Server Application"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Canonical information
    name = models.CharField(max_length=255, db_index=True)
    publisher = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=100, blank=True)
    application_type = models.CharField(
        max_length=50,
        choices=ApplicationType.choices,
        default=ApplicationType.DESKTOP,
    )

    # Status flags
    is_managed = models.BooleanField(default=False, db_index=True, help_text="In EUCORA portfolio")
    is_approved = models.BooleanField(default=False, db_index=True, help_text="Approved for use")
    is_restricted = models.BooleanField(default=False, db_index=True, help_text="Restricted/blocked")

    # Linkages
    portfolio_app = models.ForeignKey(
        "application_portfolio.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="normalized_apps",
    )
    license_sku = models.ForeignKey(
        "license_management.LicenseSKU",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="normalized_apps",
    )

    # Fingerprint for deduplication
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)

    # Aggregated statistics
    total_installs = models.IntegerField(default=0)
    first_discovered = models.DateTimeField(null=True, blank=True)
    last_discovered = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Normalized Application"
        verbose_name_plural = "Normalized Applications"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "publisher"]),
            models.Index(fields=["is_managed", "is_approved"]),
            models.Index(fields=["fingerprint"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.publisher})"

    @staticmethod
    def generate_fingerprint(name: str, publisher: str) -> str:
        """Generate unique fingerprint for deduplication."""
        normalized_name = name.lower().strip()
        normalized_publisher = publisher.lower().strip()
        combined = f"{normalized_publisher}::{normalized_name}"
        return hashlib.sha256(combined.encode()).hexdigest()[:64]


class ApplicationVersion(TimeStampedModel):
    """
    Version of a normalized application.

    Tracks version lifecycle and installation counts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE, related_name="versions")

    # Version info
    version = models.CharField(max_length=100, db_index=True)
    version_major = models.IntegerField(null=True, blank=True)
    version_minor = models.IntegerField(null=True, blank=True)
    version_patch = models.IntegerField(null=True, blank=True)

    # Lifecycle
    release_date = models.DateField(null=True, blank=True)
    end_of_life = models.DateField(null=True, blank=True)
    has_security_updates = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False, db_index=True)

    # Installation statistics
    install_count = models.IntegerField(default=0)
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Application Version"
        verbose_name_plural = "Application Versions"
        ordering = ["-is_current", "-version"]
        indexes = [
            models.Index(fields=["application", "version"]),
            models.Index(fields=["is_current"]),
            models.Index(fields=["end_of_life"]),
        ]
        unique_together = [["application", "version"]]

    def __str__(self) -> str:
        return f"{self.application.name} v{self.version}"


class LicenseGap(TimeStampedModel, CorrelationIdModel):
    """
    Identified license compliance gaps.

    Tracks discrepancies between installed applications and license entitlements.
    """

    class GapType(models.TextChoices):
        MISSING_LICENSE = "missing_license", "Missing License"
        OVER_DEPLOYMENT = "over_deployment", "Over-Deployment"
        UNDER_LICENSED = "under_licensed", "Under-Licensed"
        EXPIRED_LICENSE = "expired_license", "Expired License"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE, related_name="license_gaps")

    # Gap details
    gap_type = models.CharField(max_length=50, choices=GapType.choices, db_index=True)
    detected_installs = models.IntegerField()
    licensed_count = models.IntegerField()
    gap_count = models.IntegerField(help_text="Positive = over-deployed, Negative = under-utilized")

    # Risk assessment
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, db_index=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_license_gaps",
    )
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "License Gap"
        verbose_name_plural = "License Gaps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "status"]),
            models.Index(fields=["gap_type", "risk_level"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.application.name} - {self.gap_type} ({self.gap_count})"


class PatchGap(TimeStampedModel, CorrelationIdModel):
    """
    Identified patch/update gaps.

    Tracks applications needing updates or at end-of-life.
    """

    class GapType(models.TextChoices):
        SECURITY_PATCH = "security_patch", "Security Patch Required"
        MAJOR_UPGRADE = "major_upgrade", "Major Upgrade Available"
        EOL_VERSION = "eol_version", "End-of-Life Version"
        MINOR_UPDATE = "minor_update", "Minor Update Available"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        EXCEPTION = "exception", "Exception Granted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE, related_name="patch_gaps")

    # Version info
    current_version = models.ForeignKey(
        ApplicationVersion,
        on_delete=models.CASCADE,
        related_name="patch_gaps_current",
    )
    target_version = models.ForeignKey(
        ApplicationVersion,
        on_delete=models.CASCADE,
        related_name="patch_gaps_target",
        null=True,
        blank=True,
    )

    # Gap details
    affected_devices = models.IntegerField()
    gap_type = models.CharField(max_length=50, choices=GapType.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)

    # CVE information
    cve_ids = models.JSONField(default=list, help_text="Related CVE identifiers")

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    planned_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Patch Gap"
        verbose_name_plural = "Patch Gaps"
        ordering = ["-severity", "-created_at"]
        indexes = [
            models.Index(fields=["application", "status"]),
            models.Index(fields=["gap_type", "severity"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.application.name} - {self.gap_type} ({self.severity})"


class DiscoveryReport(TimeStampedModel, CorrelationIdModel):
    """
    Generated discovery report.

    Aggregates discovery findings into a comprehensive report.
    """

    class ReportType(models.TextChoices):
        INVENTORY = "inventory", "Application Inventory"
        SHADOW_IT = "shadow_it", "Shadow IT Report"
        LICENSE_COMPLIANCE = "license_compliance", "License Compliance"
        PATCH_COMPLIANCE = "patch_compliance", "Patch Compliance"
        RISK_ASSESSMENT = "risk_assessment", "Risk Assessment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=50, choices=ReportType.choices, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Report data
    summary = models.JSONField(default=dict)
    details = models.JSONField(default=dict)

    # Generation info
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    generated_at = models.DateTimeField(default=timezone.now)

    # Scope
    sources_included = models.JSONField(default=list)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Discovery Report"
        verbose_name_plural = "Discovery Reports"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["report_type", "generated_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.report_type})"
