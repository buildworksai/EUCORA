# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Request Coordination Agent.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.request_coordination.models import (
    CommunicationTemplate,
    EscalationEvent,
    EscalationRule,
    RequestCommunication,
    RequestStakeholder,
    RequestStatusUpdate,
    TrackedRequest,
)


@pytest.fixture
def tracked_request():
    """Create a test tracked request."""
    return TrackedRequest.objects.create(
        servicenow_number="REQ001234",
        servicenow_sys_id="abc123",
        request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
        short_description="Install Test Application",
        requestor_email="user@example.com",
        requestor_name="Test User",
        status=TrackedRequest.Status.IN_PROGRESS,
        priority=TrackedRequest.Priority.MEDIUM,
        sla_due=timezone.now() + timedelta(hours=4),
    )


@pytest.mark.django_db
class TestTrackedRequest:
    """Test TrackedRequest model."""

    def test_create_request(self):
        """Test request creation."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001234",
            servicenow_sys_id="abc123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Install Test Application",
            requestor_email="user@example.com",
            requestor_name="Test User",
            status=TrackedRequest.Status.NEW,
            priority=TrackedRequest.Priority.MEDIUM,
        )
        assert request.servicenow_number == "REQ001234"
        assert request.status == TrackedRequest.Status.NEW
        assert request.correlation_id is not None

    def test_request_str(self, tracked_request):
        """Test request string representation."""
        assert "REQ001234" in str(tracked_request)
        assert "Install Test Application" in str(tracked_request)


@pytest.mark.django_db
class TestRequestStakeholder:
    """Test RequestStakeholder model."""

    def test_create_stakeholder(self, tracked_request):
        """Test stakeholder creation."""
        stakeholder = RequestStakeholder.objects.create(
            request=tracked_request,
            email="stakeholder@example.com",
            name="Stakeholder User",
            role=RequestStakeholder.Role.WATCHER,
        )
        assert stakeholder.request == tracked_request
        assert stakeholder.role == RequestStakeholder.Role.WATCHER
        assert stakeholder.email == "stakeholder@example.com"

    def test_stakeholder_str(self, tracked_request):
        """Test stakeholder string representation."""
        stakeholder = RequestStakeholder.objects.create(
            request=tracked_request,
            email="stakeholder@example.com",
            name="Stakeholder User",
            role=RequestStakeholder.Role.WATCHER,
        )
        assert "Stakeholder User" in str(stakeholder)
        assert "REQ001234" in str(stakeholder)


@pytest.mark.django_db
class TestRequestStatusUpdate:
    """Test RequestStatusUpdate model."""

    def test_create_status_update(self, tracked_request):
        """Test status update creation."""
        update = RequestStatusUpdate.objects.create(
            request=tracked_request,
            old_status=TrackedRequest.Status.NEW,
            new_status=TrackedRequest.Status.IN_PROGRESS,
            updated_by="system",
        )
        assert update.request == tracked_request
        assert update.old_status == TrackedRequest.Status.NEW
        assert update.new_status == TrackedRequest.Status.IN_PROGRESS


@pytest.mark.django_db
class TestRequestCommunication:
    """Test RequestCommunication model."""

    def test_create_communication(self, tracked_request):
        """Test communication creation."""
        communication = RequestCommunication.objects.create(
            request=tracked_request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            channel=RequestCommunication.Channel.EMAIL,
            recipients=["user@example.com"],
            subject="Request Update",
            body="Your request has been updated.",
        )
        assert communication.request == tracked_request
        assert communication.correlation_id is not None
        assert communication.status == RequestCommunication.Status.PENDING


@pytest.mark.django_db
class TestEscalationRule:
    """Test EscalationRule model."""

    def test_create_escalation_rule(self):
        """Test escalation rule creation."""
        rule = EscalationRule.objects.create(
            name="SLA Warning - 4 Hours",
            description="Warn when SLA is approaching",
            trigger_type=EscalationRule.TriggerType.SLA_WARNING,
            trigger_config={"hours_before_breach": 4},
            escalation_actions=[{"type": "notify", "recipients": ["manager"]}],
        )
        assert rule.name == "SLA Warning - 4 Hours"
        assert rule.is_active is True


@pytest.mark.django_db
class TestEscalationEvent:
    """Test EscalationEvent model."""

    def test_create_escalation_event(self, tracked_request):
        """Test escalation event creation."""
        rule = EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[],
        )
        event = EscalationEvent.objects.create(
            request=tracked_request,
            rule=rule,
            trigger_reason="SLA breached",
            escalation_level=1,
            actions_taken=[],
        )
        assert event.request == tracked_request
        assert event.correlation_id is not None
        assert event.escalation_level == 1


@pytest.mark.django_db
class TestCommunicationTemplate:
    """Test CommunicationTemplate model."""

    def test_create_template(self):
        """Test template creation."""
        template = CommunicationTemplate.objects.create(
            name="SLA Warning Template",
            communication_type=CommunicationTemplate.CommunicationType.SLA_WARNING,
            channel=CommunicationTemplate.Channel.EMAIL,
            subject_template="SLA Warning: ${request_number}",
            body_template="Request ${request_number} is approaching SLA deadline.",
            variables=["request_number", "sla_due"],
        )
        assert template.name == "SLA Warning Template"
        assert template.is_active is True
