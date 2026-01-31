# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin for SLA Governance Agent.
"""
from django.contrib import admin

from .models import (
    KPIDefinition,
    KPIMeasurement,
    ServiceCatalogItem,
    SLABreach,
    SLACompliance,
    SLADefinition,
    SLAKPILink,
    SLATarget,
    SLATemplate,
)


@admin.register(ServiceCatalogItem)
class ServiceCatalogItemAdmin(admin.ModelAdmin):
    """Admin for service catalog items."""

    list_display = ["name", "category", "owner", "status", "created_at"]
    list_filter = ["category", "status"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SLADefinition)
class SLADefinitionAdmin(admin.ModelAdmin):
    """Admin for SLA definitions."""

    list_display = ["name", "version", "service", "status", "effective_from", "approved_by", "created_at"]
    list_filter = ["status", "effective_from"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "approved_at"]
    raw_id_fields = ["service", "created_by", "approved_by"]


@admin.register(SLATarget)
class SLATargetAdmin(admin.ModelAdmin):
    """Admin for SLA targets."""

    list_display = ["name", "sla", "metric_type", "target_value", "target_unit", "measurement_period"]
    list_filter = ["metric_type", "measurement_period"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["sla"]


@admin.register(KPIDefinition)
class KPIDefinitionAdmin(admin.ModelAdmin):
    """Admin for KPI definitions."""

    list_display = ["name", "unit", "direction", "is_active", "created_at"]
    list_filter = ["direction", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SLAKPILink)
class SLAKPILinkAdmin(admin.ModelAdmin):
    """Admin for SLA-KPI links."""

    list_display = ["sla_target", "kpi", "weight"]
    list_filter = ["kpi"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["sla_target", "kpi"]


@admin.register(KPIMeasurement)
class KPIMeasurementAdmin(admin.ModelAdmin):
    """Admin for KPI measurements."""

    list_display = ["kpi", "measurement_time", "value", "status"]
    list_filter = ["status", "measurement_time"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["kpi"]


@admin.register(SLACompliance)
class SLAComplianceAdmin(admin.ModelAdmin):
    """Admin for SLA compliance records."""

    list_display = ["sla", "period_start", "period_end", "overall_compliance", "status", "breach_count"]
    list_filter = ["status", "period_start", "period_end"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["sla"]


@admin.register(SLABreach)
class SLABreachAdmin(admin.ModelAdmin):
    """Admin for SLA breaches."""

    list_display = ["sla", "target", "breach_time", "severity", "target_value", "actual_value"]
    list_filter = ["severity", "breach_time"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["sla", "target"]


@admin.register(SLATemplate)
class SLATemplateAdmin(admin.ModelAdmin):
    """Admin for SLA templates."""

    list_display = ["name", "category", "is_active", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
