# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
License Management models for EUCORA Control Plane.

Implements enterprise-grade Software Asset Management (SAM) with:
- Vendor and SKU master data
- Entitlement tracking with approval workflow
- Consumption signal ingestion and normalization
- Deterministic reconciliation with immutable snapshots
- Evidence-first governance for all changes
"""
import uuid
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel

User = get_user_model()


class LicenseModelType(models.TextChoices):
    """License model type for SKU configuration."""

    DEVICE = "device", "Per Device"
    USER = "user", "Per User"
    CONCURRENT = "concurrent", "Concurrent"
    SUBSCRIPTION = "subscription", "Subscription Seat"
    FEATURE = "feature", "Feature Add-on"
    CORE = "core", "Per Core/CPU"
    INSTANCE = "instance", "Per Instance"


class EntitlementStatus(models.TextChoices):
    """Status for license entitlements."""

    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    PENDING = "pending", "Pending Approval"
    SUSPENDED = "suspended", "Suspended"
    TERMINATED = "terminated", "Terminated"


class AssignmentStatus(models.TextChoices):
    """Status for license assignments."""

    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"
    PENDING = "pending", "Pending"


class AlertSeverity(models.TextChoices):
    """Severity levels for license alerts."""

    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    CRITICAL = "critical", "Critical"


class AlertType(models.TextChoices):
    """Types of license alerts."""

    OVERCONSUMPTION = "overconsumption", "Over Consumption"
    EXPIRING = "expiring", "Expiring Soon"
    SPIKE = "spike", "Usage Spike"
    UNDERUTILIZED = "underutilized", "Underutilized"
    RECONCILIATION_FAILED = "reconciliation_failed", "Reconciliation Failed"
    STALE_DATA = "stale_data", "Stale Data"


class ScopeType(models.TextChoices):
    """Scope types for license pools."""

    GLOBAL = "global", "Global"
    REGION = "region", "Region"
    BUSINESS_UNIT = "bu", "Business Unit"
    DEPARTMENT = "department", "Department"
    SITE = "site", "Site"


class PrincipalType(models.TextChoices):
    """Types of principals for assignments and consumption."""

    USER = "user", "User"
    DEVICE = "device", "Device"
    SERVICE = "service", "Service Account"


class ReconciliationStatus(models.TextChoices):
    """Status for reconciliation runs."""

    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Vendor(TimeStampedModel):
    """
    Software vendor master data.

    Represents a software publisher/vendor for license tracking.
    All vendor data changes are audit-logged.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True, help_text="Vendor display name")
    identifier = models.CharField(
        max_length=100, unique=True, db_index=True, help_text="Unique vendor identifier (slug)"
    )
    website = models.URLField(blank=True, help_text="Vendor website URL")
    support_contact = models.EmailField(blank=True, help_text="Support contact email")
    notes = models.TextField(blank=True, help_text="Internal notes about the vendor")
    is_active = models.BooleanField(default=True, help_text="Whether vendor is active for new entitlements")

    class Meta:
        db_table = "license_vendor"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


class LicenseSKU(TimeStampedModel):
    """
    License SKU with model type and computation rules.

    Defines how licenses are counted, consumed, and reconciled.
    Unit rules control normalization of consumption signals.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="skus", help_text="Software vendor")
    sku_code = models.CharField(max_length=100, db_index=True, help_text="Vendor's SKU code")
    name = models.CharField(max_length=255, help_text="SKU display name")
    description = models.TextField(blank=True, help_text="SKU description")
    license_model_type = models.CharField(
        max_length=20,
        choices=LicenseModelType.choices,
        default=LicenseModelType.USER,
        help_text="How licenses are counted",
    )

    # Computation rules stored as JSON for flexibility
    unit_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rules for computing license units (e.g., core multipliers)",
    )
    normalization_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rules for normalizing consumption signals from different sources",
    )

    # Metadata
    is_active = models.BooleanField(default=True, help_text="Whether SKU is active for new entitlements")
    requires_approval = models.BooleanField(default=False, help_text="Whether entitlement changes require CAB approval")
    cost_per_unit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, help_text="Cost per license unit (for reporting)"
    )
    currency = models.CharField(max_length=3, default="USD", help_text="Currency code for cost")

    class Meta:
        db_table = "license_sku"
        ordering = ["vendor__name", "name"]
        unique_together = ["vendor", "sku_code"]
        indexes = [
            models.Index(fields=["vendor", "sku_code"]),
            models.Index(fields=["license_model_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor.name} - {self.name} ({self.sku_code})"


class Entitlement(TimeStampedModel, CorrelationIdModel):
    """
    Purchased/contracted license entitlement.

    Represents a legal entitlement to use software licenses.
    All changes require approval workflow and are audit-logged.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(LicenseSKU, on_delete=models.PROTECT, related_name="entitlements", help_text="License SKU")
    contract_id = models.CharField(max_length=100, db_index=True, help_text="Contract or PO reference")
    entitled_quantity = models.IntegerField(help_text="Number of licenses entitled")
    start_date = models.DateField(help_text="Entitlement start date")
    end_date = models.DateField(null=True, blank=True, help_text="Entitlement end date (null = perpetual)")
    renewal_date = models.DateField(null=True, blank=True, help_text="Next renewal date")

    # Terms and documentation
    terms = models.JSONField(default=dict, blank=True, help_text="License terms and conditions")
    document_refs = models.JSONField(
        default=list, blank=True, help_text="References to contract documents (MinIO paths)"
    )

    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=EntitlementStatus.choices,
        default=EntitlementStatus.PENDING,
        db_index=True,
        help_text="Entitlement status",
    )

    # Audit trail
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_entitlements",
        help_text="User who created this entitlement",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_entitlements",
        help_text="User who approved this entitlement",
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When entitlement was approved")

    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes")

    class Meta:
        db_table = "license_entitlement"
        ordering = ["-start_date", "sku__name"]
        indexes = [
            models.Index(fields=["sku", "status"]),
            models.Index(fields=["contract_id"]),
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["status", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku.name} x{self.entitled_quantity} ({self.contract_id})"

    @property
    def is_expired(self) -> bool:
        """Check if entitlement has expired."""
        if self.end_date is None:
            return False
        return self.end_date < timezone.now().date()

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry (None if perpetual)."""
        if self.end_date is None:
            return None
        delta = self.end_date - timezone.now().date()
        return delta.days


class LicensePool(TimeStampedModel):
    """
    Allocation pool for a SKU with optional scope.

    Allows segmentation of licenses by region, BU, or other scope.
    Enables tracking of reserved quantities for specific purposes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(LicenseSKU, on_delete=models.PROTECT, related_name="pools", help_text="License SKU")
    name = models.CharField(max_length=255, help_text="Pool display name")
    description = models.TextField(blank=True, help_text="Pool description")

    # Scope
    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
        default=ScopeType.GLOBAL,
        help_text="Type of scope restriction",
    )
    scope_value = models.CharField(max_length=100, blank=True, help_text="Scope value (e.g., region code, BU name)")

    # Quantity overrides
    entitled_quantity_override = models.IntegerField(
        null=True, blank=True, help_text="Override total entitled quantity for this pool"
    )
    reserved_quantity = models.IntegerField(default=0, help_text="Quantity reserved for specific purposes")

    # Status
    is_active = models.BooleanField(default=True, help_text="Whether pool is active")

    class Meta:
        db_table = "license_pool"
        ordering = ["sku__name", "name"]
        unique_together = ["sku", "scope_type", "scope_value"]
        indexes = [
            models.Index(fields=["sku", "scope_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        scope = f" ({self.scope_type}:{self.scope_value})" if self.scope_value else ""
        return f"{self.name}{scope}"


class Assignment(TimeStampedModel):
    """
    License assignment to user or device.

    Tracks explicit license assignments for manual allocation models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pool = models.ForeignKey(
        LicensePool, on_delete=models.PROTECT, related_name="assignments", help_text="License pool"
    )
    principal_type = models.CharField(max_length=20, choices=PrincipalType.choices, help_text="Type of assignee")
    principal_id = models.CharField(max_length=255, db_index=True, help_text="Assignee identifier")
    principal_name = models.CharField(max_length=255, blank=True, help_text="Assignee display name")

    # Timing
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="When assignment was made")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When assignment expires")

    # Status
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.ACTIVE,
        db_index=True,
    )

    # Audit
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="license_assignments",
        help_text="User who made the assignment",
    )
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_assignments",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)

    class Meta:
        db_table = "license_assignment"
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["pool", "status"]),
            models.Index(fields=["principal_type", "principal_id"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.pool.name} → {self.principal_type}:{self.principal_id}"


class ConsumptionSignal(TimeStampedModel):
    """
    Raw consumption signal from source system.

    Ingested from MDM platforms, telemetry, or other sources.
    Normalized into ConsumptionUnits during reconciliation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_system = models.CharField(
        max_length=50, db_index=True, help_text="Source system identifier (intune, jamf, etc.)"
    )
    raw_id = models.CharField(max_length=255, db_index=True, help_text="ID from source system")
    timestamp = models.DateTimeField(db_index=True, help_text="When consumption was detected")

    # Principal
    principal_type = models.CharField(max_length=20, choices=PrincipalType.choices)
    principal_id = models.CharField(max_length=255, db_index=True)
    principal_name = models.CharField(max_length=255, blank=True)

    # SKU reference
    sku = models.ForeignKey(
        LicenseSKU,
        on_delete=models.PROTECT,
        related_name="consumption_signals",
        help_text="Matched license SKU",
    )

    # Confidence and evidence
    confidence = models.FloatField(default=1.0, help_text="Match confidence (0.0-1.0)")
    raw_payload_hash = models.CharField(max_length=64, help_text="SHA-256 of raw signal payload")
    raw_payload = models.JSONField(default=dict, blank=True, help_text="Original signal payload")

    # Processing
    is_processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "license_consumption_signal"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["source_system", "raw_id"]),
            models.Index(fields=["sku", "timestamp"]),
            models.Index(fields=["is_processed", "timestamp"]),
            models.Index(fields=["principal_type", "principal_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_system}:{self.raw_id} → {self.sku.sku_code}"


class ConsumptionUnit(TimeStampedModel):
    """
    Normalized, deduplicated consumption unit.

    Represents one unit of license consumption after signal normalization.
    Links to source signals for audit trail.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(
        LicenseSKU, on_delete=models.PROTECT, related_name="consumption_units", help_text="License SKU"
    )
    pool = models.ForeignKey(
        LicensePool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumption_units",
        help_text="Allocated pool (if applicable)",
    )

    # Principal
    principal_type = models.CharField(max_length=20, choices=PrincipalType.choices)
    principal_id = models.CharField(max_length=255, db_index=True)
    principal_name = models.CharField(max_length=255, blank=True)

    # Source signals (ManyToMany for deduplication)
    signals = models.ManyToManyField(ConsumptionSignal, related_name="consumption_units", help_text="Source signals")

    # Effective period
    effective_from = models.DateTimeField(help_text="When consumption became effective")
    effective_to = models.DateTimeField(null=True, blank=True, help_text="When consumption ended")

    # Status
    status = models.CharField(
        max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.ACTIVE, db_index=True
    )

    # Metadata
    unit_count = models.IntegerField(default=1, help_text="Number of license units consumed")

    class Meta:
        db_table = "license_consumption_unit"
        ordering = ["-effective_from"]
        indexes = [
            models.Index(fields=["sku", "status"]),
            models.Index(fields=["principal_type", "principal_id"]),
            models.Index(fields=["effective_from", "effective_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku.sku_code} - {self.principal_type}:{self.principal_id}"


class ConsumptionSnapshot(TimeStampedModel):
    """
    Immutable reconciled truth snapshot.

    Generated during reconciliation runs.
    Provides point-in-time view of license position.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(
        LicenseSKU,
        on_delete=models.PROTECT,
        related_name="consumption_snapshots",
        help_text="License SKU",
    )
    pool = models.ForeignKey(
        LicensePool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumption_snapshots",
        help_text="License pool (null for SKU-level snapshot)",
    )

    # Timing
    reconciled_at = models.DateTimeField(db_index=True, help_text="When snapshot was created")
    ruleset_version = models.CharField(max_length=50, help_text="Version of reconciliation rules used")

    # Quantities (immutable after creation)
    entitled = models.IntegerField(help_text="Total entitled quantity")
    consumed = models.IntegerField(help_text="Total consumed quantity")
    reserved = models.IntegerField(default=0, help_text="Reserved quantity")
    remaining = models.IntegerField(help_text="Remaining available (entitled - consumed - reserved)")

    # Computed metrics
    utilization_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Utilization percentage")

    # Evidence
    evidence_pack_hash = models.CharField(max_length=64, help_text="SHA-256 of evidence pack")
    evidence_pack_ref = models.CharField(max_length=500, help_text="MinIO path to evidence pack")

    # Link to reconciliation run
    reconciliation_run = models.ForeignKey(
        "ReconciliationRun",
        on_delete=models.SET_NULL,
        null=True,
        related_name="snapshots",
        help_text="Source reconciliation run",
    )

    class Meta:
        db_table = "license_consumption_snapshot"
        ordering = ["-reconciled_at"]
        indexes = [
            models.Index(fields=["sku", "reconciled_at"]),
            models.Index(fields=["reconciled_at"]),
            models.Index(fields=["pool", "reconciled_at"]),
        ]

    def __str__(self) -> str:
        pool_str = f" ({self.pool.name})" if self.pool else ""
        return f"{self.sku.sku_code}{pool_str} @ {self.reconciled_at.isoformat()}"

    def save(self, *args, **kwargs):
        """Calculate derived fields before save."""
        if self.entitled > 0:
            self.utilization_percent = Decimal((self.consumed / self.entitled) * 100).quantize(Decimal("0.01"))
        else:
            self.utilization_percent = Decimal("0.00")
        super().save(*args, **kwargs)


class ReconciliationRun(TimeStampedModel, CorrelationIdModel):
    """
    Tracks a reconciliation job execution.

    Reconciliation creates ConsumptionSnapshots and detects drift.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=20,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.RUNNING,
        db_index=True,
    )
    ruleset_version = models.CharField(max_length=50, help_text="Version of reconciliation rules")

    # Timing
    started_at = models.DateTimeField(default=timezone.now, help_text="When run started")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When run completed")

    # Progress tracking
    skus_total = models.IntegerField(default=0, help_text="Total SKUs to process")
    skus_processed = models.IntegerField(default=0, help_text="SKUs processed so far")
    snapshots_created = models.IntegerField(default=0, help_text="Snapshots created")
    signals_processed = models.IntegerField(default=0, help_text="Signals processed")

    # Error tracking
    errors = models.JSONField(default=list, blank=True, help_text="List of errors encountered")

    # Diff summary
    diff_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of changes from previous reconciliation",
    )

    # Audit
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconciliation_runs",
        help_text="User who triggered the run (null for scheduled)",
    )
    trigger_type = models.CharField(
        max_length=20, default="manual", help_text="How run was triggered (manual, scheduled, signal)"
    )

    class Meta:
        db_table = "license_reconciliation_run"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "started_at"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self) -> str:
        return f"Reconciliation {self.id} ({self.status}) @ {self.started_at.isoformat()}"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.skus_total == 0:
            return 0.0
        return (self.skus_processed / self.skus_total) * 100


class LicenseAlert(TimeStampedModel):
    """
    Alert for license anomalies.

    Generated during reconciliation or monitoring.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.ForeignKey(
        LicenseSKU,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="Related SKU",
    )
    pool = models.ForeignKey(
        LicensePool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="Related pool (if applicable)",
    )

    # Alert details
    alert_type = models.CharField(max_length=50, choices=AlertType.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=AlertSeverity.choices, db_index=True)
    message = models.TextField(help_text="Alert message")
    details = models.JSONField(default=dict, blank=True, help_text="Additional alert details")

    # Timing
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Resolution
    acknowledged = models.BooleanField(default=False, db_index=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Auto-resolve
    auto_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "license_alert"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["sku", "alert_type"]),
            models.Index(fields=["severity", "acknowledged"]),
            models.Index(fields=["detected_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.alert_type}: {self.sku.sku_code}"


class ImportJob(TimeStampedModel, CorrelationIdModel):
    """
    Tracks license data import jobs.

    Supports CSV/JSON imports with validation and audit logging.
    """

    IMPORT_TYPE_CHOICES = [
        ("entitlements", "Entitlements"),
        ("vendors", "Vendors"),
        ("skus", "SKUs"),
        ("assignments", "Assignments"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("validating", "Validating"),
        ("importing", "Importing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)

    # File info
    file_name = models.CharField(max_length=255, help_text="Original file name")
    file_hash = models.CharField(max_length=64, help_text="SHA-256 of uploaded file")
    file_ref = models.CharField(max_length=500, help_text="MinIO path to uploaded file")

    # Progress
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # Errors
    validation_errors = models.JSONField(default=list, blank=True)
    import_errors = models.JSONField(default=list, blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Audit
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="license_imports",
    )

    class Meta:
        db_table = "license_import_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["import_type", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Import {self.import_type} ({self.file_name}) - {self.status}"
