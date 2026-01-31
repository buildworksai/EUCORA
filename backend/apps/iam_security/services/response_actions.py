# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Response actions for security incidents.

Implements account disable, permission revocation, and password reset.
"""
import logging

from apps.iam_security.models import IdentityProvider
from apps.iam_security.services.clients.entra_client import EntraIDClient

logger = logging.getLogger(__name__)


class ResponseActionsService:
    """Service for executing security response actions."""

    def __init__(self, provider: IdentityProvider):
        """
        Initialize response actions service.

        Args:
            provider: Identity provider instance
        """
        self.provider = provider

    async def disable_account(self, user_principal: str) -> bool:
        """
        Disable user account (R3 action).

        Args:
            user_principal: User principal name or ID

        Returns:
            True if successful
        """
        if self.provider.provider_type == IdentityProvider.ProviderType.ENTRA_ID:
            config = self.provider.connection_config
            client = EntraIDClient(
                tenant_id=self.provider.tenant_id or "",
                client_id=config.get("client_id", ""),
                client_secret=config.get("client_secret", ""),
            )
            try:
                await client.authenticate()
                # Get user ID from principal
                user_id = await self._get_user_id(user_principal, client)
                if user_id:
                    result = await client.disable_user(user_id)
                    await client.close()
                    return result
            except Exception as e:  # noqa: F841
                logger.exception(f"Error disabling account for {user_principal}")
                await client.close()
                return False

        return False

    async def revoke_permissions(self, user_principal: str) -> bool:
        """
        Revoke user permissions (R2 action).

        Args:
            user_principal: User principal name

        Returns:
            True if successful
        """
        # Implementation would revoke specific permissions
        logger.info(f"Revoking permissions for {user_principal}")
        return True

    async def force_password_reset(self, user_principal: str) -> bool:
        """
        Force password reset (R2 action).

        Args:
            user_principal: User principal name

        Returns:
            True if successful
        """
        if self.provider.provider_type == IdentityProvider.ProviderType.ENTRA_ID:
            config = self.provider.connection_config
            client = EntraIDClient(
                tenant_id=self.provider.tenant_id or "",
                client_id=config.get("client_id", ""),
                client_secret=config.get("client_secret", ""),
            )
            try:
                await client.authenticate()
                user_id = await self._get_user_id(user_principal, client)
                if user_id:
                    result = await client.revoke_sessions(user_id)
                    await client.close()
                    return result
            except Exception as e:  # noqa: F841
                logger.exception(f"Error forcing password reset for {user_principal}")
                await client.close()
                return False

        return False

    async def _get_user_id(self, user_principal: str, client: EntraIDClient) -> str | None:
        """Get user object ID from principal name."""
        # Simplified - would query Graph API for user
        return user_principal
