# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Discovery Agent API.
"""
from rest_framework import serializers

from .models import (
    ApplicationVersion,
    DiscoveredApplication,
    DiscoveryReport,
    DiscoveryRun,
    DiscoverySource,
    LicenseGap,
    NormalizedApplication,
    PatchGap,
)


class DiscoverySourceSerializer(serializers.ModelSerializer):
    """Serializer for discovery sources."""

    run_count = serializers.SerializerMethodField()

    class Meta:
        model = DiscoverySource
        fields = [
            "id",
            "name",
            "source_type",
            "connection_config",
            "sync_schedule",
            "last_sync",
            "last_sync_status",
            "is_active",
            "include_patterns",
            "exclude_patterns",
            "run_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_sync", "last_sync_status", "created_at", "updated_at"]

    def get_run_count(self, obj: DiscoverySource) -> int:
        """Get count of discovery runs."""
        return obj.runs.count()

    def to_representation(self, instance: DiscoverySource) -> dict:
        """Mask credentials in response."""
        data = super().to_representation(instance)
        if data.get("connection_config"):
            # Mask sensitive fields
            for key in ["password", "api_key", "secret", "token"]:
                if key in data["connection_config"]:
                    data["connection_config"][key] = "***"
        return data


class DiscoveryRunSerializer(serializers.ModelSerializer):
    """Serializer for discovery runs."""

    source_name = serializers.CharField(source="source.name", read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    initiated_by_username = serializers.CharField(source="initiated_by.username", read_only=True)

    class Meta:
        model = DiscoveryRun
        fields = [
            "id",
            "correlation_id",
            "source",
            "source_name",
            "run_type",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "records_discovered",
            "records_new",
            "records_updated",
            "records_normalized",
            "normalization_failures",
            "errors",
            "initiated_by",
            "initiated_by_username",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "duration_seconds",
            "records_discovered",
            "records_new",
            "records_updated",
            "records_normalized",
            "normalization_failures",
            "errors",
            "created_at",
        ]


class DiscoveryRunStartSerializer(serializers.Serializer):
    """Serializer for starting a discovery run."""

    source_id = serializers.UUIDField()
    run_type = serializers.ChoiceField(choices=DiscoveryRun.RunType.choices, default="incremental")


class DiscoveredApplicationSerializer(serializers.ModelSerializer):
    """Serializer for discovered applications."""

    normalized_app_name = serializers.CharField(source="normalized_app.name", read_only=True)

    class Meta:
        model = DiscoveredApplication
        fields = [
            "id",
            "discovery_run",
            "source_id",
            "source_type",
            "raw_name",
            "raw_publisher",
            "raw_version",
            "install_date",
            "install_count",
            "source_metadata",
            "normalized_app",
            "normalized_app_name",
            "normalization_confidence",
            "normalization_method",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ApplicationVersionSerializer(serializers.ModelSerializer):
    """Serializer for application versions."""

    class Meta:
        model = ApplicationVersion
        fields = [
            "id",
            "application",
            "version",
            "version_major",
            "version_minor",
            "version_patch",
            "release_date",
            "end_of_life",
            "has_security_updates",
            "is_current",
            "install_count",
            "first_seen",
            "last_seen",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NormalizedApplicationSerializer(serializers.ModelSerializer):
    """Serializer for normalized applications."""

    version_count = serializers.SerializerMethodField()
    discovered_count = serializers.SerializerMethodField()
    license_gap_count = serializers.SerializerMethodField()
    patch_gap_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedApplication
        fields = [
            "id",
            "name",
            "publisher",
            "category",
            "application_type",
            "is_managed",
            "is_approved",
            "is_restricted",
            "portfolio_app",
            "license_sku",
            "fingerprint",
            "total_installs",
            "first_discovered",
            "last_discovered",
            "version_count",
            "discovered_count",
            "license_gap_count",
            "patch_gap_count",
            "latest_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "fingerprint", "created_at", "updated_at"]

    def get_version_count(self, obj: NormalizedApplication) -> int:
        """Get count of versions."""
        return obj.versions.count()

    def get_discovered_count(self, obj: NormalizedApplication) -> int:
        """Get count of discovered instances."""
        return obj.discovered_instances.count()

    def get_license_gap_count(self, obj: NormalizedApplication) -> int:
        """Get count of open license gaps."""
        return obj.license_gaps.filter(status="open").count()

    def get_patch_gap_count(self, obj: NormalizedApplication) -> int:
        """Get count of open patch gaps."""
        return obj.patch_gaps.filter(status="open").count()

    def get_latest_version(self, obj: NormalizedApplication) -> str | None:
        """Get latest version string."""
        current = obj.versions.filter(is_current=True).first()
        return current.version if current else None


class NormalizedApplicationDetailSerializer(NormalizedApplicationSerializer):
    """Detailed serializer with versions."""

    versions = ApplicationVersionSerializer(many=True, read_only=True)

    class Meta(NormalizedApplicationSerializer.Meta):
        fields = NormalizedApplicationSerializer.Meta.fields + ["versions"]


class MergeApplicationsSerializer(serializers.Serializer):
    """Serializer for merging duplicate applications."""

    source_ids = serializers.ListField(child=serializers.UUIDField(), min_length=2)
    target_id = serializers.UUIDField()


class LicenseGapSerializer(serializers.ModelSerializer):
    """Serializer for license gaps."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    application_publisher = serializers.CharField(source="application.publisher", read_only=True)
    resolved_by_username = serializers.CharField(source="resolved_by.username", read_only=True)

    class Meta:
        model = LicenseGap
        fields = [
            "id",
            "correlation_id",
            "application",
            "application_name",
            "application_publisher",
            "gap_type",
            "detected_installs",
            "licensed_count",
            "gap_count",
            "risk_level",
            "estimated_cost",
            "status",
            "resolved_at",
            "resolved_by",
            "resolved_by_username",
            "resolution_notes",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at"]


class PatchGapSerializer(serializers.ModelSerializer):
    """Serializer for patch gaps."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    current_version_str = serializers.CharField(source="current_version.version", read_only=True)
    target_version_str = serializers.CharField(source="target_version.version", read_only=True)

    class Meta:
        model = PatchGap
        fields = [
            "id",
            "correlation_id",
            "application",
            "application_name",
            "current_version",
            "current_version_str",
            "target_version",
            "target_version_str",
            "affected_devices",
            "gap_type",
            "severity",
            "cve_ids",
            "status",
            "planned_date",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at"]


class GapResolveSerializer(serializers.Serializer):
    """Serializer for resolving gaps."""

    action = serializers.ChoiceField(choices=["acknowledge", "resolve", "exception"])
    notes = serializers.CharField(required=False, allow_blank=True)
    planned_date = serializers.DateField(required=False)


class DiscoveryReportSerializer(serializers.ModelSerializer):
    """Serializer for discovery reports."""

    generated_by_username = serializers.CharField(source="generated_by.username", read_only=True)

    class Meta:
        model = DiscoveryReport
        fields = [
            "id",
            "correlation_id",
            "report_type",
            "title",
            "description",
            "summary",
            "details",
            "generated_by",
            "generated_by_username",
            "generated_at",
            "sources_included",
            "date_range_start",
            "date_range_end",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "generated_at", "created_at"]


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for report generation."""

    report_type = serializers.ChoiceField(choices=DiscoveryReport.ReportType.choices)
    title = serializers.CharField(required=False)
    source_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    date_range_start = serializers.DateField(required=False)
    date_range_end = serializers.DateField(required=False)


class DiscoveryDashboardSerializer(serializers.Serializer):
    """Serializer for discovery dashboard data."""

    total_applications = serializers.IntegerField()
    managed_applications = serializers.IntegerField()
    unmanaged_applications = serializers.IntegerField()
    shadow_it_count = serializers.IntegerField()
    license_gaps_count = serializers.IntegerField()
    patch_gaps_count = serializers.IntegerField()
    total_installs = serializers.IntegerField()
    last_discovery = serializers.DateTimeField()
    applications_by_category = serializers.DictField()
    risk_distribution = serializers.DictField()
