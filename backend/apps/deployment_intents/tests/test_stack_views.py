# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for stack API endpoints (E6).
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.deployment_intents.models import DeploymentIntent, RingDeployment

User = get_user_model()


@pytest.mark.django_db
class TestStackApplications:
    """Test stack applications endpoint."""

    def setup_method(self):
        """Set up test data."""
        from apps.core.utils import get_demo_mode_enabled

        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        demo_mode = get_demo_mode_enabled()

        self.deployment1 = DeploymentIntent.objects.create(
            app_name="Test App",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.LAB,
            status=DeploymentIntent.Status.COMPLETED,
            evidence_pack_id="123e4567-e89b-12d3-a456-426614174000",
            submitter=self.user,
            is_demo=demo_mode,
        )
        self.deployment2 = DeploymentIntent.objects.create(
            app_name="Test App",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.CANARY,
            status=DeploymentIntent.Status.DEPLOYING,
            evidence_pack_id="123e4567-e89b-12d3-a456-426614174001",
            submitter=self.user,
            is_demo=demo_mode,
        )
        RingDeployment.objects.create(
            deployment_intent=self.deployment1,
            ring=DeploymentIntent.Ring.LAB,
            connector_type="intune",
            success_rate=0.98,
            success_count=98,
            failure_count=2,
            is_demo=demo_mode,
        )

    def test_stack_applications(self, authenticated_client):
        """Test getting stack applications."""
        url = "/api/v1/deployments/stack/applications/"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "applications" in response.data
        # There may be demo data, so check that our test app is present
        app_names = [app["name"] for app in response.data["applications"]]
        assert "Test App" in app_names

        # Find our test app
        test_app = next((app for app in response.data["applications"] if app["name"] == "Test App"), None)
        assert test_app is not None
        assert len(test_app["versions"]) >= 1
        # Check that our deployments are in the response
        test_version = next((v for v in test_app["versions"] if v["version"] == "1.0.0"), None)
        assert test_version is not None
        assert len(test_version["deployments"]) >= 2

    def test_stack_applications_filter_by_app(self, authenticated_client):
        """Test filtering by application name."""
        from apps.core.utils import get_demo_mode_enabled

        demo_mode = get_demo_mode_enabled()
        DeploymentIntent.objects.create(
            app_name="Other App",
            version="2.0.0",
            target_ring=DeploymentIntent.Ring.LAB,
            status=DeploymentIntent.Status.COMPLETED,
            evidence_pack_id="123e4567-e89b-12d3-a456-426614174002",
            submitter=self.user,
            is_demo=demo_mode,
        )

        url = "/api/v1/deployments/stack/applications/?app_name=Test"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should include Test App (may include others with "Test" in name)
        app_names = [app["name"] for app in response.data["applications"]]
        assert "Test App" in app_names


@pytest.mark.django_db
class TestStackEvents:
    """Test stack events endpoint."""

    def setup_method(self):
        """Set up test data."""
        from apps.core.utils import get_demo_mode_enabled

        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        demo_mode = get_demo_mode_enabled()
        DeploymentIntent.objects.create(
            app_name="Test App",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.LAB,
            status=DeploymentIntent.Status.COMPLETED,
            evidence_pack_id="123e4567-e89b-12d3-a456-426614174000",
            submitter=self.user,
            is_demo=demo_mode,
        )

    def test_stack_events(self, authenticated_client):
        """Test getting stack events."""
        url = "/api/v1/deployments/stack/events/"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "events" in response.data
        assert len(response.data["events"]) >= 1
        event = response.data["events"][0]
        assert "id" in event
        assert "type" in event
        assert "title" in event
        assert "timestamp" in event


@pytest.mark.django_db
class TestDeploymentActions:
    """Test deployment action endpoints."""

    def setup_method(self):
        """Set up test data."""
        from apps.core.utils import get_demo_mode_enabled

        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        demo_mode = get_demo_mode_enabled()
        self.deployment = DeploymentIntent.objects.create(
            app_name="Test App",
            version="1.0.0",
            target_ring=DeploymentIntent.Ring.CANARY,
            status=DeploymentIntent.Status.DEPLOYING,
            evidence_pack_id="123e4567-e89b-12d3-a456-426614174000",
            submitter=self.user,
            is_demo=demo_mode,
        )

    def test_promote_deployment(self, authenticated_client):
        """Test promoting deployment to next ring."""
        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/promote/"
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["new_ring"] == "PILOT"
        self.deployment.refresh_from_db()
        assert self.deployment.target_ring == "PILOT"

    def test_promote_deployment_max_ring(self, authenticated_client):
        """Test promoting deployment at max ring."""
        self.deployment.target_ring = DeploymentIntent.Ring.GLOBAL
        self.deployment.save()

        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/promote/"
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pause_deployment(self, authenticated_client):
        """Test pausing a deployment."""
        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/pause/"
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.deployment.refresh_from_db()
        assert self.deployment.status == DeploymentIntent.Status.REJECTED  # Using REJECTED as PAUSED doesn't exist

    def test_resume_deployment(self, authenticated_client):
        """Test resuming a paused deployment."""
        self.deployment.status = DeploymentIntent.Status.REJECTED
        self.deployment.save()

        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/resume/"
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.deployment.refresh_from_db()
        assert self.deployment.status == DeploymentIntent.Status.DEPLOYING

    def test_rollback_deployment(self, authenticated_client):
        """Test rolling back a deployment."""
        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/rollback/"
        data = {"reason": "Test rollback"}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        self.deployment.refresh_from_db()
        assert self.deployment.status == DeploymentIntent.Status.ROLLED_BACK

    def test_cancel_deployment(self, authenticated_client):
        """Test cancelling a deployment."""
        url = f"/api/v1/deployments/stack/deployments/{self.deployment.correlation_id}/cancel/"
        data = {"reason": "Test cancellation"}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.deployment.refresh_from_db()
        assert self.deployment.status == DeploymentIntent.Status.REJECTED  # Using REJECTED as CANCELLED doesn't exist
