# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin for packaging factory.
"""
from django.contrib import admin

from .models import PackagingPipeline, PackagingStageLog


class PackagingStageLogInline(admin.TabularInline):
    """Inline admin for stage logs."""

    model = PackagingStageLog
    extra = 0
    readonly_fields = ["started_at", "completed_at", "duration_seconds"]
    fields = ["stage_name", "status", "started_at", "completed_at", "duration_seconds", "output"]


@admin.register(PackagingPipeline)
class PackagingPipelineAdmin(admin.ModelAdmin):
    """Admin interface for packaging pipelines."""

    list_display = [
        "package_name",
        "package_version",
        "platform",
        "status",
        "policy_decision",
        "created_by",
        "created_at",
    ]
    list_filter = ["platform", "status", "policy_decision", "created_at"]
    search_fields = ["package_name", "package_version", "correlation_id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "completed_at",
        "is_completed",
        "has_blocking_vulnerabilities",
        "duration_seconds",
    ]

    fieldsets = [
        ("Package Info", {"fields": ["package_name", "package_version", "platform", "package_type"]}),
        ("Pipeline Status", {"fields": ["status", "current_stage", "policy_decision", "policy_reason"]}),
        (
            "Artifacts",
            {"fields": ["source_artifact_url", "source_artifact_hash", "output_artifact_url", "output_artifact_hash"]},
        ),
        ("SBOM", {"fields": ["sbom_format", "sbom_url", "sbom_generated_at"], "classes": ["collapse"]}),
        (
            "Vulnerability Scan",
            {
                "fields": [
                    "scan_tool",
                    "scan_completed_at",
                    "critical_count",
                    "high_count",
                    "medium_count",
                    "low_count",
                    "scan_results",
                ],
                "classes": ["collapse"],
            },
        ),
        ("Signing", {"fields": ["signing_certificate", "signature_url", "signed_at"], "classes": ["collapse"]}),
        (
            "Provenance",
            {"fields": ["build_id", "builder_identity", "source_repo", "source_commit"], "classes": ["collapse"]},
        ),
        (
            "Metadata",
            {
                "fields": [
                    "id",
                    "created_by",
                    "created_at",
                    "updated_at",
                    "completed_at",
                    "correlation_id",
                    "is_completed",
                    "has_blocking_vulnerabilities",
                    "duration_seconds",
                ]
            },
        ),
        ("Errors", {"fields": ["error_message", "error_stage"], "classes": ["collapse"]}),
    ]

    inlines = [PackagingStageLogInline]


@admin.register(PackagingStageLog)
class PackagingStageLogAdmin(admin.ModelAdmin):
    """Admin interface for stage logs."""

    list_display = ["pipeline", "stage_name", "status", "started_at", "duration_seconds"]
    list_filter = ["stage_name", "status", "started_at"]
    search_fields = ["pipeline__package_name", "stage_name"]
    readonly_fields = ["id", "started_at", "completed_at", "duration_seconds"]
