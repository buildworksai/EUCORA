# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for deployment_intents views.
"""
import uuid

import pytest

from apps.deployment_intents.models import DeploymentIntent
from apps.policy_engine.models import RiskModel


@pytest.mark.django_db
class TestDeploymentIntentsViews:
    """Test deployment intents view endpoints."""

    def test_get_deployment(self, authenticated_client, sample_deployment_intent):
        """Test retrieving a deployment intent."""
        url = f"/api/v1/deployments/{sample_deployment_intent.correlation_id}/"
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == sample_deployment_intent.app_name
        assert data["version"] == sample_deployment_intent.version
        assert data["correlation_id"] == str(sample_deployment_intent.correlation_id)

    def test_create_deployment_missing_fields(self, authenticated_client):
        """Test creating deployment with missing required fields."""
        url = "/api/v1/deployments/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data

    def test_list_deployments(self, authenticated_client, authenticated_user):
        """Test listing deployment intents."""
        # Create test deployment
        DeploymentIntent.objects.create(
            app_name="TestApp",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )

        url = "/api/v1/deployments/list"
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "deployments" in response.data
        assert len(response.data["deployments"]) > 0

    def test_list_deployments_with_filters(self, authenticated_client, authenticated_user):
        """Test listing deployments with status filter."""
        DeploymentIntent.objects.create(
            app_name="TestApp",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.APPROVED,
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )

        url = "/api/v1/deployments/list"
        response = authenticated_client.get(url, {"status": "APPROVED"})

        assert response.status_code == 200
        assert len(response.data["deployments"]) > 0

    def test_get_deployment_not_found(self, authenticated_client):
        """Test getting non-existent deployment."""
        url = f"/api/v1/deployments/{uuid.uuid4()}/"
