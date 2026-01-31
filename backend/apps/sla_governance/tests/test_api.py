# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SLA Governance Agent API endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.sla_governance.models import ServiceCatalogItem, SLADefinition

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(username="testuser", password="testpass")  # pragma: allowlist secret


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestServiceCatalogItemAPI:
    """Test ServiceCatalogItem API endpoints."""

    def test_list_services(self, authenticated_client):
        """Test listing service catalog items."""
        ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        response = authenticated_client.get("/api/sla-governance/services/")
        assert response.status_code == 200
        # DRF returns paginated response with 'results' key
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_create_service(self, authenticated_client):
        """Test creating a service catalog item."""
        data = {
            "name": "New Service",
            "description": "New service description",
            "category": "Application Services",
            "owner": "IT Operations",
            "status": "active",
        }
        response = authenticated_client.post("/api/sla-governance/services/", data, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "New Service"


@pytest.mark.django_db
class TestSLADefinitionAPI:
    """Test SLADefinition API endpoints."""

    def test_list_slas(self, authenticated_client, user):
        """Test listing SLA definitions."""
        service = ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        SLADefinition.objects.create(
            name="Test SLA",
            description="Test",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            created_by=user,
        )
        response = authenticated_client.get("/api/sla-governance/slas/")
        assert response.status_code == 200
        # DRF returns paginated response with 'results' key
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_correlation_id(self, authenticated_client, user):
        """Test filtering by correlation_id."""
        service = ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        sla = SLADefinition.objects.create(
            name="Test SLA",
            description="Test",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            created_by=user,
        )
        response = authenticated_client.get(f"/api/sla-governance/slas/?correlation_id={sla.correlation_id}")
        assert response.status_code == 200
        # DRF returns paginated response with 'results' key
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["id"] == str(sla.id)

    def test_approve_sla(self, authenticated_client, user):
        """Test approving an SLA."""
        service = ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        sla = SLADefinition.objects.create(
            name="Test SLA",
            description="Test",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            status=SLADefinition.Status.PENDING_APPROVAL,
            created_by=user,
        )
        response = authenticated_client.post(f"/api/sla-governance/slas/{sla.id}/approve/")
        assert response.status_code == 200
        sla.refresh_from_db()
        assert sla.status == "active"
        assert sla.approved_by == user
