# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Freshservice CMDB integration service.

Syncs asset inventory from Freshservice CMDB.
"""
import logging
from typing import Any, Dict, List

import requests

from apps.connectors.models import Asset
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class FreshserviceCMDBService(IntegrationService):
    """Freshservice CMDB integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Freshservice API connectivity."""
        api_url = config["api_url"]
        headers = self._get_auth_headers(config)

        # Test endpoint: Get asset types
        test_url = f"{api_url}/api/v2/assets"
        params = {"per_page": 1}

        try:
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Freshservice connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync assets from Freshservice CMDB."""
        assets = self.fetch_assets(system)
        created, updated, failed = 0, 0, 0

        for asset_data in assets:
            try:
                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=str(asset_data.get("display_id", asset_data.get("id"))),
                    defaults={
                        "name": asset_data.get("name", "Unknown"),
                        "serial_number": asset_data.get("serial_number", ""),
                        "location": (
                            asset_data.get("location", {}).get("name", "")
                            if isinstance(asset_data.get("location"), dict)
                            else asset_data.get("location", "")
                        ),
                        "owner": (
                            asset_data.get("assigned_on", {}).get("name", "")
                            if isinstance(asset_data.get("assigned_on"), dict)
                            else asset_data.get("assigned_on", "")
                        ),
                        "status": self._map_status(asset_data.get("asset_state_id", 1)),
                        "type": self._map_type(asset_data.get("asset_type_id", 0)),
                        "os": asset_data.get("operating_system", ""),
                        "is_demo": False,
                    },
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f'Failed to sync asset {asset_data.get("id")}: {e}')
                failed += 1

        return {
            "fetched": len(assets),
            "created": created,
            "updated": updated,
            "failed": failed,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch assets from Freshservice CMDB."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)

        url = f"{api_url}/api/v2/assets"
        params = {"per_page": 100, "page": 1}

        all_assets = []

        while True:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if "assets" in data:
                    all_assets.extend(data["assets"])

                # Check pagination
                if not data.get("meta", {}).get("has_more", False):
                    break

                params["page"] += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching Freshservice assets: {e}")
                raise

        return all_assets

    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from config."""
        credentials = config.get("credentials", {})
        api_key = credentials.get("api_key")

        if not api_key:
            raise ValueError("Freshservice API key not found in credentials")

        return {
            "Authorization": f"Basic {api_key}:X",  # Freshservice uses API key as username
            "Content-Type": "application/json",
        }

    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            "api_url": system.api_url,
            "auth_type": system.auth_type,
            "credentials": system.credentials,
        }
        return self._get_auth_headers(config)

    def _map_status(self, state_id: int) -> str:
        """Map Freshservice asset_state_id to Asset status."""
        mapping = {
            1: "Active",  # In Use
            2: "Inactive",  # In Stock
            3: "Inactive",  # In Transit
            4: "Retired",  # Retired
            5: "Maintenance",  # Under Maintenance
        }
        return mapping.get(state_id, "Active")

    def _map_type(self, type_id: int) -> str:
        """Map Freshservice asset_type_id to Asset type."""
        # Type IDs vary by Freshservice instance, use metadata mapping if available
        # Default mapping for common types
        mapping = {
            1: "Desktop",  # Desktop
            2: "Laptop",  # Laptop
            3: "Server",  # Server
            4: "Mobile",  # Mobile Device
        }
        return mapping.get(type_id, "Desktop")
