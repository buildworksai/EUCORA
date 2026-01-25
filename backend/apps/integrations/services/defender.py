# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Defender for Endpoint integration service.

Syncs device vulnerabilities and threat intelligence.
"""
import logging
from typing import Any, Dict, List

import requests

from apps.connectors.models import Asset
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class DefenderForEndpointService(IntegrationService):
    """Microsoft Defender for Endpoint integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Microsoft Graph Security API connectivity."""
        api_url = config.get("api_url", "https://graph.microsoft.com/v1.0")
        headers = self._get_auth_headers(config)

        # Test endpoint: Get security alerts
        test_url = f"{api_url}/security/alerts"
        params = {"$top": 1}

        try:
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Defender for Endpoint connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync device vulnerabilities from Defender for Endpoint."""
        vulnerabilities = self.fetch_vulnerabilities(system)
        updated = 0
        failed = 0

        for vuln_data in vulnerabilities:
            try:
                device_id = vuln_data.get("deviceId")
                if not device_id:
                    continue

                # Update asset with vulnerability data
                asset = Asset.objects.filter(connector_object_id=device_id).first()
                if asset:
                    # Enrich compliance score based on vulnerabilities
                    vuln_count = vuln_data.get("vulnerabilityCount", 0)
                    if vuln_count > 0:
                        asset.compliance_score = max(0, asset.compliance_score - (vuln_count * 5))
                        asset.save()
                        updated += 1

            except Exception as e:
                logger.error(f"Failed to sync Defender vulnerability: {e}")
                failed += 1

        return {
            "fetched": len(vulnerabilities),
            "created": 0,
            "updated": updated,
            "failed": failed,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch devices with vulnerabilities from Defender."""
        return self.fetch_vulnerabilities(system)

    def fetch_vulnerabilities(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch device vulnerabilities from Defender for Endpoint."""
        api_url = system.metadata.get("api_url", "https://graph.microsoft.com/v1.0")
        headers = self._get_auth_headers_from_system(system)

        url = f"{api_url}/security/secureScoreControlProfiles"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # This is a simplified implementation
            # In production, would query specific vulnerability endpoints
            return data.get("value", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Defender vulnerabilities: {e}")
            raise

    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            "api_url": system.metadata.get("api_url", "https://graph.microsoft.com/v1.0"),
            "auth_type": system.auth_type,
            "credentials": system.credentials,
        }
        return self._get_auth_headers(config)

    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get OAuth2 authentication headers."""
        credentials = config.get("credentials", {})
        access_token = credentials.get("access_token")

        if not access_token:
            raise ValueError("OAuth2 access_token not found in credentials")

        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
