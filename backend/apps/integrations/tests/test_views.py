# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for integration API views.
"""
import pytest
from unittest.mock import Mock, patch
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.integrations.models import ExternalSystem


@pytest.mark.django_db
class TestExternalSystemViewSet:
    """Test ExternalSystemViewSet."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_integrations(self):
        """Test listing integrations."""
        ExternalSystem.objects.create(
            name='Test System',
            type=ExternalSystem.SystemType.SERVICENOW_CMDB,
            api_url='https://test.com',
            auth_type=ExternalSystem.AuthType.BASIC,
            credentials={},
        )
        
        response = self.client.get('/api/v1/integrations/')
        
        assert response.status_code == 200
        assert len(response.data) == 1
    
    def test_create_integration(self):
        """Test creating an integration."""
        data = {
            'name': 'New Integration',
            'type': ExternalSystem.SystemType.SERVICENOW_CMDB,
            'api_url': 'https://test.com',
            'auth_type': ExternalSystem.AuthType.BASIC,
            'credentials': {'username': 'test', 'password': 'test'},
        }
        
        response = self.client.post('/api/v1/integrations/', data, format='json')
        
        assert response.status_code == 201
        assert response.data['name'] == 'New Integration'
    
    @patch('apps.integrations.services.factory.get_integration_service')
    def test_test_connection(self, mock_get_service):
        """Test connection test endpoint."""
        from apps.integrations.services.servicenow import ServiceNowCMDBService
        
        system = ExternalSystem.objects.create(
            name='Test System',
            type=ExternalSystem.SystemType.SERVICENOW_CMDB,
            api_url='https://test.com',
            auth_type=ExternalSystem.AuthType.BASIC,
            credentials={'username': 'test', 'password': 'test'},
        )
        
        mock_service = Mock(spec=ServiceNowCMDBService)
        mock_service.test_connection.return_value = {'status': 'success', 'message': 'OK'}
        mock_get_service.return_value = mock_service
        
        response = self.client.post(f'/api/v1/integrations/{system.id}/test/')
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'

