# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Change Communications API.
"""
from rest_framework import serializers

from .models import (
    ChangeAuditEvent,
    ChangeRecord,
    Communication,
    CommunicationTemplate,
    KBArticleLink,
    StakeholderGroup,
)


class ChangeRecordSerializer(serializers.ModelSerializer):
    """Serializer for change records."""

    requested_by_username = serializers.CharField(source="requested_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    communication_count = serializers.SerializerMethodField()
    kb_article_count = serializers.SerializerMethodField()

    class Meta:
        model = ChangeRecord
        fields = [
            "id",
            "correlation_id",
            "servicenow_number",
            "servicenow_sys_id",
            "deployment_intent",
            "change_type",
            "state",
            "short_description",
            "description",
            "risk_level",
            "impact",
            "planned_start",
            "planned_end",
            "actual_start",
            "actual_end",
            "close_code",
            "close_notes",
            "success",
            "requested_by",
            "requested_by_username",
            "assigned_to",
            "assigned_to_username",
            "communication_count",
            "kb_article_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]

    def get_communication_count(self, obj: ChangeRecord) -> int:
        """Get count of communications."""
        return obj.communications.count()

    def get_kb_article_count(self, obj: ChangeRecord) -> int:
        """Get count of KB articles."""
        return obj.kb_articles.count()


class ChangeRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating change records."""

    class Meta:
        model = ChangeRecord
        fields = [
            "servicenow_number",
            "servicenow_sys_id",
            "deployment_intent",
            "change_type",
            "short_description",
            "description",
            "risk_level",
            "impact",
            "planned_start",
            "planned_end",
            "requested_by",
            "assigned_to",
        ]


class StakeholderGroupSerializer(serializers.ModelSerializer):
    """Serializer for stakeholder groups."""

    class Meta:
        model = StakeholderGroup
        fields = [
            "id",
            "name",
            "description",
            "notification_channel",
            "channel_config",
            "is_active",
            "scope_filters",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommunicationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for communication templates."""

    class Meta:
        model = CommunicationTemplate
        fields = [
            "id",
            "name",
            "event_type",
            "channel",
            "subject_template",
            "body_template",
            "is_active",
            "variables",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommunicationTemplatePreviewSerializer(serializers.Serializer):
    """Serializer for previewing a template."""

    context = serializers.DictField(child=serializers.CharField())


class CommunicationSerializer(serializers.ModelSerializer):
    """Serializer for communications."""

    change_record_number = serializers.CharField(source="change_record.servicenow_number", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    stakeholder_group_name = serializers.CharField(source="stakeholder_group.name", read_only=True)

    class Meta:
        model = Communication
        fields = [
            "id",
            "correlation_id",
            "change_record",
            "change_record_number",
            "template",
            "template_name",
            "stakeholder_group",
            "stakeholder_group_name",
            "channel",
            "subject",
            "body",
            "recipients",
            "sent_at",
            "status",
            "error_message",
            "retry_count",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "sent_at", "status", "error_message", "created_at"]


class SendCommunicationSerializer(serializers.Serializer):
    """Serializer for sending a communication."""

    change_record_id = serializers.UUIDField()
    template_id = serializers.UUIDField(required=False)
    stakeholder_group_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    event_type = serializers.ChoiceField(choices=CommunicationTemplate.EventType.choices)
    custom_message = serializers.CharField(required=False, allow_blank=True)


class KBArticleLinkSerializer(serializers.ModelSerializer):
    """Serializer for KB article links."""

    change_record_number = serializers.CharField(source="change_record.servicenow_number", read_only=True)

    class Meta:
        model = KBArticleLink
        fields = [
            "id",
            "change_record",
            "change_record_number",
            "kb_article_number",
            "kb_article_sys_id",
            "kb_article_title",
            "link_type",
            "created_by_agent",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GenerateKBArticleSerializer(serializers.Serializer):
    """Serializer for generating a KB article."""

    change_record_id = serializers.UUIDField()
    title = serializers.CharField(required=False)
    include_resolution_steps = serializers.BooleanField(default=True)


class ChangeAuditEventSerializer(serializers.ModelSerializer):
    """Serializer for change audit events."""

    performed_by_username = serializers.CharField(source="performed_by.username", read_only=True)

    class Meta:
        model = ChangeAuditEvent
        fields = [
            "id",
            "change_record",
            "event_type",
            "description",
            "old_value",
            "new_value",
            "performed_by",
            "performed_by_username",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ChangeRecordCloseSerializer(serializers.Serializer):
    """Serializer for closing a change record."""

    close_code = serializers.ChoiceField(
        choices=[
            ("successful", "Successful"),
            ("successful_issues", "Successful with Issues"),
            ("unsuccessful", "Unsuccessful"),
            ("cancelled", "Cancelled"),
        ]
    )
    close_notes = serializers.CharField()
    success = serializers.BooleanField()


class ChangeDashboardSerializer(serializers.Serializer):
    """Serializer for change dashboard data."""

    active_changes = serializers.IntegerField()
    pending_notifications = serializers.IntegerField()
    communications_today = serializers.IntegerField()
    kb_articles_created = serializers.IntegerField()
    changes_by_state = serializers.DictField()
    recent_communications = CommunicationSerializer(many=True)
