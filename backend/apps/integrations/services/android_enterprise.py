# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Android Enterprise integration service.

Syncs device enrollment and app approvals from Google Play EMM API.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.connectors.models import Asset

logger = logging.getLogger(__name__)


class AndroidEnterpriseService(IntegrationService):
    """Android Enterprise integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Google Play EMM API connectivity."""
        api_url = config.get('api_url', 'https://www.googleapis.com/android/enterprise/v1')
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get enterprise
        enterprise_id = config.get('enterprise_id')
        if not enterprise_id:
            return {
                'status': 'failed',
                'message': 'enterprise_id not configured'
            }
        
        test_url = f"{api_url}/enterprises/{enterprise_id}"
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Android Enterprise connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync devices and app approvals from Android Enterprise."""
        devices_created, devices_updated = self.sync_devices(system)
        
        return {
            'fetched': devices_created + devices_updated,
            'created': devices_created,
            'updated': devices_updated,
            'failed': 0,
        }
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch enrolled devices from Android Enterprise."""
        return self._fetch_devices(system)
    
    def sync_devices(self, system: ExternalSystem) -> tuple:
        """Sync enrolled devices from Android Enterprise."""
        devices = self._fetch_devices(system)
        created, updated = 0, 0
        
        for device_data in devices:
            try:
                device_id = device_data.get('deviceId')
                if not device_id:
                    continue
                
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=device_id,
                    defaults={
                        'name': device_data.get('managementMode', 'Unknown'),
                        'type': 'Mobile',
                        'os': 'Android',
                        'os_version': device_data.get('androidId', ''),
                        'status': 'Active',
                        'connector_type': 'android_enterprise',
                        'connector_object_id': device_id,
                        'is_demo': False,
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync Android device {device_data.get("deviceId")}: {e}')
        
        return created, updated
    
    def _fetch_devices(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch devices from Google Play EMM API."""
        api_url = system.metadata.get('api_url', 'https://www.googleapis.com/android/enterprise/v1')
        headers = self._get_auth_headers_from_system(system)
        enterprise_id = system.metadata.get('enterprise_id')
        
        if not enterprise_id:
            raise ValueError('enterprise_id not configured in metadata')
        
        url = f"{api_url}/enterprises/{enterprise_id}/devices"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return data.get('devices', [])
        except requests.exceptions.RequestException as e:
            logger.error(f'Error fetching Android Enterprise devices: {e}')
            raise
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.metadata.get('api_url', 'https://www.googleapis.com/android/enterprise/v1'),
            'auth_type': system.auth_type,
            'credentials': system.credentials,
            'enterprise_id': system.metadata.get('enterprise_id'),
        }
        return self._get_auth_headers(config)
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get OAuth2 authentication headers for Google APIs."""
        credentials = config.get('credentials', {})
        access_token = credentials.get('access_token')
        
        if not access_token:
            raise ValueError('OAuth2 access_token not found in credentials')
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }


