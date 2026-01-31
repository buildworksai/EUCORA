# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Portfolio Management models for Application & Portfolio Manager personas.

Implements:
- Portfolio: Collection of applications managed by Portfolio Manager
- ApplicationOwnership: Links applications to Application Managers and Portfolios
- ApplicationManagerPerformance: Time-series performance snapshots
- LicenseTrueUpForecast: License true-up cost forecasting
- PackagingRequest: Packaging request workflow tracking
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models import TimeStampedModel

User = get_user_model()


class Portfolio(TimeStampedModel):
    """
    Portfolio of applications managed by a Portfolio Manager.
    Used for cost tracking, performance analytics, and strategic planning.
    """

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Portfolio name (e.g., 'Finance Applications', 'HR Suite')")
    description = models.TextField(blank=True)

    # Ownership
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_portfolios",
        help_text="Portfolio Manager responsible for this portfolio",
    )

    # Scope (business context)
    scope = models.JSONField(
        default=dict,
        help_text="""
        Portfolio scope definition:
        {
            "business_unit": "Finance",
            "geography": ["US", "EMEA"],
            "acquisition_boundary": "acquired_2024",
            "site_classes": ["online", "intermittent", "air_gapped"]
        }
        """,
    )

    # Budget and cost tracking
    budget_annual = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Annual budget for this portfolio (USD)"
    )
    cost_center = models.CharField(max_length=100, blank=True, help_text="Finance cost center code")

    # Status
    is_active = models.BooleanField(default=True, db_index=True, help_text="Soft delete flag")

    # Cached metrics (updated by background job)
    total_applications = models.IntegerField(default=0, help_text="Count of active applications in portfolio")
    total_licenses_entitled = models.IntegerField(default=0, help_text="Total licenses entitled across all SKUs")
    total_licenses_consumed = models.IntegerField(default=0, help_text="Total licenses consumed across all SKUs")
    total_cost_annual = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Total annual cost (licenses + deployment overhead)"
    )
    health_score = models.FloatField(default=0.0, help_text="Aggregate health score (0-100)")
    compliance_score = models.FloatField(default=0.0, help_text="Aggregate compliance score (0-100)")

    # Metadata
    last_metrics_update = models.DateTimeField(null=True, blank=True, help_text="Last time metrics were recomputed")

    class Meta:
        db_table = "portfolio_management_portfolio"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["manager", "is_active"]),
            models.Index(fields=["health_score"]),
            models.Index(fields=["compliance_score"]),
        ]

    def __str__(self):
        return f"{self.name} (Manager: {self.manager.username if self.manager else 'Unassigned'})"

    @property
    def license_utilization_percent(self):
        """Calculate license utilization percentage."""
        if self.total_licenses_entitled == 0:
            return 0.0
        return (self.total_licenses_consumed / self.total_licenses_entitled) * 100


class ApplicationOwnership(TimeStampedModel):
    """
    Maps applications to their owners (Application Managers) and portfolios.
    Supports co-ownership (PRIMARY and SECONDARY owners).
    """

    # Relationships
    application = models.ForeignKey(
        "application_portfolio.Application",
        on_delete=models.CASCADE,
        related_name="ownerships",
        help_text="Application being owned",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="application_ownerships",
        help_text="Application Manager who owns this application",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="application_ownerships",
        help_text="Portfolio this application belongs to",
    )

    # Ownership type
    ownership_type = models.CharField(
        max_length=20,
        choices=[
            ("PRIMARY", "Primary Owner"),
            ("SECONDARY", "Secondary Owner / Backup"),
        ],
        default="PRIMARY",
        help_text="Type of ownership (PRIMARY or SECONDARY)",
    )

    # Assignment tracking
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="When ownership was assigned")
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ownership_assignments",
        help_text="Portfolio Manager who assigned ownership",
    )

    # Status
    is_active = models.BooleanField(default=True, db_index=True, help_text="Soft delete flag")

    class Meta:
        db_table = "portfolio_management_ownership"
        ordering = ["-assigned_at"]
        unique_together = [
            ["application", "owner", "ownership_type"],  # Prevent duplicate ownerships
        ]
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["portfolio", "is_active"]),
            models.Index(fields=["application", "ownership_type"]),
        ]

    def __str__(self):
        return f"{self.application.name} → {self.owner.username} ({self.ownership_type})"


class ApplicationManagerPerformance(models.Model):
    """
    Immutable time-series snapshots of Application Manager performance.
    Generated by scheduled background job (daily/weekly).
    """

    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="performance_snapshots",
        help_text="Application Manager",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="manager_performance_snapshots",
        help_text="Portfolio context for this performance snapshot",
    )

    # Time period
    recorded_at = models.DateTimeField(db_index=True, help_text="Snapshot timestamp")
    period_start = models.DateTimeField(help_text="Start of measurement period (e.g., start of month)")
    period_end = models.DateTimeField(help_text="End of measurement period (e.g., end of month)")

    # Deployment metrics
    deployments_total = models.IntegerField(default=0, help_text="Total deployments in period")
    deployments_successful = models.IntegerField(default=0, help_text="Successful deployments (reached Global ring)")
    deployments_failed = models.IntegerField(default=0, help_text="Failed deployments (never reached Global)")
    deployments_rolled_back = models.IntegerField(default=0, help_text="Deployments that were rolled back")
    avg_deployment_duration_days = models.FloatField(
        default=0.0, help_text="Average days from CAB submission to Global completion"
    )
    success_rate_percent = models.FloatField(default=0.0, help_text="(successful / total) × 100")

    # Application health metrics
    applications_total = models.IntegerField(default=0, help_text="Total applications owned")
    applications_healthy = models.IntegerField(default=0, help_text="Applications with health ≥ 90%")
    applications_degraded = models.IntegerField(default=0, help_text="Applications with 70% ≤ health < 90%")
    applications_critical = models.IntegerField(default=0, help_text="Applications with health < 70%")
    avg_health_score = models.FloatField(default=0.0, help_text="Average health score across applications (0-100)")

    # License efficiency metrics
    licenses_entitled = models.IntegerField(default=0, help_text="Total licenses entitled")
    licenses_consumed = models.IntegerField(default=0, help_text="Total licenses consumed")
    licenses_wasted = models.IntegerField(
        default=0, help_text="Over-entitled licenses (entitled - consumed, if positive)"
    )
    utilization_percent = models.FloatField(default=0.0, help_text="(consumed / entitled) × 100")

    # Incident metrics
    incidents_total = models.IntegerField(default=0, help_text="Total incidents in period")
    incidents_resolved = models.IntegerField(default=0, help_text="Incidents resolved in period")
    avg_mttr_hours = models.FloatField(default=0.0, help_text="Mean time to resolution (hours)")

    # Composite score (weighted calculation)
    composite_score = models.FloatField(
        default=0.0,
        help_text="""
        Composite performance score (0-100):
        - Deployment success rate: 30%
        - Avg health score: 25%
        - License utilization: 20%
        - Time-to-deployment: 15%
        - MTTR: 10%
        """,
    )

    # Metadata
    calculation_metadata = models.JSONField(default=dict, help_text="Calculation inputs and weights for transparency")

    class Meta:
        db_table = "portfolio_management_performance"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["manager", "recorded_at"]),
            models.Index(fields=["portfolio", "recorded_at"]),
            models.Index(fields=["composite_score"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
        unique_together = [
            ["manager", "portfolio", "period_start", "period_end"],
        ]

    def __str__(self):
        return f"{self.manager.username} - {self.recorded_at.strftime('%Y-%m')} (Score: {self.composite_score:.1f})"

    def calculate_composite_score(self):
        """
        Calculate weighted composite score.
        """
        weights = {
            "success_rate": 0.30,
            "health_score": 0.25,
            "license_utilization": 0.20,
            "deployment_velocity": 0.15,
            "mttr": 0.10,
        }

        # Normalize metrics to 0-100 scale
        success_rate_normalized = self.success_rate_percent  # Already 0-100
        health_score_normalized = self.avg_health_score  # Already 0-100

        # License utilization: optimal is 70-85%, penalize outside range
        if 70 <= self.utilization_percent <= 85:
            license_score = 100
        elif self.utilization_percent < 70:
            license_score = (self.utilization_percent / 70) * 100
        else:  # > 85%
            license_score = 100 - ((self.utilization_percent - 85) / 15) * 50

        # Deployment velocity: target ≤14 days, penalize if longer
        target_days = 14
        if self.avg_deployment_duration_days <= target_days:
            velocity_score = 100
        else:
            velocity_score = max(0, 100 - ((self.avg_deployment_duration_days - target_days) / target_days) * 100)

        # MTTR: target ≤4 hours, penalize if longer
        target_mttr = 4
        if self.avg_mttr_hours <= target_mttr:
            mttr_score = 100
        else:
            mttr_score = max(0, 100 - ((self.avg_mttr_hours - target_mttr) / target_mttr) * 100)

        # Weighted sum
        composite = (
            weights["success_rate"] * success_rate_normalized
            + weights["health_score"] * health_score_normalized
            + weights["license_utilization"] * license_score
            + weights["deployment_velocity"] * velocity_score
            + weights["mttr"] * mttr_score
        )

        self.composite_score = round(composite, 2)
        self.calculation_metadata = {
            "weights": weights,
            "normalized_scores": {
                "success_rate": success_rate_normalized,
                "health_score": health_score_normalized,
                "license_utilization": license_score,
                "deployment_velocity": velocity_score,
                "mttr": mttr_score,
            },
        }


class LicenseTrueUpForecast(models.Model):
    """
    Forecasts license true-up costs for vendor ELA renewals.
    Generated by AI License Management Agent.
    """

    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        "license_management.Vendor",
        on_delete=models.CASCADE,
        related_name="true_up_forecasts",
        help_text="Vendor for this forecast",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="true_up_forecasts",
        help_text="Portfolio context (null = enterprise-wide)",
    )

    # Forecast period
    forecast_period = models.CharField(max_length=20, help_text="Forecast period (e.g., 'Q1_2027', 'FY2027')")
    forecast_generated_at = models.DateTimeField(auto_now_add=True, help_text="When forecast was generated")
    forecast_horizon_days = models.IntegerField(
        default=180, help_text="Forecast horizon in days (e.g., 180 = 6 months)"
    )

    # Current state
    entitled_quantity_current = models.IntegerField(help_text="Current entitled licenses")
    consumed_quantity_current = models.IntegerField(help_text="Current consumed licenses")
    utilization_current_percent = models.FloatField(help_text="(consumed / entitled) × 100")

    # Forecast
    consumed_quantity_forecast = models.IntegerField(help_text="Forecasted consumption at end of period")
    consumption_growth_percent = models.FloatField(help_text="Projected growth rate (%)")
    additional_licenses_needed = models.IntegerField(help_text="Additional licenses needed (if forecast > entitled)")
    estimated_cost_impact = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Estimated cost of additional licenses (USD)"
    )
    confidence_percent = models.FloatField(default=0.0, help_text="Forecast confidence (0-100)")

    # Mitigation strategies
    mitigation_recommendations = models.JSONField(
        default=list,
        help_text="""
        List of mitigation strategies:
        [
            {
                "strategy": "right_sizing",
                "description": "Reduce over-entitled SKUs",
                "licenses_saved": 50,
                "cost_savings": 25000.00
            },
            {
                "strategy": "license_harvesting",
                "description": "Reclaim unused licenses",
                "licenses_saved": 30,
                "cost_savings": 15000.00
            }
        ]
        """,
    )
    potential_savings = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Total potential savings from mitigations (USD)"
    )

    # Model metadata
    model_version = models.CharField(max_length=20, default="v1.0", help_text="Forecast model version")
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Correlation ID for audit trail")
    input_data_summary = models.JSONField(default=dict, help_text="Summary of input data used for forecast")

    class Meta:
        db_table = "portfolio_management_true_up_forecast"
        ordering = ["-forecast_generated_at"]
        indexes = [
            models.Index(fields=["vendor", "forecast_period"]),
            models.Index(fields=["portfolio", "forecast_period"]),
            models.Index(fields=["forecast_generated_at"]),
        ]

    def __str__(self):
        return f"{self.vendor.name} - {self.forecast_period} (Additional: {self.additional_licenses_needed})"


class PackagingRequest(TimeStampedModel):
    """
    Tracks packaging requests from Application Managers to Packaging Engineers.
    """

    # Relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        "application_portfolio.Application",
        on_delete=models.CASCADE,
        related_name="packaging_requests",
        help_text="Application being packaged",
    )
    version_identifier = models.CharField(max_length=100, help_text="Version being packaged (e.g., '2.5.1')")

    # Stakeholders
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="packaging_requests_initiated",
        help_text="Application Manager who requested packaging",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="packaging_requests_assigned",
        help_text="Packaging Engineer assigned to this request",
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending Assignment"),
            ("ASSIGNED", "Assigned to Engineer"),
            ("IN_PROGRESS", "Packaging in Progress"),
            ("VALIDATION", "Lab Validation"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING",
        db_index=True,
        help_text="Current status of packaging request",
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ("LOW", "Low Priority"),
            ("MEDIUM", "Medium Priority"),
            ("HIGH", "High Priority"),
            ("URGENT", "Urgent"),
        ],
        default="MEDIUM",
        help_text="Request priority",
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True, help_text="When request was submitted")
    assigned_at = models.DateTimeField(null=True, blank=True, help_text="When request was assigned to engineer")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When packaging was completed")

    # Requirements
    requirements = models.JSONField(
        default=dict,
        help_text="""
        Packaging requirements:
        {
            "platforms": ["windows", "macos"],
            "signing_required": true,
            "detection_rules": {...},
            "dependencies": [...],
            "notes": "Special instructions"
        }
        """,
    )

    # Deliverables
    artifact = models.ForeignKey(
        "application_portfolio.PackageArtifact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="packaging_requests",
        help_text="Completed artifact (when status=COMPLETED)",
    )
    notes = models.TextField(blank=True, help_text="Engineer notes, issues, resolutions")

    # Audit
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Correlation ID for audit trail")

    class Meta:
        db_table = "portfolio_management_packaging_request"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["requested_by", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["application"]),
        ]

    def __str__(self):
        return f"{self.application.name} v{self.version_identifier} - {self.status}"
