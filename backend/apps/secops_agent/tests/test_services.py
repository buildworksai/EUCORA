# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for SecOps Agent.
"""
import pytest
from django.utils import timezone

from apps.secops_agent.models import ComplianceBaseline, RemediationPlan, Vulnerability, VulnerabilityScanner
from apps.secops_agent.services.compliance_checker import ComplianceChecker
from apps.secops_agent.services.remediation_service import RemediationService
from apps.secops_agent.services.vulnerability_scanner import MockVulnerabilityScannerClient


@pytest.mark.django_db
class TestVulnerabilityScannerService:
    """Test vulnerability scanner service."""

    def test_mock_scanner_sync(self):
        """Test mock scanner sync."""
        scanner = VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        client = MockVulnerabilityScannerClient(scanner)
        vulnerabilities = client.sync_vulnerabilities()
        assert len(vulnerabilities) == 2
        assert vulnerabilities[0]["cve_id"] == "CVE-2024-0001"

    def test_mock_scanner_test_connection(self):
        """Test mock scanner connection test."""
        scanner = VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        client = MockVulnerabilityScannerClient(scanner)
        assert client.test_connection() is True


@pytest.mark.django_db
class TestRemediationService:
    """Test remediation service."""

    def test_generate_patch_plan(self):
        """Test generating patch remediation plan."""
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.CRITICAL,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )
        scanner = VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        from apps.secops_agent.models import VulnerabilityInstance

        instance = VulnerabilityInstance.objects.create(
            vulnerability=vuln,
            asset_id="ASSET-001",
            asset_name="Asset 1",
            scanner=scanner,
            detected_at=timezone.now(),
        )

        service = RemediationService()
        plan_data = service.generate_plan(vuln, [instance], "patch")

        assert plan_data["remediation_type"] == "patch"
        assert plan_data["risk_level"] == "R3"
        assert len(plan_data["steps"]) == 4


@pytest.mark.django_db
class TestComplianceChecker:
    """Test compliance checker service."""

    def test_check_asset(self):
        """Test compliance check."""
        baseline = ComplianceBaseline.objects.create(
            name="CIS Windows 10",
            framework=ComplianceBaseline.Framework.CIS,
            version="1.0",
            controls=[
                {"id": "CIS-1", "name": "Control 1", "check": "test"},
                {"id": "CIS-2", "name": "Control 2", "check": "test"},
            ],
        )

        checker = ComplianceChecker(baseline)
        results = checker.check_asset("ASSET-001", {})

        assert results["asset_id"] == "ASSET-001"
        assert "overall_score" in results
        assert "passed_controls" in results
        assert "failed_controls" in results
