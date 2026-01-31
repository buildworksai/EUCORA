# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Request Coordination models for E16 enhancement.

Implements ServiceNow request tracking, SLA monitoring, escalations,
and stakeholder communications.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class TrackedRequest(TimeStampedModel, CorrelationIdModel):
    """
    ServiceNow request being tracked.

    Tracks request lifecycle, SLA status, and escalation state.
    """

    class RequestType(models.TextChoices):
        SOFTWARE_INSTALL = "software_install", "Software Installation"
        ACCESS_REQUEST = "access_request", "Access Request"
        HARDWARE = "hardware", "Hardware Request"
        CONFIG_CHANGE = "config_change", "Configuration Change"
        EXCEPTION = "exception", "Exception Request"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In Progress"
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        CRITICAL = "1", "Critical"
        HIGH = "2", "High"
        MEDIUM = "3", "Medium"
        LOW = "4", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    servicenow_number = models.CharField(max_length=50, unique=True, db_index=True)
    servicenow_sys_id = models.CharField(max_length=100)
    request_type = models.CharField(max_length=50, choices=RequestType.choices, db_index=True)
    short_description = models.CharField(max_length=255)
    requestor_email = models.EmailField()
    requestor_name = models.CharField(max_length=255)
    assigned_to = models.CharField(max_length=255, null=True, blank=True)
    assignment_group = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.NEW, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    sla_due = models.DateTimeField(null=True, blank=True, db_index=True)
    is_escalated = models.BooleanField(default=False, db_index=True)
    escalation_level = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)
    blocked_reason = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Tracked Request"
        verbose_name_plural = "Tracked Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["sla_due", "is_escalated"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["request_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.servicenow_number}: {self.short_description}"


class RequestStakeholder(TimeStampedModel):
    """
    Stakeholder interested in a request.

    Tracks notification preferences and roles.
    """

    class Role(models.TextChoices):
        REQUESTOR = "requestor", "Requestor"
        APPROVER = "approver", "Approver"
        WATCHER = "watcher", "Watcher"
        MANAGER = "manager", "Manager"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE, related_name="stakeholders")
    email = models.EmailField()
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=Role.choices, db_index=True)
    notification_preferences = models.JSONField(
        default=dict,
        help_text="Notification preferences (channels, frequency, etc.)",
    )

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Request Stakeholder"
        verbose_name_plural = "Request Stakeholders"
        ordering = ["role", "name"]
        indexes = [
            models.Index(fields=["request", "role"]),
            models.Index(fields=["email"]),
        ]
        unique_together = [["request", "email"]]

    def __str__(self) -> str:
        return f"{self.name} ({self.role}) - {self.request.servicenow_number}"


class RequestStatusUpdate(TimeStampedModel):
    """
    Status update for a tracked request.

    Tracks all status changes for audit trail.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE, related_name="status_updates")
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    update_notes = models.TextField(null=True, blank=True)
    updated_by = models.CharField(max_length=255)

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Request Status Update"
        verbose_name_plural = "Request Status Updates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.request.servicenow_number}: {self.old_status} → {self.new_status}"


class RequestCommunication(TimeStampedModel, CorrelationIdModel):
    """
    Communication sent for a request.

    Tracks all communications sent to stakeholders.
    """

    class CommunicationType(models.TextChoices):
        STATUS_UPDATE = "status_update", "Status Update"
        SLA_WARNING = "sla_warning", "SLA Warning"
        ESCALATION = "escalation", "Escalation"
        COMPLETION = "completion", "Completion"
        WEEKLY_DIGEST = "weekly_digest", "Weekly Digest"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        TEAMS = "teams", "Microsoft Teams"
        SLACK = "slack", "Slack"
        SERVICENOW = "servicenow", "ServiceNow Notification"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE, related_name="communications")
    communication_type = models.CharField(max_length=50, choices=CommunicationType.choices, db_index=True)
    channel = models.CharField(max_length=50, choices=Channel.choices)
    recipients = models.JSONField(default=list)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Request Communication"
        verbose_name_plural = "Request Communications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request", "communication_type"]),
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["sent_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel}: {self.subject[:50]}... ({self.status})"


class EscalationRule(TimeStampedModel):
    """
    Rules for automatic escalation.

    Defines triggers and actions for request escalations.
    """

    class TriggerType(models.TextChoices):
        SLA_WARNING = "sla_warning", "SLA Warning"
        SLA_BREACH = "sla_breach", "SLA Breach"
        BLOCKED = "blocked", "Blocked"
        REASSIGNMENT = "reassignment", "Multiple Reassignments"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    request_type = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    trigger_type = models.CharField(max_length=50, choices=TriggerType.choices, db_index=True)
    trigger_config = models.JSONField(
        default=dict,
        help_text="Trigger configuration (hours_before_breach, blocked_days, etc.)",
    )
    escalation_actions = models.JSONField(
        default=list,
        help_text="Actions to take when triggered (notify, escalate, update_priority, etc.)",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Escalation Rule"
        verbose_name_plural = "Escalation Rules"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["trigger_type", "is_active"]),
            models.Index(fields=["request_type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.trigger_type})"


class EscalationEvent(TimeStampedModel, CorrelationIdModel):
    """
    Record of escalation triggered.

    Tracks all escalations for audit and resolution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE, related_name="escalation_events")
    rule = models.ForeignKey(EscalationRule, on_delete=models.SET_NULL, null=True, blank=True)
    trigger_reason = models.TextField()
    escalation_level = models.IntegerField(default=1)
    actions_taken = models.JSONField(default=list)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Escalation Event"
        verbose_name_plural = "Escalation Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request", "escalation_level"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["resolved_at"]),
        ]

    def __str__(self) -> str:
        return f"Escalation L{self.escalation_level}: {self.request.servicenow_number}"


class CommunicationTemplate(TimeStampedModel):
    """
    Templates for request communications.

    Supports variable substitution for dynamic content.
    """

    class CommunicationType(models.TextChoices):
        STATUS_UPDATE = "status_update", "Status Update"
        SLA_WARNING = "sla_warning", "SLA Warning"
        ESCALATION = "escalation", "Escalation"
        COMPLETION = "completion", "Completion"
        WEEKLY_DIGEST = "weekly_digest", "Weekly Digest"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        TEAMS = "teams", "Microsoft Teams"
        SLACK = "slack", "Slack"
        SERVICENOW = "servicenow", "ServiceNow Notification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    communication_type = models.CharField(max_length=50, choices=CommunicationType.choices, db_index=True)
    channel = models.CharField(max_length=50, choices=Channel.choices)
    subject_template = models.CharField(max_length=500)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

    # Template variables documentation
    variables = models.JSONField(
        default=list,
        help_text="List of available template variables",
    )

    class Meta:
        app_label = "request_coordination"
        verbose_name = "Communication Template"
        verbose_name_plural = "Communication Templates"
        ordering = ["communication_type", "channel"]
        indexes = [
            models.Index(fields=["communication_type", "channel", "is_active"]),
        ]
        unique_together = [["communication_type", "channel"]]

    def __str__(self) -> str:
        return f"{self.name} ({self.communication_type} - {self.channel})"
