# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for Change Communications.
"""
from django.contrib import admin

from .models import (
    ChangeAuditEvent,
    ChangeRecord,
    Communication,
    CommunicationTemplate,
    KBArticleLink,
    StakeholderGroup,
)


@admin.register(ChangeRecord)
class ChangeRecordAdmin(admin.ModelAdmin):
    """Admin for change records."""

    list_display = ["servicenow_number", "short_description", "state", "change_type", "planned_start"]
    list_filter = ["state", "change_type", "risk_level"]
    search_fields = ["servicenow_number", "short_description"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(StakeholderGroup)
class StakeholderGroupAdmin(admin.ModelAdmin):
    """Admin for stakeholder groups."""

    list_display = ["name", "notification_channel", "is_active"]
    list_filter = ["notification_channel", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    """Admin for communication templates."""

    list_display = ["name", "event_type", "channel", "is_active"]
    list_filter = ["event_type", "channel", "is_active"]
    search_fields = ["name", "subject_template"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    """Admin for communications."""

    list_display = ["change_record", "channel", "subject", "status", "sent_at"]
    list_filter = ["channel", "status"]
    search_fields = ["subject", "change_record__servicenow_number"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(KBArticleLink)
class KBArticleLinkAdmin(admin.ModelAdmin):
    """Admin for KB article links."""

    list_display = ["kb_article_number", "kb_article_title", "link_type", "change_record"]
    list_filter = ["link_type", "created_by_agent"]
    search_fields = ["kb_article_number", "kb_article_title"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ChangeAuditEvent)
class ChangeAuditEventAdmin(admin.ModelAdmin):
    """Admin for change audit events."""

    list_display = ["change_record", "event_type", "description", "created_at"]
    list_filter = ["event_type"]
    readonly_fields = ["id", "created_at", "updated_at"]
