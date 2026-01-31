# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Schedule Optimizer.

Optimizes deployment schedules considering windows and change freezes.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from django.utils import timezone

from apps.planning_agent.models import ChangeFreezePeriod, DeploymentPlan, DeploymentWindow, RingAssignment

logger = logging.getLogger(__name__)


class ScheduleOptimizer:
    """Optimize deployment schedules."""

    def optimize_schedule(self, plan: DeploymentPlan) -> List[RingAssignment]:
        """
        Optimize schedule for deployment plan.

        Args:
            plan: Deployment plan

        Returns:
            Updated ring assignments with optimized schedules
        """
        # Get active deployment windows
        windows = DeploymentWindow.objects.filter(is_active=True)

        # Get active change freezes
        freezes = ChangeFreezePeriod.objects.filter(is_active=True)

        # Optimize each ring
        optimized_rings = []
        current_time = timezone.now()

        for ring in plan.rings.all().order_by("ring_number"):
            optimized_start = self._find_optimal_start_time(ring, windows, freezes, current_time)
            optimized_end = self._calculate_end_time(optimized_start, ring.device_count)

            ring.scheduled_start = optimized_start
            ring.scheduled_end = optimized_end
            optimized_rings.append(ring)

            # Next ring starts after previous completes
            current_time = optimized_end

        return optimized_rings

    def _find_optimal_start_time(
        self,
        ring: RingAssignment,
        windows: List[DeploymentWindow],
        freezes: List[ChangeFreezePeriod],
        earliest_start: datetime,
    ) -> datetime:
        """Find optimal start time for ring."""
        # Start from earliest possible time
        candidate = earliest_start

        # Check if candidate is in a freeze period
        while self._is_in_freeze(candidate, freezes):
            # Move to after freeze
            next_freeze_end = min((f.end_date for f in freezes if f.end_date > candidate.date()), default=None)
            if next_freeze_end:
                candidate = timezone.make_aware(
                    datetime.combine(next_freeze_end + timedelta(days=1), datetime.min.time())
                )
            else:
                candidate += timedelta(days=1)

        # Check if candidate is in a deployment window
        if windows.exists():
            # Find next available window
            candidate = self._find_next_window(candidate, windows)

        return candidate

    def _is_in_freeze(self, dt: datetime, freezes: List[ChangeFreezePeriod]) -> bool:
        """Check if datetime is in a freeze period."""
        dt_date = dt.date()
        return any(f.start_date <= dt_date <= f.end_date for f in freezes)

    def _find_next_window(self, dt: datetime, windows: List[DeploymentWindow]) -> datetime:
        """Find next available deployment window."""
        # For now, return the datetime as-is
        # TODO: Implement window matching logic
        return dt

    def _calculate_end_time(self, start_time: datetime, device_count: int) -> datetime:
        """Calculate end time based on device count."""
        # Estimate: 1 minute per device, minimum 1 hour
        minutes = max(60, device_count)
        return start_time + timedelta(minutes=minutes)


def optimize_schedule(plan: DeploymentPlan) -> List[RingAssignment]:
    """
    Optimize deployment schedule.

    Args:
        plan: Deployment plan

    Returns:
        Optimized ring assignments
    """
    optimizer = ScheduleOptimizer()
    return optimizer.optimize_schedule(plan)
