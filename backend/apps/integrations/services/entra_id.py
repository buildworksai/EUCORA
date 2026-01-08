# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Entra ID (Azure AD) integration service.

Syncs users, groups, and device compliance from Microsoft Graph API.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.connectors.models import Asset
from django.contrib.auth.models import User, Group

logger = logging.getLogger(__name__)


class EntraIDService(IntegrationService):
    """Microsoft Entra ID integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Microsoft Graph API connectivity."""
        api_url = config.get('api_url', 'https://graph.microsoft.com/v1.0')
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get current user/service principal
        test_url = f"{api_url}/me"
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Entra ID connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync users, groups, and devices from Entra ID."""
        users_created, users_updated = self.sync_users(system)
        groups_created, groups_updated = self.sync_groups(system)
        devices_created, devices_updated = self.sync_devices(system)
        
        return {
            'fetched': users_created + users_updated + groups_created + groups_updated + devices_created + devices_updated,
            'created': users_created + groups_created + devices_created,
            'updated': users_updated + groups_updated + devices_updated,
            'failed': 0,
        }
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch managed devices from Entra ID."""
        return self._fetch_devices(system)
    
    def sync_users(self, system: ExternalSystem) -> tuple:
        """Sync users from Entra ID."""
        users = self._fetch_users(system)
        created, updated = 0, 0
        
        for user_data in users:
            try:
                email = user_data.get('mail') or user_data.get('userPrincipalName')
                if not email:
                    continue
                
                user, created_flag = User.objects.update_or_create(
                    username=user_data.get('userPrincipalName', email),
                    defaults={
                        'email': email,
                        'first_name': user_data.get('givenName', ''),
                        'last_name': user_data.get('surname', ''),
                        'is_active': user_data.get('accountEnabled', True),
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync user {user_data.get("userPrincipalName")}: {e}')
        
        return created, updated
    
    def sync_groups(self, system: ExternalSystem) -> tuple:
        """Sync groups from Entra ID for RBAC mapping."""
        groups = self._fetch_groups(system)
        created, updated = 0, 0
        
        for group_data in groups:
            try:
                group, created_flag = Group.objects.update_or_create(
                    name=group_data.get('displayName'),
                    defaults={}
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync group {group_data.get("displayName")}: {e}')
        
        return created, updated
    
    def sync_devices(self, system: ExternalSystem) -> tuple:
        """Sync managed devices from Entra ID."""
        devices = self._fetch_devices(system)
        created, updated = 0, 0
        
        for device_data in devices:
            try:
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=device_data.get('id'),
                    defaults={
                        'name': device_data.get('deviceName', 'Unknown'),
                        'type': self._map_device_type(device_data.get('operatingSystem', '')),
                        'os': device_data.get('operatingSystem', ''),
                        'os_version': device_data.get('osVersion', ''),
                        'status': self._map_compliance_status(device_data.get('complianceState', '')),
                        'compliance_score': self._calculate_compliance_score(device_data),
                        'connector_type': 'intune',
                        'connector_object_id': device_data.get('id'),
                        'is_demo': False,
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                logger.error(f'Failed to sync device {device_data.get("id")}: {e}')
        
        return created, updated
    
    def _fetch_users(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch users from Microsoft Graph API."""
        api_url = system.metadata.get('api_url', 'https://graph.microsoft.com/v1.0')
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/users"
        params = {
            '$select': 'id,userPrincipalName,mail,givenName,surname,accountEnabled,department,jobTitle',
            '$top': 999,
        }
        
        all_users = []
        
        while url:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                all_users.extend(data.get('value', []))
                
                # Check for next page
                url = data.get('@odata.nextLink')
                params = {}  # Next link includes all params
                
            except requests.exceptions.RequestException as e:
                logger.error(f'Error fetching Entra ID users: {e}')
                raise
        
        return all_users
    
    def _fetch_groups(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch groups from Microsoft Graph API."""
        api_url = system.metadata.get('api_url', 'https://graph.microsoft.com/v1.0')
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/groups"
        params = {
            '$select': 'id,displayName,description,groupTypes',
            '$top': 999,
        }
        
        all_groups = []
        
        while url:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                all_groups.extend(data.get('value', []))
                
                url = data.get('@odata.nextLink')
                params = {}
                
            except requests.exceptions.RequestException as e:
                logger.error(f'Error fetching Entra ID groups: {e}')
                raise
        
        return all_groups
    
    def _fetch_devices(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch managed devices from Microsoft Graph API."""
        api_url = system.metadata.get('api_url', 'https://graph.microsoft.com/v1.0')
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/deviceManagement/managedDevices"
        params = {
            '$select': 'id,deviceName,operatingSystem,osVersion,complianceState,enrollmentType,lastSyncDateTime',
            '$top': 999,
        }
        
        all_devices = []
        
        while url:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                all_devices.extend(data.get('value', []))
                
                url = data.get('@odata.nextLink')
                params = {}
                
            except requests.exceptions.RequestException as e:
                logger.error(f'Error fetching Entra ID devices: {e}')
                raise
        
        return all_devices
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.metadata.get('api_url', 'https://graph.microsoft.com/v1.0'),
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get OAuth2 authentication headers."""
        credentials = config.get('credentials', {})
        
        # Get access token (in production, handle token refresh)
        access_token = credentials.get('access_token')
        if not access_token:
            raise ValueError('OAuth2 access_token not found in credentials')
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
    
    def _map_device_type(self, os: str) -> str:
        """Map operating system to Asset type."""
        os_lower = os.lower() if os else ''
        if 'windows' in os_lower:
            return 'Desktop'  # or 'Laptop' based on additional data
        elif 'macos' in os_lower or 'mac' in os_lower:
            return 'Laptop'
        elif 'ios' in os_lower or 'ipad' in os_lower:
            return 'Mobile'
        elif 'android' in os_lower:
            return 'Mobile'
        else:
            return 'Desktop'
    
    def _map_compliance_status(self, compliance_state: str) -> str:
        """Map Entra ID compliance state to Asset status."""
        mapping = {
            'compliant': 'Active',
            'noncompliant': 'Active',  # Still active, just non-compliant
            'inGracePeriod': 'Active',
            'error': 'Inactive',
            'configManager': 'Active',
        }
        return mapping.get(compliance_state.lower(), 'Active')
    
    def _calculate_compliance_score(self, device_data: Dict[str, Any]) -> int:
        """Calculate compliance score from device data."""
        compliance_state = device_data.get('complianceState', '').lower()
        
        if compliance_state == 'compliant':
            return 100
        elif compliance_state == 'noncompliant':
            return 50
        elif compliance_state == 'ingraceperiod':
            return 75
        else:
            return 0


