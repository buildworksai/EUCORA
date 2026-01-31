# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for Change Communications models.
"""
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.change_communications.models import (
    ChangeAuditEvent,
    ChangeRecord,
    Communication,
    CommunicationTemplate,
    KBArticleLink,
    StakeholderGroup,
)


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def change_record(db, user):
    """Create a test change record."""
    return ChangeRecord.objects.create(
        servicenow_number="CHG0012345",
        servicenow_sys_id="abc123",
        change_type="normal",
        short_description="Test change",
        planned_start=timezone.now(),
        planned_end=timezone.now() + timedelta(hours=2),
        requested_by=user,
    )


@pytest.fixture
def stakeholder_group(db):
    """Create a test stakeholder group."""
    return StakeholderGroup.objects.create(
        name="IT Team",
        notification_channel="email",
        channel_config={"email_addresses": ["it@example.com"]},
    )


@pytest.fixture
def communication_template(db):
    """Create a test communication template."""
    return CommunicationTemplate.objects.create(
        name="Change Scheduled",
        event_type="scheduled",
        channel="email",
        subject_template="[EUCORA] Change ${change_number} Scheduled",
        body_template="Change ${change_number} has been scheduled for ${planned_start}.",
    )


class TestChangeRecord:
    """Tests for ChangeRecord model."""

    def test_create_change_record(self, change_record):
        """Test creating a change record."""
        assert change_record.id is not None
        assert change_record.servicenow_number == "CHG0012345"
        assert change_record.state == "new"

    def test_change_record_str(self, change_record):
        """Test change record string representation."""
        expected = "CHG0012345: Test change"
        assert str(change_record) == expected

    def test_change_record_correlation_id(self, change_record):
        """Test correlation ID is generated."""
        assert change_record.correlation_id is not None
        assert isinstance(change_record.correlation_id, uuid.UUID)

    def test_change_types(self, db, user):
        """Test all change types."""
        for change_type in ["standard", "normal", "emergency"]:
            record = ChangeRecord.objects.create(
                servicenow_number=f"CHG-{change_type}",
                servicenow_sys_id=str(uuid.uuid4()),
                change_type=change_type,
                short_description="Test",
                planned_start=timezone.now(),
                planned_end=timezone.now() + timedelta(hours=1),
            )
            assert record.change_type == change_type

    def test_change_states(self, change_record):
        """Test state transitions."""
        states = ["new", "assess", "authorize", "scheduled", "implement", "review", "closed"]
        for state in states:
            change_record.state = state
            change_record.save()
            change_record.refresh_from_db()
            assert change_record.state == state


class TestStakeholderGroup:
    """Tests for StakeholderGroup model."""

    def test_create_stakeholder_group(self, stakeholder_group):
        """Test creating a stakeholder group."""
        assert stakeholder_group.id is not None
        assert stakeholder_group.name == "IT Team"
        assert stakeholder_group.notification_channel == "email"

    def test_stakeholder_group_str(self, stakeholder_group):
        """Test stakeholder group string representation."""
        assert "IT Team" in str(stakeholder_group)

    def test_channel_types(self, db):
        """Test all notification channels."""
        for channel in ["email", "teams", "slack", "servicenow"]:
            group = StakeholderGroup.objects.create(
                name=f"Group {channel}",
                notification_channel=channel,
                channel_config={},
            )
            assert group.notification_channel == channel


class TestCommunicationTemplate:
    """Tests for CommunicationTemplate model."""

    def test_create_template(self, communication_template):
        """Test creating a template."""
        assert communication_template.id is not None
        assert communication_template.event_type == "scheduled"
        assert "${change_number}" in communication_template.subject_template

    def test_template_str(self, communication_template):
        """Test template string representation."""
        assert "Change Scheduled" in str(communication_template)

    def test_event_types(self, db):
        """Test all event types."""
        event_types = ["scheduled", "started", "progress", "completed", "failed", "rollback", "closed"]
        for i, event_type in enumerate(event_types):
            template = CommunicationTemplate.objects.create(
                name=f"Template {event_type}",
                event_type=event_type,
                channel="email",
                subject_template="Test",
                body_template="Test",
            )
            assert template.event_type == event_type


class TestCommunication:
    """Tests for Communication model."""

    def test_create_communication(self, db, change_record, communication_template, stakeholder_group):
        """Test creating a communication."""
        comm = Communication.objects.create(
            change_record=change_record,
            template=communication_template,
            stakeholder_group=stakeholder_group,
            channel="email",
            subject="Test Subject",
            body="Test Body",
            recipients=["test@example.com"],
        )
        assert comm.id is not None
        assert comm.status == "pending"

    def test_communication_correlation_id(self, db, change_record):
        """Test communication gets correlation ID."""
        comm = Communication.objects.create(
            change_record=change_record,
            channel="email",
            subject="Test",
            body="Test",
        )
        assert comm.correlation_id is not None

    def test_communication_status_transitions(self, db, change_record):
        """Test status transitions."""
        comm = Communication.objects.create(
            change_record=change_record,
            channel="email",
            subject="Test",
            body="Test",
        )
        for status in ["pending", "sent", "delivered", "failed"]:
            comm.status = status
            comm.save()
            comm.refresh_from_db()
            assert comm.status == status


class TestKBArticleLink:
    """Tests for KBArticleLink model."""

    def test_create_kb_link(self, db, change_record):
        """Test creating a KB article link."""
        link = KBArticleLink.objects.create(
            change_record=change_record,
            kb_article_number="KB0001234",
            kb_article_sys_id="kb123",
            kb_article_title="How to resolve issue X",
            link_type="created",
            created_by_agent=True,
        )
        assert link.id is not None
        assert link.created_by_agent is True

    def test_link_types(self, db, change_record):
        """Test all link types."""
        for link_type in ["created", "updated", "referenced", "linked"]:
            link = KBArticleLink.objects.create(
                change_record=change_record,
                kb_article_number=f"KB-{link_type}",
                kb_article_sys_id=str(uuid.uuid4()),
                link_type=link_type,
            )
            assert link.link_type == link_type


class TestChangeAuditEvent:
    """Tests for ChangeAuditEvent model."""

    def test_create_audit_event(self, db, change_record, user):
        """Test creating an audit event."""
        event = ChangeAuditEvent.objects.create(
            change_record=change_record,
            event_type="created",
            description="Change record created",
            performed_by=user,
        )
        assert event.id is not None
        assert event.event_type == "created"

    def test_event_types(self, db, change_record):
        """Test all event types."""
        event_types = [
            "created",
            "state_change",
            "notification_sent",
            "kb_linked",
            "evidence_attached",
            "approval_received",
            "closed",
        ]
        for event_type in event_types:
            event = ChangeAuditEvent.objects.create(
                change_record=change_record,
                event_type=event_type,
                description=f"Test {event_type}",
            )
            assert event.event_type == event_type
