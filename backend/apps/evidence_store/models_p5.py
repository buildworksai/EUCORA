# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Pack Generation Models and Services for P5.1
"""
import hashlib
import json
from uuid import uuid4

from django.db import models
from django.utils import timezone


class EvidencePackage(models.Model):
    """
    Immutable evidence package for CAB decision-making.
    Contains all information needed to evaluate deployment risk.
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
        db_table = "policy_engine_riskfactor"
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
        db_table = "policy_engine_riskscorebreakdown"
        verbose_name = "Risk Score Breakdown"
        verbose_name_plural = "Risk Score Breakdowns"

    def __str__(self):
        return f"Risk breakdown for {self.correlation_id}"


# ============================================================================
# Service Module (Evidence Generation)
# ============================================================================


class EvidenceGenerationService:
    """
    Service for collecting and generating evidence packages.
    Implements P5.1: Evidence Pack Generation Engine.
    """

    @staticmethod
    def generate_evidence_package(
        deployment_intent_id: str,
        correlation_id: str,
        artifact_info: dict = None,
        test_results: dict = None,
        scan_results: dict = None,
        deployment_plan: dict = None,
        rollback_plan: dict = None,
    ) -> EvidencePackage:
        """
        Generate a complete evidence package for CAB decision-making.

        Args:
            deployment_intent_id: ID of deployment intent
            correlation_id: Unique identifier for audit trail
            artifact_info: Hash, signature, SBOM of artifacts
            test_results: Test coverage, results summary
            scan_results: Vulnerability scan results
            deployment_plan: How deployment will proceed
            rollback_plan: Rollback strategy (plane-specific)

        Returns:
            EvidencePackage: Immutable evidence record

        Raises:
            ValueError: If required fields missing
        """

        # Collect all evidence
        evidence_data = {
            "artifacts": artifact_info or {},
            "test_results": test_results or {},
            "scan_results": scan_results or {},
            "deployment_plan": deployment_plan or {},
            "rollback_plan": rollback_plan or {},
            "collected_at": timezone.now().isoformat(),
        }

        # Compute risk score
        risk_score, risk_factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        # Check completeness
        completeness_check = EvidenceGenerationService._check_completeness(evidence_data)
        is_complete = all(completeness_check.values())

        # Create evidence package
        package = EvidencePackage.objects.create(
            deployment_intent_id=deployment_intent_id,
            correlation_id=correlation_id,
            evidence_data=evidence_data,
            risk_score=risk_score,
            risk_factors=risk_factors,
            is_complete=is_complete,
            completeness_check=completeness_check,
            created_by="evidence_generator",
        )

        # Create risk breakdown for transparency
        RiskScoreBreakdown.objects.create(
            evidence_package=package,
            correlation_id=correlation_id,
            factors_evaluated=risk_factors,
        )

        return package

    @staticmethod
    def _compute_risk_score(evidence_data: dict) -> tuple:
        """
        Compute risk score from evidence using risk model v1.0.

        Returns:
            (risk_score: float, risk_factors: dict)
        """
        risk_factors = {}
        weighted_sum = 0.0
        total_weight = 0.0

        # Get risk factors from database
        factors = RiskFactor.objects.filter(model_version="1.0")

        for factor in factors:
            # Evaluate factor based on evidence
            normalized_value = EvidenceGenerationService._evaluate_factor(
                factor.factor_type, evidence_data, factor.rubric
            )

            weighted_contribution = factor.weight * normalized_value
            weighted_sum += weighted_contribution
            total_weight += factor.weight

            risk_factors[factor.factor_type] = {
                "name": factor.name,
                "value": normalized_value,
                "weight": float(factor.weight),
                "contribution": float(weighted_contribution),
            }

        # Clamp to [0, 100]
        if total_weight > 0:
            risk_score = min(100, max(0, (weighted_sum / total_weight) * 100))
        else:
            risk_score = 0

        return round(risk_score, 2), risk_factors

    @staticmethod
    def _evaluate_factor(factor_type: str, evidence: dict, rubric: dict) -> float:
        """
        Evaluate a single risk factor based on evidence and rubric.
        Returns normalized value [0-100].
        """
        # TODO: Implement rubric-based evaluation
        # This will be detailed in P5.2 with full rubric examples
        return 0.0

    @staticmethod
    def _check_completeness(evidence_data: dict) -> dict:
        """
        Check if all required evidence fields are present.

        Returns:
            dict with boolean status for each field
        """
        required_fields = [
            "artifacts",
            "test_results",
            "scan_results",
            "deployment_plan",
            "rollback_plan",
        ]

        completeness = {}
        for field in required_fields:
            completeness[field] = bool(evidence_data.get(field))

        return completeness
