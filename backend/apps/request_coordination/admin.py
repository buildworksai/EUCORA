# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for Request Coordination.
"""
from django.contrib import admin

from .models import (
    CommunicationTemplate,
    EscalationEvent,
    EscalationRule,
    RequestCommunication,
    RequestStakeholder,
    RequestStatusUpdate,
    TrackedRequest,
)


@admin.register(TrackedRequest)
class TrackedRequestAdmin(admin.ModelAdmin):
    """Admin for tracked requests."""

    list_display = [
        "servicenow_number",
        "short_description",
        "requestor_name",
        "status",
        "priority",
        "is_escalated",
        "sla_due",
        "created_at",
    ]
    list_filter = ["status", "priority", "is_escalated", "request_type"]
    search_fields = ["servicenow_number", "short_description", "requestor_name", "requestor_email"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "last_updated"]
    date_hierarchy = "created_at"


@admin.register(RequestStakeholder)
class RequestStakeholderAdmin(admin.ModelAdmin):
    """Admin for request stakeholders."""

    list_display = ["name", "email", "role", "request", "created_at"]
    list_filter = ["role"]
    search_fields = ["name", "email", "request__servicenow_number"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(RequestStatusUpdate)
class RequestStatusUpdateAdmin(admin.ModelAdmin):
    """Admin for request status updates."""

    list_display = ["request", "old_status", "new_status", "updated_by", "created_at"]
    list_filter = ["old_status", "new_status"]
    search_fields = ["request__servicenow_number", "updated_by"]
    readonly_fields = ["id", "created_at"]


@admin.register(RequestCommunication)
class RequestCommunicationAdmin(admin.ModelAdmin):
    """Admin for request communications."""

    list_display = ["subject", "channel", "communication_type", "status", "sent_at", "created_at"]
    list_filter = ["channel", "communication_type", "status"]
    search_fields = ["subject", "request__servicenow_number"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "sent_at"]


@admin.register(EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    """Admin for escalation rules."""

    list_display = ["name", "trigger_type", "request_type", "is_active", "created_at"]
    list_filter = ["trigger_type", "is_active", "request_type"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EscalationEvent)
class EscalationEventAdmin(admin.ModelAdmin):
    """Admin for escalation events."""

    list_display = ["request", "rule", "escalation_level", "resolved_at", "created_at"]
    list_filter = ["escalation_level", "resolved_at"]
    search_fields = ["request__servicenow_number", "trigger_reason"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    """Admin for communication templates."""

    list_display = ["name", "communication_type", "channel", "is_active", "created_at"]
    list_filter = ["communication_type", "channel", "is_active"]
    search_fields = ["name", "subject_template"]
    readonly_fields = ["id", "created_at", "updated_at"]
