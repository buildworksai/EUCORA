# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Entra ID (Azure AD) client.

Integrates with Microsoft Graph API for sign-in logs and audit logs.
"""
from datetime import datetime
from typing import Any

import httpx


class EntraIDClient:
    """Client for Microsoft Entra ID (Azure AD)."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize Entra ID client.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.access_token: str | None = None

    async def authenticate(self) -> bool:
        """
        Authenticate and obtain access token.

        Returns:
            True if authentication successful
        """
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
            return False

    async def get_sign_in_logs(self, since: datetime) -> list[dict[str, Any]]:
        """
        Get sign-in audit logs.

        Args:
            since: Start datetime for log retrieval

        Returns:
            List of sign-in event dictionaries
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.graph_url}/auditLogs/signIns"
        params = {
            "$filter": f"createdDateTime ge {since.isoformat()}",
            "$top": 999,
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            return []

    async def get_directory_audit(self, since: datetime) -> list[dict[str, Any]]:
        """
        Get directory audit logs.

        Args:
            since: Start datetime for log retrieval

        Returns:
            List of audit event dictionaries
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.graph_url}/auditLogs/directoryAudits"
        params = {
            "$filter": f"activityDateTime ge {since.isoformat()}",
            "$top": 999,
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            return []

    async def get_risky_users(self) -> list[dict[str, Any]]:
        """
        Get users flagged as risky.

        Returns:
            List of risky user dictionaries
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.graph_url}/identityProtection/riskyUsers"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            return []

    async def disable_user(self, user_id: str) -> bool:
        """
        Disable user account.

        Args:
            user_id: User object ID

        Returns:
            True if successful
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.graph_url}/users/{user_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {"accountEnabled": False}

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=data)
            return response.status_code == 204

    async def revoke_sessions(self, user_id: str) -> bool:
        """
        Revoke all refresh tokens.

        Args:
            user_id: User object ID

        Returns:
            True if successful
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.graph_url}/users/{user_id}/revokeSignInSessions"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            return response.status_code == 200

    async def close(self) -> None:
        """Close client connections."""
        pass
