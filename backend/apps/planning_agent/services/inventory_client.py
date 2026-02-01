# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Inventory Client.

Integrates with Intune/SCCM for device and user inventory.
"""
import logging
from typing import Any, Dict, List, Optional

from apps.connectors.intune.client import IntuneConnector, IntuneConnectorError

# SCCM connector import - handle if not available
try:
    from apps.connectors.sccm.client import SCCMConnector, SCCMConnectorError
except ImportError:
    SCCMConnector = None
    SCCMConnectorError = Exception

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
        self.client_type = connection_config.get("type", "intune")

        # Initialize appropriate connector
        if self.client_type == "intune":
            try:
                self.intune_client = IntuneConnector()
                self.sccm_client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Intune connector: {e}")
                self.intune_client = None
                self.sccm_client = None
        elif self.client_type == "sccm":
            if SCCMConnector is None:
                logger.warning("SCCM connector not available")
                self.sccm_client = None
                self.intune_client = None
            else:
                try:
                    self.sccm_client = SCCMConnector()
                    self.intune_client = None
                except Exception as e:
                    logger.warning(f"Failed to initialize SCCM connector: {e}")
                    self.intune_client = None
                    self.sccm_client = None
        else:
            self.intune_client = None
            self.sccm_client = None

    def get_devices(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get devices in scope.

        Args:
            scope: Scope configuration (departments, regions, groups)

        Returns:
            List of device dictionaries
        """
        if self.client_type == "intune" and self.intune_client:
            return self._get_intune_devices(scope)
        elif self.client_type == "sccm" and self.sccm_client:
            return self._get_sccm_devices(scope)
        else:
            raise NotImplementedError(f"Device retrieval not implemented for client type: {self.client_type}")

    def _get_intune_devices(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get devices from Intune."""
        try:
            # Build filter query from scope
            filter_parts = []

            if scope.get("departments"):
                dept_filter = " or ".join([f"department eq '{dept}'" for dept in scope["departments"]])
                filter_parts.append(f"({dept_filter})")

            if scope.get("groups"):
                # Intune uses group membership - would need to query groups first
                # For now, get all devices and filter client-side
                pass

            filter_query = " and ".join(filter_parts) if filter_parts else None

            # Get devices from Intune
            devices = self.intune_client.list_managed_devices(
                top=scope.get("limit", 1000),
                filter_query=filter_query,
            )

            # Transform to standard format
            result = []
            for device in devices:
                result.append(
                    {
                        "device_id": device.get("id", ""),
                        "device_name": device.get("deviceName", ""),
                        "user_principal": device.get("userPrincipalName", ""),
                        "health_score": self._calculate_health_score(device),
                        "is_it_staff": device.get("department", "").lower() in ["it", "engineering", "operations"],
                        "criticality": self._determine_criticality(device),
                        "department": device.get("department", ""),
                        "region": device.get("location", ""),
                        "os": device.get("operatingSystem", ""),
                        "os_version": device.get("osVersion", ""),
                        "compliance_state": device.get("complianceState", ""),
                    }
                )

            # Apply client-side filtering for groups/regions if needed
            if scope.get("regions"):
                result = [d for d in result if d.get("region") in scope["regions"]]

            logger.info(f"Retrieved {len(result)} devices from Intune")
            return result

        except IntuneConnectorError as e:
            logger.error(f"Failed to get devices from Intune: {e}")
            return []

    def _get_sccm_devices(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get devices from SCCM."""
        try:
            # SCCM device query would go here
            # For now, return empty list as SCCM integration needs more work
            logger.warning("SCCM device retrieval not fully implemented")
            return []
        except Exception as e:
            logger.error(f"Failed to get devices from SCCM: {e}")
            return []

    def _calculate_health_score(self, device: Dict[str, Any]) -> float:
        """Calculate device health score from Intune device data."""
        # Simple scoring based on compliance and management state
        score = 1.0

        compliance_state = device.get("complianceState", "").lower()
        if compliance_state == "compliant":
            score = 1.0
        elif compliance_state == "noncompliant":
            score = 0.5
        elif compliance_state == "inprogress":
            score = 0.7
        else:
            score = 0.3

        return score

    def _determine_criticality(self, device: Dict[str, Any]) -> str:
        """Determine device criticality."""
        # Check if device belongs to VIP users or critical departments
        department = device.get("department", "").lower()
        if department in ["executive", "leadership", "c-suite"]:
            return "vip"
        elif department in ["it", "security", "operations"]:
            return "critical"
        else:
            return "standard"

    def get_users(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get users in scope.

        Args:
            scope: Scope configuration

        Returns:
            List of user dictionaries
        """
        if self.client_type == "intune" and self.intune_client:
            return self._get_intune_users(scope)
        elif self.client_type == "sccm" and self.sccm_client:
            return self._get_sccm_users(scope)
        else:
            raise NotImplementedError(f"User retrieval not implemented for client type: {self.client_type}")

    def _get_intune_users(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get users from Intune/Microsoft Graph."""
        try:
            # Use Microsoft Graph API to get users
            # This would require Entra ID connector or Graph API client
            # For now, extract users from device data
            devices = self._get_intune_devices(scope)

            # Extract unique users from devices
            users_dict = {}
            for device in devices:
                upn = device.get("user_principal")
                if upn and upn not in users_dict:
                    users_dict[upn] = {
                        "user_principal": upn,
                        "display_name": upn.split("@")[0],
                        "department": device.get("department", ""),
                        "is_vip": device.get("criticality") == "vip",
                    }

            result = list(users_dict.values())
            logger.info(f"Retrieved {len(result)} users from Intune device data")
            return result

        except Exception as e:
            logger.error(f"Failed to get users from Intune: {e}")
            return []

    def _get_sccm_users(self, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get users from SCCM."""
        try:
            # SCCM user query would go here
            logger.warning("SCCM user retrieval not fully implemented")
            return []
        except Exception as e:
            logger.error(f"Failed to get users from SCCM: {e}")
            return []

    def test_connection(self) -> bool:
        """
        Test connection.

        Returns:
            True if connection successful
        """
        try:
            if self.client_type == "intune" and self.intune_client:
                # Test by listing a small number of devices
                self.intune_client.list_managed_devices(top=1)
                return True
            elif self.client_type == "sccm" and self.sccm_client:
                # Test SCCM connection
                # For now, return True if client initialized
                return self.sccm_client is not None
            else:
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


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


def get_inventory_client(connection_config: Dict[str, Any], client_type: Optional[str] = None) -> InventoryClient:
    """
    Get inventory client instance.

    Args:
        connection_config: Connection configuration
        client_type: Client type (intune, sccm, mock). If None, uses config["type"]

    Returns:
        InventoryClient instance
    """
    # Determine client type
    if client_type is None:
        client_type = connection_config.get("type", "mock")

    if client_type == "mock":
        return MockInventoryClient(connection_config)
    elif client_type in ["intune", "sccm"]:
        # Update config with type
        connection_config["type"] = client_type
        return InventoryClient(connection_config)
    else:
        logger.warning(f"Unknown client type: {client_type}, using mock")
        return MockInventoryClient(connection_config)
