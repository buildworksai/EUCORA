# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin configuration for license_management.
"""
from django.contrib import admin

from .models import (
    Assignment,
    ConsumptionSignal,
    ConsumptionSnapshot,
    ConsumptionUnit,
    Entitlement,
    ImportJob,
    LicenseAlert,
    LicensePool,
    LicenseSKU,
    ReconciliationRun,
    Vendor,
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin for Vendor model."""

    list_display = ("name", "identifier", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "identifier")
    ordering = ("name",)


@admin.register(LicenseSKU)
class LicenseSKUAdmin(admin.ModelAdmin):
    """Admin for LicenseSKU model."""

    list_display = ("name", "vendor", "sku_code", "license_model_type", "is_active")
    list_filter = ("vendor", "license_model_type", "is_active")
    search_fields = ("name", "sku_code", "vendor__name")
    ordering = ("vendor__name", "name")


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    """Admin for Entitlement model."""

    list_display = ("sku", "contract_id", "entitled_quantity", "status", "start_date", "end_date")
    list_filter = ("status", "sku__vendor")
    search_fields = ("contract_id", "sku__name")
    ordering = ("-start_date",)
    date_hierarchy = "start_date"


@admin.register(LicensePool)
class LicensePoolAdmin(admin.ModelAdmin):
    """Admin for LicensePool model."""

    list_display = ("name", "sku", "scope_type", "scope_value", "is_active")
    list_filter = ("scope_type", "is_active", "sku__vendor")
    search_fields = ("name", "sku__name")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin for Assignment model."""

    list_display = ("pool", "principal_type", "principal_id", "status", "assigned_at")
    list_filter = ("status", "principal_type")
    search_fields = ("principal_id", "principal_name")


@admin.register(ConsumptionSignal)
class ConsumptionSignalAdmin(admin.ModelAdmin):
    """Admin for ConsumptionSignal model."""

    list_display = ("source_system", "raw_id", "sku", "principal_id", "timestamp", "is_processed")
    list_filter = ("source_system", "is_processed")
    search_fields = ("raw_id", "principal_id")
    date_hierarchy = "timestamp"


@admin.register(ConsumptionUnit)
class ConsumptionUnitAdmin(admin.ModelAdmin):
    """Admin for ConsumptionUnit model."""

    list_display = ("sku", "principal_type", "principal_id", "status", "effective_from")
    list_filter = ("status", "principal_type")
    search_fields = ("principal_id",)


@admin.register(ConsumptionSnapshot)
class ConsumptionSnapshotAdmin(admin.ModelAdmin):
    """Admin for ConsumptionSnapshot model."""

    list_display = ("sku", "pool", "reconciled_at", "entitled", "consumed", "remaining")
    list_filter = ("sku__vendor",)
    search_fields = ("sku__name",)
    date_hierarchy = "reconciled_at"


@admin.register(ReconciliationRun)
class ReconciliationRunAdmin(admin.ModelAdmin):
    """Admin for ReconciliationRun model."""

    list_display = ("id", "status", "started_at", "completed_at", "skus_processed", "snapshots_created")
    list_filter = ("status",)
    date_hierarchy = "started_at"


@admin.register(LicenseAlert)
class LicenseAlertAdmin(admin.ModelAdmin):
    """Admin for LicenseAlert model."""

    list_display = ("sku", "alert_type", "severity", "detected_at", "acknowledged")
    list_filter = ("alert_type", "severity", "acknowledged")
    search_fields = ("message",)
    date_hierarchy = "detected_at"


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """Admin for ImportJob model."""

    list_display = ("file_name", "import_type", "status", "total_rows", "success_count", "error_count")
    list_filter = ("import_type", "status")
    search_fields = ("file_name",)
