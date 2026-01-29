# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for packaging factory REST API.
"""
from rest_framework import serializers

from .models import PackagingPipeline, PackagingStageLog


class PackagingStageLogSerializer(serializers.ModelSerializer):
    """Serializer for packaging stage logs."""

    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = PackagingStageLog
        fields = [
            "id",
            "stage_name",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "output",
            "error_message",
            "metadata",
        ]


class PackagingPipelineSerializer(serializers.ModelSerializer):
    """Serializer for packaging pipeline (read)."""

    stage_logs = PackagingStageLogSerializer(many=True, read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    has_blocking_vulnerabilities = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = PackagingPipeline
        fields = [
            "id",
            "package_name",
            "package_version",
            "platform",
            "package_type",
            "status",
            "current_stage",
            "source_artifact_url",
            "source_artifact_hash",
            "output_artifact_url",
            "output_artifact_hash",
            "sbom_format",
            "sbom_url",
            "sbom_generated_at",
            "scan_tool",
            "scan_results",
            "scan_completed_at",
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
            "policy_decision",
            "policy_reason",
            "exception_id",
            "signing_certificate",
            "signature_url",
            "signed_at",
            "build_id",
            "builder_identity",
            "source_repo",
            "source_commit",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
            "completed_at",
            "error_message",
            "error_stage",
            "correlation_id",
            "is_completed",
            "has_blocking_vulnerabilities",
            "duration_seconds",
            "stage_logs",
        ]


class PackagingPipelineCreateSerializer(serializers.Serializer):
    """Serializer for creating packaging pipeline."""

    package_name = serializers.CharField(max_length=255)
    package_version = serializers.CharField(max_length=100)
    platform = serializers.ChoiceField(choices=["windows", "macos", "linux"])
    package_type = serializers.ChoiceField(choices=["MSI", "MSIX", "EXE", "PKG", "DMG", "DEB", "RPM"])
    source_artifact_url = serializers.URLField(max_length=1000)
    source_repo = serializers.URLField(max_length=1000, required=False, allow_null=True)
    source_commit = serializers.CharField(max_length=40, required=False, allow_null=True)
    exception_id = serializers.UUIDField(required=False, allow_null=True)


class PackagingPipelineListSerializer(serializers.ModelSerializer):
    """Serializer for listing packaging pipelines (summary view)."""

    duration_seconds = serializers.FloatField(read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = PackagingPipeline
        fields = [
            "id",
            "package_name",
            "package_version",
            "platform",
            "status",
            "policy_decision",
            "critical_count",
            "high_count",
            "created_by_username",
            "created_at",
            "completed_at",
            "duration_seconds",
        ]
