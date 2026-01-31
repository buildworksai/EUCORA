# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Request Coordination Agent.
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.cmdb_integration.models import CMDBConnection
from apps.request_coordination.models import (
    CommunicationTemplate,
    EscalationEvent,
    EscalationRule,
    RequestCommunication,
    RequestStakeholder,
    RequestStatusUpdate,
    TrackedRequest,
)
from apps.request_coordination.services.escalation_engine import EscalationEngine
from apps.request_coordination.services.notification_service import RequestNotificationService
from apps.request_coordination.services.servicenow_client import MockServiceNowRequestClient
from apps.request_coordination.services.sla_tracker import SLATracker
from apps.request_coordination.services.sync_service import RequestSyncService


@pytest.fixture
def tracked_request(db):
    """Create test tracked request."""
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


@pytest.fixture
def cmdb_connection(db):
    """Create test CMDB connection."""
    return CMDBConnection.objects.create(
        name="Test ServiceNow",
        instance_url="https://test.service-now.com",
        auth_type="basic",
        credentials={"username": "test", "password": "test"},
    )


class TestSLATracker:
    """Tests for SLATracker service."""

    def test_check_sla_status_ok(self, db):
        """Test SLA status check - OK."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() + timedelta(hours=10),  # Well beyond warning threshold
        )
        tracker = SLATracker(warning_hours=4)
        status, needs_action = tracker.check_sla_status(request)
        assert status == "ok"
        assert needs_action is False

    def test_check_sla_status_warning(self, db):
        """Test SLA status check - Warning."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() + timedelta(hours=2),  # Within warning threshold
        )
        tracker = SLATracker(warning_hours=4)
        status, needs_action = tracker.check_sla_status(request)
        assert status == "warning"
        assert needs_action is True

    def test_check_sla_status_breached(self, db):
        """Test SLA status check - Breached."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() - timedelta(hours=1),  # Past due
        )
        tracker = SLATracker(warning_hours=4)
        status, needs_action = tracker.check_sla_status(request)
        assert status == "breached"
        assert needs_action is True

    def test_check_sla_status_blocked(self, tracked_request):
        """Test SLA status check - Blocked."""
        tracked_request.blocked_reason = "Awaiting approval"
        tracked_request.save()
        tracker = SLATracker()
        status, needs_action = tracker.check_sla_status(tracked_request)
        assert status == "blocked"
        assert needs_action is True

    def test_check_sla_status_no_sla(self, db):
        """Test SLA status check - No SLA."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ003",
            servicenow_sys_id="sys3",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=None,
        )
        tracker = SLATracker()
        status, needs_action = tracker.check_sla_status(request)
        assert status == "ok"
        assert needs_action is False

    def test_get_requests_at_risk(self, db):
        """Test getting requests at risk."""
        # Create requests with different SLA statuses
        TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 1",
            requestor_email="user@example.com",
            requestor_name="User",
            status=TrackedRequest.Status.IN_PROGRESS,
            sla_due=timezone.now() + timedelta(hours=2),  # At risk
        )
        TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 2",
            requestor_email="user@example.com",
            requestor_name="User",
            status=TrackedRequest.Status.IN_PROGRESS,
            sla_due=timezone.now() + timedelta(hours=10),  # Not at risk
        )

        tracker = SLATracker(warning_hours=4)
        at_risk = tracker.get_requests_at_risk()
        assert len(at_risk) == 1
        assert at_risk[0].servicenow_number == "REQ001"

    def test_get_blocked_requests(self, db):
        """Test getting blocked requests."""
        threshold = timezone.now() - timedelta(days=3)
        TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 1",
            requestor_email="user@example.com",
            requestor_name="User",
            status=TrackedRequest.Status.PENDING,
            blocked_reason="Awaiting approval",
            last_updated=threshold,
        )
        TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 2",
            requestor_email="user@example.com",
            requestor_name="User",
            status=TrackedRequest.Status.PENDING,
            blocked_reason="Awaiting approval",
            last_updated=timezone.now(),  # Recently updated
        )

        tracker = SLATracker()
        blocked = tracker.get_blocked_requests(blocked_days=2)
        assert len(blocked) == 1
        assert blocked[0].servicenow_number == "REQ001"


class TestEscalationEngine:
    """Tests for EscalationEngine service."""

    def test_evaluate_sla_warning_rule(self, db):
        """Test evaluating SLA warning rule."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() + timedelta(hours=2),  # Within warning threshold
        )
        rule = EscalationRule.objects.create(
            name="SLA Warning Rule",
            description="Warn when SLA is approaching",
            trigger_type=EscalationRule.TriggerType.SLA_WARNING,
            trigger_config={"hours_before_breach": 4},
            escalation_actions=[],
        )

        engine = EscalationEngine()
        matching_rules = engine.evaluate_rules(request)
        assert len(matching_rules) == 1
        assert matching_rules[0].id == rule.id

    def test_evaluate_sla_breach_rule(self, db):
        """Test evaluating SLA breach rule."""
        request = TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() - timedelta(hours=1),  # Breached
        )
        rule = EscalationRule.objects.create(
            name="SLA Breach Rule",
            description="Escalate when SLA breached",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[],
        )

        engine = EscalationEngine()
        matching_rules = engine.evaluate_rules(request)
        assert len(matching_rules) == 1
        assert matching_rules[0].id == rule.id

    def test_evaluate_blocked_rule(self, db):
        """Test evaluating blocked rule."""
        threshold = timezone.now() - timedelta(days=3)
        request = TrackedRequest.objects.create(
            servicenow_number="REQ003",
            servicenow_sys_id="sys3",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test",
            requestor_email="user@example.com",
            requestor_name="User",
            blocked_reason="Awaiting approval",
            last_updated=threshold,
        )
        rule = EscalationRule.objects.create(
            name="Blocked Rule",
            description="Escalate when blocked too long",
            trigger_type=EscalationRule.TriggerType.BLOCKED,
            trigger_config={"blocked_days": 2},
            escalation_actions=[],
        )

        engine = EscalationEngine()
        matching_rules = engine.evaluate_rules(request)
        assert len(matching_rules) == 1
        assert matching_rules[0].id == rule.id

    def test_trigger_escalation(self, tracked_request):
        """Test triggering an escalation."""
        rule = EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[
                {"type": "notify", "recipients": ["manager"]},
                {"type": "update_priority", "new_priority": TrackedRequest.Priority.HIGH},
            ],
        )

        engine = EscalationEngine()
        event = engine.trigger_escalation(tracked_request, rule, "SLA breached")

        assert event is not None
        assert event.request == tracked_request
        assert event.rule == rule
        assert event.escalation_level == 1
        assert len(event.actions_taken) == 2

        tracked_request.refresh_from_db()
        assert tracked_request.is_escalated is True
        assert tracked_request.escalation_level == 1
        assert tracked_request.priority == TrackedRequest.Priority.HIGH

    def test_execute_notify_action(self, tracked_request):
        """Test executing notify action."""
        engine = EscalationEngine()
        action = {"type": "notify", "recipients": ["manager@example.com"]}
        result = engine._execute_action(tracked_request, action)
        assert result["type"] == "notify"
        assert result["status"] == "queued"

    def test_execute_update_priority_action(self, tracked_request):
        """Test executing update_priority action."""
        engine = EscalationEngine()
        action = {"type": "update_priority", "new_priority": TrackedRequest.Priority.CRITICAL}
        result = engine._execute_action(tracked_request, action)
        assert result["type"] == "update_priority"
        assert result["status"] == "completed"
        tracked_request.refresh_from_db()
        assert tracked_request.priority == TrackedRequest.Priority.CRITICAL

    def test_execute_escalate_action(self, tracked_request):
        """Test executing escalate action."""
        engine = EscalationEngine()
        action = {"type": "escalate", "level": 2}
        result = engine._execute_action(tracked_request, action)
        assert result["type"] == "escalate"
        assert result["status"] == "completed"
        tracked_request.refresh_from_db()
        assert tracked_request.escalation_level == 2
        assert tracked_request.is_escalated is True


class TestRequestNotificationService:
    """Tests for RequestNotificationService."""

    @patch("apps.request_coordination.services.notification_service.send_mail")
    def test_send_email_notification(self, mock_send_mail, tracked_request):
        """Test sending email notification."""
        service = RequestNotificationService()
        communication = service.send_notification(
            request=tracked_request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            recipients=["user@example.com"],
        )

        assert communication is not None
        assert communication.channel == RequestCommunication.Channel.EMAIL
        assert communication.status == RequestCommunication.Status.SENT
        mock_send_mail.assert_called_once()

    def test_render_template(self, tracked_request):
        """Test template rendering."""
        service = RequestNotificationService()
        template = "Request ${request_number} - ${short_description}"
        context = {
            "request_number": tracked_request.servicenow_number,
            "short_description": tracked_request.short_description,
        }
        result = service._render_template(template, context)
        assert tracked_request.servicenow_number in result
        assert tracked_request.short_description in result

    @patch("apps.request_coordination.services.notification_service.send_mail")
    def test_send_status_update(self, mock_send_mail, tracked_request):
        """Test sending status update notification."""
        template = CommunicationTemplate.objects.create(
            name="Status Update Template",
            communication_type=CommunicationTemplate.CommunicationType.STATUS_UPDATE,
            channel=CommunicationTemplate.Channel.EMAIL,
            subject_template="Update: ${request_number}",
            body_template="Request ${request_number} status updated to ${status}",
        )

        service = RequestNotificationService()
        communication = service.send_notification(
            request=tracked_request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            template=template,
        )

        assert communication is not None
        assert communication.communication_type == RequestCommunication.CommunicationType.STATUS_UPDATE
        assert communication.status == RequestCommunication.Status.SENT

    def test_build_context(self, tracked_request):
        """Test building template context."""
        service = RequestNotificationService()
        context = service._build_context(tracked_request)
        assert context["request_number"] == tracked_request.servicenow_number
        assert context["short_description"] == tracked_request.short_description
        assert context["requestor_name"] == tracked_request.requestor_name
        assert "time_remaining" in context

    def test_send_notification_with_stakeholders(self, tracked_request):
        """Test sending notification to stakeholders."""
        RequestStakeholder.objects.create(
            request=tracked_request,
            email="stakeholder@example.com",
            name="Stakeholder",
            role=RequestStakeholder.Role.WATCHER,
        )

        service = RequestNotificationService()
        with patch("apps.request_coordination.services.notification_service.send_mail") as mock_send_mail:
            communication = service.send_notification(
                request=tracked_request,
                communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            )
            assert communication is not None
            assert "stakeholder@example.com" in communication.recipients


class TestRequestSyncService:
    """Tests for RequestSyncService."""

    @pytest.mark.asyncio
    async def test_sync_single_request(self, cmdb_connection, db):
        """Test syncing a single request."""
        service = RequestSyncService(cmdb_connection, use_mock=True)
        try:
            tracked_request = await service.sync_request("REQ00000001")
            assert tracked_request is not None
            assert tracked_request.servicenow_number == "REQ00000001"
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_sync_all_requests_with_mock(self, cmdb_connection, db):
        """Test syncing all requests with mock client."""
        service = RequestSyncService(cmdb_connection, use_mock=True)
        try:
            synced = await service.sync_all_requests(limit=5)
            assert len(synced) > 0
            assert all(isinstance(r, TrackedRequest) for r in synced)
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_detect_status_changes(self, cmdb_connection, tracked_request):
        """Test detecting status changes."""
        service = RequestSyncService(cmdb_connection, use_mock=True)
        try:
            # Sync should detect status change
            old_status = tracked_request.status
            synced = await service.sync_request(tracked_request.servicenow_number)
            assert synced.status != old_status or RequestStatusUpdate.objects.filter(request=tracked_request).exists()
        finally:
            await service.close()


class TestMockServiceNowRequestClient:
    """Tests for MockServiceNowRequestClient."""

    @pytest.mark.asyncio
    async def test_mock_client_get_request(self, cmdb_connection):
        """Test mock client get_request."""
        client = MockServiceNowRequestClient(cmdb_connection)
        try:
            request = await client.get_request("abc123")
            assert request is not None
            assert "sys_id" in request
            assert "number" in request
            assert request["sys_id"] == "abc123"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_mock_client_query_requests(self, cmdb_connection):
        """Test mock client query_requests."""
        client = MockServiceNowRequestClient(cmdb_connection)
        try:
            requests = await client.query_requests(limit=5)
            assert len(requests) == 5
            assert all("sys_id" in r for r in requests)
            assert all("number" in r for r in requests)
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_mock_client_get_sla_info(self, cmdb_connection):
        """Test mock client get_sla_info."""
        client = MockServiceNowRequestClient(cmdb_connection)
        try:
            sla_info = await client.get_sla_info("abc123")
            assert sla_info is not None
            assert "due_date" in sla_info
            assert "task" in sla_info
        finally:
            await client.close()
