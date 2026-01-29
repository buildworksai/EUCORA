# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin interface for agent management.
"""
from django.contrib import admin

from .models import Agent, AgentDeploymentStatus, AgentOfflineQueue, AgentTask, AgentTelemetry


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin interface for agents."""

    list_display = ("hostname", "platform", "status", "agent_version", "last_heartbeat_at", "is_online")
    list_filter = ("platform", "status", "agent_version")
    search_fields = ("hostname", "ip_address", "mac_address")
    readonly_fields = ("id", "first_seen_at", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("id", "hostname", "platform", "platform_version", "agent_version")}),
        ("Status", {"fields": ("status", "last_heartbeat_at", "last_error")}),
        ("Hardware", {"fields": ("cpu_cores", "memory_mb", "disk_gb")}),
        ("Network", {"fields": ("ip_address", "mac_address")}),
        ("Metadata", {"fields": ("tags", "metadata", "registration_key"), "classes": ("collapse",)}),
        ("Audit", {"fields": ("first_seen_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    """Admin interface for agent tasks."""

    list_display = ("id", "agent", "task_type", "status", "created_at", "completed_at")
    list_filter = ("task_type", "status", "created_at")
    search_fields = ("agent__hostname", "correlation_id")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("id", "agent", "task_type", "status")}),
        ("Payload", {"fields": ("payload",)}),
        ("Execution", {"fields": ("assigned_at", "started_at", "completed_at", "timeout_seconds")}),
        ("Results", {"fields": ("result", "error_message", "exit_code")}),
        ("Audit", {"fields": ("correlation_id", "created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(AgentOfflineQueue)
class AgentOfflineQueueAdmin(admin.ModelAdmin):
    """Admin interface for offline queue."""

    list_display = ("agent", "task", "queued_at", "delivered_at", "retry_count")
    list_filter = ("queued_at", "delivered_at")
    search_fields = ("agent__hostname", "correlation_id")


@admin.register(AgentTelemetry)
class AgentTelemetryAdmin(admin.ModelAdmin):
    """Admin interface for telemetry."""

    list_display = ("agent", "cpu_usage_percent", "memory_usage_percent", "disk_usage_percent", "collected_at")
    list_filter = ("collected_at",)
    search_fields = ("agent__hostname",)
    readonly_fields = ("id", "received_at")


@admin.register(AgentDeploymentStatus)
class AgentDeploymentStatusAdmin(admin.ModelAdmin):
    """Admin interface for deployment status."""

    list_display = ("agent", "package_name", "status", "progress_percent", "started_at", "completed_at")
    list_filter = ("status", "created_at")
    search_fields = ("agent__hostname", "package_name", "deployment_intent_id", "correlation_id")
    readonly_fields = ("id", "created_at", "updated_at")
