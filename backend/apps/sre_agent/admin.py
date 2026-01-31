# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for SRE Agent.
"""
from django.contrib import admin

from .models import (
    HealthCheckResult,
    HealthEndpoint,
    MonitoringPlatform,
    Runbook,
    RunbookExecution,
    SelfHealingExecution,
    SelfHealingRule,
    SLODefinition,
    SLOMetric,
)


@admin.register(MonitoringPlatform)
class MonitoringPlatformAdmin(admin.ModelAdmin):
    """Admin for monitoring platforms."""

    list_display = ["name", "platform_type", "is_active", "created_at"]
    list_filter = ["platform_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(HealthEndpoint)
class HealthEndpointAdmin(admin.ModelAdmin):
    """Admin for health endpoints."""

    list_display = ["name", "url", "is_active", "check_interval_minutes", "created_at"]
    list_filter = ["is_active", "application"]
    search_fields = ["name", "url"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    """Admin for health check results."""

    list_display = ["endpoint", "status", "response_time_ms", "check_time"]
    list_filter = ["status", "check_time"]
    search_fields = ["endpoint__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SLODefinition)
class SLODefinitionAdmin(admin.ModelAdmin):
    """Admin for SLO definitions."""

    list_display = ["name", "service_name", "slo_type", "target_value", "is_active", "created_at"]
    list_filter = ["slo_type", "is_active", "measurement_window"]
    search_fields = ["name", "service_name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SLOMetric)
class SLOMetricAdmin(admin.ModelAdmin):
    """Admin for SLO metrics."""

    list_display = ["slo", "actual_value", "target_met", "measurement_time"]
    list_filter = ["target_met", "measurement_time"]
    search_fields = ["slo__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SelfHealingRule)
class SelfHealingRuleAdmin(admin.ModelAdmin):
    """Admin for self-healing rules."""

    list_display = ["name", "trigger_type", "target_type", "risk_level", "is_active", "created_at"]
    list_filter = ["trigger_type", "target_type", "risk_level", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SelfHealingExecution)
class SelfHealingExecutionAdmin(admin.ModelAdmin):
    """Admin for self-healing executions."""

    list_display = ["rule", "status", "started_at", "completed_at", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["rule__name"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(Runbook)
class RunbookAdmin(admin.ModelAdmin):
    """Admin for runbooks."""

    list_display = ["name", "category", "automation_level", "risk_level", "is_active", "created_at"]
    list_filter = ["category", "automation_level", "risk_level", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(RunbookExecution)
class RunbookExecutionAdmin(admin.ModelAdmin):
    """Admin for runbook executions."""

    list_display = ["runbook", "status", "current_step", "started_at", "completed_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["runbook__name"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
