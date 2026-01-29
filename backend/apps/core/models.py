# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core models and abstract base classes.
"""
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps.

    All models should inherit from this to ensure consistent timestamp tracking.
    """

    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CorrelationIdModel(models.Model):
    """
    Abstract base model with correlation_id for audit trail.

    Correlation IDs enable end-to-end tracing across all system components.
    """

    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Unique correlation ID for audit trail and tracing",
    )

    class Meta:
        abstract = True


class DemoQuerySet(models.QuerySet):
    """
    QuerySet helpers for demo data filtering.
    """

    def demo(self):
        return self.filter(is_demo=True)

    def production(self):
        return self.filter(is_demo=False)


class DemoModeConfig(TimeStampedModel):
    """
    Global toggle for demo mode behavior.
    """

    is_enabled = models.BooleanField(default=False, help_text="Whether demo mode is enabled")

    class Meta:
        verbose_name = "Demo Mode Config"
        verbose_name_plural = "Demo Mode Config"
