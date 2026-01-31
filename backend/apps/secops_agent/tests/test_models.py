# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SecOps Agent models.
"""
import pytest
from django.utils import timezone

from apps.secops_agent.models import (
    ComplianceBaseline,
    ComplianceCheck,
    RemediationPlan,
    SecurityAlert,
    SIEMConnection,
    Vulnerability,
    VulnerabilityInstance,
    VulnerabilityScanner,
)


@pytest.mark.django_db
class TestVulnerabilityScanner:
    """Test VulnerabilityScanner model."""

    def test_create_scanner(self):
        """Test creating a vulnerability scanner."""
        scanner = VulnerabilityScanner.objects.create(
            name="Test Qualys Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
            connection_config={"url": "https://qualys.example.com"},
        )
        assert scanner.name == "Test Qualys Scanner"
        assert scanner.scanner_type == "qualys"
        assert scanner.is_active is True


@pytest.mark.django_db
class TestVulnerability:
    """Test Vulnerability model."""

    def test_create_vulnerability(self):
        """Test creating a vulnerability."""
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            severity=Vulnerability.Severity.CRITICAL,
            cvss_score=9.8,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )
        assert vuln.cve_id == "CVE-2024-0001"
        assert vuln.severity == "critical"
        assert vuln.cvss_score == 9.8


@pytest.mark.django_db
class TestVulnerabilityInstance:
    """Test VulnerabilityInstance model."""

    def test_create_instance(self):
        """Test creating a vulnerability instance."""
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
            asset_name="Test Asset",
            scanner=scanner,
            detected_at=timezone.now(),
        )
        assert instance.asset_id == "ASSET-001"
        assert instance.status == VulnerabilityInstance.Status.OPEN
        assert instance.correlation_id is not None


@pytest.mark.django_db
class TestRemediationPlan:
    """Test RemediationPlan model."""

    def test_create_plan(self):
        """Test creating a remediation plan."""
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.CRITICAL,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )
        plan = RemediationPlan.objects.create(
            name="Test Plan",
            vulnerability=vuln,
            remediation_type=RemediationPlan.RemediationType.PATCH,
            description="Test description",
            steps=[],
            risk_level=RemediationPlan.RiskLevel.R3,
        )
        assert plan.name == "Test Plan"
        assert plan.status == RemediationPlan.Status.DRAFT
        assert plan.correlation_id is not None


@pytest.mark.django_db
class TestSIEMConnection:
    """Test SIEMConnection model."""

    def test_create_siem(self):
        """Test creating a SIEM connection."""
        siem = SIEMConnection.objects.create(
            name="Test Sentinel",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
            connection_config={"workspace_id": "test"},
        )
        assert siem.name == "Test Sentinel"
        assert siem.siem_type == "sentinel"
        assert siem.is_active is True


@pytest.mark.django_db
class TestSecurityAlert:
    """Test SecurityAlert model."""

    def test_create_alert(self):
        """Test creating a security alert."""
        siem = SIEMConnection.objects.create(
            name="Test SIEM",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
        )
        alert = SecurityAlert.objects.create(
            siem=siem,
            alert_id="ALERT-001",
            title="Test Alert",
            severity=SecurityAlert.Severity.HIGH,
            description="Test description",
            source="Test Source",
            alert_time=timezone.now(),
        )
        assert alert.alert_id == "ALERT-001"
        assert alert.status == SecurityAlert.Status.NEW
        assert alert.correlation_id is not None


@pytest.mark.django_db
class TestComplianceBaseline:
    """Test ComplianceBaseline model."""

    def test_create_baseline(self):
        """Test creating a compliance baseline."""
        baseline = ComplianceBaseline.objects.create(
            name="CIS Windows 10",
            framework=ComplianceBaseline.Framework.CIS,
            version="1.0",
            controls=[{"id": "CIS-1", "name": "Test Control"}],
        )
        assert baseline.name == "CIS Windows 10"
        assert baseline.framework == "cis"
        assert baseline.is_active is True


@pytest.mark.django_db
class TestComplianceCheck:
    """Test ComplianceCheck model."""

    def test_create_check(self):
        """Test creating a compliance check."""
        baseline = ComplianceBaseline.objects.create(
            name="Test Baseline",
            framework=ComplianceBaseline.Framework.CIS,
            version="1.0",
            controls=[],
        )
        check = ComplianceCheck.objects.create(
            baseline=baseline,
            asset_id="ASSET-001",
            overall_score=85.5,
            passed_controls=17,
            failed_controls=3,
            control_results={},
        )
        assert check.asset_id == "ASSET-001"
        assert check.overall_score == 85.5
        assert check.correlation_id is not None
