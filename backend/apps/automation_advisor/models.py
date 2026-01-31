# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Automation Advisor models for E13 enhancement.

Implements task pattern detection, automation candidate scoring, ROI calculation,
and recommendation tracking.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class TaskPattern(TimeStampedModel):
    """
    Detected task patterns from operational data.

    Identifies repetitive, manual, or error-prone tasks.
    """

    class PatternType(models.TextChoices):
        REPETITIVE = "repetitive", "Repetitive Task"
        MANUAL = "manual", "Manual Process"
        ERROR_PRONE = "error_prone", "Error-Prone Operation"

    class Source(models.TextChoices):
        SERVICENOW = "servicenow", "ServiceNow"
        EUCORA = "eucora", "EUCORA"
        LOGS = "logs", "Activity Logs"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Pattern name/description")
    pattern_type = models.CharField(max_length=50, choices=PatternType.choices)
    source = models.CharField(max_length=50, choices=Source.choices)
    source_query = models.JSONField(
        default=dict,
        help_text="Query/filter used to detect this pattern",
    )
    occurrence_count = models.IntegerField(default=0, help_text="Number of occurrences detected")
    avg_duration_minutes = models.FloatField(default=0.0, help_text="Average duration per occurrence in minutes")
    error_rate = models.FloatField(default=0.0, help_text="Error rate (0.0 to 1.0)")
    last_detected = models.DateTimeField(help_text="Last time this pattern was detected")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Task Pattern"
        verbose_name_plural = "Task Patterns"
        ordering = ["-last_detected"]
        indexes = [
            models.Index(fields=["pattern_type", "is_active"]),
            models.Index(fields=["source", "last_detected"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.pattern_type})"


class AutomationCandidate(TimeStampedModel, CorrelationIdModel):
    """
    Identified automation opportunity.

    Tracks automation candidates with scoring and ROI calculations.
    """

    class Status(models.TextChoices):
        IDENTIFIED = "identified", "Identified"
        REVIEWED = "reviewed", "Under Review"
        APPROVED = "approved", "Approved"
        IMPLEMENTED = "implemented", "Implemented"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern = models.ForeignKey(TaskPattern, on_delete=models.CASCADE, related_name="candidates")
    title = models.CharField(max_length=255, help_text="Automation opportunity title")
    description = models.TextField(help_text="Detailed description")
    current_process = models.TextField(help_text="Current manual process description")
    proposed_automation = models.TextField(help_text="Proposed automation approach")

    # Scoring (0.0 to 100.0)
    frequency_score = models.FloatField(help_text="Frequency impact score")
    time_impact_score = models.FloatField(help_text="Time impact score")
    error_reduction_score = models.FloatField(help_text="Error reduction score")
    complexity_score = models.FloatField(help_text="Automation complexity score (inverse)")
    overall_score = models.FloatField(help_text="Overall automation score")

    # ROI
    annual_occurrences = models.IntegerField(help_text="Expected annual occurrences")
    time_saved_per_occurrence = models.FloatField(help_text="Time saved per occurrence in hours")
    estimated_annual_savings = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Estimated annual cost savings"
    )
    development_cost_estimate = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Estimated development cost"
    )
    payback_period_months = models.FloatField(help_text="Payback period in months")

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IDENTIFIED)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_automations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    implementation_notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Automation Candidate"
        verbose_name_plural = "Automation Candidates"
        ordering = ["-overall_score"]
        indexes = [
            models.Index(fields=["status", "overall_score"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["pattern", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} (Score: {self.overall_score:.1f})"


class AutomationAnalysis(TimeStampedModel, CorrelationIdModel):
    """
    Analysis run for automation opportunities.

    Tracks analysis execution with correlation ID for audit trail.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Analysis name")
    date_range_start = models.DateField(help_text="Start date for analysis")
    date_range_end = models.DateField(help_text="End date for analysis")
    sources_analyzed = models.JSONField(default=list, help_text="List of data sources analyzed")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    patterns_detected = models.IntegerField(default=0, help_text="Number of patterns detected")
    candidates_generated = models.IntegerField(default=0, help_text="Number of candidates generated")

    class Meta:
        verbose_name = "Automation Analysis"
        verbose_name_plural = "Automation Analyses"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "started_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.status}"


class ROIConfiguration(TimeStampedModel):
    """
    Configuration for ROI calculations.

    Stores labor costs, development rates, and complexity multipliers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Configuration name")
    hourly_labor_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Hourly labor cost")
    development_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Development hourly rate")
    complexity_multipliers = models.JSONField(
        default=dict,
        help_text="Complexity multipliers: {low: hours, medium: hours, high: hours}",
    )
    is_default = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "ROI Configuration"
        verbose_name_plural = "ROI Configurations"
        ordering = ["-is_default", "name"]
        indexes = [
            models.Index(fields=["is_default"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({'Default' if self.is_default else 'Custom'})"
