# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for SecOps Agent.
"""
from django.contrib import admin

from .models import (
    ComplianceBaseline,
    ComplianceCheck,
    RemediationPlan,
    SecurityAlert,
    SIEMConnection,
    Vulnerability,
    VulnerabilityInstance,
    VulnerabilityScanner,
)


@admin.register(VulnerabilityScanner)
class VulnerabilityScannerAdmin(admin.ModelAdmin):
    """Admin for vulnerability scanners."""

    list_display = ["name", "scanner_type", "is_active", "last_sync", "created_at"]
    list_filter = ["scanner_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_sync"]


@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    """Admin for vulnerabilities."""

    list_display = ["cve_id", "title", "severity", "cvss_score", "published_date"]
    list_filter = ["severity", "published_date"]
    search_fields = ["cve_id", "title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(VulnerabilityInstance)
class VulnerabilityInstanceAdmin(admin.ModelAdmin):
    """Admin for vulnerability instances."""

    list_display = ["vulnerability", "asset_name", "status", "detected_at", "remediation_due"]
    list_filter = ["status", "vulnerability__severity", "scanner"]
    search_fields = ["asset_id", "asset_name", "vulnerability__cve_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(RemediationPlan)
class RemediationPlanAdmin(admin.ModelAdmin):
    """Admin for remediation plans."""

    list_display = ["name", "vulnerability", "remediation_type", "risk_level", "status", "approved_by", "created_at"]
    list_filter = ["status", "risk_level", "remediation_type"]
    search_fields = ["name", "vulnerability__cve_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "approved_at", "executed_at", "completed_at"]


@admin.register(SIEMConnection)
class SIEMConnectionAdmin(admin.ModelAdmin):
    """Admin for SIEM connections."""

    list_display = ["name", "siem_type", "is_active", "created_at"]
    list_filter = ["siem_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    """Admin for security alerts."""

    list_display = ["alert_id", "title", "severity", "status", "siem", "alert_time"]
    list_filter = ["severity", "status", "siem"]
    search_fields = ["alert_id", "title", "description"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(ComplianceBaseline)
class ComplianceBaselineAdmin(admin.ModelAdmin):
    """Admin for compliance baselines."""

    list_display = ["name", "framework", "version", "is_active", "created_at"]
    list_filter = ["framework", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    """Admin for compliance checks."""

    list_display = ["baseline", "asset_id", "overall_score", "check_time"]
    list_filter = ["baseline__framework", "check_time"]
    search_fields = ["asset_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
