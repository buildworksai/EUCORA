# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SLA Breach Detector.

Detects SLA breaches and generates alerts.
"""
import logging
from datetime import datetime
from typing import List, Optional

from django.utils import timezone

from apps.sla_governance.models import KPIMeasurement, SLABreach, SLATarget

logger = logging.getLogger(__name__)


class BreachDetector:
    """Detect SLA breaches from measurements."""

    def detect_breaches(self, target: SLATarget, measurement: KPIMeasurement) -> Optional[SLABreach]:
        """
        Detect if a measurement indicates a breach.

        Args:
            target: SLA target
            measurement: KPI measurement

        Returns:
            SLABreach if breach detected, None otherwise
        """
        is_breach = False
        severity = SLABreach.Severity.LOW

        if target.metric_type == SLATarget.MetricType.AVAILABILITY:
            # For availability, value should be >= target
            if measurement.value < target.target_value:
                is_breach = True
                # Calculate severity based on deviation
                deviation = (target.target_value - measurement.value) / target.target_value
                if deviation > 0.1:  # >10% deviation
                    severity = SLABreach.Severity.CRITICAL
                elif deviation > 0.05:  # >5% deviation
                    severity = SLABreach.Severity.HIGH
                elif deviation > 0.02:  # >2% deviation
                    severity = SLABreach.Severity.MEDIUM
        else:
            # For response/resolution time, value should be <= target
            if measurement.value > target.target_value:
                is_breach = True
                # Calculate severity based on deviation
                deviation = (measurement.value - target.target_value) / target.target_value
                if deviation > 0.5:  # >50% over target
                    severity = SLABreach.Severity.CRITICAL
                elif deviation > 0.25:  # >25% over target
                    severity = SLABreach.Severity.HIGH
                elif deviation > 0.1:  # >10% over target
                    severity = SLABreach.Severity.MEDIUM

        if not is_breach:
            return None

        # Create breach record
        breach = SLABreach.objects.create(
            sla=target.sla,
            target=target,
            breach_time=measurement.measurement_time,
            severity=severity,
            target_value=target.target_value,
            actual_value=measurement.value,
        )

        logger.warning(
            f"SLA breach detected: {breach.sla.name} - {breach.target.name} "
            f"(target: {target.target_value}, actual: {measurement.value})"
        )

        return breach

    def check_recent_breaches(self, hours: int = 24) -> List[SLABreach]:
        """
        Check for recent breaches.

        Args:
            hours: Hours to look back

        Returns:
            List of recent breaches
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        return list(SLABreach.objects.filter(breach_time__gte=since).order_by("-breach_time"))


def detect_breach(target: SLATarget, measurement: KPIMeasurement) -> Optional[SLABreach]:
    """
    Detect SLA breach.

    Args:
        target: SLA target
        measurement: KPI measurement

    Returns:
        Breach record if detected
    """
    detector = BreachDetector()
    return detector.detect_breaches(target, measurement)
