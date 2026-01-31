# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for correlation ID isolation in SLA Governance Agent.

MANDATORY per EUCORA standards - ensures correlation IDs properly isolate
deployment events and audit trails.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.sla_governance.models import SLABreach, SLACompliance, SLADefinition

User = get_user_model()


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation."""

    def test_sla_definitions_have_unique_correlation_ids(self):
        """Test that each SLA definition has a unique correlation ID."""
        from apps.sla_governance.models import ServiceCatalogItem

        service = ServiceCatalogItem.objects.create(
            name="Test Service",
            description="Test",
            category="Test",
            owner="Test",
        )
        user = User.objects.create_user(username="testuser", password="testpass")

        sla1 = SLADefinition.objects.create(
            name="SLA 1",
            description="Test",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            created_by=user,
        )
        sla2 = SLADefinition.objects.create(
            name="SLA 2",
            description="Test",
            service=service,
            version="1.0",
            effective_from=timezone.now().date(),
            created_by=user,
        )

        assert sla1.correlation_id != sla2.correlation_id
        assert sla1.correlation_id is not None
        assert sla2.correlation_id is not None

    def test_compliance_records_have_unique_correlation_ids(self):
        """Test that compliance records have unique correlation IDs."""
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

        compliance1 = SLACompliance.objects.create(
            sla=sla,
            period_start=timezone.now().date(),
            period_end=timezone.now().date(),
            overall_compliance=99.5,
            target_compliances={},
            breach_count=0,
            near_miss_count=0,
            status=SLACompliance.Status.COMPLIANT,
        )
        compliance2 = SLACompliance.objects.create(
            sla=sla,
            period_start=timezone.now().date(),
            period_end=timezone.now().date(),
            overall_compliance=98.5,
            target_compliances={},
            breach_count=0,
            near_miss_count=0,
            status=SLACompliance.Status.COMPLIANT,
        )

        assert compliance1.correlation_id != compliance2.correlation_id

    def test_breaches_have_unique_correlation_ids(self):
        """Test that breaches have unique correlation IDs."""
        from apps.sla_governance.models import ServiceCatalogItem, SLATarget

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

        breach1 = SLABreach.objects.create(
            sla=sla,
            target=target,
            breach_time=timezone.now(),
            severity=SLABreach.Severity.HIGH,
            target_value=99.9,
            actual_value=98.5,
        )
        breach2 = SLABreach.objects.create(
            sla=sla,
            target=target,
            breach_time=timezone.now(),
            severity=SLABreach.Severity.MEDIUM,
            target_value=99.9,
            actual_value=99.0,
        )

        assert breach1.correlation_id != breach2.correlation_id
