# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Models for packaging factory pipeline.
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class PackagingPipeline(models.Model):
    """
    Packaging pipeline execution tracking.

    Pipeline stages: INTAKE → BUILD → SIGN → SBOM → SCAN → POLICY → STORE
    """

    PLATFORM_CHOICES = [
        ("windows", "Windows"),
        ("macos", "macOS"),
        ("linux", "Linux"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("INTAKE", "Intake"),
        ("BUILD", "Build"),
        ("SIGN", "Sign"),
        ("SBOM", "SBOM Generation"),
        ("SCAN", "Vulnerability Scan"),
        ("POLICY", "Policy Decision"),
        ("STORE", "Store"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    PACKAGE_TYPE_CHOICES = [
        ("MSI", "MSI Installer"),
        ("MSIX", "MSIX Package"),
        ("EXE", "Executable"),
        ("PKG", "macOS Package"),
        ("DMG", "macOS Disk Image"),
        ("DEB", "Debian Package"),
        ("RPM", "RPM Package"),
    ]

    POLICY_DECISION_CHOICES = [
        ("PASS", "Pass - No blocking issues"),
        ("FAIL", "Fail - Blocking vulnerabilities found"),
        ("EXCEPTION", "Exception - Approved with compensating controls"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Package metadata
    package_name = models.CharField(max_length=255, db_index=True)
    package_version = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, db_index=True)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES)

    # Pipeline status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    current_stage = models.CharField(max_length=50, null=True, blank=True)

    # Input/Output
    source_artifact_url = models.URLField(max_length=1000)
    source_artifact_hash = models.CharField(max_length=64)  # SHA-256
    output_artifact_url = models.URLField(max_length=1000, null=True, blank=True)
    output_artifact_hash = models.CharField(max_length=64, null=True, blank=True)

    # SBOM
    sbom_format = models.CharField(max_length=50, null=True, blank=True)  # SPDX, CycloneDX
    sbom_url = models.URLField(max_length=1000, null=True, blank=True)
    sbom_generated_at = models.DateTimeField(null=True, blank=True)

    # Vulnerability scan
    scan_tool = models.CharField(max_length=100, null=True, blank=True)  # trivy, grype
    scan_results = models.JSONField(default=dict, blank=True)
    scan_completed_at = models.DateTimeField(null=True, blank=True)
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    low_count = models.IntegerField(default=0)

    # Policy decision
    policy_decision = models.CharField(max_length=20, choices=POLICY_DECISION_CHOICES, null=True, blank=True)
    policy_reason = models.TextField(null=True, blank=True)
    exception_id = models.UUIDField(null=True, blank=True)  # Link to CABException if applicable

    # Signing
    signing_certificate = models.CharField(max_length=255, null=True, blank=True)
    signature_url = models.URLField(max_length=1000, null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    # Provenance
    build_id = models.CharField(max_length=255, null=True, blank=True)
    builder_identity = models.CharField(max_length=255, null=True, blank=True)
    source_repo = models.URLField(max_length=1000, null=True, blank=True)
    source_commit = models.CharField(max_length=40, null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="packaging_pipelines")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(null=True, blank=True)
    error_stage = models.CharField(max_length=50, null=True, blank=True)

    # Observability
    correlation_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)

    class Meta:
        db_table = "packaging_pipeline"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["package_name", "package_version"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["policy_decision"]),
        ]

    def __str__(self):
        return f"{self.package_name} {self.package_version} ({self.platform}) - {self.status}"

    @property
    def is_completed(self):
        """Check if pipeline completed successfully."""
        return self.status == "COMPLETED"

    @property
    def has_blocking_vulnerabilities(self):
        """Check if scan found blocking (Critical/High) vulnerabilities."""
        return self.critical_count > 0 or self.high_count > 0

    @property
    def duration_seconds(self):
        """Calculate pipeline execution duration."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None


class PackagingStageLog(models.Model):
    """
    Detailed logs for each pipeline stage.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(PackagingPipeline, on_delete=models.CASCADE, related_name="stage_logs")

    stage_name = models.CharField(max_length=50, db_index=True)
    status = models.CharField(max_length=20)  # SUCCESS, FAILED, SKIPPED

    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "packaging_stage_log"
        ordering = ["started_at"]
        indexes = [
            models.Index(fields=["pipeline", "stage_name"]),
        ]

    def __str__(self):
        return f"{self.pipeline.package_name} - {self.stage_name} ({self.status})"

    @property
    def duration_seconds(self):
        """Calculate stage execution duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
