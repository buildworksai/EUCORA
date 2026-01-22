# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ServiceNow CMDB integration service.

Syncs asset inventory from ServiceNow CMDB tables.
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


class ServiceNowCMDBService(IntegrationService):
    """
    ServiceNow CMDB integration service.
    
    Uses circuit breaker protection and automatic retries for API calls.
    """
    
    SERVICE_NAME = 'servicenow'
    
    def __init__(self):
        """Initialize ServiceNow service with resilient HTTP client."""
        super().__init__()
        self.http_client = ResilientHTTPClient(
            service_name=self.SERVICE_NAME,
            timeout=30,
            max_retries=3,
        )
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test ServiceNow API connectivity.
        
        Args:
            config: Configuration with api_url, credentials, etc.
        
        Returns:
            Dict with 'status' and 'message'
        """
        api_url = config['api_url']
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get a single CI
        test_url = f"{api_url}/api/now/table/cmdb_ci_computer"
        params = {'sysparm_limit': 1}
        
        try:
            response = self.http_client.get(
                test_url,
                headers=headers,
                params=params,
                timeout=10,
            )
            
            return {
                'status': 'success',
                'message': 'Connection successful',
                'details': {
                    'api_version': response.headers.get('X-Total-Count', 'unknown'),
                }
            }
        except CircuitBreakerOpen as e:
            logger.warning(f'ServiceNow circuit breaker open: {e}')
            return {
                'status': 'failed',
                'message': 'ServiceNow service temporarily unavailable (circuit breaker open)',
            }
        except Exception as e:
            logger.error(f'ServiceNow connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync assets from ServiceNow CMDB.
        
        Args:
            system: ExternalSystem instance
            correlation_id: Optional correlation ID for audit trail
        
        Returns:
            Dict with sync results
        """
        try:
            assets = self.fetch_assets(system, correlation_id=correlation_id)
        except CircuitBreakerOpen:
            logger.warning('ServiceNow sync aborted: circuit breaker open')
            return {
                'fetched': 0,
                'created': 0,
                'updated': 0,
                'failed': 0,
                'error': 'ServiceNow service temporarily unavailable',
            }
        
        created, updated, failed = 0, 0, 0
        
        for asset_data in assets:
            try:
                # Map ServiceNow fields to Asset model
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=asset_data.get('sys_id'),
                    defaults={
                        'name': asset_data.get('name', 'Unknown'),
                        'serial_number': asset_data.get('serial_number', ''),
                        'location': asset_data.get('location', {}).get('display_value', ''),
                        'owner': asset_data.get('assigned_to', {}).get('display_value', ''),
                        'status': self._map_status(asset_data.get('install_status', '1')),
                        'type': self._map_type(asset_data.get('category', '')),
                        'os': asset_data.get('os', '') or asset_data.get('os_version', ''),
                        'is_demo': False,
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync asset {asset_data.get("sys_id")}: {e}')
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
        Fetch computer CIs from ServiceNow CMDB.
        
        Uses circuit breaker protection and automatic retries.
        
        Args:
            system: ExternalSystem instance
            correlation_id: Optional correlation ID for audit trail
        
        Returns:
            List of asset dictionaries
        
        Raises:
            CircuitBreakerOpen: If ServiceNow service is unavailable
        """
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        # Query active computer CIs
        url = f"{api_url}/api/now/table/cmdb_ci_computer"
        params = {
            'sysparm_query': 'install_status=1',  # Active
            'sysparm_limit': 10000,
            'sysparm_offset': 0,
        }
        
        all_assets = []
        
        while True:
            response = self.http_client.get(
                url,
                headers=headers,
                params=params,
                correlation_id=correlation_id,
            )
            data = response.json()
            
            if 'result' in data:
                all_assets.extend(data['result'])
            
            # Check if there are more records
            if len(data.get('result', [])) < params['sysparm_limit']:
                break
            
            params['sysparm_offset'] += params['sysparm_limit']
        
        logger.info(
            f'Fetched {len(all_assets)} assets from ServiceNow',
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
        elif auth_type == 'oauth2':
            token = credentials.get('access_token')
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        else:
            raise ValueError(f'Unsupported auth_type for ServiceNow: {auth_type}')
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.api_url,
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _map_status(self, install_status: str) -> str:
        """Map ServiceNow install_status to Asset status."""
        mapping = {
            '1': 'Active',
            '2': 'Inactive',
            '3': 'Retired',
            '6': 'Maintenance',
        }
        return mapping.get(str(install_status), 'Active')
    
    def _map_type(self, category: str) -> str:
        """Map ServiceNow category to Asset type."""
        category_lower = category.lower() if category else ''
        
        if 'laptop' in category_lower:
            return 'Laptop'
        elif 'desktop' in category_lower or 'workstation' in category_lower:
            return 'Desktop'
        elif 'server' in category_lower:
            return 'Server'
        elif 'mobile' in category_lower or 'phone' in category_lower:
            return 'Mobile'
        else:
            return 'Desktop'  # Default

