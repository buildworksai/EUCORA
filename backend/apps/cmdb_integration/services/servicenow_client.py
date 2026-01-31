# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ServiceNow CMDB Table API Client.

Provides async interface for CMDB operations including
query, create, update, and relationship management.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..models import CMDBConnection

logger = logging.getLogger(__name__)


class ServiceNowCMDBClient:
    """
    Async client for ServiceNow CMDB Table API.

    Supports:
    - Basic, OAuth, and API key authentication
    - CRUD operations on CMDB tables
    - Query with encoded query strings
    - Relationship management
    - Pagination and rate limiting
    """

    def __init__(self, connection: CMDBConnection):
        """
        Initialize ServiceNow CMDB client.

        Args:
            connection: CMDBConnection model instance
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
                # OAuth token should be pre-fetched and stored
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

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to ServiceNow instance.

        Returns:
            Dict with connection status and details
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/now/table/sys_properties", params={"sysparm_limit": 1})
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "instance": self.instance_url,
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "instance": self.instance_url,
            }

    async def get_ci(self, table: str, sys_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single CI by sys_id.

        Args:
            table: CMDB table name (e.g., 'cmdb_ci_computer')
            sys_id: ServiceNow sys_id

        Returns:
            CI record as dict or None if not found
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/now/table/{table}/{sys_id}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()
            return data.get("result")

        except Exception as e:
            logger.error(f"Failed to get CI {sys_id}: {e}")
            raise

    async def query_cis(
        self,
        table: str,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query CIs with encoded query string.

        Args:
            table: CMDB table name
            query: ServiceNow encoded query string
            fields: List of fields to return
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of CI records
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

            response = await client.get(f"/api/now/table/{table}", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("result", [])

        except Exception as e:
            logger.error(f"Failed to query CIs from {table}: {e}")
            raise

    async def query_all_cis(
        self,
        table: str,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        batch_size: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Query all CIs with automatic pagination.

        Args:
            table: CMDB table name
            query: ServiceNow encoded query string
            fields: List of fields to return
            batch_size: Records per request

        Returns:
            List of all matching CI records
        """
        all_records = []
        offset = 0

        while True:
            records = await self.query_cis(
                table=table,
                query=query,
                fields=fields,
                limit=batch_size,
                offset=offset,
            )

            if not records:
                break

            all_records.extend(records)
            offset += len(records)

            if len(records) < batch_size:
                break

        return all_records

    async def create_ci(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new CI.

        Args:
            table: CMDB table name
            data: CI field values

        Returns:
            Created CI record with sys_id
        """
        try:
            client = await self._get_client()
            response = await client.post(f"/api/now/table/{table}", json=data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Created CI in {table}: {result.get('result', {}).get('sys_id')}")
            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to create CI in {table}: {e}")
            raise

    async def update_ci(
        self,
        table: str,
        sys_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update an existing CI.

        Args:
            table: CMDB table name
            sys_id: ServiceNow sys_id
            data: Fields to update

        Returns:
            Updated CI record
        """
        try:
            client = await self._get_client()
            response = await client.patch(f"/api/now/table/{table}/{sys_id}", json=data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Updated CI {sys_id} in {table}")
            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to update CI {sys_id}: {e}")
            raise

    async def delete_ci(self, table: str, sys_id: str) -> bool:
        """
        Delete a CI.

        Args:
            table: CMDB table name
            sys_id: ServiceNow sys_id

        Returns:
            True if deleted successfully
        """
        try:
            client = await self._get_client()
            response = await client.delete(f"/api/now/table/{table}/{sys_id}")
            response.raise_for_status()

            logger.info(f"Deleted CI {sys_id} from {table}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete CI {sys_id}: {e}")
            raise

    async def get_relationships(
        self,
        ci_sys_id: str,
        direction: str = "both",
    ) -> List[Dict[str, Any]]:
        """
        Get CI relationships.

        Args:
            ci_sys_id: Parent CI sys_id
            direction: 'parent', 'child', or 'both'

        Returns:
            List of relationship records
        """
        try:
            client = await self._get_client()

            queries = []
            if direction in ["parent", "both"]:
                queries.append(f"child={ci_sys_id}")
            if direction in ["child", "both"]:
                queries.append(f"parent={ci_sys_id}")

            query = "^OR".join(queries) if len(queries) > 1 else queries[0]

            response = await client.get(
                "/api/now/table/cmdb_rel_ci",
                params={"sysparm_query": query},
            )
            response.raise_for_status()

            data = response.json()
            return data.get("result", [])

        except Exception as e:
            logger.error(f"Failed to get relationships for {ci_sys_id}: {e}")
            raise

    async def create_relationship(
        self,
        parent_sys_id: str,
        child_sys_id: str,
        type_sys_id: str,
    ) -> Dict[str, Any]:
        """
        Create a CI relationship.

        Args:
            parent_sys_id: Parent CI sys_id
            child_sys_id: Child CI sys_id
            type_sys_id: Relationship type sys_id

        Returns:
            Created relationship record
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/now/table/cmdb_rel_ci",
                json={
                    "parent": parent_sys_id,
                    "child": child_sys_id,
                    "type": type_sys_id,
                },
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Created relationship between {parent_sys_id} and {child_sys_id}")
            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            raise

    async def get_table_schema(self, table: str) -> Dict[str, Any]:
        """
        Get table schema/metadata.

        Args:
            table: CMDB table name

        Returns:
            Table schema information
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/now/table/sys_dictionary",
                params={
                    "sysparm_query": f"name={table}",
                    "sysparm_fields": "element,column_label,internal_type,mandatory",
                },
            )
            response.raise_for_status()

            data = response.json()
            return {
                "table": table,
                "fields": data.get("result", []),
            }

        except Exception as e:
            logger.error(f"Failed to get schema for {table}: {e}")
            raise


class MockServiceNowCMDBClient(ServiceNowCMDBClient):
    """
    Mock ServiceNow client for development and testing.

    Provides realistic mock data for CMDB operations.
    """

    def __init__(self, connection: CMDBConnection):
        """Initialize mock client."""
        super().__init__(connection)
        self._mock_data = self._generate_mock_data()

    def _generate_mock_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mock CMDB data."""
        import random
        import uuid

        computers = []
        for i in range(50):
            computers.append(
                {
                    "sys_id": str(uuid.uuid4()),
                    "name": f"DESKTOP-{random.randint(1000, 9999)}",
                    "serial_number": f"SN-{random.randint(100000, 999999)}",
                    "os": random.choice(["Windows 11", "Windows 10", "macOS 14"]),
                    "manufacturer": random.choice(["Dell", "HP", "Lenovo", "Apple"]),
                    "model_id": f"Model-{random.randint(100, 999)}",
                    "ip_address": f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}",
                    "install_status": random.choice(["1", "2", "6"]),  # Installed, In Stock, Retired
                    "u_department": random.choice(["IT", "Finance", "HR", "Engineering"]),
                    "assigned_to": str(uuid.uuid4()) if random.random() > 0.3 else "",
                    "last_discovered": "2026-01-15 12:00:00",
                }
            )

        servers = []
        for i in range(20):
            servers.append(
                {
                    "sys_id": str(uuid.uuid4()),
                    "name": f"SRV-{random.choice(['WEB', 'APP', 'DB', 'FILE'])}-{random.randint(1, 99):02d}",
                    "serial_number": f"SRV-{random.randint(100000, 999999)}",
                    "os": random.choice(["Windows Server 2022", "Ubuntu 22.04", "RHEL 9"]),
                    "manufacturer": random.choice(["Dell", "HP", "VMware"]),
                    "ip_address": f"10.1.{random.randint(0, 255)}.{random.randint(1, 254)}",
                    "install_status": "1",
                    "environment": random.choice(["Production", "Staging", "Development"]),
                    "virtual": random.choice([True, False]),
                }
            )

        applications = []
        for i in range(30):
            applications.append(
                {
                    "sys_id": str(uuid.uuid4()),
                    "name": f"App-{i+1:03d}",
                    "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                    "vendor": random.choice(["Microsoft", "Oracle", "SAP", "Internal"]),
                    "operational_status": random.choice(["1", "2", "3"]),  # Operational, Repair, Retired
                    "business_criticality": random.choice(["1", "2", "3", "4"]),
                }
            )

        return {
            "cmdb_ci_computer": computers,
            "cmdb_ci_server": servers,
            "cmdb_ci_appl": applications,
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Mock connection test."""
        return {
            "success": True,
            "status_code": 200,
            "instance": self.instance_url,
            "mock": True,
        }

    async def get_ci(self, table: str, sys_id: str) -> Optional[Dict[str, Any]]:
        """Mock get CI."""
        records = self._mock_data.get(table, [])
        for record in records:
            if record.get("sys_id") == sys_id:
                return record
        return None

    async def query_cis(
        self,
        table: str,
        query: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Mock query CIs."""
        records = self._mock_data.get(table, [])[offset : offset + limit]

        if fields:
            records = [{k: r.get(k) for k in fields if k in r} for r in records]

        return records

    async def create_ci(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create CI."""
        import uuid

        sys_id = str(uuid.uuid4())
        record = {"sys_id": sys_id, **data}

        if table not in self._mock_data:
            self._mock_data[table] = []
        self._mock_data[table].append(record)

        return record

    async def update_ci(
        self,
        table: str,
        sys_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mock update CI."""
        records = self._mock_data.get(table, [])
        for i, record in enumerate(records):
            if record.get("sys_id") == sys_id:
                self._mock_data[table][i].update(data)
                return self._mock_data[table][i]
        raise ValueError(f"CI {sys_id} not found in {table}")

    async def delete_ci(self, table: str, sys_id: str) -> bool:
        """Mock delete CI."""
        records = self._mock_data.get(table, [])
        self._mock_data[table] = [r for r in records if r.get("sys_id") != sys_id]
        return True

    async def get_relationships(
        self,
        ci_sys_id: str,
        direction: str = "both",
    ) -> List[Dict[str, Any]]:
        """Mock get relationships."""
        return []

    async def close(self) -> None:
        """No-op for mock client."""
        pass
