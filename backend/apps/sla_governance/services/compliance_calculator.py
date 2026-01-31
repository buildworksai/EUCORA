# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SLA Compliance Calculator.

Calculates SLA compliance from KPI measurements.
"""
import logging
from datetime import date

from django.db.models import Avg

from apps.sla_governance.models import KPIMeasurement, SLACompliance, SLADefinition, SLATarget

logger = logging.getLogger(__name__)


class ComplianceCalculator:
    """Calculate SLA compliance from measurements."""

    def calculate_compliance(self, sla: SLADefinition, period_start: date, period_end: date) -> SLACompliance:
        """
        Calculate compliance for an SLA period.

        Args:
            sla: SLA definition
            period_start: Period start date
            period_end: Period end date

        Returns:
            SLACompliance record
        """
        target_compliances = {}
        breach_count = 0
        near_miss_count = 0

        for target in sla.targets.all():
            compliance = self._calculate_target_compliance(target, period_start, period_end)
            target_compliances[target.id] = compliance

            # Check for breaches and near-misses
            if compliance < target.target_value * 0.95:  # 5% threshold for breach
                breach_count += 1
            elif compliance < target.target_value * 0.98:  # 2% threshold for near-miss
                near_miss_count += 1

        # Calculate overall compliance (weighted average)
        overall_compliance = sum(target_compliances.values()) / len(target_compliances) if target_compliances else 0.0

        # Determine status
        if breach_count > 0:
            status = SLACompliance.Status.BREACHED
        elif near_miss_count > 0:
            status = SLACompliance.Status.AT_RISK
        else:
            status = SLACompliance.Status.COMPLIANT

        # Create or update compliance record
        compliance, _ = SLACompliance.objects.update_or_create(
            sla=sla,
            period_start=period_start,
            period_end=period_end,
            defaults={
                "overall_compliance": overall_compliance,
                "target_compliances": {str(k): v for k, v in target_compliances.items()},
                "breach_count": breach_count,
                "near_miss_count": near_miss_count,
                "status": status,
            },
        )

        return compliance

    def _calculate_target_compliance(self, target: SLATarget, period_start: date, period_end: date) -> float:
        """Calculate compliance for a specific target."""
        # Get KPI measurements for this target
        kpi_links = target.kpi_links.all()
        if not kpi_links:
            return 100.0  # No KPIs linked, assume compliant

        # Aggregate measurements from linked KPIs
        measurements = KPIMeasurement.objects.filter(
            kpi__in=[link.kpi for link in kpi_links],
            measurement_time__date__gte=period_start,
            measurement_time__date__lte=period_end,
        )

        if not measurements.exists():
            return 100.0  # No measurements, assume compliant

        # Calculate average value
        avg_value = measurements.aggregate(Avg("value"))["value__avg"] or 0.0

        # Compare to target
        if target.metric_type == SLATarget.MetricType.AVAILABILITY:
            # For availability, value should be >= target
            compliance = min(100.0, (avg_value / target.target_value) * 100.0)
        else:
            # For response/resolution time, value should be <= target
            compliance = min(100.0, (target.target_value / avg_value) * 100.0) if avg_value > 0 else 100.0

        return compliance


def calculate_sla_compliance(sla: SLADefinition, period_start: date, period_end: date) -> SLACompliance:
    """
    Calculate SLA compliance.

    Args:
        sla: SLA definition
        period_start: Period start
        period_end: Period end

    Returns:
        Compliance record
    """
    calculator = ComplianceCalculator()
    return calculator.calculate_compliance(sla, period_start, period_end)
