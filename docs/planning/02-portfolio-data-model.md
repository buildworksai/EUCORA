# Portfolio Management Data Model

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Phase**: 0 — Foundation
**Document Version**: 1.0
**Date**: 2026-01-30

---

## Overview

This document defines the database schema for Portfolio Management, Application Ownership, and Performance Analytics features.

### Design Principles

1. **Separation of Concerns**: Portfolio management models are distinct from application_portfolio core models
2. **Time-Series Analytics**: Performance metrics stored as time-series for trend analysis
3. **Immutability**: Performance snapshots are immutable once created (append-only)
4. **Correlation ID Threading**: All deployment events linked via correlation_id for audit trails
5. **Soft Deletes**: Portfolios and ownerships use soft deletes (is_active flag) for audit history

---

## Entity Relationship Diagram

```
┌─────────────────┐
│   Portfolio     │
│                 │
│ - id (PK)       │
│ - name          │
│ - manager_id    │◄───────┐
│ - scope (JSON)  │        │
│ - budget        │        │
│ - cost_center   │        │
│ - metrics       │        │
└────────┬────────┘        │
         │                 │
         │ 1               │
         │                 │
         │                 │
         │ N               │ 1
         │                 │
┌────────▼────────────────┐│
│ ApplicationOwnership    ││
│                         ││
│ - id (PK)               ││
│ - application_id (FK)   ││
│ - owner_id (FK) ────────┘
│ - portfolio_id (FK)     │
│ - ownership_type        │
│ - assigned_at           │
│ - assigned_by_id (FK)   │
└────────┬────────────────┘
         │
         │ 1
         │
         │
         │ 1
         │
┌────────▼────────────────────────────┐
│         Application                 │
│  (from application_portfolio app)   │
│                                     │
│ - id (PK)                           │
│ - identifier                        │
│ - name                              │
│ - publisher_id (FK)                 │
│ - category                          │
│ - status                            │
│ - risk_score                        │
└─────────────────────────────────────┘


┌──────────────────────────────────────┐
│  ApplicationManagerPerformance       │
│                                      │
│ - id (PK)                            │
│ - manager_id (FK)                    │
│ - portfolio_id (FK)                  │
│ - recorded_at (indexed)              │
│ - deployment_metrics (JSON)          │
│ - health_metrics (JSON)              │
│ - license_metrics (JSON)             │
│ - incident_metrics (JSON)            │
│ - composite_score                    │
└──────────────────────────────────────┘


┌──────────────────────────────────────┐
│      LicenseTrueUpForecast           │
│                                      │
│ - id (PK)                            │
│ - vendor_id (FK)                     │
│ - portfolio_id (FK) [optional]       │
│ - forecast_period                    │
│ - forecast_generated_at              │
│ - current_state (JSON)               │
│ - forecast_state (JSON)              │
│ - mitigation_strategies (JSON)       │
│ - model_version                      │
│ - correlation_id                     │
└──────────────────────────────────────┘


┌──────────────────────────────────────┐
│      PackagingRequest                │
│                                      │
│ - id (PK)                            │
│ - application_id (FK)                │
│ - requested_by_id (FK)               │
│ - assigned_to_id (FK) [engineer]     │
│ - status                             │
│ - priority                           │
│ - requested_at                       │
│ - completed_at                       │
│ - artifact_id (FK) [when complete]   │
└──────────────────────────────────────┘
```

---

## Model Specifications

### 1. Portfolio

**Purpose**: Represents a collection of applications managed by a Portfolio Manager.

```python
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel

User = get_user_model()


class Portfolio(TimeStampedModel):
    """
    Portfolio of applications managed by a Portfolio Manager.
    Used for cost tracking, performance analytics, and strategic planning.
    """

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        help_text="Portfolio name (e.g., 'Finance Applications', 'HR Suite')"
    )
    description = models.TextField(blank=True)

    # Ownership
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_portfolios',
        help_text="Portfolio Manager responsible for this portfolio"
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
        """
    )

    # Budget and cost tracking
    budget_annual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Annual budget for this portfolio (USD)"
    )
    cost_center = models.CharField(
        max_length=100,
        blank=True,
        help_text="Finance cost center code"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Soft delete flag"
    )

    # Cached metrics (updated by background job)
    total_applications = models.IntegerField(
        default=0,
        help_text="Count of active applications in portfolio"
    )
    total_licenses_entitled = models.IntegerField(
        default=0,
        help_text="Total licenses entitled across all SKUs"
    )
    total_licenses_consumed = models.IntegerField(
        default=0,
        help_text="Total licenses consumed across all SKUs"
    )
    total_cost_annual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total annual cost (licenses + deployment overhead)"
    )
    health_score = models.FloatField(
        default=0.0,
        help_text="Aggregate health score (0-100)"
    )
    compliance_score = models.FloatField(
        default=0.0,
        help_text="Aggregate compliance score (0-100)"
    )

    # Metadata
    last_metrics_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time metrics were recomputed"
    )

    class Meta:
        db_table = 'portfolio_management_portfolio'
        ordering = ['name']
        indexes = [
            models.Index(fields=['manager', 'is_active']),
            models.Index(fields=['health_score']),
            models.Index(fields=['compliance_score']),
        ]

    def __str__(self):
        return f"{self.name} (Manager: {self.manager.username if self.manager else 'Unassigned'})"

    @property
    def license_utilization_percent(self):
        """Calculate license utilization percentage."""
        if self.total_licenses_entitled == 0:
            return 0.0
        return (self.total_licenses_consumed / self.total_licenses_entitled) * 100
```

### 2. ApplicationOwnership

**Purpose**: Links applications to Application Managers and Portfolios.

```python
class ApplicationOwnership(TimeStampedModel):
    """
    Maps applications to their owners (Application Managers) and portfolios.
    Supports co-ownership (PRIMARY and SECONDARY owners).
    """

    # Relationships
    application = models.ForeignKey(
        'application_portfolio.Application',
        on_delete=models.CASCADE,
        related_name='ownerships',
        help_text="Application being owned"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_applications',
        help_text="Application Manager who owns this application"
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='application_ownerships',
        help_text="Portfolio this application belongs to"
    )

    # Ownership type
    ownership_type = models.CharField(
        max_length=20,
        choices=[
            ('PRIMARY', 'Primary Owner'),
            ('SECONDARY', 'Secondary Owner / Backup'),
        ],
        default='PRIMARY',
        help_text="Type of ownership (PRIMARY or SECONDARY)"
    )

    # Assignment tracking
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When ownership was assigned"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ownership_assignments',
        help_text="Portfolio Manager who assigned ownership"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Soft delete flag"
    )

    class Meta:
        db_table = 'portfolio_management_ownership'
        ordering = ['-assigned_at']
        unique_together = [
            ['application', 'owner', 'ownership_type'],  # Prevent duplicate ownerships
        ]
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['portfolio', 'is_active']),
            models.Index(fields=['application', 'ownership_type']),
        ]

    def __str__(self):
        return f"{self.application.name} → {self.owner.username} ({self.ownership_type})"
```

### 3. ApplicationManagerPerformance

**Purpose**: Time-series snapshots of Application Manager performance metrics.

```python
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
        related_name='performance_snapshots',
        help_text="Application Manager"
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='manager_performance_snapshots',
        help_text="Portfolio context for this performance snapshot"
    )

    # Time period
    recorded_at = models.DateTimeField(
        db_index=True,
        help_text="Snapshot timestamp"
    )
    period_start = models.DateTimeField(
        help_text="Start of measurement period (e.g., start of month)"
    )
    period_end = models.DateTimeField(
        help_text="End of measurement period (e.g., end of month)"
    )

    # Deployment metrics
    deployments_total = models.IntegerField(
        default=0,
        help_text="Total deployments in period"
    )
    deployments_successful = models.IntegerField(
        default=0,
        help_text="Successful deployments (reached Global ring)"
    )
    deployments_failed = models.IntegerField(
        default=0,
        help_text="Failed deployments (never reached Global)"
    )
    deployments_rolled_back = models.IntegerField(
        default=0,
        help_text="Deployments that were rolled back"
    )
    avg_deployment_duration_days = models.FloatField(
        default=0.0,
        help_text="Average days from CAB submission to Global completion"
    )
    success_rate_percent = models.FloatField(
        default=0.0,
        help_text="(successful / total) × 100"
    )

    # Application health metrics
    applications_total = models.IntegerField(
        default=0,
        help_text="Total applications owned"
    )
    applications_healthy = models.IntegerField(
        default=0,
        help_text="Applications with health ≥ 90%"
    )
    applications_degraded = models.IntegerField(
        default=0,
        help_text="Applications with 70% ≤ health < 90%"
    )
    applications_critical = models.IntegerField(
        default=0,
        help_text="Applications with health < 70%"
    )
    avg_health_score = models.FloatField(
        default=0.0,
        help_text="Average health score across applications (0-100)"
    )

    # License efficiency metrics
    licenses_entitled = models.IntegerField(
        default=0,
        help_text="Total licenses entitled"
    )
    licenses_consumed = models.IntegerField(
        default=0,
        help_text="Total licenses consumed"
    )
    licenses_wasted = models.IntegerField(
        default=0,
        help_text="Over-entitled licenses (entitled - consumed, if positive)"
    )
    utilization_percent = models.FloatField(
        default=0.0,
        help_text="(consumed / entitled) × 100"
    )

    # Incident metrics
    incidents_total = models.IntegerField(
        default=0,
        help_text="Total incidents in period"
    )
    incidents_resolved = models.IntegerField(
        default=0,
        help_text="Incidents resolved in period"
    )
    avg_mttr_hours = models.FloatField(
        default=0.0,
        help_text="Mean time to resolution (hours)"
    )

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
        """
    )

    # Metadata
    calculation_metadata = models.JSONField(
        default=dict,
        help_text="Calculation inputs and weights for transparency"
    )

    class Meta:
        db_table = 'portfolio_management_performance'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['manager', 'recorded_at']),
            models.Index(fields=['portfolio', 'recorded_at']),
            models.Index(fields=['composite_score']),
            models.Index(fields=['period_start', 'period_end']),
        ]
        unique_together = [
            ['manager', 'portfolio', 'period_start', 'period_end'],
        ]

    def __str__(self):
        return f"{self.manager.username} - {self.recorded_at.strftime('%Y-%m')} (Score: {self.composite_score:.1f})"

    def calculate_composite_score(self):
        """
        Calculate weighted composite score.
        """
        weights = {
            'success_rate': 0.30,
            'health_score': 0.25,
            'license_utilization': 0.20,
            'deployment_velocity': 0.15,
            'mttr': 0.10,
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
            weights['success_rate'] * success_rate_normalized +
            weights['health_score'] * health_score_normalized +
            weights['license_utilization'] * license_score +
            weights['deployment_velocity'] * velocity_score +
            weights['mttr'] * mttr_score
        )

        self.composite_score = round(composite, 2)
        self.calculation_metadata = {
            'weights': weights,
            'normalized_scores': {
                'success_rate': success_rate_normalized,
                'health_score': health_score_normalized,
                'license_utilization': license_score,
                'deployment_velocity': velocity_score,
                'mttr': mttr_score,
            },
        }
```

### 4. LicenseTrueUpForecast

**Purpose**: Forecast license true-up costs for vendor ELA renewals.

```python
class LicenseTrueUpForecast(models.Model):
    """
    Forecasts license true-up costs for vendor ELA renewals.
    Generated by AI License Management Agent.
    """

    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        'license_management.Vendor',
        on_delete=models.CASCADE,
        related_name='true_up_forecasts',
        help_text="Vendor for this forecast"
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='true_up_forecasts',
        help_text="Portfolio context (null = enterprise-wide)"
    )

    # Forecast period
    forecast_period = models.CharField(
        max_length=20,
        help_text="Forecast period (e.g., 'Q1_2027', 'FY2027')"
    )
    forecast_generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When forecast was generated"
    )
    forecast_horizon_days = models.IntegerField(
        default=180,
        help_text="Forecast horizon in days (e.g., 180 = 6 months)"
    )

    # Current state
    entitled_quantity_current = models.IntegerField(
        help_text="Current entitled licenses"
    )
    consumed_quantity_current = models.IntegerField(
        help_text="Current consumed licenses"
    )
    utilization_current_percent = models.FloatField(
        help_text="(consumed / entitled) × 100"
    )

    # Forecast
    consumed_quantity_forecast = models.IntegerField(
        help_text="Forecasted consumption at end of period"
    )
    consumption_growth_percent = models.FloatField(
        help_text="Projected growth rate (%)"
    )
    additional_licenses_needed = models.IntegerField(
        help_text="Additional licenses needed (if forecast > entitled)"
    )
    estimated_cost_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Estimated cost of additional licenses (USD)"
    )
    confidence_percent = models.FloatField(
        default=0.0,
        help_text="Forecast confidence (0-100)"
    )

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
        """
    )
    potential_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total potential savings from mitigations (USD)"
    )

    # Model metadata
    model_version = models.CharField(
        max_length=20,
        default='v1.0',
        help_text="Forecast model version"
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Correlation ID for audit trail"
    )
    input_data_summary = models.JSONField(
        default=dict,
        help_text="Summary of input data used for forecast"
    )

    class Meta:
        db_table = 'portfolio_management_true_up_forecast'
        ordering = ['-forecast_generated_at']
        indexes = [
            models.Index(fields=['vendor', 'forecast_period']),
            models.Index(fields=['portfolio', 'forecast_period']),
            models.Index(fields=['forecast_generated_at']),
        ]

    def __str__(self):
        return f"{self.vendor.name} - {self.forecast_period} (Additional: {self.additional_licenses_needed})"
```

### 5. PackagingRequest

**Purpose**: Track packaging requests from Application Managers to Packaging Engineers.

```python
class PackagingRequest(TimeStampedModel):
    """
    Tracks packaging requests from Application Managers to Packaging Engineers.
    """

    # Relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'application_portfolio.Application',
        on_delete=models.CASCADE,
        related_name='packaging_requests',
        help_text="Application being packaged"
    )
    version_identifier = models.CharField(
        max_length=100,
        help_text="Version being packaged (e.g., '2.5.1')"
    )

    # Stakeholders
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='packaging_requests_initiated',
        help_text="Application Manager who requested packaging"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packaging_requests_assigned',
        help_text="Packaging Engineer assigned to this request"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Assignment'),
            ('ASSIGNED', 'Assigned to Engineer'),
            ('IN_PROGRESS', 'Packaging in Progress'),
            ('VALIDATION', 'Lab Validation'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PENDING',
        db_index=True,
        help_text="Current status of packaging request"
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Low Priority'),
            ('MEDIUM', 'Medium Priority'),
            ('HIGH', 'High Priority'),
            ('URGENT', 'Urgent'),
        ],
        default='MEDIUM',
        help_text="Request priority"
    )

    # Timestamps
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When request was submitted"
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When request was assigned to engineer"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When packaging was completed"
    )

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
        """
    )

    # Deliverables
    artifact = models.ForeignKey(
        'application_portfolio.PackageArtifact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packaging_requests',
        help_text="Completed artifact (when status=COMPLETED)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Engineer notes, issues, resolutions"
    )

    # Audit
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Correlation ID for audit trail"
    )

    class Meta:
        db_table = 'portfolio_management_packaging_request'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['requested_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['application']),
        ]

    def __str__(self):
        return f"{self.application.name} v{self.version_identifier} - {self.status}"
```

---

## Database Migrations

### Migration Plan

**Migration 0001: Create Portfolio Management Tables**
```python
# apps/portfolio_management/migrations/0001_initial.py

operations = [
    migrations.CreateModel(
        name='Portfolio',
        fields=[...],  # As defined above
    ),
    migrations.CreateModel(
        name='ApplicationOwnership',
        fields=[...],
    ),
    migrations.CreateModel(
        name='ApplicationManagerPerformance',
        fields=[...],
    ),
    migrations.CreateModel(
        name='LicenseTrueUpForecast',
        fields=[...],
    ),
    migrations.CreateModel(
        name='PackagingRequest',
        fields=[...],
    ),
]
```

### Data Population

**Populate Demo Data**:
```python
# In demo_data.py

def _seed_portfolios(count=3):
    """Create demo portfolios with Application Managers."""
    portfolios = [
        {
            'name': 'Finance Applications',
            'description': 'Applications for Finance department',
            'scope': {
                'business_unit': 'Finance',
                'geography': ['US', 'EMEA'],
            },
            'budget_annual': 500000,
            'cost_center': 'FIN-001',
        },
        {
            'name': 'HR Suite',
            'description': 'Human Resources applications',
            'scope': {
                'business_unit': 'HR',
                'geography': ['Global'],
            },
            'budget_annual': 300000,
            'cost_center': 'HR-001',
        },
        {
            'name': 'Engineering Tools',
            'description': 'Developer productivity tools',
            'scope': {
                'business_unit': 'Engineering',
                'geography': ['US', 'APAC'],
            },
            'budget_annual': 750000,
            'cost_center': 'ENG-001',
        },
    ]

    # Create portfolios with managers
    # Assign applications to portfolios with ownerships
    # Generate performance snapshots
```

---

## API Endpoints

### Portfolio Management Endpoints

```python
# GET /api/v1/portfolios/
# List all portfolios (filtered by user role)

# POST /api/v1/portfolios/
# Create new portfolio (Portfolio Manager or Admin)

# GET /api/v1/portfolios/{portfolio_id}/
# Get portfolio details

# PATCH /api/v1/portfolios/{portfolio_id}/
# Update portfolio metadata

# DELETE /api/v1/portfolios/{portfolio_id}/
# Soft delete portfolio (is_active = False)

# GET /api/v1/portfolios/{portfolio_id}/dashboard/
# Get portfolio dashboard data (applications, metrics, health)

# GET /api/v1/portfolios/{portfolio_id}/performance/
# Get team performance metrics for portfolio

# GET /api/v1/portfolios/{portfolio_id}/cost-analysis/
# Get cost breakdown (licenses, deployment, support)

# POST /api/v1/portfolios/{portfolio_id}/assign-application/
# Assign application to portfolio with owner
```

### Application Ownership Endpoints

```python
# POST /api/v1/applications/{app_id}/assign-owner/
# Assign Application Manager to application

# GET /api/v1/applications/my-applications/
# Get applications owned by current user

# GET /api/v1/applications/{app_id}/owners/
# List all owners (primary + secondary)
```

### Packaging Request Endpoints

```python
# POST /api/v1/packaging-requests/
# Create packaging request

# GET /api/v1/packaging-requests/
# List packaging requests (filtered by role)

# GET /api/v1/packaging-requests/{request_id}/
# Get packaging request details

# PATCH /api/v1/packaging-requests/{request_id}/
# Update packaging request (assign engineer, update status)

# POST /api/v1/packaging-requests/{request_id}/complete/
# Mark packaging request as completed (with artifact)
```

---

## Performance Considerations

### Caching Strategy

**Portfolio Metrics Caching**:
- Portfolio aggregate metrics (health_score, compliance_score, total_cost) are cached in Portfolio model
- Updated by scheduled background job (every 1 hour)
- Cache invalidation triggered by:
  - New deployment completion
  - Application health change
  - License consumption reconciliation

**Performance Snapshot Generation**:
- ApplicationManagerPerformance snapshots generated daily at midnight
- Immutable once created (append-only)
- Indexed on (manager, recorded_at) for efficient time-series queries

### Query Optimization

**Materialized Views** (PostgreSQL):
```sql
CREATE MATERIALIZED VIEW portfolio_manager_rankings AS
SELECT
    p.id AS portfolio_id,
    p.name AS portfolio_name,
    amp.manager_id,
    u.username AS manager_username,
    AVG(amp.composite_score) AS avg_composite_score,
    COUNT(amp.id) AS snapshot_count
FROM
    portfolio_management_performance amp
JOIN
    portfolio_management_portfolio p ON amp.portfolio_id = p.id
JOIN
    auth_user u ON amp.manager_id = u.id
WHERE
    amp.recorded_at >= NOW() - INTERVAL '90 days'
GROUP BY
    p.id, p.name, amp.manager_id, u.username
ORDER BY
    avg_composite_score DESC;

-- Refresh daily
REFRESH MATERIALIZED VIEW portfolio_manager_rankings;
```

---

## Security Considerations

### Role-Based Access Control (RBAC)

**Portfolio Manager**:
- Can view/edit own portfolios
- Can view all applications in their portfolios
- Can assign/reassign Application Managers
- Can approve CAB requests for their portfolios (high-risk deployments)

**Application Manager**:
- Can view/edit applications they own
- Can create packaging requests
- Can create deployment intents for their applications
- Can view performance metrics for their applications

**Packaging Engineer**:
- Can view all packaging requests
- Can create/update artifacts
- Cannot create deployments

### Data Isolation

**Row-Level Security** (PostgreSQL RLS):
```sql
-- Portfolio Managers can only access their own portfolios
CREATE POLICY portfolio_manager_access ON portfolio_management_portfolio
    FOR ALL
    USING (manager_id = current_user_id());

-- Application Managers can only access applications they own
CREATE POLICY application_owner_access ON portfolio_management_ownership
    FOR ALL
    USING (owner_id = current_user_id());
```

---

## Testing Strategy

### Unit Tests

**Model Tests**:
- Portfolio CRUD operations
- ApplicationOwnership assignment/revocation
- ApplicationManagerPerformance composite score calculation
- LicenseTrueUpForecast mitigation strategies

**Service Tests**:
- Performance metrics aggregation
- True-up forecasting engine
- Portfolio dashboard data generation

### Integration Tests

**End-to-End Workflows**:
- Application Manager creates packaging request → Packaging Engineer completes → Application Manager deploys
- Portfolio Manager assigns ownership → Application Manager creates deployment → Portfolio Manager reviews performance
- License true-up forecast → mitigation execution → savings tracking

---

## Next Steps

1. **Create Django app**: `python manage.py startapp portfolio_management`
2. **Implement models**: Copy model specifications to `models.py`
3. **Create migrations**: `python manage.py makemigrations portfolio_management`
4. **Run migrations**: `python manage.py migrate`
5. **Implement serializers**: DRF serializers for API endpoints
6. **Implement views**: DRF viewsets for CRUD operations
7. **Implement services**: Business logic for performance calculation, forecasting
8. **Write tests**: Unit + integration tests
9. **Populate demo data**: Extend `demo_data.py` with portfolio data

---

**Document Owner**: Backend Engineering Lead
**Review Required From**: Database Architect, Security Reviewer
**Next Review Date**: 2026-02-06
