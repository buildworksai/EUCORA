# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
1E DEX Platform API client.

Implements the 1E Consumer API for fetching DEX metrics.
Supports NTLM and Basic authentication.
"""
import logging
from typing import AsyncGenerator, Dict, Optional

import httpx
from httpx_ntlm import HttpNtlmAuth

from apps.integrations.dex.clients.base import DEXClientBase

logger = logging.getLogger(__name__)


class OneEAPIClient(DEXClientBase):
    """
    Client for 1E Consumer API.

    Handles authentication, pagination, rate limiting, and error classification.
    """

    def __init__(self, config):
        """
        Initialize 1E API client.

        Args:
            config: DEXProvider instance with connection configuration
        """
        self.config = config
        self.base_url = config.server_url.rstrip("/") if config.server_url else ""
        self._client = None

    def _get_auth(self):
        """Get authentication handler based on config."""
        if self.config.auth_method == self.config.AuthMethod.NTLM:
            return HttpNtlmAuth(self.config.username, self.config.password)
        elif self.config.auth_method == self.config.AuthMethod.BASIC:
            return httpx.BasicAuth(self.config.username, self.config.password)
        elif self.config.auth_method == self.config.AuthMethod.API_KEY:
            # API key auth via header
            return None
        return None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including API key if configured."""
        headers = {"Content-Type": "application/json"}
        if self.config.auth_method == self.config.AuthMethod.API_KEY and self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make authenticated request to 1E API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (relative to /Consumer/)
            **kwargs: Additional request arguments

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"{self.base_url}/Consumer/{endpoint.lstrip('/')}"
        auth = self._get_auth()
        headers = self._get_headers()

        async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def get_devices(self, page: int = 1, page_size: int = 100) -> Dict:
        """
        Get device list from 1E.

        Args:
            page: Page number (1-indexed)
            page_size: Number of devices per page

        Returns:
            Device list response
        """
        return await self._request(
            "GET",
            "Devices",
            params={"page": page, "pageSize": page_size},
        )

    async def get_device_metrics(self, device_id: str) -> Dict:
        """
        Get DEX metrics for a specific device.

        Args:
            device_id: Device identifier

        Returns:
            Device experience metrics
        """
        return await self._request("GET", f"Devices/{device_id}/Experience")

    async def get_experience_scores(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream experience scores for all devices.

        Handles pagination automatically.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Yields:
            Device experience score dictionaries
        """
        page = 1
        while True:
            try:
                result = await self._request(
                    "GET",
                    "Experience/Scores",
                    params={
                        "page": page,
                        "pageSize": 100,
                        "startDate": start_date,
                        "endDate": end_date,
                    },
                )

                # Handle different response formats
                data = result.get("data") or result.get("devices") or result.get("value", [])

                if not data:
                    break

                for device in data:
                    # Normalize device data to consistent format
                    yield {
                        "device_id": device.get("deviceId") or device.get("id", ""),
                        "device_name": device.get("deviceName") or device.get("name", ""),
                        "dex_score": device.get("dexScore") or device.get("dex_score"),
                        "performance_score": device.get("performanceScore") or device.get("performance_score"),
                        "stability_score": device.get("stabilityScore") or device.get("stability_score"),
                        "responsiveness_score": device.get("responsivenessScore") or device.get("responsiveness_score"),
                        "boot_time_seconds": device.get("bootTimeSeconds") or device.get("boot_time_seconds"),
                        "login_time_seconds": device.get("loginTimeSeconds") or device.get("login_time_seconds"),
                        "user_sentiment": device.get("userSentiment") or device.get("user_sentiment", ""),
                        "sentiment_score": device.get("sentimentScore") or device.get("sentiment_score"),
                        "carbon_footprint_kg": device.get("carbonFootprintKg") or device.get("carbon_footprint_kg"),
                        "power_consumption_kwh": device.get("powerConsumptionKwh")
                        or device.get("power_consumption_kwh"),
                        "collected_at": device.get("collectedAt") or device.get("collected_at"),
                    }

                # Check for next page
                next_link = result.get("@odata.nextLink") or result.get("next")
                if not next_link:
                    break

                page += 1

            except httpx.HTTPError as e:
                logger.error(f"Error fetching experience scores page {page}: {e}")
                raise

    async def get_sustainability_metrics(self) -> Dict:
        """
        Get Green IT / sustainability metrics.

        Returns:
            Sustainability metrics response
        """
        return await self._request("GET", "Sustainability/Metrics")

    async def health_check(self) -> bool:
        """
        Check 1E API connectivity.

        Returns:
            True if API is reachable, False otherwise
        """
        try:
            await self._request("GET", "System/Health")
            return True
        except Exception as e:
            logger.warning(f"1E API health check failed: {e}")
            return False
