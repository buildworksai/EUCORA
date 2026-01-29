# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Portfolio serializers.

REST API serializers for application catalog, versions, artifacts,
and deployment management.
"""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    Application,
    ApplicationDependency,
    ApplicationHealth,
    ApplicationVersion,
    DeploymentIntent,
    DeploymentMetric,
    PackageArtifact,
    Publisher,
)

# =============================================================================
# PUBLISHER SERIALIZERS
# =============================================================================


class PublisherSerializer(serializers.ModelSerializer):
    """Full publisher serializer."""

    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "identifier",
            "website",
            "support_url",
            "is_verified",
            "trust_score",
            "notes",
            "is_active",
            "application_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "application_count"]

    def get_application_count(self, obj: Publisher) -> int:
        """Get count of applications from this publisher."""
        return obj.applications.filter(is_active=True).count()


class PublisherListSerializer(serializers.ModelSerializer):
    """Lightweight publisher serializer for lists."""

    class Meta:
        model = Publisher
        fields = ["id", "name", "identifier", "is_verified", "is_active"]


# =============================================================================
# APPLICATION SERIALIZERS
# =============================================================================


class ApplicationSerializer(serializers.ModelSerializer):
    """Full application serializer."""

    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True, allow_null=True)
    latest_version_str = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    artifact_count = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "identifier",
            "publisher",
            "publisher_name",
            "description",
            "category",
            "tags",
            "homepage_url",
            "documentation_url",
            "icon_url",
            "owner",
            "owner_username",
            "team",
            "status",
            "supported_platforms",
            "risk_score",
            "requires_cab_approval",
            "is_privileged",
            "is_internal",
            "is_active",
            "latest_version_str",
            "version_count",
            "artifact_count",
            "platform_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "platform_count",
            "latest_version_str",
            "version_count",
            "artifact_count",
        ]

    def get_latest_version_str(self, obj: Application) -> str | None:
        """Get latest version string."""
        latest = obj.latest_version
        return latest.version if latest else None

    def get_version_count(self, obj: Application) -> int:
        """Get count of versions."""
        return obj.versions.count()

    def get_artifact_count(self, obj: Application) -> int:
        """Get total artifact count across all versions."""
        return PackageArtifact.objects.filter(version__application=obj).count()


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight application serializer for lists."""

    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "identifier",
            "publisher_name",
            "category",
            "status",
            "supported_platforms",
            "risk_score",
            "is_privileged",
            "is_active",
            "latest_version",
        ]

    def get_latest_version(self, obj: Application) -> str | None:
        """Get latest version string."""
        latest = obj.latest_version
        return latest.version if latest else None


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications."""

    class Meta:
        model = Application
        fields = [
            "name",
            "identifier",
            "publisher",
            "description",
            "category",
            "tags",
            "homepage_url",
            "documentation_url",
            "icon_url",
            "team",
            "supported_platforms",
            "is_internal",
        ]


# =============================================================================
# VERSION SERIALIZERS
# =============================================================================


class ApplicationVersionSerializer(serializers.ModelSerializer):
    """Full version serializer."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)
    artifact_count = serializers.SerializerMethodField()
    platforms_available = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationVersion
        fields = [
            "id",
            "application",
            "application_name",
            "version",
            "version_code",
            "release_notes",
            "release_date",
            "is_latest",
            "is_security_update",
            "deprecation_date",
            "end_of_life_date",
            "min_os_versions",
            "system_requirements",
            "dependencies",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "artifact_count",
            "platforms_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "artifact_count",
            "platforms_available",
        ]

    def get_artifact_count(self, obj: ApplicationVersion) -> int:
        """Get artifact count for this version."""
        return obj.artifacts.count()

    def get_platforms_available(self, obj: ApplicationVersion) -> list[str]:
        """Get list of platforms with artifacts."""
        return list(obj.artifacts.values_list("platform", flat=True).distinct())


class ApplicationVersionListSerializer(serializers.ModelSerializer):
    """Lightweight version serializer for lists."""

    artifact_count = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationVersion
        fields = [
            "id",
            "version",
            "version_code",
            "release_date",
            "is_latest",
            "is_security_update",
            "artifact_count",
            "created_at",
        ]

    def get_artifact_count(self, obj: ApplicationVersion) -> int:
        """Get artifact count."""
        return obj.artifacts.count()


# =============================================================================
# ARTIFACT SERIALIZERS
# =============================================================================


class PackageArtifactSerializer(serializers.ModelSerializer):
    """Full package artifact serializer."""

    application_name = serializers.CharField(source="version.application.name", read_only=True)
    version_str = serializers.CharField(source="version.version", read_only=True)
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True, allow_null=True)

    class Meta:
        model = PackageArtifact
        fields = [
            "id",
            "version",
            "application_name",
            "version_str",
            "platform",
            "architecture",
            "package_type",
            "file_name",
            "file_size",
            "file_hash_sha256",
            "storage_ref",
            "is_signed",
            "signature_type",
            "signer_identity",
            "signature_timestamp",
            "sbom_ref",
            "sbom_format",
            "scan_status",
            "scan_completed_at",
            "vulnerability_count_critical",
            "vulnerability_count_high",
            "vulnerability_count_medium",
            "vulnerability_count_low",
            "scan_report_ref",
            "status",
            "install_command",
            "uninstall_command",
            "detection_rules",
            "requirement_rules",
            "uploaded_by",
            "uploaded_by_username",
            "has_vulnerabilities",
            "total_vulnerabilities",
            "correlation_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "correlation_id",
            "has_vulnerabilities",
            "total_vulnerabilities",
        ]


class PackageArtifactListSerializer(serializers.ModelSerializer):
    """Lightweight artifact serializer for lists."""

    class Meta:
        model = PackageArtifact
        fields = [
            "id",
            "platform",
            "architecture",
            "package_type",
            "file_name",
            "file_size",
            "is_signed",
            "status",
            "vulnerability_count_critical",
            "vulnerability_count_high",
            "created_at",
        ]


class PackageArtifactUploadSerializer(serializers.ModelSerializer):
    """Serializer for initiating artifact upload."""

    class Meta:
        model = PackageArtifact
        fields = [
            "version",
            "platform",
            "architecture",
            "package_type",
            "file_name",
            "file_size",
            "file_hash_sha256",
            "install_command",
            "uninstall_command",
            "detection_rules",
            "requirement_rules",
        ]


# =============================================================================
# DEPLOYMENT SERIALIZERS
# =============================================================================


class DeploymentIntentSerializer(serializers.ModelSerializer):
    """Full deployment intent serializer."""

    artifact_name = serializers.SerializerMethodField()
    application_name = serializers.CharField(source="artifact.version.application.name", read_only=True)
    version_str = serializers.CharField(source="artifact.version.version", read_only=True)
    platform = serializers.CharField(source="artifact.platform", read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)
    latest_metrics = serializers.SerializerMethodField()

    class Meta:
        model = DeploymentIntent
        fields = [
            "id",
            "artifact",
            "artifact_name",
            "application_name",
            "version_str",
            "platform",
            "target_ring",
            "target_scope",
            "target_device_count",
            "scheduled_start",
            "scheduled_end",
            "deadline",
            "status",
            "risk_score",
            "risk_model_version",
            "requires_cab_approval",
            "cab_request_id",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "approval_notes",
            "evidence_pack_ref",
            "evidence_pack_hash",
            "started_at",
            "completed_at",
            "created_by",
            "created_by_username",
            "rollout_config",
            "rollback_plan",
            "rollback_triggered",
            "rollback_at",
            "rollback_reason",
            "latest_metrics",
            "correlation_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "correlation_id",
            "latest_metrics",
        ]

    def get_artifact_name(self, obj: DeploymentIntent) -> str:
        """Get formatted artifact name."""
        return str(obj.artifact)

    def get_latest_metrics(self, obj: DeploymentIntent) -> dict | None:
        """Get latest deployment metrics."""
        latest = obj.metrics.first()
        if not latest:
            return None
        return {
            "devices_targeted": latest.devices_targeted,
            "devices_succeeded": latest.devices_succeeded,
            "devices_failed": latest.devices_failed,
            "success_rate": str(latest.success_rate),
            "recorded_at": latest.recorded_at.isoformat(),
        }


class DeploymentIntentListSerializer(serializers.ModelSerializer):
    """Lightweight deployment intent serializer for lists."""

    application_name = serializers.CharField(source="artifact.version.application.name", read_only=True)
    version_str = serializers.CharField(source="artifact.version.version", read_only=True)
    platform = serializers.CharField(source="artifact.platform", read_only=True)

    class Meta:
        model = DeploymentIntent
        fields = [
            "id",
            "application_name",
            "version_str",
            "platform",
            "target_ring",
            "status",
            "risk_score",
            "requires_cab_approval",
            "scheduled_start",
            "created_at",
        ]


class DeploymentIntentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deployment intents."""

    class Meta:
        model = DeploymentIntent
        fields = [
            "artifact",
            "target_ring",
            "target_scope",
            "scheduled_start",
            "scheduled_end",
            "deadline",
            "rollout_config",
            "rollback_plan",
        ]


# =============================================================================
# METRICS SERIALIZERS
# =============================================================================


class DeploymentMetricSerializer(serializers.ModelSerializer):
    """Deployment metrics serializer."""

    class Meta:
        model = DeploymentMetric
        fields = [
            "id",
            "deployment",
            "recorded_at",
            "devices_targeted",
            "devices_pending",
            "devices_in_progress",
            "devices_succeeded",
            "devices_failed",
            "devices_not_applicable",
            "success_rate",
            "avg_install_time_seconds",
            "time_to_compliance_avg_seconds",
            "error_summary",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# =============================================================================
# HEALTH SERIALIZERS
# =============================================================================


class ApplicationHealthSerializer(serializers.ModelSerializer):
    """Application health serializer."""

    application_name = serializers.CharField(source="application.name", read_only=True)

    class Meta:
        model = ApplicationHealth
        fields = [
            "id",
            "application",
            "application_name",
            "recorded_at",
            "health_status",
            "health_message",
            "total_installations",
            "healthy_installations",
            "unhealthy_installations",
            "unknown_installations",
            "version_distribution",
            "compliance_status",
            "compliance_score",
            "active_incidents",
            "open_vulnerabilities",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# =============================================================================
# DEPENDENCY SERIALIZERS
# =============================================================================


class ApplicationDependencySerializer(serializers.ModelSerializer):
    """Application dependency serializer."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    depends_on_name = serializers.CharField(source="depends_on.name", read_only=True)

    class Meta:
        model = ApplicationDependency
        fields = [
            "id",
            "application",
            "application_name",
            "depends_on",
            "depends_on_name",
            "dependency_type",
            "min_version",
            "max_version",
            "is_required",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# =============================================================================
# SUMMARY SERIALIZERS
# =============================================================================


class ApplicationPortfolioSummarySerializer(serializers.Serializer):
    """Portfolio summary statistics."""

    total_applications = serializers.IntegerField()
    active_applications = serializers.IntegerField()
    total_versions = serializers.IntegerField()
    total_artifacts = serializers.IntegerField()
    applications_by_status = serializers.DictField()
    applications_by_category = serializers.DictField()
    platforms_coverage = serializers.DictField()
    publishers_count = serializers.IntegerField()
    pending_deployments = serializers.IntegerField()
    active_deployments = serializers.IntegerField()
    health_summary = serializers.DictField()
