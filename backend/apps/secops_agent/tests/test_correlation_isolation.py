# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for SecOps Agent (MANDATORY).
"""
import uuid

import pytest
from django.utils import timezone

from apps.secops_agent.models import ComplianceCheck, RemediationPlan, SecurityAlert, VulnerabilityInstance


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation for SecOps Agent models."""

    def test_vulnerability_instance_correlation_id_unique(self):
        """Test that VulnerabilityInstance has unique correlation_id."""
        from apps.secops_agent.models import Vulnerability, VulnerabilityScanner

        scanner = VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.HIGH,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )

        instance1 = VulnerabilityInstance.objects.create(
            vulnerability=vuln,
            asset_id="ASSET-001",
            asset_name="Asset 1",
            scanner=scanner,
            detected_at=timezone.now(),
        )

        # Verify correlation_id is set and unique
        assert instance1.correlation_id is not None

        # Create another instance - should have different correlation_id
        instance2 = VulnerabilityInstance.objects.create(
            vulnerability=vuln,
            asset_id="ASSET-002",
            asset_name="Asset 2",
            scanner=scanner,
            detected_at=timezone.now(),
        )

        assert instance1.correlation_id != instance2.correlation_id

    def test_remediation_plan_correlation_id_unique(self):
        """Test that RemediationPlan has unique correlation_id."""
        from apps.secops_agent.models import Vulnerability

        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.CRITICAL,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )

        plan1 = RemediationPlan.objects.create(
            name="Plan 1",
            vulnerability=vuln,
            remediation_type=RemediationPlan.RemediationType.PATCH,
            description="Test",
            steps=[],
        )

        plan2 = RemediationPlan.objects.create(
            name="Plan 2",
            vulnerability=vuln,
            remediation_type=RemediationPlan.RemediationType.CONFIG,
            description="Test",
            steps=[],
        )

        assert plan1.correlation_id != plan2.correlation_id

    def test_security_alert_correlation_id_unique(self):
        """Test that SecurityAlert has unique correlation_id."""
        from apps.secops_agent.models import SIEMConnection

        siem = SIEMConnection.objects.create(
            name="Test SIEM",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
        )

        alert1 = SecurityAlert.objects.create(
            siem=siem,
            alert_id="ALERT-001",
            title="Alert 1",
            severity=SecurityAlert.Severity.HIGH,
            description="Test",
            source="Test",
            alert_time=timezone.now(),
        )

        alert2 = SecurityAlert.objects.create(
            siem=siem,
            alert_id="ALERT-002",
            title="Alert 2",
            severity=SecurityAlert.Severity.MEDIUM,
            description="Test",
            source="Test",
            alert_time=timezone.now(),
        )

        assert alert1.correlation_id != alert2.correlation_id

    def test_compliance_check_correlation_id_unique(self):
        """Test that ComplianceCheck has unique correlation_id."""
        from apps.secops_agent.models import ComplianceBaseline

        baseline = ComplianceBaseline.objects.create(
            name="Test Baseline",
            framework=ComplianceBaseline.Framework.CIS,
            version="1.0",
            controls=[],
        )

        check1 = ComplianceCheck.objects.create(
            baseline=baseline,
            asset_id="ASSET-001",
            overall_score=85.0,
            passed_controls=17,
            failed_controls=3,
            control_results={},
        )

        check2 = ComplianceCheck.objects.create(
            baseline=baseline,
            asset_id="ASSET-002",
            overall_score=90.0,
            passed_controls=18,
            failed_controls=2,
            control_results={},
        )

        assert check1.correlation_id != check2.correlation_id

    def test_correlation_id_filtering(self):
        """Test filtering by correlation_id."""
        from apps.secops_agent.models import Vulnerability, VulnerabilityScanner

        scanner = VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.HIGH,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )

        instance = VulnerabilityInstance.objects.create(
            vulnerability=vuln,
            asset_id="ASSET-001",
            asset_name="Asset 1",
            scanner=scanner,
            detected_at=timezone.now(),
        )

        correlation_id = instance.correlation_id

        # Filter by correlation_id
        filtered = VulnerabilityInstance.objects.filter(correlation_id=correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == instance
