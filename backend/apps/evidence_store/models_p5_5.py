# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Defense-in-Depth Security Controls
Blast Radius Classification, Incident Tracking, Risk Model Versioning

Implementation Date: 2026-01-23
Go-Live Target: 2026-02-10
"""
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RiskModelVersion(models.Model):
    """
    Versioned risk model configuration with CAB approval workflow.

    Risk model changes require:
    - Version increment (v1.0 → v1.1)
    - CAB approval
    - Calibration evidence
    - Effective date

    Only ONE version can be active at a time.
    """

    MODE_CHOICES = [
        ("GREENFIELD_CONSERVATIVE", "Greenfield Conservative (100% CAB Review)"),
        ("CAUTIOUS", "Cautious (Limited Auto-Approve)"),
        ("MODERATE", "Moderate (Balanced)"),
        ("MATURE", "Mature (Evidence-Based Automation)"),
        ("OPTIMIZED", "Optimized (Maximum Automation)"),
    ]

    # Version identity
    version = models.CharField(max_length=10, unique=True, help_text="e.g., '1.0', '1.1', '2.0'")
    mode = models.CharField(max_length=50, choices=MODE_CHOICES, help_text="Operating mode")

    # Lifecycle
    effective_date = models.DateTimeField(help_text="When this version becomes active")
    review_date = models.DateTimeField(help_text="When to review for calibration")
    is_active = models.BooleanField(default=False, db_index=True, help_text="Only one version can be active")

    # Approval
    approved_by_cab = models.BooleanField(default=False, help_text="CAB approval required for activation")
    cab_approval_date = models.DateTimeField(null=True, blank=True)
    cab_approval_notes = models.TextField(blank=True)

    # Configuration (JSON for flexibility)
    auto_approve_thresholds = models.JSONField(
        help_text="Thresholds per blast radius class: {'CRITICAL_INFRASTRUCTURE': 0, 'BUSINESS_CRITICAL': 0, ...}"
    )
    risk_factor_weights = models.JSONField(
        help_text="Risk factor weights (must sum to 1.0): {'test_coverage': 0.20, 'security_issues': 0.15, ...}"
    )

    # Calibration evidence
    calibration_data = models.JSONField(
        default=dict, help_text="Incident correlation, risk score distribution, false positive/negative rates"
    )
    calibration_notes = models.TextField(blank=True, help_text="Evidence supporting this version")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, default="system")

    class Meta:
        db_table = "evidence_store_riskmodelversion"
        ordering = ["-version"]
        verbose_name = "Risk Model Version"
        verbose_name_plural = "Risk Model Versions"
        indexes = [
            models.Index(fields=["is_active", "effective_date"]),
            models.Index(fields=["version"]),
        ]

    def __str__(self):
        active_status = " (ACTIVE)" if self.is_active else ""
        return f"Risk Model v{self.version} - {self.mode}{active_status}"

    def clean(self):
        """Validate risk model configuration."""
        # Validate risk factor weights sum to 1.0
        if self.risk_factor_weights:
            total_weight = sum(self.risk_factor_weights.values())
            if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
                raise ValidationError(f"Risk factor weights must sum to 1.0, got {total_weight:.4f}")

        # Validate only one active version
        if self.is_active:
            active_count = RiskModelVersion.objects.filter(is_active=True).exclude(pk=self.pk).count()
            if active_count > 0:
                raise ValidationError("Only one risk model version can be active at a time")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_active_version(cls):
        """Get the currently active risk model version."""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            raise ValueError("No active risk model version configured")

    def get_auto_approve_threshold(self, blast_radius_class: str) -> int:
        """Get auto-approve threshold for a given blast radius class."""
        return self.auto_approve_thresholds.get(blast_radius_class, 0)


class BlastRadiusClass(models.Model):
    """
    Blast radius classification for deployments.

    Defines impact scope and approval requirements per application category.
    Can be populated from CMDB or manually classified.
    """

    CLASS_CHOICES = [
        ("CRITICAL_INFRASTRUCTURE", "Critical Infrastructure"),
        ("BUSINESS_CRITICAL", "Business Critical"),
        ("PRODUCTIVITY_TOOLS", "Productivity Tools"),
        ("NON_CRITICAL", "Non-Critical"),
    ]

    # Classification
    name = models.CharField(
        max_length=50, choices=CLASS_CHOICES, unique=True, help_text="Blast radius classification level"
    )
    description = models.TextField(help_text="What qualifies for this classification")

    # Impact assessment
    user_impact_max = models.IntegerField(
        help_text="Maximum users that can be impacted (enterprise-wide, department, team)"
    )
    business_criticality = models.CharField(
        max_length=20,
        choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")],
        help_text="Business criticality level",
    )

    # CAB requirements
    cab_quorum_required = models.IntegerField(default=1, help_text="Minimum CAB members required for approval")
    auto_approve_allowed = models.BooleanField(
        default=False, help_text="Whether auto-approve is ever allowed for this class"
    )

    # Examples
    example_applications = models.JSONField(
        default=list, help_text="Example applications in this class: ['Windows Security Update', 'Antivirus Engine']"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evidence_store_blastradiusclass"
        verbose_name = "Blast Radius Class"
        verbose_name_plural = "Blast Radius Classes"

    def __str__(self):
        return f"{self.get_name_display()} (CAB Quorum: {self.cab_quorum_required})"


class DeploymentIncident(models.Model):
    """
    Track production incidents caused by deployments.

    Links incidents to:
    - Deployment intent
    - Evidence package
    - CAB approval (if applicable)
    - Risk score at time of approval

    Used for risk model calibration and trust maturity progression.
    """

    SEVERITY_CHOICES = [
        ("P1", "P1 - Critical (Service Down)"),
        ("P2", "P2 - High (Major Degradation)"),
        ("P3", "P3 - Medium (Minor Impact)"),
        ("P4", "P4 - Low (Cosmetic)"),
    ]

    DETECTION_METHOD_CHOICES = [
        ("MONITORING_ALERT", "Monitoring Alert"),
        ("USER_REPORT", "User Report"),
        ("CAB_REVIEW", "CAB Review"),
        ("SECURITY_SCAN", "Security Scan"),
        ("AUTOMATED_TEST", "Automated Test"),
    ]

    RESOLUTION_METHOD_CHOICES = [
        ("ROLLBACK", "Rollback to Previous Version"),
        ("HOTFIX", "Hotfix Deployment"),
        ("MANUAL_REMEDIATION", "Manual Remediation"),
        ("WORKAROUND", "Temporary Workaround"),
    ]

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Linkage to deployment
    deployment_intent_id = models.CharField(max_length=255, db_index=True, help_text="Deployment intent correlation ID")
    evidence_package_id = models.CharField(max_length=255, db_index=True, help_text="Evidence package ID")
    cab_approval_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="CAB approval request ID (if CAB-reviewed)"
    )

    # Incident details
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, db_index=True)
    incident_date = models.DateTimeField(db_index=True, help_text="When incident occurred")
    detection_method = models.CharField(max_length=50, choices=DETECTION_METHOD_CHOICES)

    title = models.CharField(max_length=255, help_text="Incident title")
    description = models.TextField(help_text="Detailed incident description")
    root_cause = models.TextField(blank=True, help_text="Root cause analysis")

    # Deployment context at time of incident
    was_auto_approved = models.BooleanField(db_index=True, help_text="Was deployment auto-approved (vs CAB-reviewed)")
    risk_score_at_approval = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Risk score when deployment was approved"
    )
    risk_model_version = models.CharField(max_length=10, help_text="Risk model version used for approval")
    blast_radius_class = models.CharField(max_length=50, help_text="Blast radius classification of deployment")

    # Impact
    affected_user_count = models.IntegerField(default=0, help_text="Number of users affected")
    downtime_minutes = models.IntegerField(default=0, help_text="Total downtime in minutes")
    business_impact_usd = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, help_text="Estimated business impact in USD"
    )

    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When incident was resolved")
    resolution_method = models.CharField(max_length=50, choices=RESOLUTION_METHOD_CHOICES, blank=True)
    resolution_notes = models.TextField(blank=True)
    time_to_resolution_minutes = models.IntegerField(
        null=True, blank=True, help_text="Time from detection to resolution"
    )

    # Preventability assessment
    was_preventable = models.BooleanField(null=True, help_text="Could this have been prevented by better controls?")
    preventability_notes = models.TextField(
        blank=True, help_text="Analysis of whether CAB review or additional controls would have caught this"
    )

    # Control improvements
    control_improvements = models.JSONField(
        default=dict, help_text="Recommended improvements: risk factor adjustments, new controls, threshold changes"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, default="system")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evidence_store_deploymentincident"
        ordering = ["-incident_date"]
        verbose_name = "Deployment Incident"
        verbose_name_plural = "Deployment Incidents"
        indexes = [
            models.Index(fields=["incident_date", "severity"]),
            models.Index(fields=["was_auto_approved", "severity"]),
            models.Index(fields=["blast_radius_class", "incident_date"]),
            models.Index(fields=["risk_score_at_approval"]),
        ]

    def __str__(self):
        resolved_status = "RESOLVED" if self.resolved_at else "OPEN"
        return f"[{self.severity}] {self.title} - {resolved_status}"

    def save(self, *args, **kwargs):
        # Calculate time to resolution if resolved
        if self.resolved_at and not self.time_to_resolution_minutes:
            delta = self.resolved_at - self.incident_date
            self.time_to_resolution_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    @property
    def is_resolved(self) -> bool:
        """Check if incident is resolved."""
        return self.resolved_at is not None

    @property
    def was_high_severity(self) -> bool:
        """Check if incident was P1 or P2."""
        return self.severity in ["P1", "P2"]


class TrustMaturityLevel(models.Model):
    """
    Trust maturity progression levels for progressive automation.

    Defines criteria for advancing from conservative (100% CAB) to
    mature (risk-based auto-approve) based on incident data.

    Levels progress based on:
    - Incident rate (% of deployments causing incidents)
    - P1/P2 incident count
    - Weeks of clean operation
    - Control effectiveness
    """

    LEVEL_CHOICES = [
        ("LEVEL_0_BASELINE", "Level 0: Baseline (100% CAB Review)"),
        ("LEVEL_1_CAUTIOUS", "Level 1: Cautious (Limited Auto-Approve)"),
        ("LEVEL_2_MODERATE", "Level 2: Moderate (Balanced)"),
        ("LEVEL_3_MATURE", "Level 3: Mature (Evidence-Based)"),
        ("LEVEL_4_OPTIMIZED", "Level 4: Optimized (Maximum Automation)"),
    ]

    # Level identity
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES, unique=True)
    description = models.TextField(help_text="What this maturity level represents")

    # Entry criteria
    weeks_required = models.IntegerField(help_text="Minimum weeks at previous level")
    max_incident_rate = models.DecimalField(
        max_digits=5, decimal_places=4, help_text="Maximum incident rate (0.01 = 1%)"
    )
    max_p1_incidents = models.IntegerField(help_text="Maximum P1 incidents allowed")
    max_p2_incidents = models.IntegerField(help_text="Maximum P2 incidents allowed")

    # Associated risk model version
    risk_model_version = models.CharField(
        max_length=10, help_text="Risk model version to activate when reaching this level"
    )

    # Thresholds (denormalized for quick access)
    auto_approve_thresholds = models.JSONField(help_text="Auto-approve thresholds per blast radius class")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidence_store_trustmaturitylevel"
        ordering = ["level"]
        verbose_name = "Trust Maturity Level"
        verbose_name_plural = "Trust Maturity Levels"

    def __str__(self):
        return f"{self.get_level_display()} → v{self.risk_model_version}"


class TrustMaturityProgress(models.Model):
    """
    Tracks progress through trust maturity levels.

    Records:
    - Current level
    - Evaluation results
    - Progression decisions
    - Incident data per evaluation period
    """

    STATUS_CHOICES = [
        ("EVALUATING", "Evaluating"),
        ("CRITERIA_MET", "Criteria Met - Ready to Progress"),
        ("CRITERIA_NOT_MET", "Criteria Not Met"),
        ("PROGRESSED", "Progressed to Next Level"),
        ("REGRESSED", "Regressed Due to Incidents"),
    ]

    # Evaluation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    evaluation_date = models.DateTimeField(db_index=True)
    current_level = models.CharField(max_length=50)
    next_level = models.CharField(max_length=50, blank=True)

    # Evaluation period data
    evaluation_period_start = models.DateTimeField()
    evaluation_period_end = models.DateTimeField()

    deployments_total = models.IntegerField(help_text="Total deployments in period")
    incidents_total = models.IntegerField(help_text="Total incidents in period")
    incident_rate = models.DecimalField(
        max_digits=5, decimal_places=4, help_text="Incident rate (incidents / deployments)"
    )

    p1_incidents = models.IntegerField(default=0)
    p2_incidents = models.IntegerField(default=0)
    p3_incidents = models.IntegerField(default=0)
    p4_incidents = models.IntegerField(default=0)

    auto_approved_deployments = models.IntegerField(default=0)
    auto_approved_incidents = models.IntegerField(default=0)

    # Decision
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    decision_notes = models.TextField(help_text="Rationale for progression decision")
    blocking_criteria = models.JSONField(default=list, help_text="List of criteria that blocked progression (if any)")

    # CAB approval
    requires_cab_approval = models.BooleanField(default=True)
    cab_approved = models.BooleanField(default=False)
    cab_approval_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidence_store_trustmaturityprogress"
        ordering = ["-evaluation_date"]
        verbose_name = "Trust Maturity Progress"
        verbose_name_plural = "Trust Maturity Progress Records"
        indexes = [
            models.Index(fields=["evaluation_date", "status"]),
            models.Index(fields=["current_level"]),
        ]

    def __str__(self):
        return f"{self.evaluation_date.date()} - {self.current_level}: {self.status}"
