# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for KB & Triage Agent API.
"""
from rest_framework import serializers

from .models import (
    IncidentPattern,
    KnowledgeArticle,
    KnowledgeSource,
    ResolutionStep,
    TriageFeedback,
    TriageRequest,
    TriageSuggestion,
)


class KnowledgeSourceSerializer(serializers.ModelSerializer):
    """Serializer for knowledge sources."""

    class Meta:
        model = KnowledgeSource
        fields = [
            "id",
            "name",
            "source_type",
            "connection_config",
            "sync_schedule",
            "last_sync",
            "article_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_sync", "article_count"]


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    """Serializer for knowledge articles."""

    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = [
            "id",
            "source",
            "source_name",
            "external_id",
            "title",
            "content",
            "category",
            "tags",
            "url",
            "author",
            "published_date",
            "last_updated",
            "view_count",
            "helpful_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "view_count", "helpful_count"]


class TriageRequestSerializer(serializers.ModelSerializer):
    """Serializer for triage requests."""

    suggestion_count = serializers.SerializerMethodField()
    resolution_step_count = serializers.SerializerMethodField()

    class Meta:
        model = TriageRequest
        fields = [
            "id",
            "correlation_id",
            "servicenow_number",
            "caller_name",
            "caller_email",
            "affected_service",
            "short_description",
            "description",
            "symptoms",
            "suggested_category",
            "suggested_subcategory",
            "suggested_priority",
            "suggested_assignment_group",
            "confidence_score",
            "reasoning",
            "status",
            "triage_time_ms",
            "suggestion_count",
            "resolution_step_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "created_at",
            "updated_at",
            "triage_time_ms",
        ]

    def get_suggestion_count(self, obj: TriageRequest) -> int:
        """Get count of suggestions."""
        return obj.suggestions.count()

    def get_resolution_step_count(self, obj: TriageRequest) -> int:
        """Get count of resolution steps."""
        return obj.resolution_steps.count()


class TriageSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for triage suggestions."""

    source_article_title = serializers.CharField(source="source_article.title", read_only=True)

    class Meta:
        model = TriageSuggestion
        fields = [
            "id",
            "triage_request",
            "suggestion_type",
            "title",
            "content",
            "source_article",
            "source_article_title",
            "relevance_score",
            "was_helpful",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ResolutionStepSerializer(serializers.ModelSerializer):
    """Serializer for resolution steps."""

    class Meta:
        model = ResolutionStep
        fields = [
            "id",
            "triage_request",
            "step_number",
            "instruction",
            "expected_outcome",
            "script",
            "script_type",
            "requires_approval",
            "status",
            "completed_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class IncidentPatternSerializer(serializers.ModelSerializer):
    """Serializer for incident patterns."""

    class Meta:
        model = IncidentPattern
        fields = [
            "id",
            "correlation_id",
            "name",
            "pattern_type",
            "description",
            "category",
            "occurrence_count",
            "affected_users",
            "first_detected",
            "last_detected",
            "related_change",
            "status",
            "root_cause",
            "resolution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class TriageFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for triage feedback."""

    submitted_by_name = serializers.CharField(source="submitted_by.username", read_only=True)

    class Meta:
        model = TriageFeedback
        fields = [
            "id",
            "triage_request",
            "feedback_type",
            "was_accurate",
            "correct_value",
            "comments",
            "submitted_by",
            "submitted_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
