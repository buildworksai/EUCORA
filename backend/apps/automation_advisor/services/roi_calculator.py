# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ROI calculation engine for automation opportunities.

Calculates ROI, payback period, and automation scores.
"""
from decimal import Decimal
from typing import Any

from apps.automation_advisor.models import ROIConfiguration


class ROICalculator:
    """Calculates ROI for automation opportunities."""

    def __init__(self, roi_config: ROIConfiguration | None = None):
        """
        Initialize calculator with ROI configuration.

        Args:
            roi_config: ROI configuration (uses default if None)
        """
        if roi_config is None:
            roi_config = ROIConfiguration.objects.filter(is_default=True).first()
            if roi_config is None:
                # Default configuration
                roi_config = ROIConfiguration(
                    hourly_labor_cost=Decimal("50.00"),
                    development_hourly_rate=Decimal("100.00"),
                    complexity_multipliers={"low": 8, "medium": 40, "high": 160},
                )
        self.config = roi_config

    def calculate_automation_score(
        self,
        frequency: int,
        time_per_occurrence: float,
        error_rate: float,
        complexity: str,
    ) -> dict[str, float]:
        """
        Calculate automation score.

        Formula: (Frequency × TimePerOccurrence × ErrorRate) / AutomationComplexity

        Args:
            frequency: Number of occurrences
            time_per_occurrence: Time per occurrence in hours
            error_rate: Error rate (0.0 to 1.0)
            complexity: Complexity level (low, medium, high)

        Returns:
            Dictionary with scoring breakdown
        """
        # Get complexity multiplier (inverse - higher complexity = lower score)
        complexity_multipliers = self.config.complexity_multipliers
        complexity_hours = complexity_multipliers.get(complexity, 40)
        complexity_factor = 1.0 / max(complexity_hours / 40.0, 0.1)  # Normalize

        # Calculate component scores (normalized to 0-100)
        frequency_score = min(frequency / 100.0 * 100, 100.0)
        time_score = min(time_per_occurrence * 10, 100.0)
        error_score = error_rate * 100.0

        # Overall score
        overall_score = (
            (frequency_score * 0.3) + (time_score * 0.3) + (error_score * 0.2) + (complexity_factor * 100 * 0.2)
        )

        return {
            "frequency_score": round(frequency_score, 2),
            "time_impact_score": round(time_score, 2),
            "error_reduction_score": round(error_score, 2),
            "complexity_score": round(complexity_factor * 100, 2),
            "overall_score": round(overall_score, 2),
        }

    def calculate_roi(
        self,
        annual_occurrences: int,
        time_saved_per_occurrence: float,
        complexity: str,
    ) -> dict[str, Any]:
        """
        Calculate ROI for automation opportunity.

        Formula: (AnnualTimeSaved × HourlyCost) - AutomationDevelopmentCost

        Args:
            annual_occurrences: Expected annual occurrences
            time_saved_per_occurrence: Time saved per occurrence in hours
            complexity: Complexity level (low, medium, high)

        Returns:
            Dictionary with ROI calculations
        """
        # Calculate annual time saved
        annual_time_saved_hours = annual_occurrences * time_saved_per_occurrence

        # Calculate annual cost savings
        annual_savings = Decimal(str(annual_time_saved_hours)) * self.config.hourly_labor_cost

        # Calculate development cost
        complexity_multipliers = self.config.complexity_multipliers
        development_hours = complexity_multipliers.get(complexity, 40)
        development_cost = Decimal(str(development_hours)) * self.config.development_hourly_rate

        # Calculate net annual benefit
        net_annual_benefit = annual_savings - development_cost

        # Calculate payback period (months)
        if annual_savings > 0:
            payback_period_months = (development_cost / annual_savings) * 12
        else:
            payback_period_months = float("inf")

        return {
            "annual_occurrences": annual_occurrences,
            "time_saved_per_occurrence": time_saved_per_occurrence,
            "annual_time_saved_hours": round(annual_time_saved_hours, 2),
            "estimated_annual_savings": annual_savings,
            "development_cost_estimate": development_cost,
            "development_hours": development_hours,
            "net_annual_benefit": net_annual_benefit,
            "payback_period_months": round(payback_period_months, 2),
        }
