# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for integration services.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.integrations.models import ExternalSystem
from apps.integrations.services.factory import get_integration_service
from apps.integrations.services.base import IntegrationService


@pytest.mark.django_db
class TestServiceFactory:
    """Test service factory."""
    
    def test_get_servicenow_cmdb_service(self):
        """Test getting ServiceNow CMDB service."""
        service = get_integration_service(ExternalSystem.SystemType.SERVICENOW_CMDB)
        assert isinstance(service, IntegrationService)
    
    def test_get_unknown_service(self):
        """Test getting unknown service raises error."""
        with pytest.raises(ValueError, match='No service registered'):
            get_integration_service('unknown_type')


@pytest.mark.django_db
class TestServiceNowCMDBService:
    """Test ServiceNow CMDB service."""
    
    @patch('apps.integrations.services.servicenow.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection test."""
        from apps.integrations.services.servicenow import ServiceNowCMDBService
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        service = ServiceNowCMDBService()
        config = {
            'api_url': 'https://test.service-now.com',
            'auth_type': 'basic',
            'credentials': {'username': 'test', 'password': 'test'},
        }
        
        result = service.test_connection(config)
        
        assert result['status'] == 'success'
        mock_get.assert_called_once()
    
    @patch('apps.integrations.services.servicenow.requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed connection test."""
        from apps.integrations.services.servicenow import ServiceNowCMDBService
        
        mock_get.side_effect = Exception('Connection failed')
        
        service = ServiceNowCMDBService()
        config = {
            'api_url': 'https://test.service-now.com',
            'auth_type': 'basic',
            'credentials': {'username': 'test', 'password': 'test'},
        }
        
        result = service.test_connection(config)
        
        assert result['status'] == 'failed'


@pytest.mark.django_db
class TestEntraIDService:
    """Test Entra ID service."""
    
    @patch('apps.integrations.services.entra_id.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection test."""
        from apps.integrations.services.entra_id import EntraIDService
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        service = EntraIDService()
        config = {
            'api_url': 'https://graph.microsoft.com/v1.0',
            'auth_type': 'oauth2',
            'credentials': {'access_token': 'test-token'},
        }
        
        result = service.test_connection(config)
        
        assert result['status'] == 'success'


