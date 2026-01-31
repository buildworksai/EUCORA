# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Planning Agent services.
"""
import pytest
from django.utils import timezone

from apps.planning_agent.models import DeploymentPlan
from apps.planning_agent.services.blast_radius import BlastRadiusCalculator
from apps.planning_agent.services.rollback_generator import RollbackPlanGenerator


@pytest.mark.django_db
class TestBlastRadiusCalculator:
    """Test BlastRadiusCalculator service."""

    def test_calculate_blast_radius(self):
        """Test calculating blast radius."""
        from django.contrib.auth import get_user_model

        from apps.application_portfolio.models import Application, Publisher
        from apps.planning_agent.models import RingAssignment, RingDevice

        User = get_user_model()
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
        ring = RingAssignment.objects.create(
            plan=plan,
            ring_number=1,
            ring_name="Ring 1",
            device_count=2,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
        )
        RingDevice.objects.create(
            ring=ring,
            device_id="DEVICE-001",
            device_name="Device 1",
            user_principal="user1@example.com",
            selection_reason="Test",
            criticality=RingDevice.Criticality.STANDARD,
        )
        RingDevice.objects.create(
            ring=ring,
            device_id="DEVICE-002",
            device_name="Device 2",
            user_principal="user2@example.com",
            selection_reason="Test",
            criticality=RingDevice.Criticality.VIP,
        )

        calculator = BlastRadiusCalculator()
        analysis = calculator.calculate_blast_radius(plan)
        assert analysis is not None
        assert analysis.plan == plan
        assert analysis.total_users_affected >= 0


@pytest.mark.django_db
class TestRollbackPlanGenerator:
    """Test RollbackPlanGenerator service."""

    def test_generate_rollback_plan(self):
        """Test generating a rollback plan."""
        from django.contrib.auth import get_user_model

        from apps.application_portfolio.models import Application, Publisher
        from apps.planning_agent.models import RingAssignment

        User = get_user_model()
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
        RingAssignment.objects.create(
            plan=plan,
            ring_number=1,
            ring_name="Ring 1",
            device_count=10,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
        )

        generator = RollbackPlanGenerator()
        rollback = generator.generate_rollback_plan(plan)
        assert rollback is not None
        assert rollback.deployment_plan == plan
        assert len(rollback.rollback_steps) > 0
