# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ServiceNow Request API Client.

Provides async interface for request operations including
query, sync, and status updates.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from apps.cmdb_integration.models import CMDBConnection

logger = logging.getLogger(__name__)


class ServiceNowRequestClient:
    """
    Async client for ServiceNow Request API.

    Supports:
    - Basic, OAuth, and API key authentication
    - Query requests (sc_request table)
    - Status updates
    - SLA tracking
    """

    def __init__(self, connection: CMDBConnection):
        """
        Initialize ServiceNow Request client.

        Args:
            connection: CMDBConnection model instance (reuses CMDB connection)
        """
        self.connection = connection
        self.instance_url = connection.instance_url.rstrip("/")
        self.auth_type = connection.auth_type
        self.credentials = connection.credentials
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self._client is None:
            auth = None
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            if self.auth_type == "basic":
                auth = httpx.BasicAuth(
                    username=self.credentials.get("username", ""),
                    password=self.credentials.get("password", ""),
                )
            elif self.auth_type == "api_key":
                headers["Authorization"] = f"Bearer {self.credentials.get('api_key', '')}"
            elif self.auth_type == "oauth":
                headers["Authorization"] = f"Bearer {self.credentials.get('access_token', '')}"

            self._client = httpx.AsyncClient(
                base_url=self.instance_url,
                auth=auth,
                headers=headers,
                timeout=30.0,
            )

        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_request(self, sys_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single request by sys_id.

        Args:
            sys_id: ServiceNow sys_id

        Returns:
            Request record as dict or None if not found
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/now/table/sc_request/{sys_id}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()
            return data.get("result")

        except Exception as e:
            logger.error(f"Failed to get request {sys_id}: {e}")
            raise

    async def query_requests(
        self,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query requests from ServiceNow.

        Args:
            query: Encoded query string (e.g., "state=2^active=true")
            fields: List of fields to return
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of request records
        """
        try:
            client = await self._get_client()
            params = {
                "sysparm_limit": limit,
                "sysparm_offset": offset,
            }

            if query:
                params["sysparm_query"] = query
            if fields:
                params["sysparm_fields"] = ",".join(fields)

            response = await client.get("/api/now/table/sc_request", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])

        except Exception as e:
            logger.error(f"Failed to query requests: {e}")
            raise

    async def get_sla_info(self, sys_id: str) -> Optional[Dict[str, Any]]:
        """
        Get SLA information for a request.

        Args:
            sys_id: Request sys_id

        Returns:
            SLA information dict or None
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"/api/now/table/task_sla",
                params={"sysparm_query": f"task={sys_id}^type=1", "sysparm_fields": "task,sla,due_date,state"},
            )

            response.raise_for_status()
            data = response.json()
            results = data.get("result", [])
            if results:
                return results[0]  # Return first SLA
            return None

        except Exception as e:
            logger.error(f"Failed to get SLA info for {sys_id}: {e}")
            return None


class MockServiceNowRequestClient:
    """
    Mock ServiceNow Request client for development/testing.

    Returns mock request data without requiring ServiceNow instance.
    """

    def __init__(self, connection: CMDBConnection):
        """Initialize mock client."""
        self.connection = connection

    async def close(self) -> None:
        """No-op for mock client."""
        pass

    async def get_request(self, sys_id: str) -> Optional[Dict[str, Any]]:
        """Return mock request."""
        return {
            "sys_id": sys_id,
            "number": f"REQ{int(sys_id[:8], 16)}",
            "short_description": "Mock Software Installation Request",
            "requestor": {"email": "user@example.com", "name": "Test User"},
            "assigned_to": {"name": "IT Support"},
            "assignment_group": {"name": "IT Operations"},
            "state": "2",  # In Progress
            "priority": "3",  # Medium
            "sys_updated_on": "2026-01-31 12:00:00",
        }

    async def query_requests(
        self,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return mock requests."""
        return [
            {
                "sys_id": f"mock{i:08x}",
                "number": f"REQ{i:08d}",
                "short_description": f"Mock Request {i}",
                "requestor": {"email": f"user{i}@example.com", "name": f"User {i}"},
                "assigned_to": {"name": "IT Support"},
                "assignment_group": {"name": "IT Operations"},
                "state": "2",
                "priority": "3",
                "sys_updated_on": "2026-01-31 12:00:00",
            }
            for i in range(1, min(limit + 1, 11))
        ]

    async def get_sla_info(self, sys_id: str) -> Optional[Dict[str, Any]]:
        """Return mock SLA info."""
        from datetime import datetime, timedelta

        return {
            "task": sys_id,
            "sla": "Response SLA",
            "due_date": (datetime.now() + timedelta(hours=4)).isoformat(),
            "state": "1",  # In Progress
        }
