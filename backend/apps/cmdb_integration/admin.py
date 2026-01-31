# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for CMDB Integration.
"""
from django.contrib import admin

from .models import (
    CMDBConnection,
    CMDBDataQualityReport,
    CMDBDiscrepancy,
    CMDBSyncRecord,
    CMDBTableMapping,
    CMDBValidationRule,
)


@admin.register(CMDBConnection)
class CMDBConnectionAdmin(admin.ModelAdmin):
    """Admin for CMDB connections."""

    list_display = ["name", "instance_url", "auth_type", "is_active", "last_sync"]
    list_filter = ["is_active", "auth_type"]
    search_fields = ["name", "instance_url"]
    readonly_fields = ["id", "created_at", "updated_at", "last_sync", "last_sync_status"]


@admin.register(CMDBTableMapping)
class CMDBTableMappingAdmin(admin.ModelAdmin):
    """Admin for CMDB table mappings."""

    list_display = ["source_type", "source_table", "cmdb_table", "sync_enabled", "priority"]
    list_filter = ["source_type", "sync_enabled", "connection"]
    search_fields = ["source_table", "cmdb_table"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CMDBValidationRule)
class CMDBValidationRuleAdmin(admin.ModelAdmin):
    """Admin for CMDB validation rules."""

    list_display = ["name", "cmdb_table", "field_name", "rule_type", "severity", "is_active"]
    list_filter = ["rule_type", "severity", "is_active", "cmdb_table"]
    search_fields = ["name", "cmdb_table", "field_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CMDBSyncRecord)
class CMDBSyncRecordAdmin(admin.ModelAdmin):
    """Admin for CMDB sync records."""

    list_display = ["id", "connection", "sync_type", "status", "started_at", "records_processed"]
    list_filter = ["status", "sync_type", "connection"]
    search_fields = ["correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(CMDBDiscrepancy)
class CMDBDiscrepancyAdmin(admin.ModelAdmin):
    """Admin for CMDB discrepancies."""

    list_display = ["ci_name", "discrepancy_type", "recommended_action", "status", "created_at"]
    list_filter = ["discrepancy_type", "status", "recommended_action"]
    search_fields = ["ci_name", "ci_sys_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CMDBDataQualityReport)
class CMDBDataQualityReportAdmin(admin.ModelAdmin):
    """Admin for CMDB data quality reports."""

    list_display = ["connection", "overall_score", "completeness_score", "created_at"]
    list_filter = ["connection"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
