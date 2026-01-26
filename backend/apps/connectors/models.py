# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connectors models for asset inventory (CMDB) and reconciliation engine.

Includes:
- Asset and Application models for CMDB
- ConnectorInstance for connector configurations
- SyncJob for tracking sync operations
- DriftEvent for drift detection and remediation
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models import CorrelationIdModel, DemoQuerySet, TimeStampedModel

User = get_user_model()


class Asset(TimeStampedModel):
    """
    Asset inventory model (CMDB).

    Represents devices managed by the endpoint management system.
    """

    class AssetType(models.TextChoices):
        LAPTOP = "Laptop", "Laptop"
        DESKTOP = "Desktop", "Desktop"
        VIRTUAL_MACHINE = "Virtual Machine", "Virtual Machine"
        MOBILE = "Mobile", "Mobile"
        SERVER = "Server", "Server"

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        INACTIVE = "Inactive", "Inactive"
        RETIRED = "Retired", "Retired"
        MAINTENANCE = "Maintenance", "Maintenance"

    class UserSentiment(models.TextChoices):
        POSITIVE = "Positive", "Positive"
        NEUTRAL = "Neutral", "Neutral"
        NEGATIVE = "Negative", "Negative"

    # Basic identification
    name = models.CharField(max_length=255, db_index=True, help_text="Device name/hostname")
    asset_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="Unique asset identifier")
    serial_number = models.CharField(max_length=100, blank=True, db_index=True)

    # Classification
    type = models.CharField(max_length=20, choices=AssetType.choices, db_index=True)
    os = models.CharField(max_length=100, db_index=True, help_text="Operating system version")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    # Location and ownership
    location = models.CharField(max_length=255, db_index=True, help_text="Physical or logical location")
    owner = models.CharField(max_length=255, db_index=True, help_text="Asset owner/assigned user")

    # Network
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)

    # Security
    disk_encryption = models.BooleanField(default=False, help_text="Disk encryption enabled")
    firewall_enabled = models.BooleanField(default=True, help_text="Firewall enabled")

    # Compliance
    compliance_score = models.IntegerField(default=0, help_text="Compliance score (0-100)")
    last_checkin = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Last check-in timestamp")

    # DEX & Green IT metrics
    dex_score = models.FloatField(null=True, blank=True, help_text="Digital Experience Score (0-10)")
    boot_time = models.IntegerField(null=True, blank=True, help_text="Boot time in seconds")
    carbon_footprint = models.FloatField(null=True, blank=True, help_text="Carbon footprint (kg CO2e per year)")
    user_sentiment = models.CharField(max_length=20, choices=UserSentiment.choices, null=True, blank=True)

    # Metadata
    connector_type = models.CharField(
        max_length=20, blank=True, help_text="Source connector (intune, jamf, sccm, landscape)"
    )
    connector_object_id = models.CharField(max_length=255, blank=True, help_text="Platform-specific object ID")
    is_demo = models.BooleanField(default=False, db_index=True, help_text="Whether this is demo data")

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["type", "status"]),
            models.Index(fields=["os", "status"]),
            models.Index(fields=["location", "status"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["compliance_score"]),
            models.Index(fields=["last_checkin"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Asset"
        verbose_name_plural = "Assets"

    def __str__(self):
        return f"{self.name} ({self.type}) - {self.status}"


class Application(TimeStampedModel):
    """
    Application catalog model.

    Represents applications that can be deployed.
    """

    class Platform(models.TextChoices):
        WINDOWS = "Windows", "Windows"
        MACOS = "macOS", "macOS"
        LINUX = "Linux", "Linux"
        MOBILE = "Mobile", "Mobile"
        MULTI_PLATFORM = "Multi-Platform", "Multi-Platform"

    class Category(models.TextChoices):
        PRODUCTIVITY = "Productivity", "Productivity"
        SECURITY = "Security", "Security"
        DEVELOPMENT = "Development", "Development"
        MEDIA = "Media", "Media"
        BROWSER = "Browser", "Browser"
        COMMUNICATION = "Communication", "Communication"
        UTILITY = "Utility", "Utility"
        ENTERPRISE = "Enterprise", "Enterprise"

    # Basic identification
    name = models.CharField(max_length=255, db_index=True)
    vendor = models.CharField(max_length=255, blank=True, db_index=True)
    version = models.CharField(max_length=50, db_index=True)

    # Classification
    platform = models.CharField(max_length=20, choices=Platform.choices, db_index=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.UTILITY, db_index=True)

    # Metadata
    description = models.TextField(blank=True)
    homepage_url = models.URLField(blank=True)
    license_type = models.CharField(max_length=100, blank=True)

    # Risk assessment
    default_risk_score = models.IntegerField(default=30, help_text="Default risk score (0-100)")
    is_demo = models.BooleanField(default=False, db_index=True, help_text="Whether this is demo data")

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["name", "version"]),
            models.Index(fields=["platform", "category"]),
            models.Index(fields=["vendor"]),
        ]
        unique_together = [["name", "version", "platform"]]
        ordering = ["name", "version"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return f"{self.name} {self.version} ({self.platform})"


# =============================================================================
# RECONCILIATION ENGINE MODELS (D6.8)
# =============================================================================


class ConnectorType(models.TextChoices):
    """Supported connector types."""

    INTUNE = "intune", "Microsoft Intune"
    JAMF = "jamf", "Jamf Pro"
    SCCM = "sccm", "Microsoft SCCM"
    LANDSCAPE = "landscape", "Canonical Landscape"
    ANSIBLE = "ansible", "Ansible/AWX"
    ENTRA = "entra", "Microsoft Entra ID"


class ConnectorStatus(models.TextChoices):
    """Connector instance status."""

    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ERROR = "error", "Error"
    MAINTENANCE = "maintenance", "Maintenance"


class HealthStatus(models.TextChoices):
    """Health status for connectors."""

    HEALTHY = "healthy", "Healthy"
    DEGRADED = "degraded", "Degraded"
    UNHEALTHY = "unhealthy", "Unhealthy"
    UNKNOWN = "unknown", "Unknown"


class SyncJobType(models.TextChoices):
    """Types of sync jobs."""

    FULL_SYNC = "full_sync", "Full Sync"
    DELTA_SYNC = "delta_sync", "Delta Sync"
    PUSH = "push", "Push to Execution Plane"
    RECONCILE = "reconcile", "Reconciliation"


class SyncJobStatus(models.TextChoices):
    """Status for sync jobs."""

    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class DriftType(models.TextChoices):
    """Types of drift detected."""

    MISSING = "missing", "Missing in Execution Plane"
    EXTRA = "extra", "Extra in Execution Plane"
    MODIFIED = "modified", "Modified"
    STALE = "stale", "Stale Data"


class RemediationStatus(models.TextChoices):
    """Status for drift remediation."""

    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"
    REQUIRES_APPROVAL = "requires_approval", "Requires Approval"


class ConnectorInstance(TimeStampedModel):
    """
    Configuration for a specific connector deployment.

    Stores encrypted credentials and tracks connection health.
    Each connector instance represents a connection to an execution plane.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connector_type = models.CharField(
        max_length=20,
        choices=ConnectorType.choices,
        db_index=True,
        help_text="Type of connector",
    )
    name = models.CharField(max_length=255, help_text="Display name for this instance")
    description = models.TextField(blank=True, help_text="Instance description")

    # Configuration (encrypted at rest)
    config_encrypted = models.BinaryField(null=True, blank=True, help_text="Encrypted configuration/credentials")
    config_schema_version = models.CharField(max_length=20, default="1.0", help_text="Schema version for config")

    # Status and health
    status = models.CharField(
        max_length=20,
        choices=ConnectorStatus.choices,
        default=ConnectorStatus.INACTIVE,
        db_index=True,
    )
    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
        db_index=True,
    )
    health_message = models.TextField(blank=True, help_text="Last health check message")
    health_checked_at = models.DateTimeField(null=True, blank=True)

    # Sync tracking
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text="Last successful sync")
    last_sync_status = models.CharField(max_length=20, blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled next sync")

    # Sync configuration
    sync_interval_minutes = models.IntegerField(default=60, help_text="Sync interval in minutes")
    auto_sync_enabled = models.BooleanField(default=True, help_text="Enable automatic sync")
    auto_remediate = models.BooleanField(default=False, help_text="Automatically remediate drift (R1 only)")

    # Scope restrictions
    scope_filter = models.JSONField(default=dict, blank=True, help_text="Scope filter for this connector")

    # Audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_connectors",
    )
    is_demo = models.BooleanField(default=False, db_index=True)

    objects = DemoQuerySet.as_manager()

    class Meta:
        db_table = "connector_instance"
        ordering = ["connector_type", "name"]
        indexes = [
            models.Index(fields=["connector_type", "status"]),
            models.Index(fields=["health_status"]),
            models.Index(fields=["next_sync_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_connector_type_display()})"


class SyncJob(TimeStampedModel, CorrelationIdModel):
    """
    Tracks sync operations between control plane and execution plane.

    Every sync operation creates a job record for audit and monitoring.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connector = models.ForeignKey(
        ConnectorInstance,
        on_delete=models.CASCADE,
        related_name="sync_jobs",
        help_text="Connector instance",
    )
    job_type = models.CharField(
        max_length=20,
        choices=SyncJobType.choices,
        db_index=True,
        help_text="Type of sync operation",
    )
    status = models.CharField(
        max_length=20,
        choices=SyncJobStatus.choices,
        default=SyncJobStatus.PENDING,
        db_index=True,
    )

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Progress tracking
    total_records = models.IntegerField(default=0, help_text="Total records to process")
    records_processed = models.IntegerField(default=0, help_text="Records processed so far")
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_deleted = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)

    # Results
    errors = models.JSONField(default=list, blank=True, help_text="List of errors")
    warnings = models.JSONField(default=list, blank=True, help_text="List of warnings")
    summary = models.JSONField(default=dict, blank=True, help_text="Job summary")

    # Drift detection results
    drift_events_created = models.IntegerField(default=0, help_text="New drift events detected")

    # Audit
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_sync_jobs",
    )
    trigger_type = models.CharField(
        max_length=20,
        default="manual",
        help_text="How job was triggered (manual, scheduled, webhook)",
    )

    class Meta:
        db_table = "connector_sync_job"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["connector", "status"]),
            models.Index(fields=["job_type", "status"]),
            models.Index(fields=["started_at"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"SyncJob {self.id} ({self.job_type}) - {self.status}"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.records_processed / self.total_records) * 100


class DriftEvent(TimeStampedModel):
    """
    Records drift between desired and actual state.

    Detected during sync/reconciliation and tracked for remediation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connector = models.ForeignKey(
        ConnectorInstance,
        on_delete=models.CASCADE,
        related_name="drift_events",
        help_text="Connector instance",
    )
    sync_job = models.ForeignKey(
        SyncJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drift_events",
        help_text="Sync job that detected this drift",
    )

    # Entity identification
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of entity (app, assignment, policy, device)",
    )
    entity_id = models.CharField(max_length=255, db_index=True, help_text="Entity identifier")
    entity_name = models.CharField(max_length=255, blank=True, help_text="Entity display name")

    # Drift details
    drift_type = models.CharField(
        max_length=20,
        choices=DriftType.choices,
        db_index=True,
        help_text="Type of drift",
    )
    desired_state = models.JSONField(help_text="Expected/desired state")
    actual_state = models.JSONField(help_text="Actual state in execution plane")
    diff_summary = models.JSONField(default=dict, blank=True, help_text="Summary of differences")

    # Timing
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    # Remediation
    remediation_status = models.CharField(
        max_length=20,
        choices=RemediationStatus.choices,
        default=RemediationStatus.PENDING,
        db_index=True,
    )
    remediation_attempts = models.IntegerField(default=0)
    last_remediation_at = models.DateTimeField(null=True, blank=True)
    remediation_error = models.TextField(blank=True)

    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True, db_index=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_drift_events",
    )
    resolution_notes = models.TextField(blank=True)

    # Risk assessment
    severity = models.CharField(
        max_length=20,
        default="medium",
        help_text="Drift severity (low, medium, high, critical)",
    )
    requires_cab_approval = models.BooleanField(default=False, help_text="Requires CAB approval for remediation")

    class Meta:
        db_table = "connector_drift_event"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["connector", "drift_type"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["remediation_status"]),
            models.Index(fields=["detected_at"]),
            models.Index(fields=["resolved_at"]),
            models.Index(fields=["severity", "remediation_status"]),
        ]

    def __str__(self) -> str:
        return f"Drift {self.drift_type}: {self.entity_type}/{self.entity_id}"

    @property
    def is_resolved(self) -> bool:
        """Check if drift is resolved."""
        return self.resolved_at is not None

    @property
    def age_seconds(self) -> float:
        """Calculate age of drift event in seconds."""
        from django.utils import timezone

        return (timezone.now() - self.detected_at).total_seconds()
