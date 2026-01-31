# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Automation Advisor.
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
class TestTaskPattern:
    """Test TaskPattern model."""

    def test_create_pattern(self):
        """Test pattern creation."""
        pattern = TaskPattern.objects.create(
            name="Test Pattern",
            pattern_type=TaskPattern.PatternType.MANUAL,
            source=TaskPattern.Source.EUCORA,
            occurrence_count=20,
            avg_duration_minutes=30.0,
            error_rate=0.2,
            last_detected=timezone.now(),
        )
        assert pattern.name == "Test Pattern"
        assert pattern.pattern_type == TaskPattern.PatternType.MANUAL
        assert pattern.is_active is True


@pytest.mark.django_db
class TestAutomationCandidate:
    """Test AutomationCandidate model."""

    def test_create_candidate(self, task_pattern):
        """Test candidate creation."""
        candidate = AutomationCandidate.objects.create(
            pattern=task_pattern,
            title="Test Automation",
            description="Test description",
            current_process="Manual process",
            proposed_automation="Automated process",
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
        assert candidate.pattern == task_pattern
        assert candidate.overall_score == 65.0
        assert candidate.correlation_id is not None
        assert candidate.status == AutomationCandidate.Status.IDENTIFIED


@pytest.mark.django_db
class TestAutomationAnalysis:
    """Test AutomationAnalysis model."""

    def test_create_analysis(self):
        """Test analysis creation."""
        analysis = AutomationAnalysis.objects.create(
            name="Test Analysis",
            date_range_start="2026-01-01",
            date_range_end="2026-01-31",
            sources_analyzed=["servicenow"],
            status=AutomationAnalysis.Status.PENDING,
        )
        assert analysis.name == "Test Analysis"
        assert analysis.correlation_id is not None
        assert analysis.status == AutomationAnalysis.Status.PENDING
