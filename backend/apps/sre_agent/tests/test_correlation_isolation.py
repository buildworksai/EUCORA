# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for SRE Agent (MANDATORY).
"""
import pytest

from apps.sre_agent.models import RunbookExecution, SelfHealingExecution


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation for SRE Agent models."""

    def test_self_healing_execution_correlation_id_unique(self):
        """Test that SelfHealingExecution has unique correlation_id."""
        from apps.sre_agent.models import SelfHealingRule

        rule = SelfHealingRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=SelfHealingRule.TriggerType.THRESHOLD,
            trigger_config={},
            target_type=SelfHealingRule.TargetType.SERVICE,
            target_config={},
            remediation_script="test",
        )

        execution1 = SelfHealingExecution.objects.create(
            rule=rule,
            trigger_event={"cpu": 90},
            status=SelfHealingExecution.Status.PENDING,
        )

        execution2 = SelfHealingExecution.objects.create(
            rule=rule,
            trigger_event={"cpu": 95},
            status=SelfHealingExecution.Status.PENDING,
        )

        assert execution1.correlation_id != execution2.correlation_id

    def test_runbook_execution_correlation_id_unique(self):
        """Test that RunbookExecution has unique correlation_id."""
        from apps.sre_agent.models import Runbook

        runbook = Runbook.objects.create(
            name="Test Runbook",
            description="Test",
            category="Test",
            steps=[],
            automation_level=Runbook.AutomationLevel.MANUAL,
            risk_level=Runbook.RiskLevel.R1,
            estimated_duration_minutes=10,
        )

        execution1 = RunbookExecution.objects.create(
            runbook=runbook,
            trigger_reason="Reason 1",
            status=RunbookExecution.Status.PENDING,
        )

        execution2 = RunbookExecution.objects.create(
            runbook=runbook,
            trigger_reason="Reason 2",
            status=RunbookExecution.Status.PENDING,
        )

        assert execution1.correlation_id != execution2.correlation_id

    def test_correlation_id_filtering(self):
        """Test filtering by correlation_id."""
        from apps.sre_agent.models import SelfHealingRule

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
            trigger_event={},
            status=SelfHealingExecution.Status.PENDING,
        )

        correlation_id = execution.correlation_id

        # Filter by correlation_id
        filtered = SelfHealingExecution.objects.filter(correlation_id=correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == execution
