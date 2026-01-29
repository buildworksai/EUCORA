# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for event store maintenance.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.event_store.tasks.cleanup_old_events")
def cleanup_old_events():
    """
    Cleanup old events based on retention policy.

    Note: Event store is append-only, so this task should only archive,
    not delete. Actual deletion requires CAB approval and compliance review.
    """
    from apps.event_store.models import DeploymentEvent

    # Retention policy: Keep events for 7 years (compliance requirement)
    # This task only logs statistics, actual archival handled by compliance team
    retention_date = timezone.now() - timedelta(days=2555)  # ~7 years

    old_events_count = DeploymentEvent.objects.filter(created_at__lt=retention_date).count()

    logger.info(
        f"Event cleanup check: {old_events_count} events older than retention period",
        extra={"retention_date": retention_date.isoformat()},
    )

    # In production, this would trigger archival workflow, not deletion
    return {"old_events_count": old_events_count, "retention_date": retention_date.isoformat()}
