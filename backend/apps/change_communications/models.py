# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Change Communications models for E11 enhancement.

Implements change records, stakeholder groups, communication templates,
and KB article linking for deployment lifecycle management.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class ChangeRecord(TimeStampedModel, CorrelationIdModel):
    """
    Linked ServiceNow change record.

    Tracks the lifecycle of a change from creation through closure,
    with links to deployment intents and evidence.
    """

    class ChangeType(models.TextChoices):
        STANDARD = "standard", "Standard (Pre-approved)"
        NORMAL = "normal", "Normal (CAB Approval)"
        EMERGENCY = "emergency", "Emergency (Expedited)"

    class State(models.TextChoices):
        NEW = "new", "New"
        ASSESS = "assess", "Assess"
        AUTHORIZE = "authorize", "Authorize"
        SCHEDULED = "scheduled", "Scheduled"
        IMPLEMENT = "implement", "Implement"
        REVIEW = "review", "Review"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ServiceNow linkage
    servicenow_number = models.CharField(max_length=50, unique=True, help_text="CHG number")
    servicenow_sys_id = models.CharField(max_length=100, help_text="ServiceNow sys_id")

    # Deployment link
    deployment_intent = models.ForeignKey(
        "deployment_intents.DeploymentIntent",
        on_delete=models.CASCADE,
        related_name="change_records",
        null=True,
        blank=True,
    )

    # Change details
    change_type = models.CharField(max_length=20, choices=ChangeType.choices, default=ChangeType.NORMAL)
    state = models.CharField(max_length=50, choices=State.choices, default=State.NEW, db_index=True)
    short_description = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, default="moderate")
    impact = models.CharField(max_length=20, default="low")

    # Scheduling
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Closure
    close_code = models.CharField(max_length=50, blank=True)
    close_notes = models.TextField(blank=True)
    success = models.BooleanField(null=True)

    # Ownership
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_changes",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_changes",
    )

    class Meta:
        verbose_name = "Change Record"
        verbose_name_plural = "Change Records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["servicenow_number"]),
            models.Index(fields=["state", "created_at"]),
            models.Index(fields=["change_type"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["planned_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.servicenow_number}: {self.short_description}"


class StakeholderGroup(TimeStampedModel):
    """
    Groups of stakeholders for communication.

    Defines notification channels and recipients for change communications.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        TEAMS = "teams", "Microsoft Teams"
        SLACK = "slack", "Slack"
        SERVICENOW = "servicenow", "ServiceNow Notification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    notification_channel = models.CharField(max_length=50, choices=Channel.choices)
    channel_config = models.JSONField(
        default=dict,
        help_text="Channel-specific configuration (emails, webhook URLs, etc.)",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Scope mapping
    scope_filters = models.JSONField(
        default=dict,
        help_text="Filters for when to notify this group (apps, BUs, etc.)",
    )

    class Meta:
        verbose_name = "Stakeholder Group"
        verbose_name_plural = "Stakeholder Groups"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["notification_channel", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.notification_channel})"


class CommunicationTemplate(TimeStampedModel):
    """
    Templates for stakeholder communications.

    Supports variable substitution for dynamic content.
    """

    class EventType(models.TextChoices):
        SCHEDULED = "scheduled", "Change Scheduled"
        STARTED = "started", "Deployment Started"
        PROGRESS = "progress", "Progress Update"
        COMPLETED = "completed", "Deployment Completed"
        FAILED = "failed", "Deployment Failed"
        ROLLBACK = "rollback", "Rollback Initiated"
        CLOSED = "closed", "Change Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    channel = models.CharField(max_length=50, choices=StakeholderGroup.Channel.choices)
    subject_template = models.CharField(max_length=500)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

    # Template variables documentation
    variables = models.JSONField(
        default=list,
        help_text="List of available template variables",
    )

    class Meta:
        verbose_name = "Communication Template"
        verbose_name_plural = "Communication Templates"
        ordering = ["event_type", "channel"]
        indexes = [
            models.Index(fields=["event_type", "channel", "is_active"]),
        ]
        unique_together = [["event_type", "channel"]]

    def __str__(self) -> str:
        return f"{self.name} ({self.event_type} - {self.channel})"


class Communication(TimeStampedModel, CorrelationIdModel):
    """
    Record of sent communications.

    Tracks all communications sent for audit and troubleshooting.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_record = models.ForeignKey(ChangeRecord, on_delete=models.CASCADE, related_name="communications")
    template = models.ForeignKey(
        CommunicationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    stakeholder_group = models.ForeignKey(
        StakeholderGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Rendered content
    channel = models.CharField(max_length=50)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    recipients = models.JSONField(default=list)

    # Status tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["change_record", "status"]),
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["sent_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel}: {self.subject[:50]}... ({self.status})"


class KBArticleLink(TimeStampedModel):
    """
    Links between deployments and KB articles.

    Tracks auto-generated and referenced KB articles.
    """

    class LinkType(models.TextChoices):
        CREATED = "created", "Created by Agent"
        UPDATED = "updated", "Updated by Agent"
        REFERENCED = "referenced", "Referenced"
        LINKED = "linked", "Manually Linked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_record = models.ForeignKey(ChangeRecord, on_delete=models.CASCADE, related_name="kb_articles")

    # ServiceNow KB article
    kb_article_number = models.CharField(max_length=50)
    kb_article_sys_id = models.CharField(max_length=100)
    kb_article_title = models.CharField(max_length=500, blank=True)

    # Link details
    link_type = models.CharField(max_length=50, choices=LinkType.choices)
    created_by_agent = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "KB Article Link"
        verbose_name_plural = "KB Article Links"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["change_record"]),
            models.Index(fields=["kb_article_number"]),
            models.Index(fields=["link_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.kb_article_number}: {self.kb_article_title[:50] or 'Untitled'}"


class ChangeAuditEvent(TimeStampedModel):
    """
    Audit trail for change record activities.

    Tracks all state transitions and communications.
    """

    class EventType(models.TextChoices):
        CREATED = "created", "Change Created"
        STATE_CHANGE = "state_change", "State Change"
        NOTIFICATION_SENT = "notification_sent", "Notification Sent"
        KB_LINKED = "kb_linked", "KB Article Linked"
        EVIDENCE_ATTACHED = "evidence_attached", "Evidence Attached"
        APPROVAL_RECEIVED = "approval_received", "Approval Received"
        CLOSED = "closed", "Change Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_record = models.ForeignKey(ChangeRecord, on_delete=models.CASCADE, related_name="audit_events")
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Change Audit Event"
        verbose_name_plural = "Change Audit Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["change_record", "created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.change_record.servicenow_number} - {self.event_type}"
