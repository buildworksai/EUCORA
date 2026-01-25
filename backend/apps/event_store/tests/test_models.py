# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for event_store app.
"""
import uuid

import pytest

from apps.event_store.models import DeploymentEvent


@pytest.mark.django_db
class TestDeploymentEvent:
    """Test DeploymentEvent model."""

    def test_create_deployment_event(self):
        """Test creating a deployment event."""
        correlation_id = uuid.uuid4()
        event = DeploymentEvent.objects.create(
            correlation_id=correlation_id,
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={"app_name": "TestApp", "version": "1.0.0"},
            actor="testuser",
        )
        assert event.correlation_id == correlation_id
        assert event.event_type == DeploymentEvent.EventType.DEPLOYMENT_CREATED

    def test_append_only_no_updates(self):
        """Test that deployment events cannot be updated."""
        event = DeploymentEvent.objects.create(
            correlation_id=uuid.uuid4(),
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={},
            actor="testuser",
        )

        # Attempt to update should raise ValueError
        with pytest.raises(ValueError, match="append-only"):
            event.event_data = {"modified": True}
            event.save()

    def test_append_only_no_deletes(self):
        """Test that deployment events cannot be deleted."""
        event = DeploymentEvent.objects.create(
            correlation_id=uuid.uuid4(),
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={},
            actor="testuser",
        )

        # Attempt to delete should raise ValueError
        with pytest.raises(ValueError, match="append-only"):
            event.delete()

    def test_query_events_by_correlation_id(self):
        """Test querying events by correlation ID."""
        correlation_id = uuid.uuid4()

        # Create multiple events for same deployment
        DeploymentEvent.objects.create(
            correlation_id=correlation_id,
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={},
            actor="testuser",
        )
        DeploymentEvent.objects.create(
            correlation_id=correlation_id,
            event_type=DeploymentEvent.EventType.RISK_ASSESSED,
            event_data={},
            actor="system",
        )

        events = DeploymentEvent.objects.filter(correlation_id=correlation_id)
        assert events.count() == 2
