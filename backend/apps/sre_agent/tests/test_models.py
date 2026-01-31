# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SRE Agent models.
"""
import pytest
from django.utils import timezone

from apps.sre_agent.models import (
    HealthCheckResult,
    HealthEndpoint,
    MonitoringPlatform,
    Runbook,
    RunbookExecution,
    SelfHealingExecution,
    SelfHealingRule,
    SLODefinition,
    SLOMetric,
)


@pytest.mark.django_db
class TestMonitoringPlatform:
    """Test MonitoringPlatform model."""

    def test_create_platform(self):
        """Test creating a monitoring platform."""
        platform = MonitoringPlatform.objects.create(
            name="Test Prometheus",
            platform_type=MonitoringPlatform.PlatformType.PROMETHEUS,
            connection_config={"url": "https://prometheus.example.com"},
        )
        assert platform.name == "Test Prometheus"
        assert platform.platform_type == "prometheus"
        assert platform.is_active is True


@pytest.mark.django_db
class TestHealthEndpoint:
    """Test HealthEndpoint model."""

    def test_create_endpoint(self):
        """Test creating a health endpoint."""
        endpoint = HealthEndpoint.objects.create(
            name="Test API Health",
            url="https://api.example.com/health",
            method="GET",
            expected_status=200,
            timeout_seconds=30,
            check_interval_minutes=5,
        )
        assert endpoint.name == "Test API Health"
        assert endpoint.url == "https://api.example.com/health"
        assert endpoint.is_active is True


@pytest.mark.django_db
class TestHealthCheckResult:
    """Test HealthCheckResult model."""

    def test_create_result(self):
        """Test creating a health check result."""
        endpoint = HealthEndpoint.objects.create(
            name="Test Endpoint",
            url="https://example.com/health",
        )
        result = HealthCheckResult.objects.create(
            endpoint=endpoint,
            status=HealthCheckResult.Status.HEALTHY,
            response_time_ms=100,
            status_code=200,
        )
        assert result.status == "healthy"
        assert result.response_time_ms == 100


@pytest.mark.django_db
class TestSLODefinition:
    """Test SLODefinition model."""

    def test_create_slo(self):
        """Test creating an SLO definition."""
        slo = SLODefinition.objects.create(
            name="API Availability",
            service_name="api-service",
            slo_type=SLODefinition.SLOType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
            measurement_window=SLODefinition.MeasurementWindow.DAILY,
        )
        assert slo.name == "API Availability"
        assert slo.target_value == 99.9
        assert slo.is_active is True


@pytest.mark.django_db
class TestSLOMetric:
    """Test SLOMetric model."""

    def test_create_metric(self):
        """Test creating an SLO metric."""
        slo = SLODefinition.objects.create(
            name="Test SLO",
            service_name="test-service",
            slo_type=SLODefinition.SLOType.AVAILABILITY,
            target_value=99.9,
            target_unit="percent",
            measurement_window=SLODefinition.MeasurementWindow.DAILY,
        )
        metric = SLOMetric.objects.create(
            slo=slo,
            actual_value=99.95,
            target_met=True,
        )
        assert metric.actual_value == 99.95
        assert metric.target_met is True


@pytest.mark.django_db
class TestSelfHealingRule:
    """Test SelfHealingRule model."""

    def test_create_rule(self):
        """Test creating a self-healing rule."""
        rule = SelfHealingRule.objects.create(
            name="Restart Service on High CPU",
            description="Restart service when CPU exceeds 90%",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={"metric": "cpu", "threshold": 90},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={"service_name": "test-service"},
            remediation_script="Restart-Service test-service",
            script_type=SelfHealingRule.ScriptType.POWERSHELL,
            risk_level=SelfHealingRule.RiskLevel.R2,
        )
        assert rule.name == "Restart Service on High CPU"
        assert rule.trigger_type == "threshold"
        assert rule.is_active is True


@pytest.mark.django_db
class TestSelfHealingExecution:
    """Test SelfHealingExecution model."""

    def test_create_execution(self):
        """Test creating a self-healing execution."""
        rule = SelfHealingRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test",
        )
        execution = SelfHealingExecution.objects.create(
            rule=rule,
            trigger_event={"cpu": 95},
            status=SelfHealingExecution.Status.PENDING,
        )
        assert execution.rule == rule
        assert execution.status == "pending"
        assert execution.correlation_id is not None


@pytest.mark.django_db
class TestRunbook:
    """Test Runbook model."""

    def test_create_runbook(self):
        """Test creating a runbook."""
        runbook = Runbook.objects.create(
            name="Service Restart Runbook",
            description="Step-by-step service restart procedure",
            category="Operations",
            steps=[
                {"step": 1, "action": "Stop service"},
                {"step": 2, "action": "Verify stopped"},
                {"step": 3, "action": "Start service"},
            ],
            automation_level=Runbook.AutomationLevel.SEMI_AUTO,
            risk_level=Runbook.RiskLevel.R2,
            estimated_duration_minutes=15,
        )
        assert runbook.name == "Service Restart Runbook"
        assert runbook.category == "Operations"
        assert runbook.is_active is True


@pytest.mark.django_db
class TestRunbookExecution:
    """Test RunbookExecution model."""

    def test_create_execution(self):
        """Test creating a runbook execution."""
        runbook = Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="Test",
            steps=[],
            automation_level=Runbook.AutomationLevel.MANUAL,
            risk_level=Runbook.RiskLevel.R1,
            estimated_duration_minutes=10,
        )
        execution = RunbookExecution.objects.create(
            runbook=runbook,
            trigger_reason="Service failure detected",
            status=RunbookExecution.Status.PENDING,
        )
        assert execution.runbook == runbook
        assert execution.status == "pending"
        assert execution.correlation_id is not None
