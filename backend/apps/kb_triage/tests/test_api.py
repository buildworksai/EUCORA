# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for KB & Triage Agent.
"""
import pytest
from rest_framework.test import APIClient

from apps.kb_triage.models import KnowledgeSource, TriageRequest


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
class TestKnowledgeSourceAPI:
    """Test KnowledgeSource API endpoints."""

    def test_list_sources(self, authenticated_client):
        """Test listing knowledge sources."""
        KnowledgeSource.objects.create(
            name="Test Source",
            source_type=KnowledgeSource.SourceType.CUSTOM,
        )
        response = authenticated_client.get("/api/kb-triage/sources/")
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestTriageRequestAPI:
    """Test TriageRequest API endpoints."""

    def test_list_requests(self, authenticated_client):
        """Test listing triage requests."""
        TriageRequest.objects.create(
            caller_name="Test User",
            short_description="Test issue",
            description="Test description",
        )
        response = authenticated_client.get("/api/kb-triage/triage/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_request(self, authenticated_client):
        """Test creating a triage request."""
        data = {
            "caller_name": "John Doe",
            "short_description": "Outlook not syncing",
            "description": "User reports Outlook emails not syncing",
        }
        response = authenticated_client.post("/api/kb-triage/triage/", data, format="json")
        assert response.status_code == 201
        assert response.data["caller_name"] == "John Doe"
