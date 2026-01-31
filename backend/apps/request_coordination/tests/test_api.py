# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for Request Coordination Agent.
"""
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

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


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Create authenticated API client."""
    user = User.objects.create_user(username="testuser", password="testpass")
    client = APIClient()
    client.force_authenticate(user=user)
    client.user = user
    return client


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


class TestTrackedRequestViewSet:
    """Tests for TrackedRequestViewSet."""

    def test_list_requests_unauthenticated(self, api_client):
        """Test listing requests without authentication."""
        response = api_client.get("/api/request-coordination/requests/")
        # DRF may return 403 instead of 401 depending on settings
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_list_requests(self, authenticated_client, tracked_request):
        """Test listing requests."""
        response = authenticated_client.get("/api/request-coordination/requests/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(r["servicenow_number"] == "REQ001234" for r in data)

    def test_create_request(self, authenticated_client):
        """Test creating a request."""
        data = {
            "servicenow_number": "REQ005678",
            "servicenow_sys_id": "xyz789",
            "request_type": TrackedRequest.RequestType.ACCESS_REQUEST,
            "short_description": "Access Request Test",
            "requestor_email": "requester@example.com",
            "requestor_name": "Requester User",
            "status": TrackedRequest.Status.NEW,
            "priority": TrackedRequest.Priority.HIGH,
        }
        response = authenticated_client.post("/api/request-coordination/requests/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert TrackedRequest.objects.filter(servicenow_number="REQ005678").exists()

    def test_retrieve_request(self, authenticated_client, tracked_request):
        """Test retrieving a single request."""
        response = authenticated_client.get(f"/api/request-coordination/requests/{tracked_request.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["servicenow_number"] == "REQ001234"
        assert response.data["stakeholder_count"] == 0
        assert response.data["communication_count"] == 0

    def test_update_request(self, authenticated_client, tracked_request):
        """Test updating a request."""
        data = {"status": TrackedRequest.Status.RESOLVED}
        response = authenticated_client.patch(
            f"/api/request-coordination/requests/{tracked_request.id}/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        tracked_request.refresh_from_db()
        assert tracked_request.status == TrackedRequest.Status.RESOLVED

    def test_delete_request(self, authenticated_client, tracked_request):
        """Test deleting a request."""
        response = authenticated_client.delete(f"/api/request-coordination/requests/{tracked_request.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TrackedRequest.objects.filter(id=tracked_request.id).exists()

    def test_sync_requests_action(self, authenticated_client, cmdb_connection):
        """Test sync requests action."""
        data = {"connection_id": str(cmdb_connection.id), "limit": 10}
        response = authenticated_client.post("/api/request-coordination/requests/sync/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "synced" in response.data
        assert "request_ids" in response.data

    def test_sync_requests_missing_connection(self, authenticated_client):
        """Test sync requests without connection_id."""
        data = {"limit": 10}
        response = authenticated_client.post("/api/request-coordination/requests/sync/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_timeline_action(self, authenticated_client, tracked_request):
        """Test timeline action."""
        # Create status update
        RequestStatusUpdate.objects.create(
            request=tracked_request,
            old_status=TrackedRequest.Status.NEW,
            new_status=TrackedRequest.Status.IN_PROGRESS,
            updated_by="system",
        )
        # Create communication
        RequestCommunication.objects.create(
            request=tracked_request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            channel=RequestCommunication.Channel.EMAIL,
            recipients=["user@example.com"],
            subject="Test",
            body="Test body",
        )

        response = authenticated_client.get(f"/api/request-coordination/requests/{tracked_request.id}/timeline/")
        assert response.status_code == status.HTTP_200_OK
        assert "timeline" in response.data
        assert len(response.data["timeline"]) == 2

    def test_filter_by_correlation_id(self, authenticated_client):
        """Test filtering by correlation_id."""
        # Create a request and get its correlation_id
        request = TrackedRequest.objects.create(
            servicenow_number="REQ999999",
            servicenow_sys_id="test123",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test Request",
            requestor_email="user@example.com",
            requestor_name="Test User",
        )
        correlation_id = str(request.correlation_id)

        response = authenticated_client.get(f"/api/request-coordination/requests/?correlation_id={correlation_id}")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        # Check that at least one result matches the correlation_id
        matching = [r for r in data if str(r.get("correlation_id")) == correlation_id]
        assert (
            len(matching) >= 1
        ), f"Expected to find request with correlation_id={correlation_id}, got {len(data)} results"

    def test_filter_by_status(self, authenticated_client, tracked_request):
        """Test filtering by status."""
        response = authenticated_client.get(
            f"/api/request-coordination/requests/?status={TrackedRequest.Status.IN_PROGRESS}"
        )
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(r["status"] == TrackedRequest.Status.IN_PROGRESS for r in data)

    def test_filter_by_priority(self, authenticated_client, tracked_request):
        """Test filtering by priority."""
        response = authenticated_client.get(
            f"/api/request-coordination/requests/?priority={TrackedRequest.Priority.MEDIUM}"
        )
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(r["priority"] == TrackedRequest.Priority.MEDIUM for r in data)


class TestRequestStakeholderViewSet:
    """Tests for RequestStakeholderViewSet."""

    def test_list_stakeholders(self, authenticated_client, tracked_request):
        """Test listing stakeholders."""
        RequestStakeholder.objects.create(
            request=tracked_request,
            email="stakeholder@example.com",
            name="Stakeholder",
            role=RequestStakeholder.Role.WATCHER,
        )
        response = authenticated_client.get("/api/request-coordination/stakeholders/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    def test_create_stakeholder(self, authenticated_client, tracked_request):
        """Test creating a stakeholder."""
        data = {
            "request": str(tracked_request.id),
            "email": "new@example.com",
            "name": "New Stakeholder",
            "role": RequestStakeholder.Role.APPROVER,
        }
        response = authenticated_client.post("/api/request-coordination/stakeholders/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert RequestStakeholder.objects.filter(email="new@example.com").exists()

    def test_filter_by_request_id(self, authenticated_client, tracked_request):
        """Test filtering by request_id."""
        RequestStakeholder.objects.create(
            request=tracked_request,
            email="stakeholder@example.com",
            name="Stakeholder",
            role=RequestStakeholder.Role.WATCHER,
        )
        response = authenticated_client.get(f"/api/request-coordination/stakeholders/?request_id={tracked_request.id}")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1


class TestRequestCommunicationViewSet:
    """Tests for RequestCommunicationViewSet."""

    def test_list_communications(self, authenticated_client, tracked_request):
        """Test listing communications."""
        RequestCommunication.objects.create(
            request=tracked_request,
            communication_type=RequestCommunication.CommunicationType.STATUS_UPDATE,
            channel=RequestCommunication.Channel.EMAIL,
            recipients=["user@example.com"],
            subject="Test",
            body="Test body",
        )
        response = authenticated_client.get("/api/request-coordination/communications/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    def test_send_action(self, authenticated_client, tracked_request):
        """Test send communication action."""
        data = {
            "request_id": str(tracked_request.id),
            "communication_type": RequestCommunication.CommunicationType.STATUS_UPDATE,
        }
        response = authenticated_client.post("/api/request-coordination/communications/send/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.data
        assert response.data["communication_type"] == RequestCommunication.CommunicationType.STATUS_UPDATE

    def test_send_action_with_template(self, authenticated_client, tracked_request):
        """Test send communication with template."""
        template = CommunicationTemplate.objects.create(
            name="Test Template",
            communication_type=CommunicationTemplate.CommunicationType.STATUS_UPDATE,
            channel=CommunicationTemplate.Channel.EMAIL,
            subject_template="Update: ${request_number}",
            body_template="Request ${request_number} updated",
        )
        data = {
            "request_id": str(tracked_request.id),
            "communication_type": RequestCommunication.CommunicationType.STATUS_UPDATE,
            "template_id": str(template.id),
        }
        response = authenticated_client.post("/api/request-coordination/communications/send/", data, format="json")
        assert response.status_code == status.HTTP_200_OK


class TestEscalationRuleViewSet:
    """Tests for EscalationRuleViewSet."""

    def test_list_rules(self, authenticated_client):
        """Test listing escalation rules."""
        EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_WARNING,
            trigger_config={"hours_before_breach": 4},
            escalation_actions=[],
        )
        response = authenticated_client.get("/api/request-coordination/escalation-rules/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    def test_create_rule(self, authenticated_client):
        """Test creating an escalation rule."""
        data = {
            "name": "New Rule",
            "description": "New rule description",
            "trigger_type": EscalationRule.TriggerType.SLA_BREACH,
            "trigger_config": {},
            "escalation_actions": [{"type": "notify", "recipients": ["manager"]}],
        }
        response = authenticated_client.post("/api/request-coordination/escalation-rules/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert EscalationRule.objects.filter(name="New Rule").exists()

    def test_filter_by_active(self, authenticated_client):
        """Test filtering by active status."""
        EscalationRule.objects.create(
            name="Active Rule",
            description="Active",
            trigger_type=EscalationRule.TriggerType.SLA_WARNING,
            trigger_config={},
            escalation_actions=[],
            is_active=True,
        )
        EscalationRule.objects.create(
            name="Inactive Rule",
            description="Inactive",
            trigger_type=EscalationRule.TriggerType.SLA_WARNING,
            trigger_config={},
            escalation_actions=[],
            is_active=False,
        )
        response = authenticated_client.get("/api/request-coordination/escalation-rules/?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(r["name"] == "Active Rule" for r in data)


class TestEscalationEventViewSet:
    """Tests for EscalationEventViewSet."""

    def test_list_events(self, authenticated_client, tracked_request):
        """Test listing escalation events."""
        rule = EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[],
        )
        EscalationEvent.objects.create(
            request=tracked_request,
            rule=rule,
            trigger_reason="SLA breached",
            escalation_level=1,
            actions_taken=[],
        )
        response = authenticated_client.get("/api/request-coordination/escalations/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    def test_resolve_action(self, authenticated_client, tracked_request):
        """Test resolve escalation action."""
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
        data = {"un_escalate": True}
        response = authenticated_client.post(
            f"/api/request-coordination/escalations/{event.id}/resolve/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        event.refresh_from_db()
        assert event.resolved_at is not None
        tracked_request.refresh_from_db()
        assert tracked_request.is_escalated is False

    def test_filter_by_resolved(self, authenticated_client, tracked_request):
        """Test filtering by resolved status."""
        rule = EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[],
        )
        EscalationEvent.objects.create(
            request=tracked_request,
            rule=rule,
            trigger_reason="SLA breached",
            escalation_level=1,
            actions_taken=[],
            resolved_at=timezone.now(),
        )
        EscalationEvent.objects.create(
            request=tracked_request,
            rule=rule,
            trigger_reason="Another breach",
            escalation_level=2,
            actions_taken=[],
        )
        response = authenticated_client.get("/api/request-coordination/escalations/?resolved=true")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert all(e.get("resolved_at") is not None for e in data)


class TestCommunicationTemplateViewSet:
    """Tests for CommunicationTemplateViewSet."""

    def test_list_templates(self, authenticated_client):
        """Test listing templates."""
        CommunicationTemplate.objects.create(
            name="Test Template",
            communication_type=CommunicationTemplate.CommunicationType.STATUS_UPDATE,
            channel=CommunicationTemplate.Channel.EMAIL,
            subject_template="Test",
            body_template="Test body",
        )
        response = authenticated_client.get("/api/request-coordination/templates/")
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1

    def test_create_template(self, authenticated_client):
        """Test creating a template."""
        data = {
            "name": "New Template",
            "communication_type": CommunicationTemplate.CommunicationType.SLA_WARNING,
            "channel": CommunicationTemplate.Channel.EMAIL,
            "subject_template": "SLA Warning: ${request_number}",
            "body_template": "Request ${request_number} is approaching SLA deadline.",
            "variables": ["request_number", "sla_due"],
        }
        response = authenticated_client.post("/api/request-coordination/templates/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert CommunicationTemplate.objects.filter(name="New Template").exists()

    def test_filter_by_type_and_channel(self, authenticated_client):
        """Test filtering by communication_type and channel."""
        CommunicationTemplate.objects.create(
            name="Email Template",
            communication_type=CommunicationTemplate.CommunicationType.STATUS_UPDATE,
            channel=CommunicationTemplate.Channel.EMAIL,
            subject_template="Test",
            body_template="Test body",
        )
        CommunicationTemplate.objects.create(
            name="Teams Template",
            communication_type=CommunicationTemplate.CommunicationType.STATUS_UPDATE,
            channel=CommunicationTemplate.Channel.TEAMS,
            subject_template="Test",
            body_template="Test body",
        )
        response = authenticated_client.get(
            f"/api/request-coordination/templates/?communication_type={CommunicationTemplate.CommunicationType.STATUS_UPDATE}&channel={CommunicationTemplate.Channel.EMAIL}"
        )
        assert response.status_code == status.HTTP_200_OK
        # Handle paginated response
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(t["name"] == "Email Template" for t in data)


class TestRequestCoordinationReportsViewSet:
    """Tests for RequestCoordinationReportsViewSet."""

    def test_sla_compliance_report(self, authenticated_client):
        """Test SLA compliance report."""
        # Create requests with different SLA statuses
        TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 1",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() + timedelta(hours=10),  # Compliant
        )
        TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 2",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() + timedelta(hours=2),  # At risk
        )
        TrackedRequest.objects.create(
            servicenow_number="REQ003",
            servicenow_sys_id="sys3",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 3",
            requestor_email="user@example.com",
            requestor_name="User",
            sla_due=timezone.now() - timedelta(hours=1),  # Breached
        )

        response = authenticated_client.get("/api/request-coordination/reports/sla_compliance/")
        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "compliant" in response.data
        assert "at_risk" in response.data
        assert "breached" in response.data
        assert "compliance_rate" in response.data

    def test_workload_report(self, authenticated_client):
        """Test workload report."""
        TrackedRequest.objects.create(
            servicenow_number="REQ001",
            servicenow_sys_id="sys1",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 1",
            requestor_email="user@example.com",
            requestor_name="User",
            assignment_group="IT Support",
            status=TrackedRequest.Status.IN_PROGRESS,
        )
        TrackedRequest.objects.create(
            servicenow_number="REQ002",
            servicenow_sys_id="sys2",
            request_type=TrackedRequest.RequestType.SOFTWARE_INSTALL,
            short_description="Test 2",
            requestor_email="user@example.com",
            requestor_name="User",
            assignment_group="IT Support",
            status=TrackedRequest.Status.NEW,
        )

        response = authenticated_client.get("/api/request-coordination/reports/workload/")
        assert response.status_code == status.HTTP_200_OK
        assert "workload" in response.data
        assert len(response.data["workload"]) > 0

    def test_trends_report(self, authenticated_client, tracked_request):
        """Test trends report."""
        rule = EscalationRule.objects.create(
            name="Test Rule",
            description="Test",
            trigger_type=EscalationRule.TriggerType.SLA_BREACH,
            trigger_config={},
            escalation_actions=[],
        )
        EscalationEvent.objects.create(
            request=tracked_request,
            rule=rule,
            trigger_reason="Test",
            escalation_level=1,
            actions_taken=[],
        )

        response = authenticated_client.get("/api/request-coordination/reports/trends/?days=30")
        assert response.status_code == status.HTTP_200_OK
        assert "trends" in response.data
