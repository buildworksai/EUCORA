# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for Automation Advisor.
"""
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.automation_advisor.models import AutomationAnalysis, AutomationCandidate, TaskPattern


@pytest.fixture
def task_pattern():
    """Create a test task pattern."""
    return TaskPattern.objects.create(
        name="Test Pattern",
        pattern_type=TaskPattern.PatternType.REPETITIVE,
        source=TaskPattern.Source.SERVICENOW,
        occurrence_count=50,
        avg_duration_minutes=15.0,
        error_rate=0.1,
        last_detected=timezone.now(),
    )


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation."""

    def test_candidate_correlation_id_generated(self, task_pattern):
        """Verify correlation_id is auto-generated."""
        candidate = AutomationCandidate.objects.create(
            pattern=task_pattern,
            title="Test",
            description="Test",
            current_process="Test",
            proposed_automation="Test",
            frequency_score=80.0,
            time_impact_score=70.0,
            error_reduction_score=60.0,
            complexity_score=50.0,
            overall_score=65.0,
            annual_occurrences=100,
            time_saved_per_occurrence=0.5,
            estimated_annual_savings=Decimal("5000.00"),
            development_cost_estimate=Decimal("2000.00"),
            payback_period_months=4.8,
        )
        assert candidate.correlation_id is not None

    def test_analysis_correlation_id_generated(self):
        """Verify correlation_id is auto-generated."""
        analysis = AutomationAnalysis.objects.create(
            name="Test",
            date_range_start="2026-01-01",
            date_range_end="2026-01-31",
            sources_analyzed=[],
            status=AutomationAnalysis.Status.PENDING,
        )
        assert analysis.correlation_id is not None
