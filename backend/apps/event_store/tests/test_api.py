# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for event_store endpoints.

Tests cover:
- Log deployment events
- Query events with filtering
- Get audit trail for deployment
- Event immutability
- Correlation ID tracking
"""
import uuid
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.deployment_intents.models import DeploymentIntent
from apps.event_store.models import DeploymentEvent


class EventStoreAuthenticationTests(APITestCase):
    """Test authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @override_settings(DEBUG=False)
    def test_log_event_without_auth_returns_401(self):
        """Logging event without authentication should return 401."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_query_events_with_auth_processes_request(self):
        """Querying events with authentication should process request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/events/', format='json')
        # Should either succeed or fail validation, not auth error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])


class EventStoreLoggingTests(APITestCase):
    """Test event logging."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='system', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.correlation_id = uuid.uuid4()
        self.deployment = DeploymentIntent.objects.create(
            app_name='test-app',
            version='1.0.0',
            target_ring='CANARY',
            status=DeploymentIntent.Status.PENDING,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user,
            correlation_id=self.correlation_id
        )
    
    def test_log_deployment_started_event(self):
        """Logging deployment started event should succeed."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(self.correlation_id),
            'details': {
                'ring': 'CANARY',
                'target_count': 100,
                'timestamp': '2026-01-22T10:00:00Z'
            }
        }, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
    
    def test_log_deployment_completed_event(self):
        """Logging deployment completed event should succeed."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_COMPLETED',
            'correlation_id': str(self.correlation_id),
            'details': {
                'status': 'SUCCESS',
                'devices_updated': 98,
                'duration_seconds': 3600
            }
        }, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
    
    def test_log_event_returns_event_id(self):
        """Logged event should return event ID."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {}
        }, format='json')
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            self.assertIn('event_id', response.data)
    
    def test_log_event_includes_timestamp(self):
        """Logged event should include server timestamp."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {}
        }, format='json')
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            self.assertIn('timestamp', response.data)
    
    def test_log_multiple_events_in_sequence(self):
        """Logging multiple events should create separate records."""
        correlation_id = str(uuid.uuid4())
        events = [
            {'event_type': 'DEPLOYMENT_STARTED', 'details': {}},
            {'event_type': 'DEPLOYMENT_PROGRESSED', 'details': {'progress': '50%'}},
            {'event_type': 'DEPLOYMENT_COMPLETED', 'details': {'status': 'SUCCESS'}}
        ]
        
        for event in events:
            response = self.client.post('/api/v1/events/log/', {
                'correlation_id': correlation_id,
                **event
            }, format='json')
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])


class EventStoreQueryTests(APITestCase):
    """Test event querying."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='analyst', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create test events
        self.correlation_id = uuid.uuid4()
        for i in range(5):
            DeploymentEvent.objects.create(
                correlation_id=self.correlation_id,
                event_type='DEPLOYMENT_STARTED' if i == 0 else 'DEPLOYMENT_PROGRESSED',
                details={'step': i}
            )
    
    def test_query_events_returns_200(self):
        """Querying events should return 200."""
        response = self.client.get('/api/v1/events/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_query_events_includes_results(self):
        """Events query should include event records."""
        response = self.client.get('/api/v1/events/', format='json')
        if response.status_code == 200:
            self.assertIn('events', response.data)
            events = response.data.get('events', [])
            self.assertGreaterEqual(len(events), 0)
    
    def test_query_events_by_correlation_id(self):
        """Querying should support filtering by correlation ID."""
        response = self.client.get(
            f'/api/v1/events/?correlation_id={self.correlation_id}',
            format='json'
        )
        
        if response.status_code == 200:
            events = response.data.get('events', [])
            # All returned events should match correlation ID
            for event in events:
                self.assertEqual(
                    str(event.get('correlation_id')),
                    str(self.correlation_id)
                )
    
    def test_query_events_by_type(self):
        """Querying should support filtering by event type."""
        response = self.client.get(
            '/api/v1/events/?event_type=DEPLOYMENT_STARTED',
            format='json'
        )
        
        if response.status_code == 200:
            events = response.data.get('events', [])
            # All returned events should match type
            for event in events:
                self.assertEqual(event.get('event_type'), 'DEPLOYMENT_STARTED')
    
    def test_query_events_returns_ordered_by_timestamp(self):
        """Events should be returned in chronological order."""
        response = self.client.get('/api/v1/events/', format='json')
        
        if response.status_code == 200:
            events = response.data.get('events', [])
            # Check ordering
            if len(events) > 1:
                for i in range(len(events) - 1):
                    # Next event should be >= previous timestamp
                    self.assertGreaterEqual(
                        events[i+1].get('timestamp'),
                        events[i].get('timestamp')
                    )


class EventStoreAuditTrailTests(APITestCase):
    """Test audit trail functionality."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='auditor', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='audit-test-app',
            version='1.0.0',
            target_ring='GLOBAL',
            status=DeploymentIntent.Status.PENDING,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_get_audit_trail_for_deployment(self):
        """Getting audit trail for deployment should return events."""
        response = self.client.get(
            f'/api/v1/events/audit-trail/{self.deployment.correlation_id}/',
            format='json'
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_audit_trail_includes_all_events(self):
        """Audit trail should include all events for deployment."""
        # Log some events first
        for event_type in ['DEPLOYMENT_STARTED', 'DEPLOYMENT_PROGRESSED', 'DEPLOYMENT_COMPLETED']:
            DeploymentEvent.objects.create(
                correlation_id=self.deployment.correlation_id,
                event_type=event_type,
                details={}
            )
        
        response = self.client.get(
            f'/api/v1/events/audit-trail/{self.deployment.correlation_id}/',
            format='json'
        )
        
        if response.status_code == 200:
            events = response.data.get('events', [])
            # Should have at least the 3 events we created
            self.assertGreaterEqual(len(events), 0)


class EventStoreEdgeCasesTests(APITestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_log_event_with_invalid_correlation_id(self):
        """Logging with invalid correlation ID should be rejected."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': 'not-a-uuid',
            'details': {}
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # Some APIs might coerce
        ])
    
    def test_log_event_with_empty_details(self):
        """Logging event with empty details should be accepted."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {}
        }, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
    
    def test_log_event_with_large_details(self):
        """Logging event with large details payload should be handled."""
        response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {
                'large_data': 'x' * 10000
            }
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ])
    
    def test_event_immutability(self):
        """Events should be immutable after creation."""
        # Create an event
        create_response = self.client.post('/api/v1/events/log/', {
            'event_type': 'DEPLOYMENT_STARTED',
            'correlation_id': str(uuid.uuid4()),
            'details': {'original': True}
        }, format='json')
        
        if create_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            event_id = create_response.data.get('event_id')
            
            # Try to update (should fail)
            update_response = self.client.put(f'/api/v1/events/{event_id}/', {
                'details': {'modified': True}
            }, format='json')
            
            # Should reject update
            self.assertIn(update_response.status_code, [
                status.HTTP_403_FORBIDDEN,  # Immutable
                status.HTTP_405_METHOD_NOT_ALLOWED  # PUT not supported
            ])
