# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Portfolio admin configuration.
"""
from django.contrib import admin

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


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin for Publisher model."""

    list_display = [
        "name",
        "identifier",
        "is_verified",
        "trust_score",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_verified", "is_active"]
    search_fields = ["name", "identifier"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin for Application model."""

    list_display = [
        "name",
        "identifier",
        "publisher",
        "category",
        "status",
        "risk_score",
        "is_active",
    ]
    list_filter = ["status", "category", "is_privileged", "is_internal", "is_active"]
    search_fields = ["name", "identifier", "publisher__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["publisher", "owner"]


@admin.register(ApplicationVersion)
class ApplicationVersionAdmin(admin.ModelAdmin):
    """Admin for ApplicationVersion model."""

    list_display = [
        "application",
        "version",
        "is_latest",
        "is_security_update",
        "release_date",
        "created_at",
    ]
    list_filter = ["is_latest", "is_security_update"]
    search_fields = ["application__name", "version"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["application", "approved_by"]


@admin.register(PackageArtifact)
class PackageArtifactAdmin(admin.ModelAdmin):
    """Admin for PackageArtifact model."""

    list_display = [
        "version",
        "platform",
        "architecture",
        "package_type",
        "status",
        "is_signed",
        "vulnerability_count_critical",
    ]
    list_filter = ["platform", "package_type", "status", "is_signed"]
    search_fields = ["version__application__name", "file_name", "file_hash_sha256"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["version", "uploaded_by"]


@admin.register(DeploymentIntent)
class DeploymentIntentAdmin(admin.ModelAdmin):
    """Admin for DeploymentIntent model."""

    list_display = [
        "artifact",
        "target_ring",
        "status",
        "risk_score",
        "requires_cab_approval",
        "scheduled_start",
        "created_at",
    ]
    list_filter = ["target_ring", "status", "requires_cab_approval"]
    search_fields = ["artifact__version__application__name", "cab_request_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["artifact", "approved_by", "created_by"]


@admin.register(DeploymentMetric)
class DeploymentMetricAdmin(admin.ModelAdmin):
    """Admin for DeploymentMetric model."""

    list_display = [
        "deployment",
        "devices_targeted",
        "devices_succeeded",
        "devices_failed",
        "success_rate",
        "recorded_at",
    ]
    list_filter = []
    search_fields = ["deployment__artifact__version__application__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["deployment"]


@admin.register(ApplicationHealth)
class ApplicationHealthAdmin(admin.ModelAdmin):
    """Admin for ApplicationHealth model."""

    list_display = [
        "application",
        "health_status",
        "compliance_status",
        "total_installations",
        "active_incidents",
        "recorded_at",
    ]
    list_filter = ["health_status", "compliance_status"]
    search_fields = ["application__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["application"]


@admin.register(ApplicationDependency)
class ApplicationDependencyAdmin(admin.ModelAdmin):
    """Admin for ApplicationDependency model."""

    list_display = [
        "application",
        "depends_on",
        "dependency_type",
        "is_required",
    ]
    list_filter = ["dependency_type", "is_required"]
    search_fields = ["application__name", "depends_on__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["application", "depends_on"]
