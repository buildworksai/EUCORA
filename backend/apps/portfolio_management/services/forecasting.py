# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
License true-up forecasting service.

Generates predictions for vendor ELA renewals including true-up quantities
and costs based on historical consumption trends and growth projections.
"""
from datetime import timedelta
from decimal import Decimal
from typing import Dict

from django.db.models import Avg
from django.utils import timezone

from apps.license_management.models import ConsumptionSnapshot, LicenseSKU, Vendor
from apps.portfolio_management.models import LicenseTrueUpForecast, Portfolio


def generate_license_true_up_forecast(
    vendor: Vendor,
    portfolio: Portfolio,
    forecast_period: str,
    entitled_quantity: int,
) -> LicenseTrueUpForecast:
    """
    Generate a license true-up forecast for a vendor ELA renewal.

    Args:
        vendor: Vendor instance
        portfolio: Portfolio instance to scope forecast to
        forecast_period: Period identifier (e.g., "2026-Q4", "FY2027")
        entitled_quantity: Current entitled quantity from ELA

    Returns:
        Created LicenseTrueUpForecast instance

    Algorithm:
        1. Gather historical consumption data for vendor SKUs in portfolio
        2. Calculate growth trend (linear regression or simple average growth)
        3. Project consumption to forecast period
        4. Calculate true-up quantity (projected - entitled)
        5. Calculate true-up cost (true-up qty * avg cost per unit)
        6. Determine risk level based on true-up magnitude
        7. Generate recommendations for Portfolio Manager
    """
    # TODO: Implement actual forecasting logic
    # For now, this is a placeholder that would:
    # 1. Query ConsumptionSnapshot for vendor SKUs in portfolio
    # 2. Calculate trend from historical data
    # 3. Project future consumption
    # 4. Determine risk level and recommendations

    # Placeholder calculations
    projected_consumption = _project_consumption(vendor, portfolio, forecast_period, entitled_quantity)
    true_up_quantity = max(0, projected_consumption - entitled_quantity)
    true_up_cost = _calculate_true_up_cost(vendor, true_up_quantity)
    risk_level = _determine_risk_level(true_up_quantity, entitled_quantity)
    confidence_score = _calculate_confidence_score(vendor, portfolio)
    recommendations = _generate_recommendations(vendor, true_up_quantity, entitled_quantity, risk_level)

    # Create forecast
    forecast = LicenseTrueUpForecast.objects.create(
        vendor=vendor,
        portfolio=portfolio,
        forecast_period=forecast_period,
        forecast_generated_at=timezone.now(),
        entitled_quantity=entitled_quantity,
        projected_consumption=projected_consumption,
        true_up_quantity=true_up_quantity,
        true_up_cost=true_up_cost,
        recommendations=recommendations,
        risk_level=risk_level,
        confidence_score=confidence_score,
    )

    return forecast


def _project_consumption(vendor: Vendor, portfolio: Portfolio, forecast_period: str, entitled_quantity: int) -> int:
    """
    Project future consumption based on historical trends.

    Uses ConsumptionSnapshot data to calculate growth trend and project future consumption.

    Args:
        vendor: Vendor instance
        portfolio: Portfolio instance
        forecast_period: Period identifier
        entitled_quantity: Current entitled quantity

    Returns:
        Projected consumption quantity
    """
    # Get SKUs for vendor in portfolio
    # portfolio_apps = ApplicationOwnership.objects.filter(portfolio=portfolio, is_active=True).values_list(
    #     "application_id", flat=True
    # )

    skus = LicenseSKU.objects.filter(vendor=vendor, is_active=True)
    # Filter SKUs by portfolio applications if possible
    # For now, use all vendor SKUs

    # Get historical consumption snapshots (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    snapshots = ConsumptionSnapshot.objects.filter(
        sku__in=skus,
        reconciled_at__gte=six_months_ago,
    ).order_by("reconciled_at")

    if not snapshots.exists():
        # No historical data - use conservative 5% growth
        return int(entitled_quantity * 1.05)

    # Calculate average consumption from snapshots
    avg_consumption = snapshots.aggregate(avg=Avg("consumed"))["avg"] or 0

    # Get most recent snapshot
    latest_snapshot = snapshots.order_by("-reconciled_at").first()
    current_consumption = latest_snapshot.consumed if latest_snapshot else entitled_quantity

    # Calculate growth rate from historical data
    if len(snapshots) >= 2:
        # Simple linear growth calculation
        first_consumption = snapshots.first().consumed
        last_consumption = snapshots.last().consumed

        if first_consumption > 0:
            growth_rate = (last_consumption / first_consumption) ** (1.0 / max(1, len(snapshots) - 1))
        else:
            growth_rate = 1.10  # Default 10% growth
    else:
        # Not enough data - use average vs current
        if avg_consumption > 0 and current_consumption > 0:
            growth_rate = current_consumption / avg_consumption
        else:
            growth_rate = 1.10  # Default 10% growth

    # Cap growth rate at reasonable bounds (0.95 to 1.20 = -5% to +20%)
    growth_rate = max(0.95, min(1.20, growth_rate))

    # Project consumption
    projected = int(current_consumption * growth_rate)

    return projected


def _calculate_true_up_cost(vendor: Vendor, true_up_quantity: int) -> Decimal:
    """
    Calculate estimated cost for true-up quantity.

    Args:
        vendor: Vendor instance
        true_up_quantity: Number of licenses to true-up

    Returns:
        Estimated cost in Decimal
    """
    # TODO: Get actual cost per unit from LicenseSKU
    # Placeholder: $100 per license
    avg_cost_per_unit = Decimal("100.00")

    skus = LicenseSKU.objects.filter(vendor=vendor, is_active=True)
    if skus.exists():
        # Get average cost from SKUs with cost data
        skus_with_cost = skus.exclude(cost_per_unit__isnull=True)
        if skus_with_cost.exists():
            avg_cost_per_unit = skus_with_cost.aggregate(Avg("cost_per_unit"))["cost_per_unit__avg"]

    true_up_cost = avg_cost_per_unit * Decimal(true_up_quantity)

    return true_up_cost


def _determine_risk_level(true_up_quantity: int, entitled_quantity: int) -> str:
    """
    Determine risk level based on true-up magnitude.

    Risk levels:
    - LOW: < 10% true-up
    - MEDIUM: 10-25% true-up
    - HIGH: 25-50% true-up
    - CRITICAL: > 50% true-up

    Args:
        true_up_quantity: Number of licenses to true-up
        entitled_quantity: Current entitled quantity

    Returns:
        Risk level string (LOW, MEDIUM, HIGH, CRITICAL)
    """
    if entitled_quantity == 0:
        return "LOW"

    true_up_percent = (true_up_quantity / entitled_quantity) * 100

    if true_up_percent < 10:
        return "LOW"
    elif true_up_percent < 25:
        return "MEDIUM"
    elif true_up_percent < 50:
        return "HIGH"
    else:
        return "CRITICAL"


def _calculate_confidence_score(vendor: Vendor, portfolio: Portfolio) -> float:
    """
    Calculate confidence score for forecast based on data quality.

    Factors:
    - Historical data availability (more data = higher confidence)
    - Consumption pattern stability (stable = higher confidence)
    - Recent data recency (recent = higher confidence)

    Args:
        vendor: Vendor instance
        portfolio: Portfolio instance

    Returns:
        Confidence score (0.0-1.0)
    """
    # Get SKUs for vendor
    skus = LicenseSKU.objects.filter(vendor=vendor, is_active=True)

    # Get historical snapshots
    six_months_ago = timezone.now() - timedelta(days=180)
    snapshots = ConsumptionSnapshot.objects.filter(
        sku__in=skus,
        reconciled_at__gte=six_months_ago,
    ).order_by("reconciled_at")

    if not snapshots.exists():
        return 0.3  # Low confidence - no historical data

    snapshot_count = snapshots.count()

    # Factor 1: Data availability (0-0.4 points)
    # More snapshots = higher confidence
    if snapshot_count >= 12:
        data_availability_score = 0.4
    elif snapshot_count >= 6:
        data_availability_score = 0.3
    elif snapshot_count >= 3:
        data_availability_score = 0.2
    else:
        data_availability_score = 0.1

    # Factor 2: Data recency (0-0.3 points)
    # More recent data = higher confidence
    latest_snapshot = snapshots.order_by("-reconciled_at").first()
    if latest_snapshot:
        days_old = (timezone.now() - latest_snapshot.reconciled_at).days
        if days_old <= 7:
            recency_score = 0.3
        elif days_old <= 30:
            recency_score = 0.2
        elif days_old <= 90:
            recency_score = 0.1
        else:
            recency_score = 0.05
    else:
        recency_score = 0.0

    # Factor 3: Pattern stability (0-0.3 points)
    # Stable consumption = higher confidence
    if snapshot_count >= 3:
        consumption_values = list(snapshots.values_list("consumed", flat=True))
        if len(consumption_values) > 1:
            min_consumption = min(consumption_values)
            max_consumption = max(consumption_values)
            avg_consumption = sum(consumption_values) / len(consumption_values)

            if avg_consumption > 0:
                variation = (max_consumption - min_consumption) / avg_consumption
                # Lower variation = higher stability score
                if variation < 0.1:  # <10% variation
                    stability_score = 0.3
                elif variation < 0.2:  # <20% variation
                    stability_score = 0.2
                elif variation < 0.3:  # <30% variation
                    stability_score = 0.1
                else:
                    stability_score = 0.05
            else:
                stability_score = 0.1
        else:
            stability_score = 0.1
    else:
        stability_score = 0.1

    # Total confidence score
    confidence = data_availability_score + recency_score + stability_score

    # Ensure score is between 0.0 and 1.0
    return max(0.0, min(1.0, confidence))


def _generate_recommendations(vendor: Vendor, true_up_quantity: int, entitled_quantity: int, risk_level: str) -> Dict:
    """
    Generate actionable recommendations for Portfolio Manager.

    Args:
        vendor: Vendor instance
        true_up_quantity: Number of licenses to true-up
        entitled_quantity: Current entitled quantity
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)

    Returns:
        Dictionary of recommendations
    """
    recommendations = {
        "actions": [],
        "budget_impact": "Estimated true-up cost",
        "negotiation_points": [],
    }

    if risk_level == "LOW":
        recommendations["actions"].append("Monitor consumption trends")
        recommendations["negotiation_points"].append("Current consumption within entitlement")

    elif risk_level == "MEDIUM":
        recommendations["actions"].append("Review license allocation and reclaim unused licenses")
        recommendations["actions"].append("Consider purchasing additional licenses")
        recommendations["negotiation_points"].append("Request volume discount for true-up")

    elif risk_level == "HIGH":
        recommendations["actions"].append("Immediate license optimization required")
        recommendations["actions"].append("Budget for true-up costs")
        recommendations["negotiation_points"].append("Negotiate multi-year agreement for better pricing")
        recommendations["negotiation_points"].append("Request grace period for true-up payment")

    elif risk_level == "CRITICAL":
        recommendations["actions"].append("URGENT: Significant overage detected")
        recommendations["actions"].append("Conduct full license audit")
        recommendations["actions"].append("Engage vendor account manager immediately")
        recommendations["negotiation_points"].append("Negotiate settlement for historical overages")
        recommendations["negotiation_points"].append("Request ELA restructuring")

    return recommendations
