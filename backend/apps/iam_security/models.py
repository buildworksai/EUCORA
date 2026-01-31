# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
IAM Security models for E15 enhancement.

Implements identity provider configuration, sign-in event tracking, permission change monitoring,
anomaly detection, and security alerting.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class IdentityProvider(TimeStampedModel):
    """
    Configured identity provider.

    Supports Entra ID, Okta, ServiceNow, and on-premises Active Directory.
    """

    class ProviderType(models.TextChoices):
        ENTRA_ID = "entra_id", "Microsoft Entra ID"
        OKTA = "okta", "Okta"
        AD = "ad", "Active Directory"
        SERVICENOW = "servicenow", "ServiceNow IAM"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Display name for this provider")
    provider_type = models.CharField(max_length=50, choices=ProviderType.choices)
    tenant_id = models.CharField(max_length=255, null=True, blank=True, help_text="Tenant ID (for Entra ID)")
    connection_config = models.JSONField(default=dict, help_text="Connection configuration (credentials, endpoints)")
    sync_interval_minutes = models.IntegerField(default=15, help_text="Sync interval in minutes")
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Identity Provider"
        verbose_name_plural = "Identity Providers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider_type", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.provider_type})"


class SignInEvent(TimeStampedModel):
    """
    Captured sign-in event.

    High-volume table for tracking all sign-in attempts.
    """

    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILURE = "failure", "Failure"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE, related_name="sign_in_events")
    event_id = models.CharField(max_length=255, unique=True, help_text="Provider event ID")
    user_principal = models.CharField(max_length=255, db_index=True)
    user_display_name = models.CharField(max_length=255)
    app_display_name = models.CharField(max_length=255, null=True, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    location = models.JSONField(null=True, blank=True, help_text="Geographic location data")
    device_detail = models.JSONField(null=True, blank=True, help_text="Device information")
    status = models.CharField(max_length=20, choices=Status.choices)
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    risk_level = models.CharField(max_length=20, null=True, blank=True, help_text="Provider risk assessment")
    event_time = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Sign-In Event"
        verbose_name_plural = "Sign-In Events"
        ordering = ["-event_time"]
        indexes = [
            models.Index(fields=["provider", "event_time"]),
            models.Index(fields=["user_principal", "event_time"]),
            models.Index(fields=["status", "event_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_principal} - {self.status} ({self.event_time})"


class PermissionChange(TimeStampedModel):
    """
    Captured permission/role change.

    Tracks all permission modifications for audit trail.
    """

    class ChangeType(models.TextChoices):
        ADD = "add", "Add"
        REMOVE = "remove", "Remove"
        MODIFY = "modify", "Modify"

    class ResourceType(models.TextChoices):
        ROLE = "role", "Role"
        GROUP = "group", "Group"
        PERMISSION = "permission", "Permission"
        APP_ACCESS = "app_access", "Application Access"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE, related_name="permission_changes")
    event_id = models.CharField(max_length=255, unique=True, help_text="Provider event ID")
    actor_principal = models.CharField(max_length=255, db_index=True)
    target_principal = models.CharField(max_length=255, db_index=True)
    change_type = models.CharField(max_length=50, choices=ChangeType.choices)
    resource_type = models.CharField(max_length=50, choices=ResourceType.choices)
    resource_name = models.CharField(max_length=255)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    event_time = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Permission Change"
        verbose_name_plural = "Permission Changes"
        ordering = ["-event_time"]
        indexes = [
            models.Index(fields=["provider", "event_time"]),
            models.Index(fields=["target_principal", "event_time"]),
            models.Index(fields=["change_type", "resource_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.change_type} {self.resource_type} for {self.target_principal}"


class AnomalyDetection(TimeStampedModel, CorrelationIdModel):
    """
    Detected security anomaly.

    Tracks detected anomalies with correlation ID for audit trail.
    """

    class AnomalyType(models.TextChoices):
        SUSPICIOUS_LOGIN = "suspicious_login", "Suspicious Login"
        AUTHENTICATION_ATTACK = "authentication_attack", "Authentication Attack"
        UNUSUAL_ACTIVITY = "unusual_activity", "Unusual Activity"
        NEW_DEVICE = "new_device", "New Device"
        PRIVILEGE_CHANGE = "privilege_change", "Privilege Change"
        DORMANT_ACTIVATION = "dormant_activation", "Dormant Account Activation"
        SERVICE_ACCOUNT_ABUSE = "service_account_abuse", "Service Account Abuse"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        NEW = "new", "New"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        FALSE_POSITIVE = "false_positive", "False Positive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE, related_name="anomalies")
    anomaly_type = models.CharField(max_length=50, choices=AnomalyType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    user_principal = models.CharField(max_length=255, db_index=True)
    description = models.TextField(help_text="Anomaly description")
    evidence = models.JSONField(default=dict, help_text="Supporting evidence")
    related_events = models.JSONField(default=list, help_text="Related event IDs")
    detection_rule = models.CharField(max_length=255, help_text="Rule that triggered detection")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_anomalies",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Anomaly Detection"
        verbose_name_plural = "Anomaly Detections"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "severity", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["user_principal", "status"]),
            models.Index(fields=["anomaly_type", "severity"]),
        ]

    def __str__(self) -> str:
        return f"{self.anomaly_type} - {self.user_principal} ({self.severity})"


class DetectionRule(TimeStampedModel):
    """
    Anomaly detection rules.

    Configurable rules for detecting security anomalies.
    """

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Rule name")
    description = models.TextField(help_text="Rule description")
    anomaly_type = models.CharField(max_length=50, choices=AnomalyDetection.AnomalyType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    rule_config = models.JSONField(default=dict, help_text="Rule configuration")
    threshold_config = models.JSONField(default=dict, help_text="Threshold configuration")
    is_active = models.BooleanField(default=True, db_index=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Detection Rule"
        verbose_name_plural = "Detection Rules"
        ordering = ["anomaly_type", "name"]
        indexes = [
            models.Index(fields=["anomaly_type", "is_active"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.anomaly_type})"


class SecurityAlert(TimeStampedModel, CorrelationIdModel):
    """
    Security alert sent to stakeholders.

    Tracks all alerts sent with correlation ID for audit trail.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        TEAMS = "teams", "Microsoft Teams"
        SERVICENOW = "servicenow", "ServiceNow"

    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anomaly = models.ForeignKey(AnomalyDetection, on_delete=models.CASCADE, related_name="alerts")
    channel = models.CharField(max_length=50, choices=Channel.choices)
    recipients = models.JSONField(default=list, help_text="Alert recipients")
    subject = models.CharField(max_length=500)
    body = models.TextField(help_text="Alert body content")
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)

    class Meta:
        verbose_name = "Security Alert"
        verbose_name_plural = "Security Alerts"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["anomaly", "channel"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "sent_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel} alert for {self.anomaly.user_principal}"
