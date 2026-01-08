# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ServiceNow CMDB integration service.

Syncs asset inventory from ServiceNow CMDB tables.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.connectors.models import Asset

logger = logging.getLogger(__name__)


class ServiceNowCMDBService(IntegrationService):
    """ServiceNow CMDB integration service."""
    
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
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
                'details': {
                    'api_version': response.headers.get('X-Total-Count', 'unknown'),
                }
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'ServiceNow connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """
        Sync assets from ServiceNow CMDB.
        
        Args:
            system: ExternalSystem instance
        
        Returns:
            Dict with sync results
        """
        assets = self.fetch_assets(system)
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
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """
        Fetch computer CIs from ServiceNow CMDB.
        
        Args:
            system: ExternalSystem instance
        
        Returns:
            List of asset dictionaries
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
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'result' in data:
                    all_assets.extend(data['result'])
                
                # Check if there are more records
                if len(data.get('result', [])) < params['sysparm_limit']:
                    break
                
                params['sysparm_offset'] += params['sysparm_limit']
                
            except requests.exceptions.RequestException as e:
                logger.error(f'Error fetching ServiceNow assets: {e}')
                raise
        
        return all_assets
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from config."""
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

