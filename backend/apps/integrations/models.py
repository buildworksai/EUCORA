# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Models for external system integrations.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class ExternalSystem(TimeStampedModel, CorrelationIdModel):
    """
    Base model for external system integrations.

    Stores configuration and status for integrations with:
    - Identity providers (Entra ID, Active Directory)
    - CMDB systems (ServiceNow, Jira Assets, Freshservice)
    - ITSM systems (ServiceNow, Jira Service Management, Freshservice)
    - MDM systems (Apple Business Manager, Android Enterprise)
    - Monitoring systems (Datadog, Splunk, Elastic)
    - Security scanners (Trivy, Grype, Snyk, Defender for Endpoint)
    """

    class SystemType(models.TextChoices):
        # Identity & Directory
        ENTRA_ID = "entra_id", "Microsoft Entra ID"
        ACTIVE_DIRECTORY = "active_directory", "Active Directory"

        # CMDB
        SERVICENOW_CMDB = "servicenow_cmdb", "ServiceNow CMDB"
        JIRA_ASSETS = "jira_assets", "Jira Assets"
        FRESHSERVICE_CMDB = "freshservice_cmdb", "Freshservice CMDB"

        # ITSM
        SERVICENOW_ITSM = "servicenow_itsm", "ServiceNow ITSM"
        JIRA_SERVICE_MANAGEMENT = "jira_service_management", "Jira Service Management"
        FRESHSERVICE_ITSM = "freshservice_itsm", "Freshservice ITSM"

        # MDM
        APPLE_BUSINESS_MANAGER = "apple_business_manager", "Apple Business Manager"
        ANDROID_ENTERPRISE = "android_enterprise", "Android Enterprise"

        # Monitoring
        DATADOG = "datadog", "Datadog"
        SPLUNK = "splunk", "Splunk"
        ELASTIC = "elastic", "Elastic (ELK Stack)"

        # Security & Vulnerability
        TRIVY = "trivy", "Trivy"
        GRYPE = "grype", "Grype"
        SNYK = "snyk", "Snyk"
        DEFENDER_FOR_ENDPOINT = "defender_for_endpoint", "Microsoft Defender for Endpoint"

    class AuthType(models.TextChoices):
        OAUTH2 = "oauth2", "OAuth 2.0"
        BASIC = "basic", "Basic Authentication"
        CERTIFICATE = "certificate", "Certificate-based"
        TOKEN = "token", "API Token"
        SERVER_TOKEN = "server_token", "Server Token (ABM)"

    name = models.CharField(max_length=255, help_text="Display name for this integration")
    type = models.CharField(max_length=50, choices=SystemType.choices, help_text="Type of external system")
    is_enabled = models.BooleanField(default=False, help_text="Whether this integration is active")
    api_url = models.URLField(help_text="Base URL for the external system API")
    auth_type = models.CharField(
        max_length=50, choices=AuthType.choices, default=AuthType.TOKEN, help_text="Authentication method"
    )
    credentials = models.JSONField(
        default=dict, help_text="Vault path reference for encrypted credentials (never store plaintext)"
    )
    sync_interval_minutes = models.IntegerField(
        default=60, help_text="How often to sync data from this system (in minutes)"
    )
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last successful sync")
    last_sync_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("partial", "Partial"),
            ("running", "Running"),
        ],
        help_text="Status of last sync operation",
    )
    metadata = models.JSONField(default=dict, help_text="System-specific configuration (field mappings, filters, etc.)")
    is_demo = models.BooleanField(default=False, help_text="Whether this is demo/test integration data")

    class Meta:
        db_table = "integrations_external_system"
        verbose_name = "External System Integration"
        verbose_name_plural = "External System Integrations"
        indexes = [
            models.Index(fields=["type", "is_enabled"]),
            models.Index(fields=["last_sync_at"]),
            models.Index(fields=["is_demo"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class IntegrationSyncLog(TimeStampedModel, CorrelationIdModel):
    """
    Audit log for integration sync operations.

    Tracks all sync operations for troubleshooting, compliance, and performance monitoring.
    """

    class SyncStatus(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"
        RUNNING = "running", "Running"
        CANCELLED = "cancelled", "Cancelled"

    system = models.ForeignKey(
        ExternalSystem, on_delete=models.CASCADE, related_name="sync_logs", help_text="External system that was synced"
    )
    sync_started_at = models.DateTimeField(help_text="When the sync operation started")
    sync_completed_at = models.DateTimeField(null=True, blank=True, help_text="When the sync operation completed")
    status = models.CharField(
        max_length=50,
        choices=SyncStatus.choices,
        default=SyncStatus.RUNNING,
        help_text="Final status of the sync operation",
    )
    records_fetched = models.IntegerField(default=0, help_text="Number of records fetched from external system")
    records_created = models.IntegerField(default=0, help_text="Number of new records created in local database")
    records_updated = models.IntegerField(default=0, help_text="Number of existing records updated in local database")
    records_failed = models.IntegerField(default=0, help_text="Number of records that failed to sync")
    error_message = models.TextField(blank=True, help_text="Error message if sync failed")
    error_details = models.JSONField(
        default=dict, help_text="Detailed error information (stack trace, API response, etc.)"
    )
    duration_seconds = models.FloatField(null=True, blank=True, help_text="Sync duration in seconds")

    class Meta:
        db_table = "integrations_sync_log"
        verbose_name = "Integration Sync Log"
        verbose_name_plural = "Integration Sync Logs"
        ordering = ["-sync_started_at"]
        indexes = [
            models.Index(fields=["system", "-sync_started_at"]),
            models.Index(fields=["status", "-sync_started_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.system.name} sync at {self.sync_started_at} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Calculate duration when sync completes."""
        if self.sync_completed_at and self.sync_started_at:
            delta = self.sync_completed_at - self.sync_started_at
            self.duration_seconds = delta.total_seconds()
        super().save(*args, **kwargs)
