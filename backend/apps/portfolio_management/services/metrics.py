# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Portfolio metrics aggregation service.

Aggregates cached metrics for portfolios including application counts,
license utilization, health scores, and compliance scores.
"""
from typing import Dict

from apps.portfolio_management.models import ApplicationOwnership, Portfolio


def aggregate_portfolio_metrics(portfolio: Portfolio) -> Dict:
    """
    Aggregate and refresh cached metrics for a portfolio.

    This calculates:
    - Total applications in portfolio
    - Total licenses entitled (from all SKUs for apps in portfolio)
    - Total licenses consumed
    - Average health score across all apps
    - Average compliance score across all apps

    Args:
        portfolio: Portfolio instance to aggregate metrics for

    Returns:
        Dictionary of aggregated metrics

    Algorithm:
        1. Count active application ownerships
        2. Sum entitled licenses from license pools for portfolio apps
        3. Sum consumed licenses from consumption snapshots
        4. Average health scores from ApplicationHealth
        5. Average compliance scores from ApplicationHealth
    """
    # Get active applications in portfolio
    active_ownerships = ApplicationOwnership.objects.filter(
        portfolio=portfolio, is_active=True, ownership_type="PRIMARY"
    )

    total_applications = active_ownerships.count()
    application_ids = list(active_ownerships.values_list("application_id", flat=True))  # noqa: F841

    # TODO: Implement actual aggregation from license and health data
    # For now, return placeholder metrics

    metrics = {
        "total_applications": total_applications,
        "total_licenses_entitled": 0,  # TODO: Sum from LicensePool for apps
        "total_licenses_consumed": 0,  # TODO: Sum from ConsumptionSnapshot for apps
        "health_score": 0.0,  # TODO: Average from ApplicationHealth
        "compliance_score": 0.0,  # TODO: Average from ApplicationHealth
    }

    return metrics


def refresh_portfolio_metrics(portfolio: Portfolio) -> Portfolio:
    """
    Refresh and persist cached metrics for a portfolio.

    This should be called by a background job when:
    - Applications are added/removed from portfolio
    - License data changes
    - Health scores are updated

    Args:
        portfolio: Portfolio instance to refresh

    Returns:
        Updated Portfolio instance
    """
    metrics = aggregate_portfolio_metrics(portfolio)

    # Update cached metrics
    portfolio.total_applications = metrics["total_applications"]
    portfolio.total_licenses_entitled = metrics["total_licenses_entitled"]
    portfolio.total_licenses_consumed = metrics["total_licenses_consumed"]
    portfolio.health_score = metrics["health_score"]
    portfolio.compliance_score = metrics["compliance_score"]

    portfolio.save(
        update_fields=[
            "total_applications",
            "total_licenses_entitled",
            "total_licenses_consumed",
            "health_score",
            "compliance_score",
            "updated_at",
        ]
    )

    return portfolio


def refresh_all_portfolio_metrics() -> int:
    """
    Refresh cached metrics for all active portfolios.

    This should be called by a periodic background job (e.g., hourly).

    Returns:
        Number of portfolios updated
    """
    portfolios = Portfolio.objects.all()
    count = 0

    for portfolio in portfolios:
        refresh_portfolio_metrics(portfolio)
        count += 1

    return count
