# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Active Directory (On-Premises) integration service.

Syncs users, groups, and computer objects via LDAP/LDAPS.
"""
import logging
from typing import Any, Dict, List

from django.contrib.auth.models import Group, User
from ldap3 import ALL, SUBTREE, Connection, Server

from apps.connectors.models import Asset
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class ActiveDirectoryService(IntegrationService):
    """Active Directory integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test LDAP connectivity."""
        server_url = config.get("server_url")
        credentials = config.get("credentials", {})
        username = credentials.get("username")
        password = credentials.get("password")

        if not all([server_url, username, password]):
            return {"status": "failed", "message": "Missing required configuration (server_url, username, password)"}

        try:
            server = Server(server_url, get_info=ALL)
            conn = Connection(server, user=username, password=password, auto_bind=True)
            conn.unbind()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except Exception as e:
            logger.error(f"Active Directory connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync users, groups, and computers from Active Directory."""
        users_created, users_updated = self.sync_users(system)
        groups_created, groups_updated = self.sync_groups(system)
        computers_created, computers_updated = self.sync_computers(system)

        return {
            "fetched": users_created
            + users_updated
            + groups_created
            + groups_updated
            + computers_created
            + computers_updated,
            "created": users_created + groups_created + computers_created,
            "updated": users_updated + groups_updated + computers_updated,
            "failed": 0,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch computer objects from Active Directory."""
        return self._fetch_computers(system)

    def sync_users(self, system: ExternalSystem) -> tuple:
        """Sync users from Active Directory."""
        users = self._fetch_users(system)
        created, updated = 0, 0

        for user_data in users:
            try:
                sam_account_name = user_data.get("sAMAccountName")
                if not sam_account_name:
                    continue

                user, created_flag = User.objects.update_or_create(
                    username=sam_account_name,
                    defaults={
                        "email": user_data.get("mail", ""),
                        "first_name": user_data.get("givenName", ""),
                        "last_name": user_data.get("sn", ""),
                        "is_active": not user_data.get("userAccountControl", 0) & 0x2,  # ACCOUNTDISABLE flag
                    },
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f'Failed to sync user {user_data.get("sAMAccountName")}: {e}')

        return created, updated

    def sync_groups(self, system: ExternalSystem) -> tuple:
        """Sync security groups from Active Directory."""
        groups = self._fetch_groups(system)
        created, updated = 0, 0

        for group_data in groups:
            try:
                group_name = group_data.get("cn") or group_data.get("name")
                if not group_name:
                    continue

                group, created_flag = Group.objects.update_or_create(name=group_name, defaults={})

                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f'Failed to sync group {group_data.get("cn")}: {e}')

        return created, updated

    def sync_computers(self, system: ExternalSystem) -> tuple:
        """Sync computer objects from Active Directory."""
        computers = self._fetch_computers(system)
        created, updated = 0, 0

        for computer_data in computers:
            try:
                computer_name = computer_data.get("cn") or computer_data.get("name")
                if not computer_name:
                    continue

                asset, created_flag = Asset.objects.update_or_create(
                    asset_id=computer_data.get("distinguishedName", computer_name),
                    defaults={
                        "name": computer_name,
                        "type": "Desktop",  # Could be enhanced with additional AD attributes
                        "os": computer_data.get("operatingSystem", ""),
                        "os_version": computer_data.get("operatingSystemVersion", ""),
                        "status": "Active" if computer_data.get("userAccountControl", 0) & 0x2 == 0 else "Inactive",
                        "connector_type": "ad",
                        "is_demo": False,
                    },
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f'Failed to sync computer {computer_data.get("cn")}: {e}')

        return created, updated

    def _fetch_users(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch users from Active Directory via LDAP."""
        conn = self._get_ldap_connection(system)
        base_dn = system.metadata.get("base_dn", "")
        search_filter = system.metadata.get("user_filter", "(objectClass=user)")

        attributes = ["sAMAccountName", "mail", "givenName", "sn", "userAccountControl", "department", "title"]

        try:
            conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=attributes)

            users = []
            for entry in conn.entries:
                user_dict = {}
                for attr in attributes:
                    value = getattr(entry, attr, None)
                    if value:
                        user_dict[attr] = (
                            str(value[0]) if hasattr(value, "__iter__") and not isinstance(value, str) else str(value)
                        )
                users.append(user_dict)

            return users
        finally:
            conn.unbind()

    def _fetch_groups(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch security groups from Active Directory."""
        conn = self._get_ldap_connection(system)
        base_dn = system.metadata.get("base_dn", "")
        search_filter = system.metadata.get("group_filter", "(objectClass=group)")

        attributes = ["cn", "name", "description", "member"]

        try:
            conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=attributes)

            groups = []
            for entry in conn.entries:
                group_dict = {}
                for attr in attributes:
                    value = getattr(entry, attr, None)
                    if value:
                        group_dict[attr] = (
                            str(value[0]) if hasattr(value, "__iter__") and not isinstance(value, str) else str(value)
                        )
                groups.append(group_dict)

            return groups
        finally:
            conn.unbind()

    def _fetch_computers(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """Fetch computer objects from Active Directory."""
        conn = self._get_ldap_connection(system)
        base_dn = system.metadata.get("base_dn", "")
        search_filter = system.metadata.get("computer_filter", "(objectClass=computer)")

        attributes = [
            "cn",
            "name",
            "distinguishedName",
            "operatingSystem",
            "operatingSystemVersion",
            "lastLogon",
            "userAccountControl",
        ]

        try:
            conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=attributes)

            computers = []
            for entry in conn.entries:
                computer_dict = {}
                for attr in attributes:
                    value = getattr(entry, attr, None)
                    if value:
                        computer_dict[attr] = (
                            str(value[0]) if hasattr(value, "__iter__") and not isinstance(value, str) else str(value)
                        )
                computers.append(computer_dict)

            return computers
        finally:
            conn.unbind()

    def _get_ldap_connection(self, system: ExternalSystem):
        """Get LDAP connection for Active Directory."""
        server_url = system.metadata.get("server_url", system.api_url)
        credentials = system.credentials
        username = credentials.get("username")
        password = credentials.get("password")

        server = Server(server_url, get_info=ALL)
        conn = Connection(server, user=username, password=password, auto_bind=True)
        return conn
