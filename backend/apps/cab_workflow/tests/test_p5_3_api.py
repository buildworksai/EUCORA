# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.3: Comprehensive tests for CAB Submission REST API.
Tests all endpoints with proper authentication and role-based access control.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.cab_workflow.models import CABApprovalRequest, CABException, CABApprovalDecision
from apps.evidence_store.models import EvidencePackage
from apps.deployment_intents.models import DeploymentIntent


class CABAPITestSetup(TestCase):
    """Setup fixtures for CAB API tests."""
    
    @classmethod
    def setUpTestData(cls):
        """Create common test data."""
        # Create users
        cls.requester = User.objects.create_user(
            username='requester',
            email='requester@example.com',
            password='testpass123'
        )
        
        cls.cab_member = User.objects.create_user(
            username='cab_member',
            email='cab@example.com',
            password='testpass123'
        )
        
        cls.security_reviewer = User.objects.create_user(
            username='security_reviewer',
            email='security@example.com',
            password='testpass123'
        )
        
        cls.unauthorized_user = User.objects.create_user(
            username='unauthorized',
            email='unauthorized@example.com',
            password='testpass123'
        )
        
        # Create groups
        cab_group, _ = Group.objects.get_or_create(name='cab_member')
        security_group, _ = Group.objects.get_or_create(name='security_reviewer')
        
        cls.cab_member.groups.add(cab_group)
        cls.security_reviewer.groups.add(security_group)
        
        # Create evidence package FIRST
        from uuid import uuid4
        evidence_id = uuid4()
        
        cls.evidence = EvidencePackage.objects.create(
            id=evidence_id,
            evidence_data={
                'test_coverage': 92,
                'security_issues': 0,
                'manual_testing': 'completed',
                'rollback_validated': True,
                'change_scope': 5,
            },
            risk_score=Decimal('45'),
            risk_factors={
                'coverage': 0,
                'security': 0,
                'testing': 0,
                'rollback': 0,
                'scope': 0,
            },
            deployment_intent_id='',  # Will update after creating deployment
            correlation_id=f'EVIDENCE-{evidence_id}',  # Generate unique correlation_id
        )
        
        # Create deployment intent with evidence pack
        cls.deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring='CANARY',
            evidence_pack_id=str(cls.evidence.id),
            submitter=cls.requester,
        )
        
        # Now update evidence with deployment intent reference
        cls.evidence.deployment_intent_id = str(cls.deployment.id)
        cls.evidence.save(update_fields=['deployment_intent_id'])
    
    def setUp(self):
        """Setup for each test."""
        self.client = APIClient()


class TestCABSubmitEndpoint(CABAPITestSetup):
    """Test CAB submission endpoint."""
    
    def test_submit_requires_authentication(self):
        """Submission without auth should fail."""
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '45.0',
                'notes': 'Test submission'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_submit_low_risk_auto_approved(self):
        """Low risk submission should auto-approve."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '40.0',
                'notes': 'Low risk deployment'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'auto_approved')
        self.assertEqual(response.data['decision_status'], 'auto_approved')
        self.assertIn('auto-approved', response.data['message'].lower())
    
    def test_submit_medium_risk_pending_review(self):
        """Medium risk submission should be pending."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '60.0',
                'notes': 'Medium risk deployment'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'submitted')
        self.assertEqual(response.data['decision_status'], 'manual_review')
        self.assertIn('submitted', response.data['message'].lower())
    
    def test_submit_high_risk_exception_required(self):
        """High risk submission should require exception."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '80.0',
                'notes': 'High risk deployment'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'exception_required')
        self.assertEqual(response.data['decision_status'], 'exception_required')
    
    def test_submit_invalid_evidence_package(self):
        """Submit with invalid evidence package should fail."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': 'nonexistent',
                'risk_score': '40.0'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['error'].lower())
    
    def test_submit_invalid_risk_score_negative(self):
        """Submit with negative risk score should fail."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '-10.0'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_invalid_risk_score_too_high(self):
        """Submit with risk > 100 should fail."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '101.0'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_returns_correlation_id(self):
        """Submission should return correlation ID."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '45.0'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['correlation_id'])
        self.assertTrue(response.data['correlation_id'].startswith('CAB-'))


class TestCABRetrievalEndpoints(CABAPITestSetup):
    """Test CAB request retrieval endpoints."""
    
    def setUp(self):
        """Create a pending CAB request for testing."""
        super().setUp()
        
        self.client.force_authenticate(user=self.requester)
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '60.0',
                'notes': 'Test request'
            }
        )
        self.cab_request_id = response.data['id']
        self.client.force_authenticate(user=None)
    
    def test_get_request_requires_auth(self):
        """Getting request without auth should fail."""
        response = self.client.get(f'/api/v1/cab/{self.cab_request_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_request_by_requester(self):
        """Requester can view their own request."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.get(f'/api/v1/cab/{self.cab_request_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.cab_request_id))
    
    def test_get_request_by_cab_member(self):
        """CAB member can view any request."""
        self.client.force_authenticate(user=self.cab_member)
        
        response = self.client.get(f'/api/v1/cab/{self.cab_request_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_request_unauthorized_user_denied(self):
        """Unauthorized user cannot view request."""
        self.client.force_authenticate(user=self.unauthorized_user)
        
        response = self.client.get(f'/api/v1/cab/{self.cab_request_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_nonexistent_request(self):
        """Getting nonexistent request should fail."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.get(f'/api/v1/cab/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_pending_requests(self):
        """List pending requests endpoint."""
        self.client.force_authenticate(user=self.cab_member)
        
        response = self.client.get('/api/v1/cab/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_list_pending_requests_filter_status(self):
        """Filter pending requests by status."""
        self.client.force_authenticate(user=self.cab_member)
        
        response = self.client.get('/api/v1/cab/pending/?status=submitted')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for req in response.data['results']:
            self.assertEqual(req['status'], 'submitted')
    
    def test_list_my_requests(self):
        """List requests by requester."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.get('/api/v1/cab/my-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.cab_request_id))


class TestCABApprovalEndpoints(CABAPITestSetup):
    """Test CAB approval/rejection endpoints."""
    
    def setUp(self):
        """Create a pending CAB request for testing."""
        super().setUp()
        
        self.client.force_authenticate(user=self.requester)
        response = self.client.post(
            '/api/v1/cab/submit/',
            {
                'evidence_package_id': str(self.evidence.id),
                'risk_score': '60.0'
            }
        )
        self.cab_request_id = response.data['id']
        self.client.force_authenticate(user=None)
    
    def test_approve_requires_cab_member(self):
        """Only CAB members can approve."""
        self.client.force_authenticate(user=self.unauthorized_user)
        
        response = self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/approve/',
            {'rationale': 'Approved'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_approve_by_cab_member(self):
        """CAB member can approve request."""
        self.client.force_authenticate(user=self.cab_member)
        
        response = self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/approve/',
            {'rationale': 'Risk acceptable, approved for deployment'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        self.assertIsNotNone(response.data['approved_at'])
    
    def test_approve_with_conditions(self):
        """CAB member can approve with conditions."""
        self.client.force_authenticate(user=self.cab_member)
        
        conditions = {'max_rollout_pct': 5, 'monitoring_required': True}
        response = self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/approve/',
            {
                'rationale': 'Approved with conditions',
                'conditions': conditions
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['approval_conditions'], conditions)
    
    def test_reject_by_cab_member(self):
        """CAB member can reject request."""
        self.client.force_authenticate(user=self.cab_member)
        
        response = self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/reject/',
            {'rationale': 'Risk assessment incomplete'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')
    
    def test_cannot_approve_twice(self):
        """Cannot approve already-approved request."""
        self.client.force_authenticate(user=self.cab_member)
        
        # First approval
        self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/approve/',
            {'rationale': 'Approved'}
        )
        
        # Second approval should fail
        response = self.client.post(
            f'/api/v1/cab/{self.cab_request_id}/approve/',
            {'rationale': 'Approved again'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestCABExceptionEndpoints(CABAPITestSetup):
    """Test CAB exception endpoints."""
    
    def test_create_exception_requires_auth(self):
        """Creating exception without auth should fail."""
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 30
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_exception_valid(self):
        """Create exception with valid data."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent security patch',
                'risk_justification': 'Risk acceptable with monitoring',
                'compensating_controls': ['24/7 monitoring', 'Rollback plan'],
                'expiry_days': 30
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIsNotNone(response.data['expires_at'])
    
    def test_create_exception_no_controls(self):
        """Exception without compensating controls should fail."""
        self.client.force_authenticate(user=self.requester)
        
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': [],
                'expiry_days': 30
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_exception_invalid_expiry(self):
        """Exception with invalid expiry should fail."""
        self.client.force_authenticate(user=self.requester)
        
        # Too long (>90 days)
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 91
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_approve_exception_requires_security_reviewer(self):
        """Only Security Reviewer can approve exceptions."""
        # Create exception first
        self.client.force_authenticate(user=self.requester)
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 30
            }
        )
        exception_id = response.data['id']
        
        # Try to approve as unauthorized user
        self.client.force_authenticate(user=self.unauthorized_user)
        response = self.client.post(
            f'/api/v1/cab/exceptions/{exception_id}/approve/',
            {'rationale': 'Approved'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_approve_exception_by_security_reviewer(self):
        """Security Reviewer can approve exception."""
        # Create exception
        self.client.force_authenticate(user=self.requester)
        response = self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 30
            }
        )
        exception_id = response.data['id']
        
        # Approve as Security Reviewer
        self.client.force_authenticate(user=self.security_reviewer)
        response = self.client.post(
            f'/api/v1/cab/exceptions/{exception_id}/approve/',
            {'rationale': 'Controls sufficient'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        self.assertIsNotNone(response.data['approved_at'])
    
    def test_list_pending_exceptions(self):
        """List pending exceptions."""
        # Create exception
        self.client.force_authenticate(user=self.requester)
        self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 30
            }
        )
        
        # List pending
        response = self.client.get('/api/v1/cab/exceptions/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_list_my_exceptions(self):
        """List exceptions by requester."""
        self.client.force_authenticate(user=self.requester)
        
        # Create exception
        self.client.post(
            '/api/v1/cab/exceptions/',
            {
                'deployment_intent_id': str(self.deployment.id),
                'reason': 'Urgent',
                'risk_justification': 'Mitigated',
                'compensating_controls': ['Monitoring'],
                'expiry_days': 30
            }
        )
        
        # List my exceptions
        response = self.client.get('/api/v1/cab/exceptions/my-exceptions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
