# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Planning Agent API endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.planning_agent.models import DeploymentPlan

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestDeploymentPlanAPI:
    """Test DeploymentPlan API endpoints."""

    def test_list_plans(self, authenticated_client, user):
        """Test listing deployment plans."""
        from apps.application_portfolio.models import Application, Publisher

        publisher = Publisher.objects.create(
            name="Test Publisher",
            identifier="com.test.publisher",
        )
        app = Application.objects.create(
            name="Test App",
            identifier="com.test.app",
            publisher=publisher,
        )
        DeploymentPlan.objects.create(
            name="Test Plan",
            application=app,
            version="1.0.0",
            target_scope={},
            input_request="Test",
            reasoning="Test",
            overall_risk_score=50.0,
            risk_factors={},
            created_by=user,
        )
        response = authenticated_client.get("/api/planning/plans/")
        assert response.status_code == 200
        # DRF returns paginated response with 'results' key
        results = response.data.get("results", response.data)
        assert len(results) == 1

    def test_filter_by_correlation_id(self, authenticated_client, user):
        """Test filtering by correlation_id."""
        from apps.application_portfolio.models import Application, Publisher

        publisher = Publisher.objects.create(
            name="Test Publisher",
            identifier="com.test.publisher",
        )
        app = Application.objects.create(
            name="Test App",
            identifier="com.test.app",
            publisher=publisher,
        )
        plan = DeploymentPlan.objects.create(
            name="Test Plan",
            application=app,
            version="1.0.0",
            target_scope={},
            input_request="Test",
            reasoning="Test",
            overall_risk_score=50.0,
            risk_factors={},
            created_by=user,
        )
        response = authenticated_client.get(f"/api/planning/plans/?correlation_id={plan.correlation_id}")
        assert response.status_code == 200
        # DRF returns paginated response with 'results' key
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["id"] == str(plan.id)

    def test_approve_plan(self, authenticated_client, user):
        """Test approving a deployment plan."""
        from apps.application_portfolio.models import Application, Publisher

        publisher = Publisher.objects.create(
            name="Test Publisher",
            identifier="com.test.publisher",
        )
        app = Application.objects.create(
            name="Test App",
            identifier="com.test.app",
            publisher=publisher,
        )
        plan = DeploymentPlan.objects.create(
            name="Test Plan",
            application=app,
            version="1.0.0",
            target_scope={},
            input_request="Test",
            reasoning="Test",
            overall_risk_score=50.0,
            risk_factors={},
            status=DeploymentPlan.Status.PENDING_APPROVAL,
            created_by=user,
        )
        response = authenticated_client.post(f"/api/planning/plans/{plan.id}/approve/")
        assert response.status_code == 200
        plan.refresh_from_db()
        assert plan.status == "approved"
        assert plan.approved_by == user
