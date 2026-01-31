# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for SecOps Agent API.
"""
from rest_framework import serializers

from .models import (
    ComplianceBaseline,
    ComplianceCheck,
    RemediationPlan,
    SecurityAlert,
    SIEMConnection,
    Vulnerability,
    VulnerabilityInstance,
    VulnerabilityScanner,
)


class VulnerabilityScannerSerializer(serializers.ModelSerializer):
    """Serializer for vulnerability scanners."""

    class Meta:
        model = VulnerabilityScanner
        fields = [
            "id",
            "name",
            "scanner_type",
            "connection_config",
            "sync_schedule",
            "last_sync",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_sync"]


class VulnerabilitySerializer(serializers.ModelSerializer):
    """Serializer for vulnerabilities."""

    instance_count = serializers.SerializerMethodField()

    class Meta:
        model = Vulnerability
        fields = [
            "id",
            "cve_id",
            "title",
            "description",
            "severity",
            "cvss_score",
            "cvss_vector",
            "exploitability_score",
            "published_date",
            "modified_date",
            "references",
            "affected_products",
            "instance_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_instance_count(self, obj: Vulnerability) -> int:
        """Get count of vulnerability instances."""
        return obj.instances.count()


class VulnerabilityInstanceSerializer(serializers.ModelSerializer):
    """Serializer for vulnerability instances."""

    vulnerability_cve = serializers.CharField(source="vulnerability.cve_id", read_only=True)
    vulnerability_title = serializers.CharField(source="vulnerability.title", read_only=True)
    vulnerability_severity = serializers.CharField(source="vulnerability.severity", read_only=True)
    scanner_name = serializers.CharField(source="scanner.name", read_only=True)

    class Meta:
        model = VulnerabilityInstance
        fields = [
            "id",
            "correlation_id",
            "vulnerability",
            "vulnerability_cve",
            "vulnerability_title",
            "vulnerability_severity",
            "asset_id",
            "asset_name",
            "application",
            "scanner",
            "scanner_name",
            "detected_at",
            "status",
            "remediation_due",
            "remediated_at",
            "remediation_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class RemediationPlanSerializer(serializers.ModelSerializer):
    """Serializer for remediation plans."""

    vulnerability_cve = serializers.CharField(source="vulnerability.cve_id", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True)
    affected_instance_count = serializers.SerializerMethodField()

    class Meta:
        model = RemediationPlan
        fields = [
            "id",
            "correlation_id",
            "name",
            "vulnerability",
            "vulnerability_cve",
            "remediation_type",
            "description",
            "steps",
            "affected_instances",
            "risk_level",
            "status",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "executed_at",
            "completed_at",
            "affected_instance_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "created_at",
            "updated_at",
            "approved_at",
            "executed_at",
            "completed_at",
        ]

    def get_affected_instance_count(self, obj: RemediationPlan) -> int:
        """Get count of affected instances."""
        return obj.affected_instances.count()


class SIEMConnectionSerializer(serializers.ModelSerializer):
    """Serializer for SIEM connections."""

    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = SIEMConnection
        fields = [
            "id",
            "name",
            "siem_type",
            "connection_config",
            "is_active",
            "alert_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_alert_count(self, obj: SIEMConnection) -> int:
        """Get count of alerts."""
        return obj.alerts.count()


class SecurityAlertSerializer(serializers.ModelSerializer):
    """Serializer for security alerts."""

    siem_name = serializers.CharField(source="siem.name", read_only=True)
    related_vulnerability_count = serializers.SerializerMethodField()

    class Meta:
        model = SecurityAlert
        fields = [
            "id",
            "correlation_id",
            "siem",
            "siem_name",
            "alert_id",
            "title",
            "severity",
            "description",
            "source",
            "affected_assets",
            "alert_time",
            "status",
            "related_vulnerabilities",
            "remediation_plan",
            "related_vulnerability_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]

    def get_related_vulnerability_count(self, obj: SecurityAlert) -> int:
        """Get count of related vulnerabilities."""
        return obj.related_vulnerabilities.count()


class ComplianceBaselineSerializer(serializers.ModelSerializer):
    """Serializer for compliance baselines."""

    control_count = serializers.SerializerMethodField()
    check_count = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceBaseline
        fields = [
            "id",
            "name",
            "framework",
            "version",
            "controls",
            "is_active",
            "control_count",
            "check_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_control_count(self, obj: ComplianceBaseline) -> int:
        """Get count of controls."""
        return len(obj.controls) if isinstance(obj.controls, list) else 0

    def get_check_count(self, obj: ComplianceBaseline) -> int:
        """Get count of compliance checks."""
        return obj.checks.count()


class ComplianceCheckSerializer(serializers.ModelSerializer):
    """Serializer for compliance checks."""

    baseline_name = serializers.CharField(source="baseline.name", read_only=True)
    framework = serializers.CharField(source="baseline.framework", read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = [
            "id",
            "correlation_id",
            "baseline",
            "baseline_name",
            "framework",
            "asset_id",
            "check_time",
            "overall_score",
            "passed_controls",
            "failed_controls",
            "control_results",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]
