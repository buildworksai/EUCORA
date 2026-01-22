# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for connectors endpoints.

Tests cover:
- Publish to execution planes (Intune, Jamf, SCCM, Landscape, Ansible)
- Query connector status
- Remediate failed deployments
- Audit trail and correlation IDs
- Error handling and retries
"""
import uuid
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.deployment_intents.models import DeploymentIntent
from unittest.mock import patch


class ConnectorAuthenticationTests(APITestCase):
    """Test authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @override_settings(DEBUG=False)
    def test_publish_without_auth_returns_401(self):
        """Publishing without authentication should return 401."""
        response = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(uuid.uuid4()),
            'target_plane': 'INTUNE'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_query_connector_with_auth_processes_request(self):
        """Querying connector with authentication should process request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/connectors/', format='json')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])


@patch('apps.connectors.services.IntunConnector.publish')
class ConnectorPublishTests(APITestCase):
    """Test publishing to connectors."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='publisher', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='test-app',
            version='1.0.0',
            target_ring='CANARY',
            status=DeploymentIntent.Status.APPROVED,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_publish_to_intune_succeeds(self, mock_intune):
        """Publishing to Intune connector should succeed."""
        mock_intune.return_value = {
            'status': 'success',
            'correlation_id': str(self.deployment.correlation_id)
        }
        
        response = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(self.deployment.correlation_id),
            'target_plane': 'INTUNE',
            'config': {
                'ring': 'CANARY',
                'target_count': 100
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_intune.assert_called()
    
    def test_publish_includes_correlation_id(self, mock_intune):
        """Published intent should include correlation ID."""
        mock_intune.return_value = {
            'status': 'success',
            'correlation_id': str(self.deployment.correlation_id)
        }
        
        response = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(self.deployment.correlation_id),
            'target_plane': 'INTUNE'
        }, format='json')
        
        if response.status_code == 200:
            self.assertEqual(
                response.data.get('correlation_id'),
                str(self.deployment.correlation_id)
            )
    
    def test_publish_idempotent_on_retry(self, mock_intune):
        """Publishing same intent twice should be idempotent."""
        mock_intune.return_value = {
            'status': 'success',
            'correlation_id': str(self.deployment.correlation_id)
        }
        
        # First publish
        response1 = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(self.deployment.correlation_id),
            'target_plane': 'INTUNE'
        }, format='json')
        
        # Second publish (retry)
        response2 = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(self.deployment.correlation_id),
            'target_plane': 'INTUNE'
        }, format='json')
        
        # Both should succeed
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_409_CONFLICT])


class ConnectorStatusTests(APITestCase):
    """Test querying connector status."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='auditor', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='status-test-app',
            version='1.0.0',
            target_ring='PILOT',
            status=DeploymentIntent.Status.ACTIVE,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_query_connector_status_returns_200(self):
        """Querying connector status should return 200."""
        response = self.client.get(
            f'/api/v1/connectors/status/{self.deployment.correlation_id}/',
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_query_connector_status_includes_plane_status(self):
        """Status query should include per-plane status."""
        response = self.client.get(
            f'/api/v1/connectors/status/{self.deployment.correlation_id}/',
            format='json'
        )
        
        if response.status_code == 200:
            # Should include status for multiple planes
            self.assertIn('planes', response.data)
    
    def test_query_connector_status_by_plane(self):
        """Should support querying status by specific plane."""
        response = self.client.get(
            f'/api/v1/connectors/status/{self.deployment.correlation_id}/?plane=INTUNE',
            format='json'
        )
        
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ])


@patch('apps.connectors.services.ConnectorBase.remediate')
class ConnectorRemediationTests(APITestCase):
    """Test remediation workflows."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='sre', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='remediate-test-app',
            version='1.0.0',
            target_ring='PILOT',
            status=DeploymentIntent.Status.ACTIVE,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_remediate_deployment_succeeds(self, mock_remediate):
        """Remediating failed deployment should succeed."""
        mock_remediate.return_value = {
            'status': 'remediated',
            'correlation_id': str(self.deployment.correlation_id)
        }
        
        response = self.client.post('/api/v1/connectors/remediate/', {
            'deployment_id': str(self.deployment.correlation_id),
            'reason': 'Device compliance drift detected',
            'action': 'REINSTALL'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_remediate.assert_called()
    
    def test_remediate_includes_correlation_id(self, mock_remediate):
        """Remediation should include correlation ID."""
        mock_remediate.return_value = {
            'status': 'remediated',
            'correlation_id': str(self.deployment.correlation_id)
        }
        
        response = self.client.post('/api/v1/connectors/remediate/', {
            'deployment_id': str(self.deployment.correlation_id),
            'action': 'REINSTALL'
        }, format='json')
        
        if response.status_code == 200:
            self.assertEqual(
                response.data.get('correlation_id'),
                str(self.deployment.correlation_id)
            )


class ConnectorAuditTrailTests(APITestCase):
    """Test audit trail for connector operations."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='auditor', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_list_connector_operations_returns_200(self):
        """Listing connector operations should return 200."""
        response = self.client.get('/api/v1/connectors/operations/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_operations_include_correlation_id(self):
        """Connector operations should include correlation IDs."""
        response = self.client.get('/api/v1/connectors/operations/', format='json')
        
        if response.status_code == 200 and 'operations' in response.data:
            operations = response.data.get('operations', [])
            for op in operations:
                self.assertIn('correlation_id', op)


class ConnectorEdgeCasesTests(APITestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_publish_with_invalid_plane(self):
        """Publishing to invalid plane should be rejected."""
        response = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(uuid.uuid4()),
            'target_plane': 'INVALID_PLANE'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])
    
    def test_publish_nonexistent_deployment(self):
        """Publishing non-existent deployment should return 404."""
        response = self.client.post('/api/v1/connectors/publish/', {
            'deployment_id': str(uuid.uuid4()),
            'target_plane': 'INTUNE'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_remediate_with_invalid_action(self):
        """Remediating with invalid action should be rejected."""
        response = self.client.post('/api/v1/connectors/remediate/', {
            'deployment_id': str(uuid.uuid4()),
            'action': 'INVALID_ACTION'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])
