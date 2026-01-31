# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin for Planning Agent.
"""
from django.contrib import admin

from .models import (
    BlastRadiusAnalysis,
    ChangeFreezePeriod,
    DeploymentPlan,
    DeploymentWindow,
    RingAssignment,
    RingDevice,
    RollbackPlan,
)


@admin.register(DeploymentPlan)
class DeploymentPlanAdmin(admin.ModelAdmin):
    """Admin for deployment plans."""

    list_display = ["name", "application", "version", "status", "overall_risk_score", "created_by", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "input_request"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "approved_at"]
    raw_id_fields = ["application", "created_by", "approved_by"]


@admin.register(RingAssignment)
class RingAssignmentAdmin(admin.ModelAdmin):
    """Admin for ring assignments."""

    list_display = ["plan", "ring_number", "ring_name", "device_count", "status", "scheduled_start"]
    list_filter = ["status", "ring_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["plan"]


@admin.register(RingDevice)
class RingDeviceAdmin(admin.ModelAdmin):
    """Admin for ring devices."""

    list_display = ["ring", "device_name", "user_principal", "criticality", "health_score"]
    list_filter = ["criticality", "ring"]
    search_fields = ["device_name", "device_id", "user_principal"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["ring"]


@admin.register(DeploymentWindow)
class DeploymentWindowAdmin(admin.ModelAdmin):
    """Admin for deployment windows."""

    list_display = ["name", "start_time", "end_time", "timezone", "is_active"]
    list_filter = ["is_active", "timezone"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ChangeFreezePeriod)
class ChangeFreezePeriodAdmin(admin.ModelAdmin):
    """Admin for change freeze periods."""

    list_display = ["name", "start_date", "end_date", "is_active"]
    list_filter = ["is_active", "start_date"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(BlastRadiusAnalysis)
class BlastRadiusAnalysisAdmin(admin.ModelAdmin):
    """Admin for blast radius analysis."""

    list_display = ["plan", "total_users_affected", "vip_users_affected", "productivity_impact_score"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["plan"]


@admin.register(RollbackPlan)
class RollbackPlanAdmin(admin.ModelAdmin):
    """Admin for rollback plans."""

    list_display = ["deployment_plan", "estimated_duration_minutes", "requires_cab_approval", "tested"]
    list_filter = ["requires_cab_approval", "tested"]
    readonly_fields = ["id", "created_at", "updated_at", "tested_at"]
    raw_id_fields = ["deployment_plan"]
