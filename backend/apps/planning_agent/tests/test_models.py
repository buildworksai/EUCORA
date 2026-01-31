# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Planning Agent models.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.planning_agent.models import (
    BlastRadiusAnalysis,
    ChangeFreezePeriod,
    DeploymentPlan,
    DeploymentWindow,
    RingAssignment,
    RingDevice,
    RollbackPlan,
)

User = get_user_model()


@pytest.mark.django_db
class TestDeploymentPlan:
    """Test DeploymentPlan model."""

    def test_create_plan(self):
        """Test creating a deployment plan."""
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
            name="Test Deployment Plan",
            application=app,
            version="1.0.0",
            target_scope={"departments": ["Engineering"]},
            status=DeploymentPlan.Status.DRAFT,
            input_request="Deploy Test App to Engineering",
            reasoning="Test reasoning",
            overall_risk_score=42.0,
            risk_factors={},
            created_by=user,
        )
        assert plan.name == "Test Deployment Plan"
        assert plan.status == "draft"
        assert plan.correlation_id is not None


@pytest.mark.django_db
class TestRingAssignment:
    """Test RingAssignment model."""

    def test_create_ring(self):
        """Test creating a ring assignment."""
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
        ring = RingAssignment.objects.create(
            plan=plan,
            ring_number=1,
            ring_name="Ring 1 - IT Canary",
            device_count=10,
            device_criteria={"risk_tolerance": "moderate"},
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
            success_threshold=98.0,
        )
        assert ring.ring_number == 1
        assert ring.ring_name == "Ring 1 - IT Canary"


@pytest.mark.django_db
class TestRingDevice:
    """Test RingDevice model."""

    def test_create_device(self):
        """Test creating a ring device."""
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
        ring = RingAssignment.objects.create(
            plan=plan,
            ring_number=1,
            ring_name="Ring 1",
            device_count=1,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now(),
        )
        device = RingDevice.objects.create(
            ring=ring,
            device_id="DEVICE-001",
            device_name="Test Device",
            user_principal="user@example.com",
            selection_reason="IT staff device",
            health_score=95.0,
            criticality=RingDevice.Criticality.STANDARD,
        )
        assert device.device_id == "DEVICE-001"
        assert device.criticality == "standard"


@pytest.mark.django_db
class TestDeploymentWindow:
    """Test DeploymentWindow model."""

    def test_create_window(self):
        """Test creating a deployment window."""
        window = DeploymentWindow.objects.create(
            name="Business Hours",
            description="Monday-Friday 9am-5pm",
            day_of_week=[0, 1, 2, 3, 4],
            start_time="09:00:00",
            end_time="17:00:00",
            timezone="UTC",
        )
        assert window.name == "Business Hours"
        assert window.is_active is True


@pytest.mark.django_db
class TestChangeFreezePeriod:
    """Test ChangeFreezePeriod model."""

    def test_create_freeze(self):
        """Test creating a change freeze period."""
        freeze = ChangeFreezePeriod.objects.create(
            name="Holiday Freeze",
            reason="End of year freeze",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            scope={"departments": ["All"]},
        )
        assert freeze.name == "Holiday Freeze"
        assert freeze.is_active is True


@pytest.mark.django_db
class TestBlastRadiusAnalysis:
    """Test BlastRadiusAnalysis model."""

    def test_create_analysis(self):
        """Test creating a blast radius analysis."""
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
        analysis = BlastRadiusAnalysis.objects.create(
            plan=plan,
            total_users_affected=100,
            vip_users_affected=5,
            departments_affected=["Engineering"],
            regions_affected=["US-East"],
            critical_systems_affected=[],
            productivity_impact_score=25.0,
            recommendations=["Schedule during maintenance window"],
        )
        assert analysis.total_users_affected == 100
        assert analysis.correlation_id is not None


@pytest.mark.django_db
class TestRollbackPlan:
    """Test RollbackPlan model."""

    def test_create_rollback(self):
        """Test creating a rollback plan."""
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
        rollback = RollbackPlan.objects.create(
            deployment_plan=plan,
            trigger_conditions=["Success rate < 95%"],
            rollback_steps=[{"ring": "Ring 1", "action": "Rollback", "estimated_minutes": 10}],
            estimated_duration_minutes=30,
            requires_cab_approval=False,
        )
        assert rollback.deployment_plan == plan
        assert rollback.estimated_duration_minutes == 30
