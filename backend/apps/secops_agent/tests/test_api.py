# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for SecOps Agent.
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.secops_agent.models import RemediationPlan, Vulnerability, VulnerabilityScanner


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, django_user_model):
    """Create authenticated API client."""
    user = django_user_model.objects.create_user(username="testuser", password="testpass")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestVulnerabilityScannerAPI:
    """Test VulnerabilityScanner API endpoints."""

    def test_list_scanners(self, authenticated_client):
        """Test listing scanners."""
        VulnerabilityScanner.objects.create(
            name="Test Scanner",
            scanner_type=VulnerabilityScanner.ScannerType.QUALYS,
        )
        response = authenticated_client.get("/api/secops/scanners/")
        assert response.status_code == 200
        # Handle paginated response
        if isinstance(response.data, dict) and "results" in response.data:
            assert len(response.data["results"]) == 1
        else:
            assert len(response.data) == 1

    def test_create_scanner(self, authenticated_client):
        """Test creating a scanner."""
        data = {
            "name": "New Scanner",
            "scanner_type": "qualys",
            "connection_config": {"url": "https://example.com"},
        }
        response = authenticated_client.post("/api/secops/scanners/", data, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "New Scanner"


@pytest.mark.django_db
class TestVulnerabilityAPI:
    """Test Vulnerability API endpoints."""

    def test_list_vulnerabilities(self, authenticated_client):
        """Test listing vulnerabilities."""
        Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.CRITICAL,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )
        response = authenticated_client.get("/api/secops/vulnerabilities/")
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestRemediationPlanAPI:
    """Test RemediationPlan API endpoints."""

    def test_list_plans(self, authenticated_client):
        """Test listing remediation plans."""
        vuln = Vulnerability.objects.create(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            severity=Vulnerability.Severity.CRITICAL,
            published_date=timezone.now().date(),
            modified_date=timezone.now().date(),
        )
        RemediationPlan.objects.create(
            name="Test Plan",
            vulnerability=vuln,
            remediation_type=RemediationPlan.RemediationType.PATCH,
            description="Test",
            steps=[],
        )
        response = authenticated_client.get("/api/secops/remediation-plans/")
        assert response.status_code == 200
        assert len(response.data) >= 1
