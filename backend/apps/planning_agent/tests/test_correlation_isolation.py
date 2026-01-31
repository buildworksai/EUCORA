# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for correlation ID isolation in Planning Agent.

MANDATORY per EUCORA standards - ensures correlation IDs properly isolate
deployment events and audit trails.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.planning_agent.models import BlastRadiusAnalysis, DeploymentPlan

User = get_user_model()


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation."""

    def test_deployment_plans_have_unique_correlation_ids(self):
        """Test that each deployment plan has a unique correlation ID."""
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
        user = User.objects.create_user(username="testuser", password="testpass")

        plan1 = DeploymentPlan.objects.create(
            name="Plan 1",
            application=app,
            version="1.0.0",
            target_scope={},
            input_request="Test",
            reasoning="Test",
            overall_risk_score=50.0,
            risk_factors={},
            created_by=user,
        )
        plan2 = DeploymentPlan.objects.create(
            name="Plan 2",
            application=app,
            version="1.0.0",
            target_scope={},
            input_request="Test",
            reasoning="Test",
            overall_risk_score=50.0,
            risk_factors={},
            created_by=user,
        )

        assert plan1.correlation_id != plan2.correlation_id
        assert plan1.correlation_id is not None
        assert plan2.correlation_id is not None

    def test_blast_radius_analyses_have_unique_correlation_ids(self):
        """Test that blast radius analyses have unique correlation IDs."""
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
        user = User.objects.create_user(username="testuser", password="testpass")
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

        analysis1 = BlastRadiusAnalysis.objects.create(
            plan=plan,
            total_users_affected=100,
            vip_users_affected=5,
            departments_affected=[],
            regions_affected=[],
            critical_systems_affected=[],
            productivity_impact_score=25.0,
            recommendations=[],
        )
        analysis2 = BlastRadiusAnalysis.objects.create(
            plan=plan,
            total_users_affected=200,
            vip_users_affected=10,
            departments_affected=[],
            regions_affected=[],
            critical_systems_affected=[],
            productivity_impact_score=50.0,
            recommendations=[],
        )

        assert analysis1.correlation_id != analysis2.correlation_id
