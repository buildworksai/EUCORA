# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SLA Governance Agent services.
"""
import pytest
from django.utils import timezone

from apps.sla_governance.models import KPIDefinition, KPIMeasurement, SLADefinition, SLATarget
from apps.sla_governance.services.breach_detector import BreachDetector
from apps.sla_governance.services.compliance_calculator import ComplianceCalculator


@pytest.mark.django_db
class TestComplianceCalculator:
    """Test ComplianceCalculator service."""

    def test_calculate_compliance(self):
        """Test calculating SLA compliance."""
        from apps.sla_governance.models import ServiceCatalogItem

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
        )
        kpi = KPIDefinition.objects.create(
            name="Uptime KPI",
            description="Test",
            formula="test",
            data_sources=[],
            unit="percent",
        )
        from apps.sla_governance.models import SLAKPILink

        SLAKPILink.objects.create(sla_target=target, kpi=kpi, weight=1.0)

        # Create measurements
        KPIMeasurement.objects.create(
            kpi=kpi,
            measurement_time=timezone.now(),
            value=99.5,
            status=KPIMeasurement.Status.GREEN,
        )

        calculator = ComplianceCalculator()
        period_start = timezone.now().date()
        period_end = period_start

        compliance = calculator.calculate_compliance(sla, period_start, period_end)
        assert compliance is not None
        assert compliance.sla == sla


@pytest.mark.django_db
class TestBreachDetector:
    """Test BreachDetector service."""

    def test_detect_breach(self):
        """Test detecting an SLA breach."""
        from apps.sla_governance.models import ServiceCatalogItem

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
        )
        kpi = KPIDefinition.objects.create(
            name="Uptime KPI",
            description="Test",
            formula="test",
            data_sources=[],
            unit="percent",
        )
        measurement = KPIMeasurement.objects.create(
            kpi=kpi,
            measurement_time=timezone.now(),
            value=98.5,  # Below target
            status=KPIMeasurement.Status.RED,
        )

        detector = BreachDetector()
        breach = detector.detect_breaches(target, measurement)
        assert breach is not None
        assert breach.sla == sla
        assert breach.target == target
