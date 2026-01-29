# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Apple Business Manager (ABM) integration service.

Syncs device enrollment and app licensing from ABM API.
"""
import logging
from typing import Any, Dict, List

import requests

from apps.connectors.models import Asset
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class AppleBusinessManagerService(IntegrationService):
    """Apple Business Manager integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test ABM API connectivity."""
        api_url = config.get("api_url", "https://api.apple.com/v1")
        headers = self._get_auth_headers(config)

        # Test endpoint: Get server tokens
        test_url = f"{api_url}/devices"

        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"ABM connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync devices and app licenses from ABM."""
        devices_created, devices_updated = self.sync_devices(system)
        licenses_created, licenses_updated = self.sync_licenses(system)

        return {
            "fetched": devices_created + devices_updated + licenses_created + licenses_updated,
            "created": devices_created + licenses_created,
            "updated": devices_updated + licenses_updated,
            "failed": 0,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch enrolled devices from ABM."""
        return self._fetch_devices(system)

    def sync_devices(self, system: ExternalSystem) -> tuple:
        """Sync enrolled devices from ABM."""
        devices = self._fetch_devices(system)
        created, updated = 0, 0

        for device_data in devices:
            try:
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=device_data.get("serialNumber"),
                    defaults={
                        "name": device_data.get("deviceName", "Unknown"),
                        "serial_number": device_data.get("serialNumber", ""),
                        "type": self._map_device_type(device_data.get("model", "")),
                        "os": self._map_os(device_data.get("model", "")),
                        "status": "Active",
                        "connector_type": "abm",
                        "connector_object_id": device_data.get("serialNumber"),
                        "is_demo": False,
                    },
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f'Failed to sync ABM device {device_data.get("serialNumber")}: {e}')

        return created, updated

    def sync_licenses(self, system: ExternalSystem) -> tuple:
        """Sync VPP app licenses from ABM."""
        # This would sync license counts to Application model
        # Placeholder implementation
        return 0, 0

    def _fetch_devices(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch devices from ABM API."""
        api_url = system.metadata.get("api_url", "https://api.apple.com/v1")
        headers = self._get_auth_headers_from_system(system)

        url = f"{api_url}/devices"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            return data.get("devices", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ABM devices: {e}")
            raise

    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            "api_url": system.metadata.get("api_url", "https://api.apple.com/v1"),
            "auth_type": system.auth_type,
            "credentials": system.credentials,
        }
        return self._get_auth_headers(config)

    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get server token authentication headers."""
        credentials = config.get("credentials", {})
        server_token = credentials.get("server_token")

        if not server_token:
            raise ValueError("ABM server_token not found in credentials")

        return {
            "Authorization": f"Bearer {server_token}",
            "Content-Type": "application/json",
        }

    def _map_device_type(self, model: str) -> str:
        """Map ABM device model to Asset type."""
        model_lower = model.lower() if model else ""
        if "iphone" in model_lower:
            return "Mobile"
        elif "ipad" in model_lower:
            return "Mobile"
        elif "mac" in model_lower:
            return "Laptop"
        else:
            return "Mobile"

    def _map_os(self, model: str) -> str:
        """Map ABM device model to OS."""
        model_lower = model.lower() if model else ""
        if "iphone" in model_lower:
            return "iOS"
        elif "ipad" in model_lower:
            return "iPadOS"
        elif "mac" in model_lower:
            return "macOS"
        else:
            return "iOS"
