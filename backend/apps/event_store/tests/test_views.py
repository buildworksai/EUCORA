# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for event_store views.
"""
import pytest
from django.urls import reverse
from apps.event_store.models import DeploymentEvent
import uuid


@pytest.mark.django_db
class TestEventStoreViews:
    """Test event store view endpoints."""
    
    def test_log_event(self, authenticated_client):
        """Test logging deployment event."""
        correlation_id = uuid.uuid4()
        
        url = reverse('event_store:log')
        response = authenticated_client.post(url, {
            'correlation_id': str(correlation_id),
            'event_type': 'DEPLOYMENT_CREATED',
            'event_data': {'app_name': 'TestApp'},
        }, format='json')
        
        assert response.status_code == 200
        assert 'id' in response.data
        assert 'created_at' in response.data
        
        # Verify event was created
        event = DeploymentEvent.objects.get(id=response.data['id'])
        assert event.correlation_id == correlation_id
    
    def test_list_events(self, authenticated_client):
        """Test listing deployment events."""
        correlation_id = uuid.uuid4()
        
        # Create test events
        DeploymentEvent.objects.create(
            correlation_id=correlation_id,
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={},
            actor='testuser',
        )
        
        url = reverse('event_store:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'events' in response.data
        assert len(response.data['events']) > 0
    
    def test_list_events_with_correlation_filter(self, authenticated_client):
        """Test listing events filtered by correlation ID."""
        correlation_id = uuid.uuid4()
        
        DeploymentEvent.objects.create(
            correlation_id=correlation_id,
            event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
            event_data={},
            actor='testuser',
        )
        
        url = reverse('event_store:list')
        response = authenticated_client.get(url, {'correlation_id': str(correlation_id)})
        
        assert response.status_code == 200
        assert len(response.data['events']) > 0
        assert response.data['events'][0]['correlation_id'] == str(correlation_id)
    
    def test_list_events_with_type_filter(self, authenticated_client):
        """Test listing events filtered by event type."""
        DeploymentEvent.objects.create(
            correlation_id=uuid.uuid4(),
            event_type=DeploymentEvent.EventType.DEPLOYMENT_COMPLETED,
            event_data={},
            actor='testuser',
        )
        
        url = reverse('event_store:list')
        response = authenticated_client.get(url, {'event_type': 'DEPLOYMENT_COMPLETED'})
        
        assert response.status_code == 200
        assert len(response.data['events']) > 0
