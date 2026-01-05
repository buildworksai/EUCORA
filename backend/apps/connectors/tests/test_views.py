# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Additional tests for connectors views.
"""
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestConnectorsViews:
    """Test connectors view endpoints."""
    
    @patch('apps.connectors.services.get_connector_service')
    def test_health_check_healthy(self, mock_get_service, authenticated_client):
        """Test health check endpoint with healthy connector."""
        mock_service = MagicMock()
        mock_service.health_check.return_value = {
            'status': 'healthy',
            'message': 'Connector operational',
            'details': {}
        }
        mock_get_service.return_value = mock_service
        
        url = reverse('connectors:health', kwargs={'connector_type': 'intune'})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['status'] == 'healthy'
    
    @patch('apps.connectors.services.get_connector_service')
    def test_health_check_unhealthy(self, mock_get_service, authenticated_client):
        """Test health check endpoint with unhealthy connector."""
        mock_service = MagicMock()
        mock_service.health_check.return_value = {
            'status': 'unhealthy',
            'message': 'Connection failed',
            'details': {}
        }
        mock_get_service.return_value = mock_service
        
        url = reverse('connectors:health', kwargs={'connector_type': 'intune'})
        response = authenticated_client.get(url)
        
        assert response.status_code == 503
        assert response.data['status'] == 'unhealthy'
    
    def test_health_check_invalid_connector(self, authenticated_client):
        """Test health check with invalid connector type."""
        url = reverse('connectors:health', kwargs={'connector_type': 'invalid'})
        response = authenticated_client.get(url)
        
        assert response.status_code == 400
    
    @patch('apps.connectors.services.get_connector_service')
    def test_deploy_success(self, mock_get_service, authenticated_client):
        """Test deployment endpoint with successful deployment."""
        mock_service = MagicMock()
        mock_service.deploy.return_value = {
            'status': 'success',
            'message': 'Deployment initiated',
            'connector_object_id': '12345',
            'details': {}
        }
        mock_get_service.return_value = mock_service
        
        url = reverse('connectors:deploy', kwargs={'connector_type': 'intune'})
        response = authenticated_client.post(url, {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        }, format='json')
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
    
    def test_deploy_missing_fields(self, authenticated_client):
        """Test deployment with missing required fields."""
        url = reverse('connectors:deploy', kwargs={'connector_type': 'intune'})
        response = authenticated_client.post(url, {
            'deployment_intent_id': 'test-id',
        }, format='json')
        
        assert response.status_code == 400
