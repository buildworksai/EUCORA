# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SecOps Agent models for E17 enhancement.

Implements vulnerability management, SIEM integration, compliance monitoring,
and automated remediation workflows.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel


class VulnerabilityScanner(TimeStampedModel):
    """Configured vulnerability scanner."""

    class ScannerType(models.TextChoices):
        QUALYS = "qualys", "Qualys"
        NESSUS = "nessus", "Nessus"
        RAPID7 = "rapid7", "Rapid7"
        DEFENDER = "defender", "Microsoft Defender"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    scanner_type = models.CharField(max_length=50, choices=ScannerType.choices, db_index=True)
    connection_config = models.JSONField(default=dict, help_text="Scanner connection configuration")
    sync_schedule = models.CharField(max_length=50, default="0 */6 * * *", help_text="Cron expression")
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vulnerability Scanner"
        verbose_name_plural = "Vulnerability Scanners"
        indexes = [
            models.Index(fields=["scanner_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.scanner_type})"


class Vulnerability(TimeStampedModel):
    """Detected vulnerability (CVE)."""

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cve_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
    cvss_score = models.FloatField(null=True, blank=True)
    cvss_vector = models.CharField(max_length=100, null=True, blank=True)
    exploitability_score = models.FloatField(null=True, blank=True)
    published_date = models.DateField()
    modified_date = models.DateField()
    references = models.JSONField(default=list)
    affected_products = models.JSONField(default=list)

    class Meta:
        verbose_name = "Vulnerability"
        verbose_name_plural = "Vulnerabilities"
        ordering = ["-cvss_score", "-published_date"]
        indexes = [
            models.Index(fields=["severity", "cvss_score"]),
            models.Index(fields=["published_date"]),
        ]

    def __str__(self):
        return f"{self.cve_id} - {self.title}"


class VulnerabilityInstance(TimeStampedModel, CorrelationIdModel):
    """Vulnerability instance on a specific asset."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REMEDIATED = "remediated", "Remediated"
        ACCEPTED = "accepted", "Accepted Risk"
        FALSE_POSITIVE = "false_positive", "False Positive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vulnerability = models.ForeignKey(Vulnerability, on_delete=models.CASCADE, related_name="instances")
    asset_id = models.CharField(max_length=255, db_index=True)
    asset_name = models.CharField(max_length=255)
    application = models.ForeignKey(
        "application_portfolio.Application", null=True, blank=True, on_delete=models.SET_NULL
    )
    scanner = models.ForeignKey(VulnerabilityScanner, on_delete=models.CASCADE, related_name="instances")
    detected_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    remediation_due = models.DateField(null=True, blank=True)
    remediated_at = models.DateTimeField(null=True, blank=True)
    remediation_notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Vulnerability Instance"
        verbose_name_plural = "Vulnerability Instances"
        indexes = [
            models.Index(fields=["vulnerability", "status"]),
            models.Index(fields=["asset_id", "status"]),
            models.Index(fields=["status", "remediation_due"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.vulnerability.cve_id} on {self.asset_name}"


class RemediationPlan(TimeStampedModel, CorrelationIdModel):
    """Plan for remediating vulnerabilities."""

    class RemediationType(models.TextChoices):
        PATCH = "patch", "Patch"
        CONFIG = "config", "Configuration Change"
        COMPENSATING = "compensating", "Compensating Control"
        UPGRADE = "upgrade", "Upgrade"

    class RiskLevel(models.TextChoices):
        R1 = "R1", "R1 - Low (Auto-execute allowed)"
        R2 = "R2", "R2 - Medium (Policy-dependent approval)"
        R3 = "R3", "R3 - High (Mandatory human approval)"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        EXECUTING = "executing", "Executing"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    vulnerability = models.ForeignKey(Vulnerability, on_delete=models.CASCADE, related_name="remediation_plans")
    remediation_type = models.CharField(max_length=50, choices=RemediationType.choices)
    description = models.TextField()
    steps = models.JSONField(default=list)
    affected_instances = models.ManyToManyField(VulnerabilityInstance, related_name="remediation_plans")
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.R2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_remediation_plans",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Remediation Plan"
        verbose_name_plural = "Remediation Plans"
        indexes = [
            models.Index(fields=["status", "risk_level"]),
            models.Index(fields=["vulnerability", "status"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"


class SIEMConnection(TimeStampedModel):
    """SIEM platform connection."""

    class SIEMType(models.TextChoices):
        SENTINEL = "sentinel", "Microsoft Sentinel"
        SPLUNK = "splunk", "Splunk"
        QRADAR = "qradar", "IBM QRadar"
        ELASTIC = "elastic", "Elastic SIEM"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    siem_type = models.CharField(max_length=50, choices=SIEMType.choices, db_index=True)
    connection_config = models.JSONField(default=dict, help_text="SIEM connection configuration")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "SIEM Connection"
        verbose_name_plural = "SIEM Connections"
        indexes = [
            models.Index(fields=["siem_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.siem_type})"


class SecurityAlert(TimeStampedModel, CorrelationIdModel):
    """Security alert from SIEM."""

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        INFORMATIONAL = "informational", "Informational"

    class Status(models.TextChoices):
        NEW = "new", "New"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        FALSE_POSITIVE = "false_positive", "False Positive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siem = models.ForeignKey(SIEMConnection, on_delete=models.CASCADE, related_name="alerts")
    alert_id = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=500)
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
    description = models.TextField()
    source = models.CharField(max_length=255)
    affected_assets = models.JSONField(default=list)
    alert_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    related_vulnerabilities = models.ManyToManyField(Vulnerability, related_name="security_alerts", blank=True)
    remediation_plan = models.ForeignKey(
        RemediationPlan, null=True, blank=True, on_delete=models.SET_NULL, related_name="security_alerts"
    )

    class Meta:
        verbose_name = "Security Alert"
        verbose_name_plural = "Security Alerts"
        indexes = [
            models.Index(fields=["siem", "status"]),
            models.Index(fields=["severity", "status"]),
            models.Index(fields=["alert_time"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.alert_id} - {self.title}"


class ComplianceBaseline(TimeStampedModel):
    """Compliance baseline configuration."""

    class Framework(models.TextChoices):
        CIS = "cis", "CIS Benchmarks"
        NIST = "nist", "NIST CSF"
        SOC2 = "soc2", "SOC 2"
        ISO27001 = "iso27001", "ISO 27001"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    framework = models.CharField(max_length=50, choices=Framework.choices, db_index=True)
    version = models.CharField(max_length=50)
    controls = models.JSONField(default=list, help_text="List of compliance controls")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Compliance Baseline"
        verbose_name_plural = "Compliance Baselines"
        indexes = [
            models.Index(fields=["framework", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.framework} v{self.version})"


class ComplianceCheck(TimeStampedModel, CorrelationIdModel):
    """Compliance check result."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    baseline = models.ForeignKey(ComplianceBaseline, on_delete=models.CASCADE, related_name="checks")
    asset_id = models.CharField(max_length=255, db_index=True)
    check_time = models.DateTimeField(default=timezone.now)
    overall_score = models.FloatField(help_text="Compliance score 0-100")
    passed_controls = models.IntegerField(default=0)
    failed_controls = models.IntegerField(default=0)
    control_results = models.JSONField(default=dict, help_text="Detailed control check results")

    class Meta:
        verbose_name = "Compliance Check"
        verbose_name_plural = "Compliance Checks"
        indexes = [
            models.Index(fields=["baseline", "check_time"]),
            models.Index(fields=["asset_id", "check_time"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.baseline.name} - {self.asset_id} ({self.overall_score}%)"
