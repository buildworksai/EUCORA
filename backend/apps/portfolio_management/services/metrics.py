# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Portfolio metrics aggregation service.

Aggregates cached metrics for portfolios including application counts,
license utilization, health scores, and compliance scores.
"""
from typing import Dict

from django.db.models import Sum

from apps.application_portfolio.models import Application, ApplicationHealth
from apps.license_management.models import ConsumptionSnapshot, LicensePool
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
    application_ids = list(active_ownerships.values_list("application_id", flat=True))

    # Get applications
    applications = Application.objects.filter(id__in=application_ids)

    # Sum licenses entitled from Entitlements
    # Note: LicenseSKU doesn't have direct application linkage in current model
    # For now, sum all active entitlements (in future, would link via consumption signals)
    from apps.license_management.models import Entitlement, EntitlementStatus

    entitlements = Entitlement.objects.filter(
        status=EntitlementStatus.ACTIVE,
    )
    total_licenses_entitled = entitlements.aggregate(total=Sum("entitled_quantity"))["total"] or 0

    # Add pool overrides for all pools
    pools = LicensePool.objects.filter(is_active=True)
    pool_overrides = (
        pools.exclude(entitled_quantity_override__isnull=True).aggregate(total=Sum("entitled_quantity_override"))[
            "total"
        ]
        or 0
    )
    total_licenses_entitled += pool_overrides

    # Sum licenses consumed from latest ConsumptionSnapshot
    # Get latest snapshot per SKU
    total_licenses_consumed = 0
    processed_skus = set()
    for snapshot in ConsumptionSnapshot.objects.order_by("sku", "-reconciled_at"):
        if snapshot.sku_id not in processed_skus:
            total_licenses_consumed += snapshot.consumed
            processed_skus.add(snapshot.sku_id)

    # Average health score from ApplicationHealth
    # Get latest snapshot per application
    latest_snapshots = []
    for app in applications:
        latest = ApplicationHealth.objects.filter(application=app).order_by("-recorded_at").first()
        if latest:
            latest_snapshots.append(latest)

    if latest_snapshots:
        health_avg = sum(float(s.compliance_score) for s in latest_snapshots) / len(latest_snapshots)
        health_score = health_avg
        compliance_score = health_avg  # Using same field for both
    else:
        health_score = 0.0
        compliance_score = 0.0

    metrics = {
        "total_applications": total_applications,
        "total_licenses_entitled": total_licenses_entitled,
        "total_licenses_consumed": total_licenses_consumed,
        "health_score": health_score,
        "compliance_score": compliance_score,
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
