# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Portfolio models.

Implements P9 from MASTER-IMPLEMENTATION-PLAN-2026.md:
- Application catalog with multi-platform support
- Version tracking with artifact linkage
- Package artifacts with SBOM and signature metadata
- Deployment intents and ring progression
- Health metrics and compliance status
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel

# =============================================================================
# ENUMS
# =============================================================================


class PlatformType(models.TextChoices):
    """Supported deployment platforms."""

    WINDOWS = "windows", "Windows"
    MACOS = "macos", "macOS"
    LINUX = "linux", "Linux"
    IOS = "ios", "iOS"
    IPADOS = "ipados", "iPadOS"
    ANDROID = "android", "Android"


class ApplicationStatus(models.TextChoices):
    """Application lifecycle status."""

    DRAFT = "draft", "Draft"
    PENDING_REVIEW = "pending_review", "Pending Review"
    APPROVED = "approved", "Approved"
    PUBLISHED = "published", "Published"
    DEPRECATED = "deprecated", "Deprecated"
    RETIRED = "retired", "Retired"


class PackageType(models.TextChoices):
    """Package format types."""

    # Windows
    INTUNEWIN = "intunewin", "Intune Win32 (.intunewin)"
    MSIX = "msix", "MSIX Package"
    MSI = "msi", "Windows Installer (MSI)"
    EXE = "exe", "Executable (EXE)"
    # macOS
    PKG = "pkg", "macOS Package (PKG)"
    DMG = "dmg", "Disk Image (DMG)"
    APP = "app", "Application Bundle (APP)"
    # Linux
    DEB = "deb", "Debian Package (DEB)"
    RPM = "rpm", "RPM Package"
    SNAP = "snap", "Snap Package"
    FLATPAK = "flatpak", "Flatpak"
    APPIMAGE = "appimage", "AppImage"
    # Mobile
    IPA = "ipa", "iOS App (IPA)"
    APK = "apk", "Android Package (APK)"
    AAB = "aab", "Android App Bundle (AAB)"
    # Other
    OTHER = "other", "Other"


class ArtifactStatus(models.TextChoices):
    """Package artifact lifecycle status."""

    UPLOADING = "uploading", "Uploading"
    VALIDATING = "validating", "Validating"
    SCANNING = "scanning", "Scanning"
    SCAN_FAILED = "scan_failed", "Scan Failed"
    READY = "ready", "Ready"
    PUBLISHED = "published", "Published"
    SUPERSEDED = "superseded", "Superseded"
    REVOKED = "revoked", "Revoked"


class RingLevel(models.TextChoices):
    """Deployment ring levels."""

    RING_0 = "ring_0", "Ring 0 - Lab/Automation"
    RING_1 = "ring_1", "Ring 1 - Canary"
    RING_2 = "ring_2", "Ring 2 - Pilot"
    RING_3 = "ring_3", "Ring 3 - Department"
    RING_4 = "ring_4", "Ring 4 - Global"


class DeploymentStatus(models.TextChoices):
    """Deployment intent status."""

    DRAFT = "draft", "Draft"
    PENDING_APPROVAL = "pending_approval", "Pending CAB Approval"
    APPROVED = "approved", "Approved"
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    ROLLED_BACK = "rolled_back", "Rolled Back"
    CANCELLED = "cancelled", "Cancelled"


class HealthStatus(models.TextChoices):
    """Application health status."""

    HEALTHY = "healthy", "Healthy"
    DEGRADED = "degraded", "Degraded"
    CRITICAL = "critical", "Critical"
    UNKNOWN = "unknown", "Unknown"


class ComplianceStatus(models.TextChoices):
    """Application compliance status."""

    COMPLIANT = "compliant", "Compliant"
    NON_COMPLIANT = "non_compliant", "Non-Compliant"
    PENDING = "pending", "Pending Assessment"
    EXEMPT = "exempt", "Exempt"


# =============================================================================
# MODELS
# =============================================================================


class Publisher(TimeStampedModel):
    """
    Software publisher/vendor.

    Tracks publishers for attribution and trust scoring.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Publisher name")
    identifier = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier (e.g., reverse domain)",
    )
    website = models.URLField(blank=True, help_text="Publisher website")
    support_url = models.URLField(blank=True, help_text="Support portal URL")
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether publisher identity is verified",
    )
    trust_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.50"),
        help_text="Trust score 0.00-1.00",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"

    def __str__(self) -> str:
        return self.name


class Application(TimeStampedModel):
    """
    Application catalog entry.

    Core entity representing a software application that can be deployed
    across multiple platforms with different package formats.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Application display name")
    identifier = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique application identifier (e.g., com.vendor.appname)",
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="applications",
        help_text="Software publisher",
    )
    description = models.TextField(blank=True, help_text="Application description")
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Application category (e.g., Productivity, Security)",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Application tags for filtering",
    )
    homepage_url = models.URLField(blank=True, help_text="Application homepage")
    documentation_url = models.URLField(blank=True, help_text="Documentation URL")
    icon_url = models.URLField(blank=True, help_text="Application icon URL")

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_applications",
        help_text="Application owner",
    )
    team = models.CharField(
        max_length=100,
        blank=True,
        help_text="Owning team/department",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        help_text="Application lifecycle status",
    )

    # Platform support
    supported_platforms = models.JSONField(
        default=list,
        help_text="List of supported platform types",
    )

    # Risk and compliance
    risk_score = models.IntegerField(
        default=0,
        help_text="Calculated risk score 0-100",
    )
    requires_cab_approval = models.BooleanField(
        default=False,
        help_text="Whether CAB approval is required for deployments",
    )
    is_privileged = models.BooleanField(
        default=False,
        help_text="Whether app requires elevated privileges",
    )

    # Flags
    is_internal = models.BooleanField(
        default=False,
        help_text="Whether this is an internal/LOB application",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        indexes = [
            models.Index(fields=["identifier"]),
            models.Index(fields=["publisher"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.identifier})"

    @property
    def latest_version(self) -> ApplicationVersion | None:
        """Get the latest approved version."""
        return self.versions.filter(is_latest=True).first()

    @property
    def platform_count(self) -> int:
        """Count of supported platforms."""
        return len(self.supported_platforms) if self.supported_platforms else 0


class ApplicationVersion(TimeStampedModel):
    """
    Application version.

    Represents a specific version of an application with its metadata
    and links to platform-specific package artifacts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="Parent application",
    )
    version = models.CharField(
        max_length=100,
        help_text="Version string (semver preferred)",
    )
    version_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="Numeric version code for comparison",
    )

    # Release information
    release_notes = models.TextField(blank=True, help_text="Version release notes")
    release_date = models.DateField(
        null=True,
        blank=True,
        help_text="Official release date",
    )

    # Status
    is_latest = models.BooleanField(
        default=False,
        help_text="Whether this is the latest approved version",
    )
    is_security_update = models.BooleanField(
        default=False,
        help_text="Whether this version includes security fixes",
    )
    deprecation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when version will be deprecated",
    )
    end_of_life_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when version reaches end of life",
    )

    # Requirements
    min_os_versions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Minimum OS versions per platform",
    )
    system_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="System requirements (RAM, disk, etc.)",
    )
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="Application dependencies",
    )

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_app_versions",
        help_text="User who approved this version",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Application Version"
        verbose_name_plural = "Application Versions"
        unique_together = [["application", "version"]]
        indexes = [
            models.Index(fields=["application", "version"]),
            models.Index(fields=["is_latest"]),
        ]

    def __str__(self) -> str:
        return f"{self.application.name} v{self.version}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Ensure only one version is marked as latest."""
        if self.is_latest:
            ApplicationVersion.objects.filter(
                application=self.application,
                is_latest=True,
            ).exclude(
                pk=self.pk
            ).update(is_latest=False)
        super().save(*args, **kwargs)


class PackageArtifact(TimeStampedModel, CorrelationIdModel):
    """
    Platform-specific package artifact.

    Represents a deployable package file with its metadata, signatures,
    and SBOM linkage for supply chain security.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(
        ApplicationVersion,
        on_delete=models.CASCADE,
        related_name="artifacts",
        help_text="Application version",
    )
    platform = models.CharField(
        max_length=20,
        choices=PlatformType.choices,
        help_text="Target platform",
    )
    architecture = models.CharField(
        max_length=20,
        default="x64",
        help_text="CPU architecture (x64, arm64, universal)",
    )
    package_type = models.CharField(
        max_length=20,
        choices=PackageType.choices,
        help_text="Package format",
    )

    # File metadata
    file_name = models.CharField(max_length=255, help_text="Package file name")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_hash_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of package file",
    )
    storage_ref = models.CharField(
        max_length=500,
        help_text="Reference to artifact in object store",
    )

    # Signing
    is_signed = models.BooleanField(default=False, help_text="Whether package is signed")
    signature_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Signature type (authenticode, notarization, gpg)",
    )
    signer_identity = models.CharField(
        max_length=255,
        blank=True,
        help_text="Signing certificate subject/identity",
    )
    signature_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Signature timestamp",
    )

    # SBOM
    sbom_ref = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reference to SBOM in artifact store",
    )
    sbom_format = models.CharField(
        max_length=20,
        blank=True,
        help_text="SBOM format (spdx, cyclonedx)",
    )

    # Scanning
    scan_status = models.CharField(
        max_length=20,
        blank=True,
        help_text="Vulnerability scan status",
    )
    scan_completed_at = models.DateTimeField(null=True, blank=True)
    vulnerability_count_critical = models.IntegerField(default=0)
    vulnerability_count_high = models.IntegerField(default=0)
    vulnerability_count_medium = models.IntegerField(default=0)
    vulnerability_count_low = models.IntegerField(default=0)
    scan_report_ref = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reference to scan report",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ArtifactStatus.choices,
        default=ArtifactStatus.UPLOADING,
        help_text="Artifact lifecycle status",
    )

    # Installation commands (platform-specific)
    install_command = models.TextField(
        blank=True,
        help_text="Silent install command",
    )
    uninstall_command = models.TextField(
        blank=True,
        help_text="Silent uninstall command",
    )
    detection_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detection rules (file, registry, script)",
    )
    requirement_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Requirement/applicability rules",
    )

    # Upload tracking
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_artifacts",
        help_text="User who uploaded the artifact",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Package Artifact"
        verbose_name_plural = "Package Artifacts"
        unique_together = [["version", "platform", "architecture", "package_type"]]
        indexes = [
            models.Index(fields=["version", "platform"]),
            models.Index(fields=["status"]),
            models.Index(fields=["file_hash_sha256"]),
        ]

    def __str__(self) -> str:
        return f"{self.version} - {self.platform}/{self.architecture} ({self.package_type})"

    @property
    def has_vulnerabilities(self) -> bool:
        """Check if artifact has any vulnerabilities."""
        return self.vulnerability_count_critical > 0 or self.vulnerability_count_high > 0

    @property
    def total_vulnerabilities(self) -> int:
        """Total vulnerability count."""
        return (
            self.vulnerability_count_critical
            + self.vulnerability_count_high
            + self.vulnerability_count_medium
            + self.vulnerability_count_low
        )


class DeploymentIntent(TimeStampedModel, CorrelationIdModel):
    """
    Deployment intent - represents a planned deployment.

    Captures the intent to deploy a specific package artifact to a target
    scope with ring-based rollout progression.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact = models.ForeignKey(
        PackageArtifact,
        on_delete=models.PROTECT,
        related_name="deployment_intents",
        help_text="Package artifact to deploy",
    )

    # Targeting
    target_ring = models.CharField(
        max_length=20,
        choices=RingLevel.choices,
        help_text="Target deployment ring",
    )
    target_scope = models.JSONField(
        default=dict,
        help_text="Target scope definition (groups, sites, exclusions)",
    )
    target_device_count = models.IntegerField(
        default=0,
        help_text="Estimated target device count",
    )

    # Scheduling
    scheduled_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled deployment start time",
    )
    scheduled_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled deployment end time (for maintenance windows)",
    )
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deployment deadline (after which deployment is required)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=DeploymentStatus.choices,
        default=DeploymentStatus.DRAFT,
        help_text="Deployment status",
    )

    # Risk assessment
    risk_score = models.IntegerField(
        default=0,
        help_text="Calculated deployment risk score 0-100",
    )
    risk_model_version = models.CharField(
        max_length=20,
        default="v1.0",
        help_text="Risk model version used",
    )
    requires_cab_approval = models.BooleanField(
        default=False,
        help_text="Whether CAB approval is required",
    )

    # CAB approval
    cab_request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="CAB request identifier",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_deployments",
        help_text="CAB approver",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Evidence
    evidence_pack_ref = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reference to evidence pack in artifact store",
    )
    evidence_pack_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of evidence pack",
    )

    # Execution
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_deployments",
        help_text="User who created the deployment",
    )

    # Rollout configuration
    rollout_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rollout configuration (batch size, throttling, etc.)",
    )

    # Rollback
    rollback_plan = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rollback plan details",
    )
    rollback_triggered = models.BooleanField(default=False)
    rollback_at = models.DateTimeField(null=True, blank=True)
    rollback_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Deployment Intent"
        verbose_name_plural = "Deployment Intents"
        indexes = [
            models.Index(fields=["artifact"]),
            models.Index(fields=["status"]),
            models.Index(fields=["target_ring"]),
            models.Index(fields=["scheduled_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.artifact} -> {self.target_ring} ({self.status})"


class DeploymentMetric(TimeStampedModel):
    """
    Deployment progress metrics.

    Tracks deployment progress and success metrics for monitoring
    and promotion gate evaluation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment = models.ForeignKey(
        DeploymentIntent,
        on_delete=models.CASCADE,
        related_name="metrics",
        help_text="Parent deployment",
    )
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text="When metrics were recorded",
    )

    # Progress
    devices_targeted = models.IntegerField(default=0)
    devices_pending = models.IntegerField(default=0)
    devices_in_progress = models.IntegerField(default=0)
    devices_succeeded = models.IntegerField(default=0)
    devices_failed = models.IntegerField(default=0)
    devices_not_applicable = models.IntegerField(default=0)

    # Success rates
    success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Success rate percentage",
    )

    # Timing
    avg_install_time_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Average installation time",
    )
    time_to_compliance_avg_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Average time to compliance",
    )

    # Errors
    error_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Error code summary",
    )

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Deployment Metric"
        verbose_name_plural = "Deployment Metrics"
        indexes = [
            models.Index(fields=["deployment", "recorded_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.deployment} metrics @ {self.recorded_at}"


class ApplicationHealth(TimeStampedModel):
    """
    Application health snapshot.

    Captures point-in-time health metrics for an application across
    its deployed estate.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="health_snapshots",
        help_text="Application",
    )
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text="When health was recorded",
    )

    # Overall status
    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
        help_text="Overall health status",
    )
    health_message = models.CharField(
        max_length=255,
        blank=True,
        help_text="Health status message",
    )

    # Installation metrics
    total_installations = models.IntegerField(default=0)
    healthy_installations = models.IntegerField(default=0)
    unhealthy_installations = models.IntegerField(default=0)
    unknown_installations = models.IntegerField(default=0)

    # Version distribution
    version_distribution = models.JSONField(
        default=dict,
        blank=True,
        help_text="Installation count per version",
    )

    # Compliance
    compliance_status = models.CharField(
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.PENDING,
        help_text="Compliance status",
    )
    compliance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Compliance score percentage",
    )

    # Issues
    active_incidents = models.IntegerField(default=0)
    open_vulnerabilities = models.IntegerField(default=0)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Application Health"
        verbose_name_plural = "Application Health Records"
        indexes = [
            models.Index(fields=["application", "recorded_at"]),
            models.Index(fields=["health_status"]),
        ]
        get_latest_by = "recorded_at"

    def __str__(self) -> str:
        return f"{self.application.name} health @ {self.recorded_at}"


class ApplicationDependency(TimeStampedModel):
    """
    Application dependency relationship.

    Tracks dependencies between applications for impact analysis
    and upgrade planning.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="dependencies",
        help_text="Application that has the dependency",
    )
    depends_on = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="dependents",
        help_text="Required application",
    )
    dependency_type = models.CharField(
        max_length=50,
        default="runtime",
        help_text="Dependency type (runtime, build, optional)",
    )
    min_version = models.CharField(
        max_length=100,
        blank=True,
        help_text="Minimum required version",
    )
    max_version = models.CharField(
        max_length=100,
        blank=True,
        help_text="Maximum compatible version",
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether dependency is required",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["application", "depends_on"]
        verbose_name = "Application Dependency"
        verbose_name_plural = "Application Dependencies"
        unique_together = [["application", "depends_on"]]

    def __str__(self) -> str:
        return f"{self.application.name} -> {self.depends_on.name}"
