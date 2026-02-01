# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for inventory client implementations.
"""
from unittest.mock import Mock, patch

import pytest

from apps.planning_agent.services.inventory_client import InventoryClient, MockInventoryClient, get_inventory_client


@pytest.mark.django_db
class TestMockInventoryClient:
    """Test mock inventory client."""

    def test_get_devices(self):
        """Test getting devices from mock client."""
        client = MockInventoryClient({})
        devices = client.get_devices({})

        assert len(devices) == 100
        assert devices[0]["device_id"] == "DEVICE-000"
        assert "health_score" in devices[0]
        assert "is_it_staff" in devices[0]
        assert "criticality" in devices[0]

    def test_get_users(self):
        """Test getting users from mock client."""
        client = MockInventoryClient({})
        users = client.get_users({})

        assert len(users) == 50
        assert users[0]["user_principal"] == "user0@example.com"
        assert "display_name" in users[0]
        assert "department" in users[0]

    def test_test_connection(self):
        """Test connection test."""
        client = MockInventoryClient({})
        assert client.test_connection() is True


@pytest.mark.django_db
class TestInventoryClient:
    """Test real inventory client with Intune integration."""

    @patch("apps.planning_agent.services.inventory_client.IntuneConnector")
    def test_get_devices_intune(self, mock_intune_class):
        """Test getting devices from Intune."""
        mock_connector = Mock()
        mock_connector.list_managed_devices.return_value = [
            {
                "id": "device-1",
                "deviceName": "Test Device 1",
                "userPrincipalName": "user1@example.com",
                "department": "Engineering",
                "operatingSystem": "Windows",
                "osVersion": "10.0.19045",
                "complianceState": "compliant",
                "location": "US-East",
            },
            {
                "id": "device-2",
                "deviceName": "Test Device 2",
                "userPrincipalName": "user2@example.com",
                "department": "Sales",
                "operatingSystem": "Windows",
                "osVersion": "10.0.19045",
                "complianceState": "noncompliant",
                "location": "US-West",
            },
        ]

        mock_intune_class.return_value = mock_connector

        connection_config = {
            "type": "intune",
        }
        client = InventoryClient(connection_config)

        scope = {"limit": 100}
        devices = client.get_devices(scope)

        assert len(devices) == 2
        assert devices[0]["device_id"] == "device-1"
        assert devices[0]["device_name"] == "Test Device 1"
        assert devices[0]["department"] == "Engineering"
        assert devices[0]["health_score"] > 0
        assert devices[1]["health_score"] < devices[0]["health_score"]  # Non-compliant has lower score

    @patch("apps.planning_agent.services.inventory_client.IntuneConnector")
    def test_get_users_intune(self, mock_intune_class):
        """Test getting users from Intune."""
        mock_connector = Mock()
        mock_connector.list_managed_devices.return_value = [
            {
                "id": "device-1",
                "deviceName": "Test Device 1",
                "userPrincipalName": "user1@example.com",
                "department": "Engineering",
            },
        ]

        mock_intune_class.return_value = mock_connector

        connection_config = {"type": "intune"}
        client = InventoryClient(connection_config)

        scope = {}
        users = client.get_users(scope)

        assert len(users) >= 1
        assert users[0]["user_principal"] == "user1@example.com"

    @patch("apps.planning_agent.services.inventory_client.IntuneConnector")
    def test_test_connection_intune(self, mock_intune_class):
        """Test connection test for Intune."""
        mock_connector = Mock()
        mock_connector.list_managed_devices.return_value = [{"id": "device-1"}]

        mock_intune_class.return_value = mock_connector

        connection_config = {"type": "intune"}
        client = InventoryClient(connection_config)

        assert client.test_connection() is True

    def test_calculate_health_score(self):
        """Test health score calculation."""
        connection_config = {"type": "intune"}
        client = InventoryClient(connection_config)

        # Compliant device
        compliant_device = {"complianceState": "compliant"}
        score_compliant = client._calculate_health_score(compliant_device)
        assert score_compliant == 1.0

        # Non-compliant device
        noncompliant_device = {"complianceState": "noncompliant"}
        score_noncompliant = client._calculate_health_score(noncompliant_device)
        assert score_noncompliant == 0.5

        # In progress device
        inprogress_device = {"complianceState": "inprogress"}
        score_inprogress = client._calculate_health_score(inprogress_device)
        assert score_inprogress == 0.7

    def test_determine_criticality(self):
        """Test criticality determination."""
        connection_config = {"type": "intune"}
        client = InventoryClient(connection_config)

        # VIP department
        vip_device = {"department": "Executive"}
        assert client._determine_criticality(vip_device) == "vip"

        # Critical department
        critical_device = {"department": "IT"}
        assert client._determine_criticality(critical_device) == "critical"

        # Standard department
        standard_device = {"department": "Sales"}
        assert client._determine_criticality(standard_device) == "standard"


@pytest.mark.django_db
class TestGetInventoryClient:
    """Test inventory client factory function."""

    def test_get_mock_client(self):
        """Test getting mock client."""
        config = {"type": "mock"}
        client = get_inventory_client(config)
        assert isinstance(client, MockInventoryClient)

    @patch("apps.planning_agent.services.inventory_client.IntuneConnector")
    def test_get_intune_client(self, mock_intune_class):
        """Test getting Intune client."""
        mock_intune_class.return_value = Mock()
        config = {"type": "intune"}
        client = get_inventory_client(config)
        assert isinstance(client, InventoryClient)
        assert client.client_type == "intune"
