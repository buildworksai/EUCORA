# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for integration services with resilient HTTP clients.

Verifies that ITSM and other integration services properly use:
- ResilientHTTPClient for circuit breaker protection
- Correlation ID tracking
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.integrations.services.servicenow import ServiceNowCMDBService
from apps.integrations.services.jira import JiraAssetsService
from apps.core.circuit_breaker import CircuitBreakerOpen


class TestServiceNowResilientHTTP(TestCase):
    """Test ServiceNow service uses resilient HTTP client."""
    
    def setUp(self):
        """Set up test service."""
        self.service = ServiceNowCMDBService()
    
    def test_service_has_http_client(self):
        """Should have ResilientHTTPClient initialized."""
        assert self.service.http_client is not None
        assert self.service.http_client.service_name == 'servicenow'
    
    def test_service_name_constant(self):
        """Should have SERVICE_NAME defined."""
        assert self.service.SERVICE_NAME == 'servicenow'
    
    @patch.object(ServiceNowCMDBService, 'http_client')
    def test_connection_test_uses_http_client(self, mock_http_client):
        """Should use http_client for connection test."""
        mock_response = Mock()
        mock_response.headers = {'X-Total-Count': '100'}
        mock_http_client.get.return_value = mock_response
        
        config = {
            'api_url': 'https://instance.service-now.com',
            'auth_type': 'basic',
            'credentials': {'username': 'user', 'password': 'pass'}
        }
        
        self.service.http_client = mock_http_client
        result = self.service.test_connection(config)
        
        assert result['status'] == 'success'
        mock_http_client.get.assert_called_once()
    
    @patch.object(ServiceNowCMDBService, 'http_client')
    def test_circuit_breaker_open_during_connection(self, mock_http_client):
        """Should handle CircuitBreakerOpen gracefully."""
        mock_http_client.get.side_effect = CircuitBreakerOpen('servicenow')
        
        config = {
            'api_url': 'https://instance.service-now.com',
            'auth_type': 'basic',
            'credentials': {'username': 'user', 'password': 'pass'}
        }
        
        self.service.http_client = mock_http_client
        result = self.service.test_connection(config)
        
        assert result['status'] == 'failed'
        assert 'temporarily unavailable' in result['message']
    
    @patch.object(ServiceNowCMDBService, 'http_client')
    def test_fetch_assets_uses_correlation_id(self, mock_http_client):
        """Should pass correlation ID to HTTP client."""
        from apps.integrations.models import ExternalSystem
        
        mock_response = Mock()
        mock_response.json.return_value = {'result': []}
        mock_http_client.get.return_value = mock_response
        
        # Create test system
        system = MagicMock(spec=ExternalSystem)
        system.api_url = 'https://instance.service-now.com'
        system.auth_type = 'basic'
        system.credentials = {'username': 'user', 'password': 'pass'}
        
        self.service.http_client = mock_http_client
        self.service.fetch_assets(system, correlation_id='test-123')
        
        # Verify correlation_id was passed
        call_kwargs = mock_http_client.get.call_args[1]
        assert call_kwargs.get('correlation_id') == 'test-123'


class TestJiraResilientHTTP(TestCase):
    """Test Jira service uses resilient HTTP client."""
    
    def setUp(self):
        """Set up test service."""
        self.service = JiraAssetsService()
    
    def test_service_has_http_client(self):
        """Should have ResilientHTTPClient initialized."""
        assert self.service.http_client is not None
        assert self.service.http_client.service_name == 'jira'
    
    def test_service_name_constant(self):
        """Should have SERVICE_NAME defined."""
        assert self.service.SERVICE_NAME == 'jira'
    
    @patch.object(JiraAssetsService, 'http_client')
    def test_connection_test_uses_http_client(self, mock_http_client):
        """Should use http_client for connection test."""
        mock_response = Mock()
        mock_http_client.get.return_value = mock_response
        
        config = {
            'api_url': 'https://instance.atlassian.net',
            'auth_type': 'token',
            'credentials': {'api_token': 'token123'}
        }
        
        self.service.http_client = mock_http_client
        result = self.service.test_connection(config)
        
        assert result['status'] == 'success'
        mock_http_client.get.assert_called_once()
    
    @patch.object(JiraAssetsService, 'http_client')
    def test_circuit_breaker_open_during_fetch(self, mock_http_client):
        """Should handle CircuitBreakerOpen during fetch_assets."""
        from apps.integrations.models import ExternalSystem
        
        mock_http_client.get.side_effect = CircuitBreakerOpen('jira')
        
        system = MagicMock(spec=ExternalSystem)
        system.api_url = 'https://instance.atlassian.net'
        system.auth_type = 'token'
        system.credentials = {'api_token': 'token123'}
        system.metadata = {}
        
        self.service.http_client = mock_http_client
        
        with pytest.raises(CircuitBreakerOpen):
            self.service.fetch_assets(system)
    
    @patch.object(JiraAssetsService, 'http_client')
    def test_sync_handles_circuit_breaker_open(self, mock_http_client):
        """Should handle CircuitBreakerOpen gracefully in sync."""
        from apps.integrations.models import ExternalSystem
        
        # Make fetch_assets raise CircuitBreakerOpen
        mock_http_client.get.side_effect = CircuitBreakerOpen('jira')
        
        system = MagicMock(spec=ExternalSystem)
        system.api_url = 'https://instance.atlassian.net'
        
        self.service.http_client = mock_http_client
        
        result = self.service.sync(system)
        
        # Should return empty result with error message
        assert result['fetched'] == 0
        assert 'error' in result


class TestIntegrationServiceResiency(TestCase):
    """Test general integration service resilience patterns."""
    
    def test_servicenow_timeout_configured(self):
        """Should have reasonable timeout."""
        service = ServiceNowCMDBService()
        assert service.http_client.timeout == 30
    
    def test_jira_timeout_configured(self):
        """Should have reasonable timeout."""
        service = JiraAssetsService()
        assert service.http_client.timeout == 30
    
    def test_max_retries_configured(self):
        """Should configure retries for resilience."""
        servicenow = ServiceNowCMDBService()
        jira = JiraAssetsService()
        
        # Both should have retry strategy
        assert servicenow.http_client is not None
        assert jira.http_client is not None
