# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Event Store models for append-only audit trail.
"""
from django.db import models

from apps.core.models import DemoQuerySet, TimeStampedModel


class DeploymentEvent(TimeStampedModel):
    """
    Append-only deployment event for audit trail.

    Immutable: No updates or deletes allowed.
    """

    class EventType(models.TextChoices):
        DEPLOYMENT_CREATED = "DEPLOYMENT_CREATED", "Deployment Created"
        RISK_ASSESSED = "RISK_ASSESSED", "Risk Assessed"
        CAB_SUBMITTED = "CAB_SUBMITTED", "CAB Submitted"
        CAB_APPROVED = "CAB_APPROVED", "CAB Approved"
        CAB_REJECTED = "CAB_REJECTED", "CAB Rejected"
        DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED", "Deployment Started"
        DEPLOYMENT_COMPLETED = "DEPLOYMENT_COMPLETED", "Deployment Completed"
        DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED", "Deployment Failed"
        ROLLBACK_INITIATED = "ROLLBACK_INITIATED", "Rollback Initiated"
        ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED", "Rollback Completed"

    correlation_id = models.UUIDField(db_index=True, help_text="Deployment correlation ID")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    event_data = models.JSONField(help_text="Event payload")
    actor = models.CharField(max_length=255, help_text="User or system that triggered event")
    is_demo = models.BooleanField(default=False, db_index=True, help_text="Whether this is demo data")

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["correlation_id", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Deployment Event"
        verbose_name_plural = "Deployment Events"

    def __str__(self):
        return f"{self.event_type} - {self.correlation_id} ({self.created_at})"

    def save(self, *args, **kwargs):
        """Append-only: Only allow creation, no updates."""
        if self.pk is not None:
            raise ValueError("DeploymentEvent is append-only, updates not allowed")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Append-only: No deletes allowed."""
        raise ValueError("DeploymentEvent is append-only, deletes not allowed")
