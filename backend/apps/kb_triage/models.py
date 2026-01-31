# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
KB & Triage Agent models for E21 enhancement.

Implements knowledge source integration, semantic search, AI-powered triage,
and incident pattern detection.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class KnowledgeSource(TimeStampedModel):
    """Configured knowledge source."""

    class SourceType(models.TextChoices):
        SERVICENOW_KB = "servicenow_kb", "ServiceNow KB"
        CONFLUENCE = "confluence", "Confluence"
        SHAREPOINT = "sharepoint", "SharePoint"
        VENDOR = "vendor", "Vendor Documentation"
        CUSTOM = "custom", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SourceType.choices, db_index=True)
    connection_config = models.JSONField(default=dict, help_text="Source connection configuration")
    sync_schedule = models.CharField(max_length=50, default="0 */6 * * *", help_text="Cron expression")
    last_sync = models.DateTimeField(null=True, blank=True)
    article_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Knowledge Source"
        verbose_name_plural = "Knowledge Sources"
        indexes = [
            models.Index(fields=["source_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class KnowledgeArticle(TimeStampedModel):
    """Indexed knowledge article."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE, related_name="articles")
    external_id = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    category = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    tags = models.JSONField(default=list)
    url = models.URLField(null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)
    published_date = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)

    # Embedding for semantic search (uses E7 pgvector)
    embedding = models.JSONField(null=True, blank=True, help_text="Vector embedding for semantic search")

    class Meta:
        verbose_name = "Knowledge Article"
        verbose_name_plural = "Knowledge Articles"
        indexes = [
            models.Index(fields=["source", "category"]),
            models.Index(fields=["external_id", "source"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.source.name})"


class TriageRequest(TimeStampedModel, CorrelationIdModel):
    """Ticket triage request."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TRIAGED = "triaged", "Triaged"
        ESCALATED = "escalated", "Escalated"
        RESOLVED = "resolved", "Resolved"

    class Priority(models.TextChoices):
        CRITICAL = "1", "Critical"
        HIGH = "2", "High"
        MEDIUM = "3", "Medium"
        LOW = "4", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    servicenow_number = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    caller_name = models.CharField(max_length=255)
    caller_email = models.EmailField(null=True, blank=True)
    affected_service = models.CharField(max_length=255, null=True, blank=True)
    short_description = models.CharField(max_length=500)
    description = models.TextField()
    symptoms = models.JSONField(default=list)

    # Triage Results
    suggested_category = models.CharField(max_length=255, null=True, blank=True)
    suggested_subcategory = models.CharField(max_length=255, null=True, blank=True)
    suggested_priority = models.CharField(max_length=20, null=True, blank=True, choices=Priority.choices)
    suggested_assignment_group = models.CharField(max_length=255, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    triage_time_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Triage Request"
        verbose_name_plural = "Triage Requests"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["servicenow_number"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.servicenow_number or 'TRIAGE-' + str(self.id)[:8]} - {self.short_description}"


class TriageSuggestion(TimeStampedModel):
    """Resolution suggestion for triage request."""

    class SuggestionType(models.TextChoices):
        ARTICLE = "article", "Knowledge Article"
        SCRIPT = "script", "Script"
        ESCALATION = "escalation", "Escalation"
        WORKAROUND = "workaround", "Workaround"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE, related_name="suggestions")
    suggestion_type = models.CharField(max_length=50, choices=SuggestionType.choices)
    title = models.CharField(max_length=500)
    content = models.TextField()
    source_article = models.ForeignKey(
        KnowledgeArticle, null=True, blank=True, on_delete=models.SET_NULL, related_name="suggestions"
    )
    relevance_score = models.FloatField()
    was_helpful = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Triage Suggestion"
        verbose_name_plural = "Triage Suggestions"
        ordering = ["-relevance_score"]
        indexes = [
            models.Index(fields=["triage_request", "relevance_score"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.relevance_score:.2f})"


class ResolutionStep(TimeStampedModel):
    """Step-by-step resolution guidance."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE, related_name="resolution_steps")
    step_number = models.IntegerField()
    instruction = models.TextField()
    expected_outcome = models.TextField(null=True, blank=True)
    script = models.TextField(null=True, blank=True)
    script_type = models.CharField(max_length=20, null=True, blank=True)
    requires_approval = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Resolution Step"
        verbose_name_plural = "Resolution Steps"
        ordering = ["step_number"]
        indexes = [
            models.Index(fields=["triage_request", "step_number"]),
        ]

    def __str__(self):
        return f"Step {self.step_number}: {self.instruction[:50]}"


class IncidentPattern(TimeStampedModel, CorrelationIdModel):
    """Detected incident pattern."""

    class PatternType(models.TextChoices):
        RECURRING = "recurring", "Recurring"
        TRENDING = "trending", "Trending"
        CORRELATED = "correlated", "Correlated"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    pattern_type = models.CharField(max_length=50, choices=PatternType.choices, db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=255, db_index=True)
    occurrence_count = models.IntegerField(default=0)
    affected_users = models.IntegerField(default=0)
    first_detected = models.DateTimeField(default=timezone.now)
    last_detected = models.DateTimeField(default=timezone.now)
    related_change = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    root_cause = models.TextField(null=True, blank=True)
    resolution = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Incident Pattern"
        verbose_name_plural = "Incident Patterns"
        indexes = [
            models.Index(fields=["pattern_type", "status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.pattern_type})"


class TriageFeedback(TimeStampedModel):
    """Feedback on triage accuracy."""

    class FeedbackType(models.TextChoices):
        CATEGORY = "category", "Category"
        PRIORITY = "priority", "Priority"
        ASSIGNMENT = "assignment", "Assignment"
        RESOLUTION = "resolution", "Resolution"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE, related_name="feedback")
    feedback_type = models.CharField(max_length=50, choices=FeedbackType.choices)
    was_accurate = models.BooleanField()
    correct_value = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="triage_feedback"
    )

    class Meta:
        verbose_name = "Triage Feedback"
        verbose_name_plural = "Triage Feedback"
        indexes = [
            models.Index(fields=["triage_request", "feedback_type"]),
        ]

    def __str__(self):
        return f"{self.feedback_type} - {'Accurate' if self.was_accurate else 'Inaccurate'}"
