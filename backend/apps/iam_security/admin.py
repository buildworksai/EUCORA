# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for IAM Security.
"""
from django.contrib import admin

from .models import AnomalyDetection, DetectionRule, IdentityProvider, PermissionChange, SecurityAlert, SignInEvent


@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    """Admin for identity providers."""

    list_display = [
        "name",
        "provider_type",
        "is_active",
        "last_sync",
        "sync_interval_minutes",
        "created_at",
    ]
    list_filter = ["provider_type", "is_active", "created_at"]
    search_fields = ["name", "tenant_id"]
    readonly_fields = ["id", "created_at", "updated_at", "last_sync"]


@admin.register(SignInEvent)
class SignInEventAdmin(admin.ModelAdmin):
    """Admin for sign-in events."""

    list_display = [
        "user_principal",
        "provider",
        "status",
        "client_ip",
        "event_time",
        "risk_level",
    ]
    list_filter = ["status", "provider", "event_time", "risk_level"]
    search_fields = ["user_principal", "event_id"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["provider"]


@admin.register(PermissionChange)
class PermissionChangeAdmin(admin.ModelAdmin):
    """Admin for permission changes."""

    list_display = [
        "target_principal",
        "change_type",
        "resource_type",
        "resource_name",
        "actor_principal",
        "event_time",
    ]
    list_filter = ["change_type", "resource_type", "event_time"]
    search_fields = ["target_principal", "actor_principal", "event_id"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["provider"]


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    """Admin for anomaly detections."""

    list_display = [
        "anomaly_type",
        "severity",
        "user_principal",
        "status",
        "assigned_to",
        "detection_rule",
        "correlation_id",
    ]
    list_filter = ["anomaly_type", "severity", "status", "created_at"]
    search_fields = ["user_principal", "correlation_id", "detection_rule"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "resolved_at"]
    raw_id_fields = ["provider", "assigned_to"]


@admin.register(DetectionRule)
class DetectionRuleAdmin(admin.ModelAdmin):
    """Admin for detection rules."""

    list_display = [
        "name",
        "anomaly_type",
        "severity",
        "is_active",
        "trigger_count",
        "last_triggered",
    ]
    list_filter = ["anomaly_type", "severity", "is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "last_triggered", "trigger_count", "created_at", "updated_at"]


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    """Admin for security alerts."""

    list_display = [
        "anomaly",
        "channel",
        "status",
        "sent_at",
        "correlation_id",
    ]
    list_filter = ["channel", "status", "sent_at"]
    search_fields = ["correlation_id", "subject"]
    readonly_fields = ["id", "correlation_id", "sent_at", "created_at"]
    raw_id_fields = ["anomaly"]
