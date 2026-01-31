# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Performance calculation service for Application Managers.

Implements composite score calculation based on deployment success, health, licenses,
packaging velocity, and incident response. Scores are normalized and weighted.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.portfolio_management.models import ApplicationManagerPerformance, ApplicationOwnership, Portfolio

User = get_user_model()


def calculate_manager_performance(
    manager: User,
    portfolio: Optional[Portfolio] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> Dict:
    """
    Calculate performance metrics for an Application Manager.

    Args:
        manager: User instance of the Application Manager
        portfolio: Optional portfolio to scope metrics to
        period_start: Start of measurement period (defaults to 30 days ago)
        period_end: End of measurement period (defaults to now)

    Returns:
        Dictionary of performance metrics with composite score

    Algorithm:
        1. Aggregate deployment metrics (success rate, duration)
        2. Aggregate health metrics (avg health score, incidents)
        3. Aggregate license metrics (utilization %, alerts)
        4. Aggregate packaging metrics (requests, turnaround)
        5. Calculate composite score using weighted formula
    """
    if period_end is None:
        period_end = timezone.now()
    if period_start is None:
        period_start = period_end - timedelta(days=30)

    # Get applications owned by this manager
    ownerships = ApplicationOwnership.objects.filter(owner=manager, is_active=True, ownership_type="PRIMARY")

    if portfolio:
        ownerships = ownerships.filter(portfolio=portfolio)

    application_ids = list(ownerships.values_list("application_id", flat=True))  # noqa: F841

    # Initialize metrics
    metrics = {
        "manager": manager,
        "portfolio": portfolio,
        "period_start": period_start,
        "period_end": period_end,
        "deployments_total": 0,
        "deployments_successful": 0,
        "success_rate_percent": 0.0,
        "avg_deployment_duration_days": 0.0,
        "avg_health_score": 0.0,
        "health_incidents": 0,
        "utilization_percent": 0.0,
        "license_alerts": 0,
        "packaging_requests_total": 0,
        "packaging_requests_completed": 0,
        "avg_packaging_turnaround_days": 0.0,
        "composite_score": 0.0,
    }

    # TODO: Implement actual metric aggregation from deployment_intents, health, licenses
    # For now, this is a placeholder that would query:
    # - DeploymentIntent for deployment metrics
    # - ApplicationHealth for health metrics
    # - License consumption/alerts for license metrics
    # - PackagingRequest for packaging metrics

    # Placeholder: Calculate composite score from current metrics
    metrics["composite_score"] = _calculate_composite_score(metrics)

    return metrics


def _calculate_composite_score(metrics: Dict) -> float:
    """
    Calculate weighted composite score for Application Manager performance.

    Formula (from model docstring):
        composite_score = (
            success_rate * 0.30 +
            health_score * 0.25 +
            license_utilization * 0.20 +
            deployment_velocity * 0.15 +
            mttr * 0.10
        )

    Normalization:
        - success_rate: 0-100% (use as-is)
        - health_score: 0-100 (use as-is)
        - license_utilization: optimal 70-85%, normalize to 0-100 (100 at 77.5%)
        - deployment_velocity: inverse of avg_deployment_duration_days, normalized
        - mttr: inverse of health_incidents response time, normalized

    Args:
        metrics: Dictionary of raw metrics

    Returns:
        Composite score (0-100)
    """
    weights = {
        "success_rate": 0.30,
        "health_score": 0.25,
        "license_utilization": 0.20,
        "deployment_velocity": 0.15,
        "mttr": 0.10,
    }

    # Normalize success rate (already 0-100)
    success_normalized = metrics["success_rate_percent"]

    # Normalize health score (already 0-100)
    health_normalized = metrics["avg_health_score"]

    # Normalize license utilization (optimal range 70-85%, peak at 77.5%)
    license_util = metrics["utilization_percent"]
    if license_util < 70:
        # Below optimal: linear scale 0-100 for 0-70%
        license_normalized = (license_util / 70) * 100
    elif license_util <= 85:
        # Within optimal range: 100 points
        license_normalized = 100
    else:
        # Above optimal: deduct points (100 at 85%, 0 at 150%)
        license_normalized = max(0, 100 - ((license_util - 85) / 0.65))

    # Normalize deployment velocity (inverse of duration, cap at 14 days)
    avg_duration = metrics["avg_deployment_duration_days"]
    if avg_duration == 0:
        velocity_normalized = 100
    else:
        # Optimal: 1 day = 100 points, 14 days = 0 points
        velocity_normalized = max(0, 100 - ((avg_duration - 1) / 13) * 100)

    # Normalize MTTR (placeholder: based on health incidents)
    # TODO: Implement proper MTTR calculation from incident timestamps
    incidents = metrics["health_incidents"]
    if incidents == 0:
        mttr_normalized = 100
    else:
        # Placeholder: inverse of incident count (more incidents = lower score)
        mttr_normalized = max(0, 100 - (incidents * 10))

    # Calculate weighted composite score
    composite_score = (
        success_normalized * weights["success_rate"]
        + health_normalized * weights["health_score"]
        + license_normalized * weights["license_utilization"]
        + velocity_normalized * weights["deployment_velocity"]
        + mttr_normalized * weights["mttr"]
    )

    return round(composite_score, 2)


def record_manager_performance(
    manager: User,
    portfolio: Optional[Portfolio] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> ApplicationManagerPerformance:
    """
    Calculate and record performance snapshot for an Application Manager.

    This should be called by a background job (e.g., Celery task) to periodically
    record performance snapshots for trend analysis.

    Args:
        manager: User instance of the Application Manager
        portfolio: Optional portfolio to scope metrics to
        period_start: Start of measurement period
        period_end: End of measurement period

    Returns:
        Created ApplicationManagerPerformance instance
    """
    metrics = calculate_manager_performance(manager, portfolio, period_start, period_end)

    # Create performance snapshot
    performance = ApplicationManagerPerformance.objects.create(**metrics)

    return performance
