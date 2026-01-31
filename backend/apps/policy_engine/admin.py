# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine admin configuration.
"""
from django.contrib import admin

from .models import ApplicationPolicy, PolicySetting, PolicyTemplate


@admin.register(ApplicationPolicy)
class ApplicationPolicyAdmin(admin.ModelAdmin):
    """Admin for ApplicationPolicy."""

    list_display = ["name", "application", "platform", "is_active", "is_default", "created_at"]
    list_filter = ["platform", "is_active", "is_default", "created_at"]
    search_fields = ["name", "application__name", "description"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["application", "application_version", "created_by"]
    autocomplete_fields = ["application"]


@admin.register(PolicySetting)
class PolicySettingAdmin(admin.ModelAdmin):
    """Admin for PolicySetting."""

    list_display = ["policy", "category", "setting_key", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["policy__name", "setting_key"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["policy"]


@admin.register(PolicyTemplate)
class PolicyTemplateAdmin(admin.ModelAdmin):
    """Admin for PolicyTemplate."""

    list_display = ["name", "template_type", "platform", "is_system", "created_at"]
    list_filter = ["template_type", "is_system", "platform", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fields = [
        "name",
        "template_type",
        "description",
        "settings",
        "is_system",
        "platform",
        "created_at",
        "updated_at",
    ]
