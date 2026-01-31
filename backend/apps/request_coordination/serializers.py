# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Request Coordination API.
"""
from rest_framework import serializers

from .models import (
    CommunicationTemplate,
    EscalationEvent,
    EscalationRule,
    RequestCommunication,
    RequestStakeholder,
    RequestStatusUpdate,
    TrackedRequest,
)


class TrackedRequestSerializer(serializers.ModelSerializer):
    """Serializer for tracked requests."""

    stakeholder_count = serializers.SerializerMethodField()
    communication_count = serializers.SerializerMethodField()
    escalation_count = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()

    class Meta:
        model = TrackedRequest
        fields = [
            "id",
            "correlation_id",
            "servicenow_number",
            "servicenow_sys_id",
            "request_type",
            "short_description",
            "requestor_email",
            "requestor_name",
            "assigned_to",
            "assignment_group",
            "status",
            "priority",
            "sla_due",
            "is_escalated",
            "escalation_level",
            "last_updated",
            "blocked_reason",
            "stakeholder_count",
            "communication_count",
            "escalation_count",
            "sla_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at", "last_updated"]

    def get_stakeholder_count(self, obj: TrackedRequest) -> int:
        """Get count of stakeholders."""
        return obj.stakeholders.count()

    def get_communication_count(self, obj: TrackedRequest) -> int:
        """Get count of communications."""
        return obj.communications.count()

    def get_escalation_count(self, obj: TrackedRequest) -> int:
        """Get count of escalations."""
        return obj.escalation_events.count()

    def get_sla_status(self, obj: TrackedRequest) -> str:
        """Get SLA status."""
        if not obj.sla_due:
            return "no_sla"
        from django.utils import timezone

        if obj.sla_due < timezone.now():
            return "breached"
        from datetime import timedelta

        if obj.sla_due - timezone.now() < timedelta(hours=4):
            return "warning"
        return "ok"


class RequestStakeholderSerializer(serializers.ModelSerializer):
    """Serializer for request stakeholders."""

    class Meta:
        model = RequestStakeholder
        fields = [
            "id",
            "request",
            "email",
            "name",
            "role",
            "notification_preferences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RequestStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for request status updates."""

    class Meta:
        model = RequestStatusUpdate
        fields = [
            "id",
            "request",
            "old_status",
            "new_status",
            "update_notes",
            "updated_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RequestCommunicationSerializer(serializers.ModelSerializer):
    """Serializer for request communications."""

    class Meta:
        model = RequestCommunication
        fields = [
            "id",
            "correlation_id",
            "request",
            "communication_type",
            "channel",
            "recipients",
            "subject",
            "body",
            "sent_at",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "sent_at", "created_at", "updated_at"]


class EscalationRuleSerializer(serializers.ModelSerializer):
    """Serializer for escalation rules."""

    trigger_count = serializers.SerializerMethodField()

    class Meta:
        model = EscalationRule
        fields = [
            "id",
            "name",
            "description",
            "request_type",
            "trigger_type",
            "trigger_config",
            "escalation_actions",
            "is_active",
            "trigger_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_trigger_count(self, obj: EscalationRule) -> int:
        """Get count of times this rule has been triggered."""
        return obj.escalationevent_set.count()


class EscalationEventSerializer(serializers.ModelSerializer):
    """Serializer for escalation events."""

    rule_name = serializers.CharField(source="rule.name", read_only=True)
    request_number = serializers.CharField(source="request.servicenow_number", read_only=True)

    class Meta:
        model = EscalationEvent
        fields = [
            "id",
            "correlation_id",
            "request",
            "request_number",
            "rule",
            "rule_name",
            "trigger_reason",
            "escalation_level",
            "actions_taken",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class CommunicationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for communication templates."""

    class Meta:
        model = CommunicationTemplate
        fields = [
            "id",
            "name",
            "communication_type",
            "channel",
            "subject_template",
            "body_template",
            "variables",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
