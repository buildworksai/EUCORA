# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Inventory Client.

Integrates with Intune/SCCM for device and user inventory.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class InventoryClient:
    """
    Base client for inventory systems.

    Provides interface for Intune/SCCM integration.
    """

    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize inventory client.

        Args:
            connection_config: Connection configuration
        """
        self.config = connection_config
        # TODO: Initialize Intune/SCCM API client

    def get_devices(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get devices in scope.

        Args:
            scope: Scope configuration (departments, regions, groups)

        Returns:
            List of device dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_devices")

    def get_users(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get users in scope.

        Args:
            scope: Scope configuration

        Returns:
            List of user dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_users")

    def test_connection(self) -> bool:
        """
        Test connection.

        Returns:
            True if connection successful
        """
        raise NotImplementedError("Subclasses must implement test_connection")


class MockInventoryClient(InventoryClient):
    """Mock inventory client for development/testing."""

    def get_devices(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock devices."""
        return [
            {
                "device_id": f"DEVICE-{i:03d}",
                "device_name": f"Device {i}",
                "user_principal": f"user{i}@example.com",
                "health_score": 0.8 + (i % 3) * 0.1,
                "is_it_staff": i < 10,
                "criticality": "vip" if i < 5 else "standard",
                "department": "Engineering" if i % 2 == 0 else "Sales",
                "region": "US-East" if i % 3 == 0 else "US-West",
            }
            for i in range(100)
        ]

    def get_users(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock users."""
        return [
            {
                "user_principal": f"user{i}@example.com",
                "display_name": f"User {i}",
                "department": "Engineering" if i % 2 == 0 else "Sales",
                "is_vip": i < 5,
            }
            for i in range(50)
        ]

    def test_connection(self) -> bool:
        """Return True for mock."""
        return True


def get_inventory_client(connection_config: Dict[str, Any], client_type: str = "mock") -> InventoryClient:
    """
    Get inventory client instance.

    Args:
        connection_config: Connection configuration
        client_type: Client type (intune, sccm, mock)

    Returns:
        InventoryClient instance
    """
    if client_type == "mock":
        return MockInventoryClient(connection_config)
    # TODO: Return real clients based on type
    return MockInventoryClient(connection_config)
