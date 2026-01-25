# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store models for artifact management.
"""
import hashlib
import json
from uuid import uuid4

from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, DemoQuerySet, TimeStampedModel


class EvidencePack(TimeStampedModel, CorrelationIdModel):
    """
    Evidence pack with immutable artifact storage.
    """

    app_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    artifact_hash = models.CharField(max_length=64, help_text="SHA-256 hash of artifact")
    artifact_path = models.CharField(max_length=500, help_text="MinIO object path")
    sbom_data = models.JSONField(help_text="Software Bill of Materials (SPDX/CycloneDX)")
    vulnerability_scan_results = models.JSONField(help_text="Vulnerability scan results")
    rollback_plan = models.TextField(help_text="Rollback plan documentation")
    is_validated = models.BooleanField(default=False, help_text="Whether evidence pack is validated")
    is_demo = models.BooleanField(default=False, db_index=True, help_text="Whether this is demo data")

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["app_name", "version"]),
            models.Index(fields=["artifact_hash"]),
        ]
        verbose_name = "Evidence Pack"
        verbose_name_plural = "Evidence Packs"

    def __str__(self):
        return f"{self.app_name} {self.version} - {self.artifact_hash[:8]}"


# ============================================================================
# Phase P5.1: Evidence Pack Generation Models
# ============================================================================


class EvidencePackage(models.Model):
    """
    Immutable evidence package for CAB decision-making.
    Contains all information needed to evaluate deployment risk.

    P5.1 Deliverable: Core evidence package model with immutability verification.
    """

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid4)
    deployment_intent_id = models.CharField(max_length=255, help_text="Correlation ID linking to deployment intent")
    correlation_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier for audit trail")

    # Evidence Content
    evidence_data = models.JSONField(default=dict, help_text="Complete evidence pack (artifacts, tests, scans, etc.)")

    # Risk Assessment
    risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0, help_text="Risk score 0-100 (higher = riskier)"
    )
    risk_factors = models.JSONField(default=dict, help_text="Breakdown of all contributing risk factors")
    risk_model_version = models.CharField(max_length=50, default="1.0", help_text="Version of risk scoring model used")

    # Completeness
    is_complete = models.BooleanField(default=False, help_text="All required fields populated")
    completeness_check = models.JSONField(default=dict, help_text="Field-by-field completeness status")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(
        max_length=255, default="system", help_text="User or system that created this package"
    )

    # Content Hash (immutability proof)
    content_hash = models.CharField(
        max_length=64, help_text="SHA-256 hash of evidence_data for immutability verification"
    )

    class Meta:
        db_table = "evidence_store_evidencepackage"
        ordering = ["-created_at"]
        verbose_name = "Evidence Package"
        verbose_name_plural = "Evidence Packages"
        indexes = [
            models.Index(fields=["deployment_intent_id", "-created_at"]),
            models.Index(fields=["risk_score"]),
            models.Index(fields=["is_complete"]),
        ]

    def __str__(self):
        return f"Evidence for {self.deployment_intent_id} (Risk: {self.risk_score})"

    def save(self, *args, **kwargs):
        """Compute content hash before saving."""
        if not self.content_hash:
            content_str = json.dumps(self.evidence_data, sort_keys=True)
            self.content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        super().save(*args, **kwargs)

    def verify_immutability(self) -> bool:
        """Verify evidence package hasn't been tampered with."""
        content_str = json.dumps(self.evidence_data, sort_keys=True)
        current_hash = hashlib.sha256(content_str.encode()).hexdigest()
        return current_hash == self.content_hash


class RiskFactor(models.Model):
    """
    Risk scoring factor definition (v1.0).
    Immutable once created - versioned in risk_model_version.

    P5.2 Deliverable: Risk factor definitions with rubrics for scoring.
    """

    FACTOR_TYPES = [
        ("coverage", "Test Coverage"),
        ("security", "Security Issues"),
        ("testing", "Manual Testing"),
        ("rollback", "Rollback Validation"),
        ("scope", "Change Scope"),
        ("complexity", "Code Complexity"),
        ("impact", "User Impact"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4)
    model_version = models.CharField(
        max_length=50, default="1.0", help_text="Risk model version this factor belongs to"
    )
    factor_type = models.CharField(max_length=50, choices=FACTOR_TYPES, help_text="Category of risk factor")
    name = models.CharField(max_length=255, help_text="Human-readable name")
    description = models.TextField(help_text="What this factor measures")
    weight = models.DecimalField(max_digits=5, decimal_places=4, help_text="Percentage weight in overall score (0-1)")
    rubric = models.JSONField(default=dict, help_text="Scoring rubric (e.g., {'>90%': 0, '<90%': 20})")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidence_store_riskfactor"
        ordering = ["model_version", "factor_type"]
        verbose_name = "Risk Factor"
        verbose_name_plural = "Risk Factors"
        unique_together = ["model_version", "factor_type"]

    def __str__(self):
        return f"{self.name} (v{self.model_version}, weight: {self.weight})"


class RiskScoreBreakdown(models.Model):
    """
    Detailed breakdown of how risk score was calculated.
    Transparency: all factors and their contributions visible.
    """

    id = models.UUIDField(primary_key=True, default=uuid4)
    evidence_package = models.OneToOneField(EvidencePackage, on_delete=models.CASCADE, related_name="risk_breakdown")
    correlation_id = models.CharField(max_length=255, help_text="Link to deployment intent")

    factors_evaluated = models.JSONField(default=dict, help_text="All factors with their scores and weights")
    formula = models.TextField(
        default="Σ(weight_i * normalized_factor_i), clamped [0-100]", help_text="Risk scoring formula used"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, default="system")

    class Meta:
        db_table = "evidence_store_riskscorebreakdown"
        verbose_name = "Risk Score Breakdown"
        verbose_name_plural = "Risk Score Breakdowns"

    def __str__(self):
        return f"Risk breakdown for {self.correlation_id}"
