# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Jira Assets (formerly Insight) integration service.

Syncs asset inventory from Jira Assets.
Uses resilient HTTP client with circuit breaker protection.
"""
import base64
import logging
from typing import Dict, List, Any, Optional

from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.connectors.models import Asset
from apps.core.http import ResilientHTTPClient
from apps.core.circuit_breaker import CircuitBreakerOpen

logger = logging.getLogger(__name__)


class JiraAssetsService(IntegrationService):
    """
    Jira Assets integration service.
    
    Uses circuit breaker protection and automatic retries for API calls.
    """
    
    SERVICE_NAME = 'jira'
    
    def __init__(self):
        """Initialize Jira service with resilient HTTP client."""
        super().__init__()
        self.http_client = ResilientHTTPClient(
            service_name=self.SERVICE_NAME,
            timeout=30,
            max_retries=3,
        )
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Jira Assets API connectivity."""
        api_url = config['api_url']
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get object types
        test_url = f"{api_url}/rest/insight/1.0/objectschema/list"
        
        try:
            response = self.http_client.get(
                test_url,
                headers=headers,
                timeout=10,
            )
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except CircuitBreakerOpen as e:
            logger.warning(f'Jira circuit breaker open: {e}')
            return {
                'status': 'failed',
                'message': 'Jira service temporarily unavailable (circuit breaker open)',
            }
        except Exception as e:
            logger.error(f'Jira Assets connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync assets from Jira Assets.
        
        Args:
            system: ExternalSystem instance
            correlation_id: Optional correlation ID for audit trail
        
        Returns:
            Dict with sync results
        """
        try:
            assets = self.fetch_assets(system, correlation_id=correlation_id)
        except CircuitBreakerOpen:
            logger.warning('Jira sync aborted: circuit breaker open')
            return {
                'fetched': 0,
                'created': 0,
                'updated': 0,
                'failed': 0,
                'error': 'Jira service temporarily unavailable',
            }
        
        created, updated, failed = 0, 0, 0
        
        for asset_data in assets:
            try:
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=asset_data.get('objectKey'),
                    defaults={
                        'name': asset_data.get('label', 'Unknown'),
                        'serial_number': asset_data.get('serialNumber', ''),
                        'location': asset_data.get('location', ''),
                        'owner': asset_data.get('owner', ''),
                        'status': self._map_status(asset_data.get('status', 'Active')),
                        'type': self._map_type(asset_data.get('objectType', {})),
                        'os': asset_data.get('operatingSystem', ''),
                        'is_demo': False,
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync asset {asset_data.get("objectKey")}: {e}')
                failed += 1
        
        return {
            'fetched': len(assets),
            'created': created,
            'updated': updated,
            'failed': failed,
        }
    
    def fetch_assets(
        self,
        system: ExternalSystem,
        correlation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch assets from Jira Assets.
        
        Uses circuit breaker protection and automatic retries.
        
        Args:
            system: ExternalSystem instance
            correlation_id: Optional correlation ID for audit trail
        
        Returns:
            List of asset dictionaries
        
        Raises:
            CircuitBreakerOpen: If Jira service is unavailable
        """
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        # Get object schema ID from metadata or query
        schema_id = system.metadata.get('object_schema_id')
        if not schema_id:
            # Query for computer schema
            schema_url = f"{api_url}/rest/insight/1.0/objectschema/list"
            response = self.http_client.get(
                schema_url,
                headers=headers,
                correlation_id=correlation_id,
            )
            schemas = response.json()
            # Find computer/device schema
            schema_id = next(
                (s['id'] for s in schemas if 'computer' in s['name'].lower() or 'device' in s['name'].lower()),
                None
            )
        
        if not schema_id:
            raise ValueError('Could not find object schema for assets')
        
        # Fetch objects
        url = f"{api_url}/rest/insight/1.0/object/navlist/{schema_id}"
        params = {'page': 1, 'pageSize': 1000}
        
        all_assets = []
        
        while True:
            response = self.http_client.get(
                url,
                headers=headers,
                params=params,
                correlation_id=correlation_id,
            )
            data = response.json()
            
            if 'objectEntries' in data:
                all_assets.extend(data['objectEntries'])
            
            if not data.get('hasMore', False):
                break
            
            params['page'] += 1
        
        logger.info(
            f'Fetched {len(all_assets)} assets from Jira Assets',
            extra={
                'service': self.SERVICE_NAME,
                'asset_count': len(all_assets),
                'correlation_id': correlation_id,
            }
        )
        
        return all_assets
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from config."""
        credentials = config.get('credentials', {})
        auth_type = config.get('auth_type', 'basic')
        
        if auth_type == 'basic':
            username = credentials.get('username')
            password = credentials.get('password')
            auth_string = f'{username}:{password}'
            encoded = base64.b64encode(auth_string.encode()).decode()
            return {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        elif auth_type == 'token':
            token = credentials.get('api_token')
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        else:
            raise ValueError(f'Unsupported auth_type for Jira: {auth_type}')
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.api_url,
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _map_status(self, status: str) -> str:
        """Map Jira Assets status to Asset status."""
        status_lower = status.lower() if status else ''
        if 'active' in status_lower or 'in use' in status_lower:
            return 'Active'
        elif 'inactive' in status_lower or 'retired' in status_lower:
            return 'Inactive'
        elif 'maintenance' in status_lower:
            return 'Maintenance'
        else:
            return 'Active'
    
    def _map_type(self, object_type: Dict[str, Any]) -> str:
        """Map Jira Assets object type to Asset type."""
        type_name = object_type.get('name', '').lower() if isinstance(object_type, dict) else str(object_type).lower()
        
        if 'laptop' in type_name:
            return 'Laptop'
        elif 'desktop' in type_name or 'workstation' in type_name:
            return 'Desktop'
        elif 'server' in type_name:
            return 'Server'
        elif 'mobile' in type_name or 'phone' in type_name:
            return 'Mobile'
        else:
            return 'Desktop'

