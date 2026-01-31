# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for Request Coordination Agent.

Ensures correlation IDs are properly generated and can be used for filtering.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.request_coordination.models import EscalationEvent, RequestCommunication, TrackedRequest


@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Test correlation ID generation and isolation."""

    def test_request_correlation_id_generated(self):
        """Test that TrackedRequest generates correlation_id."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request",
            requestor_email="user@example.com",
            requestor_name="Test User",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        assert request.correlation_id is not None
        assert str(request.correlation_id) != ""

    def test_request_correlation_id_unique(self):
        """Test that correlation IDs are unique."""
        request1 = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request 1",
            requestor_email="user1@example.com",
            requestor_name="Test User 1",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        request2 = TrackedRequest.objects.create(
            servicenow_number="REQ005678",
            servicenow_sys_id="def456",
            request_type=TrackedRequest.RequestType.ACCESS_REQUEST,
            short_description="Test Request 2",
            requestor_email="user2@example.com",
            requestor_name="Test User 2",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        assert request1.correlation_id != request2.correlation_id

    def test_communication_correlation_id_generated(self):
        """Test that RequestCommunication generates correlation_id."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request",
            requestor_email="user@example.com",
            requestor_name="Test User",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        communication = RequestCommunication.objects.create(
            request=request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            channel=RequestCommunication.Channel.EMAIL,
            recipients=["user@example.com"],
            subject="Test",
            body="Test body",
        )
        assert communication.correlation_id is not None
        assert str(communication.correlation_id) != ""

    def test_escalation_correlation_id_generated(self):
        """Test that EscalationEvent generates correlation_id."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request",
            requestor_email="user@example.com",
            requestor_name="Test User",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        event = EscalationEvent.objects.create(
            request=request,
            trigger_reason="SLA breached",
            escalation_level=1,
            actions_taken=[],
        )
        assert event.correlation_id is not None
        assert str(event.correlation_id) != ""

    def test_correlation_id_filtering(self):
        """Test filtering by correlation_id."""
        request1 = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request 1",
            requestor_email="user1@example.com",
            requestor_name="Test User 1",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        request2 = TrackedRequest.objects.create(
            servicenow_number="REQ005678",
            servicenow_sys_id="def456",
            request_type=TrackedRequest.RequestType.ACCESS_REQUEST,
            short_description="Test Request 2",
            requestor_email="user2@example.com",
            requestor_name="Test User 2",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )

        # Filter by correlation_id
        filtered = TrackedRequest.objects.filter(correlation_id=request1.correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == request1

        # Verify isolation
        assert TrackedRequest.objects.filter(correlation_id=request2.correlation_id).count() == 1
