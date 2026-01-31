# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for KB & Triage Agent (MANDATORY).
"""
import pytest
from django.utils import timezone

from apps.kb_triage.models import IncidentPattern, TriageRequest


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID isolation for KB & Triage Agent models."""

    def test_triage_request_correlation_id_unique(self):
        """Test that TriageRequest has unique correlation_id."""
        request1 = TriageRequest.objects.create(
            caller_name="User 1",
            short_description="Issue 1",
            description="Description 1",
        )

        request2 = TriageRequest.objects.create(
            caller_name="User 2",
            short_description="Issue 2",
            description="Description 2",
        )

        assert request1.correlation_id != request2.correlation_id

    def test_incident_pattern_correlation_id_unique(self):
        """Test that IncidentPattern has unique correlation_id."""
        pattern1 = IncidentPattern.objects.create(
            name="Pattern 1",
            pattern_type=IncidentPattern.PatternType.RECURRING,
            description="Description 1",
            category="Category 1",
            occurrence_count=5,
            affected_users=3,
        )

        pattern2 = IncidentPattern.objects.create(
            name="Pattern 2",
            pattern_type=IncidentPattern.PatternType.TRENDING,
            description="Description 2",
            category="Category 2",
            occurrence_count=10,
            affected_users=8,
        )

        assert pattern1.correlation_id != pattern2.correlation_id

    def test_correlation_id_filtering(self):
        """Test filtering by correlation_id."""
        request = TriageRequest.objects.create(
            caller_name="Test User",
            short_description="Test",
            description="Test",
        )

        correlation_id = request.correlation_id

        # Filter by correlation_id
        filtered = TriageRequest.objects.filter(correlation_id=correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == request
