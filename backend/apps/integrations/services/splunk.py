# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Splunk integration service.

Sends logs and events to Splunk via HTTP Event Collector (HEC).
"""
import logging
from typing import Any, Dict, List

import requests

from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class SplunkService(IntegrationService):
    """Splunk integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Splunk HEC connectivity."""
        hec_url = config.get("hec_url")
        headers = self._get_auth_headers(config)

        if not hec_url:
            return {"status": "failed", "message": "hec_url not configured"}

        # Test endpoint: Send a test event
        test_url = f"{hec_url}/services/collector/event"
        payload = {
            "event": {"test": "connection"},
            "sourcetype": "eucora_test",
        }

        try:
            response = requests.post(test_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Splunk connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Monitoring services don't sync."""
        return {
            "fetched": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Monitoring services don't fetch assets."""
        return []

    def send_event(
        self, system: ExternalSystem, event: Dict[str, Any], sourcetype: str = "eucora:deployment", index: str = None
    ) -> Dict[str, Any]:
        """Send an event to Splunk via HEC."""
        hec_url = system.metadata.get("hec_url", system.api_url)
        headers = self._get_auth_headers_from_system(system)

        url = f"{hec_url}/services/collector/event"

        payload = {
            "event": event,
            "sourcetype": sourcetype,
        }

        if index:
            payload["index"] = index

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            return {"status": "success"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Splunk event: {e}")
            raise

    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            "hec_url": system.metadata.get("hec_url", system.api_url),
            "auth_type": system.auth_type,
            "credentials": system.credentials,
        }
        return self._get_auth_headers(config)

    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get HEC token authentication headers."""
        credentials = config.get("credentials", {})
        hec_token = credentials.get("hec_token")

        if not hec_token:
            raise ValueError("Splunk HEC token not found in credentials")

        return {
            "Authorization": f"Splunk {hec_token}",
            "Content-Type": "application/json",
        }
