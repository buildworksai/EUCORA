# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SLA Governance Agent models.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.sla_governance.models import (
    KPIDefinition,
    KPIMeasurement,
    ServiceCatalogItem,
    SLABreach,
    SLACompliance,
    SLADefinition,
    SLATarget,
    SLATemplate,
)

User = get_user_model()


@pytest.mark.django_db
class TestServiceCatalogItem:
    """Test ServiceCatalogItem model."""

    def test_create_service(self):
        """Test creating a service catalog item."""
        service = ServiceCatalogItem.objects.create(
            name="CRM Application",
            description="Customer Relationship Management",
            category="Application Services",
            owner="IT Operations",
            status="active",
        )
        assert service.name == "CRM Application"
        assert service.category == "Application Services"
        assert service.status == "active"


@pytest.mark.django_db
class TestSLADefinition:
    """Test SLADefinition model."""

    def test_create_sla(self):
        """Test creating an SLA definition."""
        service = ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        user = User.objects.create_user(username="testuser", password="testpass")
        sla = SLADefinition.objects.create(
            name="Test SLA",
            description="Test SLA description",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            status=SLADefinition.Status.DRAFT,
            created_by=user,
        )
        assert sla.name == "Test SLA"
        assert sla.status == "draft"
        assert sla.correlation_id is not None


@pytest.mark.django_db
class TestSLATarget:
    """Test SLATarget model."""

    def test_create_target(self):
        """Test creating an SLA target."""
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
        )
        target = SLATarget.objects.create(
            sla=sla,
            name="Availability Target",
            metric_type=SLATarget.MetricType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
            measurement_period="monthly",
        )
        assert target.metric_type == "availability"
        assert target.target_value == 99.9


@pytest.mark.django_db
class TestKPIDefinition:
    """Test KPIDefinition model."""

    def test_create_kpi(self):
        """Test creating a KPI definition."""
        kpi = KPIDefinition.objects.create(
            name="Uptime KPI",
            description="System uptime percentage",
            formula="(uptime / total_time) * 100",
            data_sources=["monitoring_system"],
            unit="percent",
            direction=KPIDefinition.Direction.HIGHER_BETTER,
            thresholds={"warning": 95, "critical": 90},
        )
        assert kpi.name == "Uptime KPI"
        assert kpi.direction == "higher_better"
        assert kpi.is_active is True


@pytest.mark.django_db
class TestKPIMeasurement:
    """Test KPIMeasurement model."""

    def test_create_measurement(self):
        """Test creating a KPI measurement."""
        kpi = KPIDefinition.objects.create(
            name="Test KPI",
            description="Test",
            formula="test",
            data_sources=[],
            unit="percent",
        )
        measurement = KPIMeasurement.objects.create(
            kpi=kpi,
            measurement_time=timezone.now(),
            value=99.5,
            status=KPIMeasurement.Status.GREEN,
        )
        assert measurement.value == 99.5
        assert measurement.status == "green"


@pytest.mark.django_db
class TestSLACompliance:
    """Test SLACompliance model."""

    def test_create_compliance(self):
        """Test creating an SLA compliance record."""
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
        )
        compliance = SLACompliance.objects.create(
            sla=sla,
            period_start=timezone.now().date(),
            period_end=timezone.now().date(),
            overall_compliance=99.5,
            target_compliances={},
            breach_count=0,
            near_miss_count=0,
            status=SLACompliance.Status.COMPLIANT,
        )
        assert compliance.overall_compliance == 99.5
        assert compliance.correlation_id is not None


@pytest.mark.django_db
class TestSLABreach:
    """Test SLABreach model."""

    def test_create_breach(self):
        """Test creating an SLA breach."""
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
        )
        target = SLATarget.objects.create(
            sla=sla,
            name="Test Target",
            metric_type=SLATarget.MetricType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
        )
        breach = SLABreach.objects.create(
            sla=sla,
            target=target,
            breach_time=timezone.now(),
            severity=SLABreach.Severity.HIGH,
            target_value=99.9,
            actual_value=98.5,
        )
        assert breach.severity == "high"
        assert breach.correlation_id is not None


@pytest.mark.django_db
class TestSLATemplate:
    """Test SLATemplate model."""

    def test_create_template(self):
        """Test creating an SLA template."""
        template = SLATemplate.objects.create(
            name="Standard Application SLA",
            description="Standard SLA template for applications",
            category="Application Services",
            default_targets=[
                {"metric_type": "availability", "target_value": 99.9, "target_unit": "percent"},
            ],
            variables={"service_name": "string", "uptime_target": "number"},
        )
        assert template.name == "Standard Application SLA"
        assert template.is_active is True
