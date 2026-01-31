# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for Automation Advisor.
"""
from django.contrib import admin

from .models import AutomationAnalysis, AutomationCandidate, ROIConfiguration, TaskPattern


@admin.register(TaskPattern)
class TaskPatternAdmin(admin.ModelAdmin):
    """Admin for task patterns."""

    list_display = [
        "name",
        "pattern_type",
        "source",
        "occurrence_count",
        "error_rate",
        "last_detected",
        "is_active",
    ]
    list_filter = ["pattern_type", "source", "is_active", "last_detected"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AutomationCandidate)
class AutomationCandidateAdmin(admin.ModelAdmin):
    """Admin for automation candidates."""

    list_display = [
        "title",
        "pattern",
        "overall_score",
        "estimated_annual_savings",
        "payback_period_months",
        "status",
        "reviewed_by",
        "correlation_id",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "reviewed_at"]
    raw_id_fields = ["pattern", "reviewed_by"]


@admin.register(AutomationAnalysis)
class AutomationAnalysisAdmin(admin.ModelAdmin):
    """Admin for automation analyses."""

    list_display = [
        "name",
        "date_range_start",
        "date_range_end",
        "status",
        "patterns_detected",
        "candidates_generated",
        "started_at",
        "correlation_id",
    ]
    list_filter = ["status", "started_at"]
    search_fields = ["name", "correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(ROIConfiguration)
class ROIConfigurationAdmin(admin.ModelAdmin):
    """Admin for ROI configuration."""

    list_display = [
        "name",
        "hourly_labor_cost",
        "development_hourly_rate",
        "is_default",
        "created_at",
    ]
    list_filter = ["is_default", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
