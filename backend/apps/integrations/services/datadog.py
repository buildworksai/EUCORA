# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Datadog integration service.

Pushes deployment metrics and events to Datadog.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class DatadogService(IntegrationService):
    """Datadog integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Datadog API connectivity."""
        api_url = config.get('api_url', 'https://api.datadoghq.com/api/v1')
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Validate API key
        test_url = f"{api_url}/validate"
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Datadog connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Monitoring services don't sync - they push data."""
        return {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
        }
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Monitoring services don't fetch assets."""
        return []
    
    def push_metric(
        self,
        system: ExternalSystem,
        metric_name: str,
        value: float,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Push a custom metric to Datadog."""
        api_url = system.metadata.get('api_url', 'https://api.datadoghq.com/api/v1')
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/series"
        
        payload = {
            'series': [{
                'metric': metric_name,
                'points': [[int(__import__('time').time()), value]],
                'tags': tags or [],
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return {'status': 'success'}
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to push Datadog metric: {e}')
            raise
    
    def push_event(
        self,
        system: ExternalSystem,
        title: str,
        text: str,
        tags: List[str] = None,
        alert_type: str = 'info'
    ) -> Dict[str, Any]:
        """Push an event to Datadog."""
        api_url = system.metadata.get('api_url', 'https://api.datadoghq.com/api/v1')
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/events"
        
        payload = {
            'title': title,
            'text': text,
            'tags': tags or [],
            'alert_type': alert_type,  # info, warning, error, success
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return {'status': 'success'}
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to push Datadog event: {e}')
            raise
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.metadata.get('api_url', 'https://api.datadoghq.com/api/v1'),
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get API key authentication headers."""
        credentials = config.get('credentials', {})
        api_key = credentials.get('api_key')
        app_key = credentials.get('app_key')
        
        if not api_key:
            raise ValueError('Datadog API key not found in credentials')
        
        headers = {
            'DD-API-KEY': api_key,
            'Content-Type': 'application/json',
        }
        
        if app_key:
            headers['DD-APPLICATION-KEY'] = app_key
        
        return headers


