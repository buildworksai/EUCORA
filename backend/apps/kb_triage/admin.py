# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for KB & Triage Agent.
"""
from django.contrib import admin

from .models import (
    IncidentPattern,
    KnowledgeArticle,
    KnowledgeSource,
    ResolutionStep,
    TriageFeedback,
    TriageRequest,
    TriageSuggestion,
)


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    """Admin for knowledge sources."""

    list_display = ["name", "source_type", "is_active", "article_count", "last_sync", "created_at"]
    list_filter = ["source_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_sync", "article_count"]


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    """Admin for knowledge articles."""

    list_display = ["title", "source", "category", "view_count", "helpful_count", "published_date"]
    list_filter = ["source", "category", "published_date"]
    search_fields = ["title", "content"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(TriageRequest)
class TriageRequestAdmin(admin.ModelAdmin):
    """Admin for triage requests."""

    list_display = [
        "servicenow_number",
        "short_description",
        "caller_name",
        "suggested_category",
        "suggested_priority",
        "status",
        "confidence_score",
        "created_at",
    ]
    list_filter = ["status", "suggested_priority", "suggested_category"]
    search_fields = ["servicenow_number", "short_description", "caller_name", "caller_email"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "triage_time_ms"]


@admin.register(TriageSuggestion)
class TriageSuggestionAdmin(admin.ModelAdmin):
    """Admin for triage suggestions."""

    list_display = ["title", "triage_request", "suggestion_type", "relevance_score", "was_helpful", "created_at"]
    list_filter = ["suggestion_type", "was_helpful"]
    search_fields = ["title", "content"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ResolutionStep)
class ResolutionStepAdmin(admin.ModelAdmin):
    """Admin for resolution steps."""

    list_display = ["triage_request", "step_number", "status", "requires_approval", "completed_at"]
    list_filter = ["status", "requires_approval"]
    search_fields = ["instruction"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(IncidentPattern)
class IncidentPatternAdmin(admin.ModelAdmin):
    """Admin for incident patterns."""

    list_display = ["name", "pattern_type", "category", "occurrence_count", "status", "last_detected"]
    list_filter = ["pattern_type", "status", "category"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(TriageFeedback)
class TriageFeedbackAdmin(admin.ModelAdmin):
    """Admin for triage feedback."""

    list_display = ["triage_request", "feedback_type", "was_accurate", "submitted_by", "created_at"]
    list_filter = ["feedback_type", "was_accurate"]
    search_fields = ["comments"]
    readonly_fields = ["id", "created_at", "updated_at"]
