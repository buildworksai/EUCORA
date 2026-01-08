# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Elastic (ELK Stack) integration service.

Sends logs to Elasticsearch for indexing and analysis.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class ElasticService(IntegrationService):
    """Elastic integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Elasticsearch API connectivity."""
        api_url = config.get('api_url', 'http://localhost:9200')
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Cluster health
        test_url = f"{api_url}/_cluster/health"
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Elastic connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Monitoring services don't sync."""
        return {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
        }
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Monitoring services don't fetch assets."""
        return []
    
    def index_document(
        self,
        system: ExternalSystem,
        index: str,
        document: Dict[str, Any],
        document_id: str = None
    ) -> Dict[str, Any]:
        """Index a document in Elasticsearch."""
        api_url = system.metadata.get('api_url', system.api_url)
        headers = self._get_auth_headers_from_system(system)
        
        if document_id:
            url = f"{api_url}/{index}/_doc/{document_id}"
            method = 'PUT'
        else:
            url = f"{api_url}/{index}/_doc"
            method = 'POST'
        
        try:
            response = requests.request(method, url, headers=headers, json=document, timeout=30)
            response.raise_for_status()
            
            return {'status': 'success', 'id': response.json().get('_id')}
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to index Elastic document: {e}')
            raise
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.metadata.get('api_url', system.api_url),
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers."""
        credentials = config.get('credentials', {})
        auth_type = config.get('auth_type', 'basic')
        
        if auth_type == 'basic':
            username = credentials.get('username')
            password = credentials.get('password')
            import base64
            auth_string = f'{username}:{password}'
            encoded = base64.b64encode(auth_string.encode()).decode()
            return {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json',
            }
        elif auth_type == 'token':
            api_key = credentials.get('api_key')
            return {
                'Authorization': f'ApiKey {api_key}',
                'Content-Type': 'application/json',
            }
        else:
            return {'Content-Type': 'application/json'}


