# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for Discovery Agent.
"""
from django.contrib import admin

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


@admin.register(DiscoverySource)
class DiscoverySourceAdmin(admin.ModelAdmin):
    """Admin for discovery sources."""

    list_display = ["name", "source_type", "sync_schedule", "is_active", "last_sync"]
    list_filter = ["source_type", "sync_schedule", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(DiscoveryRun)
class DiscoveryRunAdmin(admin.ModelAdmin):
    """Admin for discovery runs."""

    list_display = ["source", "run_type", "status", "started_at", "records_discovered"]
    list_filter = ["status", "run_type", "source"]
    search_fields = ["correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(DiscoveredApplication)
class DiscoveredApplicationAdmin(admin.ModelAdmin):
    """Admin for discovered applications."""

    list_display = ["raw_name", "raw_publisher", "raw_version", "source_type", "normalized_app"]
    list_filter = ["source_type", "discovery_run__source"]
    search_fields = ["raw_name", "raw_publisher"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(NormalizedApplication)
class NormalizedApplicationAdmin(admin.ModelAdmin):
    """Admin for normalized applications."""

    list_display = ["name", "publisher", "category", "is_managed", "is_approved", "total_installs"]
    list_filter = ["is_managed", "is_approved", "is_restricted", "application_type"]
    search_fields = ["name", "publisher"]
    readonly_fields = ["id", "fingerprint", "created_at", "updated_at"]


@admin.register(ApplicationVersion)
class ApplicationVersionAdmin(admin.ModelAdmin):
    """Admin for application versions."""

    list_display = ["application", "version", "is_current", "install_count", "end_of_life"]
    list_filter = ["is_current", "has_security_updates"]
    search_fields = ["version", "application__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(LicenseGap)
class LicenseGapAdmin(admin.ModelAdmin):
    """Admin for license gaps."""

    list_display = ["application", "gap_type", "gap_count", "risk_level", "status"]
    list_filter = ["gap_type", "risk_level", "status"]
    search_fields = ["application__name"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(PatchGap)
class PatchGapAdmin(admin.ModelAdmin):
    """Admin for patch gaps."""

    list_display = ["application", "gap_type", "severity", "affected_devices", "status"]
    list_filter = ["gap_type", "severity", "status"]
    search_fields = ["application__name"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(DiscoveryReport)
class DiscoveryReportAdmin(admin.ModelAdmin):
    """Admin for discovery reports."""

    list_display = ["title", "report_type", "generated_at", "generated_by"]
    list_filter = ["report_type"]
    search_fields = ["title"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
