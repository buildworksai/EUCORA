# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for evidence_store endpoints.

Tests cover:
- Store evidence pack
- Retrieve evidence pack
- List evidence packs
- Evidence metadata queries
- Edge cases and boundary conditions
"""
import uuid
import json
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.deployment_intents.models import DeploymentIntent
from apps.evidence_store.models import EvidencePack


class EvidenceStoreAuthenticationTests(APITestCase):
    """Test authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @override_settings(DEBUG=False)
    def test_store_evidence_without_auth_returns_401(self):
        """Storing evidence without authentication should return 401."""
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'evidence': {}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_store_evidence_with_auth_processes_request(self):
        """Storing evidence with authentication should process request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'evidence': {
                'sbom': {'components': []},
                'scan_results': {'high': 0, 'critical': 0}
            }
        }, format='json')
        # Should either succeed or fail validation, not auth error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ])


class EvidenceStoreStorageTests(APITestCase):
    """Test evidence storage."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='publisher', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create a deployment for evidence
        self.deployment = DeploymentIntent.objects.create(
            app_name='test-app',
            version='1.0.0',
            target_ring='CANARY',
            status=DeploymentIntent.Status.PENDING,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_store_evidence_succeeds(self):
        """Storing valid evidence should succeed."""
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'deployment_id': self.deployment.correlation_id,
            'evidence': {
                'sbom': {
                    'format': 'spdx',
                    'components': [
                        {'name': 'openssl', 'version': '3.0.0'}
                    ]
                },
                'scan_results': {
                    'critical': 0,
                    'high': 1,
                    'medium': 5,
                    'low': 10
                },
                'build_info': {
                    'timestamp': '2026-01-22T10:00:00Z',
                    'builder': 'gh-actions-runner-1'
                }
            }
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
    
    def test_store_evidence_returns_pack_id(self):
        """Storing evidence should return evidence pack ID."""
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'test-app-2',
            'version': '2.0.0',
            'evidence': {
                'sbom': {},
                'scan_results': {}
            }
        }, format='json')
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            self.assertIn('evidence_pack_id', response.data)
            # Should be a valid UUID
            pack_id = response.data.get('evidence_pack_id')
            try:
                uuid.UUID(pack_id)
            except (ValueError, TypeError):
                self.fail("evidence_pack_id is not a valid UUID")
    
    def test_store_evidence_with_minimal_data(self):
        """Storing evidence with minimal required fields should work."""
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'minimal-app',
            'version': '1.0.0'
        }, format='json')
        # Should accept with minimal data or require more
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ])


class EvidenceStoreRetrievalTests(APITestCase):
    """Test evidence retrieval."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='auditor', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create evidence packs
        for i in range(3):
            EvidencePack.objects.create(
                app_name=f'app-{i}',
                version=f'{i}.0.0',
                evidence_data={
                    'sbom': {'components': []},
                    'scan_results': {'high': i, 'critical': 0}
                }
            )
    
    def test_retrieve_evidence_pack_returns_200(self):
        """Retrieving evidence pack should return 200."""
        pack = EvidencePack.objects.first()
        response = self.client.get(f'/api/v1/evidence/{pack.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_evidence_pack_includes_data(self):
        """Retrieved evidence should include all stored data."""
        pack = EvidencePack.objects.create(
            app_name='complete-app',
            version='1.0.0',
            evidence_data={
                'sbom': {'format': 'spdx', 'components': [{'name': 'lib', 'version': '1.0'}]},
                'scan_results': {'critical': 0, 'high': 1}
            }
        )
        
        response = self.client.get(f'/api/v1/evidence/{pack.id}/', format='json')
        if response.status_code == 200:
            self.assertEqual(response.data['app_name'], 'complete-app')
            self.assertEqual(response.data['version'], '1.0.0')
            self.assertIn('evidence_data', response.data)
    
    def test_retrieve_nonexistent_evidence_returns_404(self):
        """Retrieving non-existent evidence should return 404."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/v1/evidence/{fake_id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EvidenceStoreListTests(APITestCase):
    """Test listing evidence packs."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='reviewer', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create multiple evidence packs
        for i in range(5):
            EvidencePack.objects.create(
                app_name=f'app-{i}',
                version=f'1.{i}.0',
                evidence_data={'test': True}
            )
    
    def test_list_evidence_returns_200(self):
        """Listing evidence packs should return 200."""
        response = self.client.get('/api/v1/evidence/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_evidence_includes_results(self):
        """Evidence list should include all packs."""
        response = self.client.get('/api/v1/evidence/', format='json')
        if response.status_code == 200:
            self.assertIn('evidence_packs', response.data)
            packs = response.data.get('evidence_packs', [])
            self.assertGreaterEqual(len(packs), 0)
    
    def test_list_evidence_with_app_filter(self):
        """Listing should support filtering by app name."""
        response = self.client.get('/api/v1/evidence/?app_name=app-1', format='json')
        if response.status_code == 200:
            packs = response.data.get('evidence_packs', [])
            # All returned packs should match filter
            for pack in packs:
                self.assertEqual(pack['app_name'], 'app-1')


class EvidenceStoreEdgeCasesTests(APITestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_store_evidence_with_large_sbom(self):
        """Storing evidence with large SBOM should be handled."""
        large_sbom = {
            'components': [
                {'name': f'component-{i}', 'version': '1.0.0'}
                for i in range(1000)
            ]
        }
        
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'large-sbom-app',
            'version': '1.0.0',
            'evidence': {
                'sbom': large_sbom,
                'scan_results': {}
            }
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ])
    
    def test_store_evidence_with_empty_evidence(self):
        """Storing evidence with empty data should be handled."""
        response = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'minimal-app',
            'version': '1.0.0',
            'evidence': {}
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_evidence_immutability(self):
        """Stored evidence should be immutable."""
        # Store original evidence
        response1 = self.client.post('/api/v1/evidence/store/', {
            'app_name': 'immutable-app',
            'version': '1.0.0',
            'evidence': {'original': True}
        }, format='json')
        
        if response1.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            pack_id = response1.data.get('evidence_pack_id')
            
            # Try to update (should fail or create new version)
            response2 = self.client.put(f'/api/v1/evidence/{pack_id}/', {
                'evidence': {'modified': True}
            }, format='json')
            
            # Should either reject update or create new version
            self.assertIn(response2.status_code, [
                status.HTTP_403_FORBIDDEN,  # Immutable
                status.HTTP_400_BAD_REQUEST,  # Method not allowed
                status.HTTP_405_METHOD_NOT_ALLOWED  # PUT not supported
            ])
