# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SLA Tracking Service.

Monitors SLA deadlines and detects warnings/breaches.
"""
import logging
from datetime import timedelta
from typing import List, Tuple

from django.utils import timezone

from ..models import TrackedRequest

logger = logging.getLogger(__name__)


class SLATracker:
    """
    Tracks SLA status for requests.

    Detects:
    - SLA warnings (approaching deadline)
    - SLA breaches (deadline passed)
    - Blocked requests (stalled)
    """

    def __init__(self, warning_hours: int = 4):
        """
        Initialize SLA tracker.

        Args:
            warning_hours: Hours before SLA due to trigger warning
        """
        self.warning_hours = warning_hours

    def check_sla_status(self, request: TrackedRequest) -> Tuple[str, bool]:
        """
        Check SLA status for a request.

        Args:
            request: TrackedRequest instance

        Returns:
            Tuple of (status, needs_action) where:
            - status: 'ok', 'warning', 'breached', 'blocked'
            - needs_action: True if action needed
        """
        now = timezone.now()

        # Check if blocked
        if request.blocked_reason:
            return ("blocked", True)

        # Check SLA if exists
        if not request.sla_due:
            return ("ok", False)

        time_remaining = request.sla_due - now

        if time_remaining.total_seconds() < 0:
            return ("breached", True)
        elif time_remaining.total_seconds() < self.warning_hours * 3600:
            return ("warning", True)
        else:
            return ("ok", False)

    def get_requests_at_risk(self) -> List[TrackedRequest]:
        """
        Get all requests with SLA warnings or breaches.

        Returns:
            List of TrackedRequest instances
        """
        now = timezone.now()
        warning_threshold = now + timedelta(hours=self.warning_hours)

        return TrackedRequest.objects.filter(
            sla_due__lte=warning_threshold,
            sla_due__isnull=False,
            status__in=[TrackedRequest.Status.NEW, TrackedRequest.Status.IN_PROGRESS, TrackedRequest.Status.PENDING],
        ).exclude(is_escalated=True)

    def get_blocked_requests(self, blocked_days: int = 2) -> List[TrackedRequest]:
        """
        Get requests blocked for more than specified days.

        Args:
            blocked_days: Minimum days blocked

        Returns:
            List of TrackedRequest instances
        """
        threshold = timezone.now() - timedelta(days=blocked_days)

        return TrackedRequest.objects.filter(
            blocked_reason__isnull=False,
            last_updated__lte=threshold,
            status__in=[TrackedRequest.Status.PENDING, TrackedRequest.Status.IN_PROGRESS],
        )
