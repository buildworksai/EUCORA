# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for policy_engine views.
"""
import pytest
from django.urls import reverse

from apps.policy_engine.models import RiskModel


@pytest.mark.django_db
class TestPolicyEngineViews:
    """Test policy engine view endpoints."""

    def setup_method(self):
        """Set up test risk model."""
        self.risk_model = RiskModel.objects.create(
            version="v1.0",
            factors=[
                {"name": "Privilege Elevation", "weight": 0.5},
                {"name": "Blast Radius", "weight": 0.5},
            ],
            threshold=50,
            is_active=True,
        )

    def test_assess_risk(self, authenticated_client):
        """Test risk assessment endpoint."""
        import uuid

        url = reverse("policy_engine:assess-risk")
        response = authenticated_client.post(
            url,
            {
                "evidence_pack": {
                    "requires_admin": False,
                    "target_ring": "lab",
                    "artifact_hash": "abc123",
                    "sbom_data": {"packages": []},
                    "vulnerability_scan_results": {},
                    "rollback_plan": "Test plan",
                },
                "correlation_id": str(uuid.uuid4()),
            },
            format="json",
        )

        assert response.status_code == 200
        assert "risk_score" in response.data
        assert "factor_scores" in response.data
        assert "requires_cab_approval" in response.data

    def test_assess_risk_missing_evidence_pack(self, authenticated_client):
        """Test risk assessment without evidence pack."""
        url = reverse("policy_engine:assess-risk")
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == 400
        assert "error" in response.data

    def test_get_active_risk_model(self, authenticated_client, authenticated_user):
        """Test getting active risk model."""
        # Make user admin
        authenticated_user.is_staff = True
        authenticated_user.save()

        url = reverse("policy_engine:risk-model")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data["version"] == "v1.0"
        assert "factors" in response.data

    def test_get_risk_model_no_active(self, authenticated_client, authenticated_user):
        """Test getting risk model when none active."""
        # Make user admin
        authenticated_user.is_staff = True
        authenticated_user.save()

        # Deactivate all risk models
        RiskModel.objects.all().update(is_active=False)

        url = reverse("policy_engine:risk-model")
        response = authenticated_client.get(url)

        assert response.status_code == 404
