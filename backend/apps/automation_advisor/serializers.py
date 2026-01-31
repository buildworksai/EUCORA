# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Automation Advisor API.
"""
from rest_framework import serializers

from .models import AutomationAnalysis, AutomationCandidate, ROIConfiguration, TaskPattern


class TaskPatternSerializer(serializers.ModelSerializer):
    """Serializer for task patterns."""

    candidate_count = serializers.SerializerMethodField()

    class Meta:
        model = TaskPattern
        fields = [
            "id",
            "name",
            "pattern_type",
            "source",
            "source_query",
            "occurrence_count",
            "avg_duration_minutes",
            "error_rate",
            "last_detected",
            "is_active",
            "candidate_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_candidate_count(self, obj: TaskPattern) -> int:
        """Get count of candidates for this pattern."""
        return obj.candidates.count()


class AutomationCandidateSerializer(serializers.ModelSerializer):
    """Serializer for automation candidates."""

    pattern_name = serializers.CharField(source="pattern.name", read_only=True)
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = AutomationCandidate
        fields = [
            "id",
            "correlation_id",
            "pattern",
            "pattern_name",
            "title",
            "description",
            "current_process",
            "proposed_automation",
            "frequency_score",
            "time_impact_score",
            "error_reduction_score",
            "complexity_score",
            "overall_score",
            "annual_occurrences",
            "time_saved_per_occurrence",
            "estimated_annual_savings",
            "development_cost_estimate",
            "payback_period_months",
            "status",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "implementation_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class AutomationAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for automation analyses."""

    class Meta:
        model = AutomationAnalysis
        fields = [
            "id",
            "correlation_id",
            "name",
            "date_range_start",
            "date_range_end",
            "sources_analyzed",
            "status",
            "started_at",
            "completed_at",
            "patterns_detected",
            "candidates_generated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class AutomationAnalysisStartSerializer(serializers.Serializer):
    """Serializer for starting an analysis."""

    name = serializers.CharField(max_length=255)
    date_range_start = serializers.DateField()
    date_range_end = serializers.DateField()
    sources_analyzed = serializers.ListField(child=serializers.CharField())


class ROIConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for ROI configuration."""

    class Meta:
        model = ROIConfiguration
        fields = [
            "id",
            "name",
            "hourly_labor_cost",
            "development_hourly_rate",
            "complexity_multipliers",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CandidateReviewSerializer(serializers.Serializer):
    """Serializer for reviewing a candidate."""

    status = serializers.ChoiceField(choices=AutomationCandidate.Status.choices)
    implementation_notes = serializers.CharField(required=False, allow_blank=True)
