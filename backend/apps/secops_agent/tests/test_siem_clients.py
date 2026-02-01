# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for SIEM client implementations.
"""
# datetime imports not needed for these tests
from unittest.mock import Mock, patch

import pytest

from apps.secops_agent.models import SIEMConnection
from apps.secops_agent.services.siem_client import (
    ElasticSIEMClient,
    QRadarSIEMClient,
    SentinelSIEMClient,
    SplunkSIEMClient,
    get_siem_client,
)


@pytest.mark.django_db
class TestSentinelSIEMClient:
    """Test Azure Sentinel SIEM client."""

    def test_sync_alerts_success(self):
        """Test successful alert sync from Sentinel."""
        connection = SIEMConnection.objects.create(
            name="Sentinel Connection",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
            connection_config={
                "workspace_id": "test-workspace",
                "tenant_id": "test-tenant",
                "client_id": "test-client",
                "client_secret": "test-secret",  # pragma: allowlist secret
            },
        )

        client = SentinelSIEMClient(connection)

        mock_token_response = Mock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.status_code = 200

        mock_query_response = Mock()
        mock_query_response.json.return_value = {
            "tables": [
                {
                    "rows": [
                        ["alert-1", "Suspicious Activity", "High", "Test description", "2024-01-20T10:00:00Z"],
                    ]
                }
            ]
        }
        mock_query_response.status_code = 200

        with patch.object(client.http_client, "post") as mock_post:
            mock_post.side_effect = [mock_token_response, mock_query_response]
            alerts = client.sync_alerts()

        assert len(alerts) == 1
        assert alerts[0]["alert_id"] == "alert-1"
        assert alerts[0]["severity"] == "high"
        assert alerts[0]["source"] == "Azure Sentinel"

    def test_test_connection_success(self):
        """Test connection test succeeds."""
        connection = SIEMConnection.objects.create(
            name="Sentinel Connection",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
            connection_config={
                "workspace_id": "test-workspace",
                "tenant_id": "test-tenant",
                "client_id": "test-client",
                "client_secret": "test-secret",  # pragma: allowlist secret
            },
        )

        client = SentinelSIEMClient(connection)

        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "test-token"}
        mock_response.status_code = 200

        with patch.object(client.http_client, "post", return_value=mock_response):
            assert client.test_connection() is True

    def test_test_connection_failure(self):
        """Test connection test fails gracefully."""
        connection = SIEMConnection.objects.create(
            name="Sentinel Connection",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
            connection_config={},
        )

        client = SentinelSIEMClient(connection)
        assert client.test_connection() is False


@pytest.mark.django_db
class TestSplunkSIEMClient:
    """Test Splunk SIEM client."""

    def test_sync_alerts_success(self):
        """Test successful alert sync from Splunk."""
        connection = SIEMConnection.objects.create(
            name="Splunk Connection",
            siem_type=SIEMConnection.SIEMType.SPLUNK,
            connection_config={
                "api_url": "https://splunk.example.com",
                "username": "test-user",
                "password": "test-pass",  # pragma: allowlist secret
            },
        )

        client = SplunkSIEMClient(connection)

        mock_search_response = Mock()
        mock_search_response.json.return_value = {"sid": "test-sid"}
        mock_search_response.status_code = 200

        mock_results_response = Mock()
        mock_results_response.json.return_value = {
            "results": [
                {
                    "_key": "alert-1",
                    "title": "Test Alert",
                    "severity": "high",
                    "description": "Test description",
                    "_time": "2024-01-20T10:00:00Z",
                }
            ]
        }
        mock_results_response.status_code = 200

        with patch.object(client.http_client, "post", return_value=mock_search_response):
            with patch.object(client.http_client, "get", return_value=mock_results_response):
                alerts = client.sync_alerts()

        assert len(alerts) > 0
        assert alerts[0]["alert_id"] == "alert-1"
        assert alerts[0]["source"] == "Splunk"


@pytest.mark.django_db
class TestQRadarSIEMClient:
    """Test IBM QRadar SIEM client."""

    def test_sync_alerts_success(self):
        """Test successful alert sync from QRadar."""
        connection = SIEMConnection.objects.create(
            name="QRadar Connection",
            siem_type=SIEMConnection.SIEMType.QRADAR,
            connection_config={
                "api_url": "https://qradar.example.com",
                "api_token": "test-token",  # pragma: allowlist secret
            },
        )

        client = QRadarSIEMClient(connection)

        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "description": "Test Offense",
                "severity": 8,
                "start_time": 1705747200000,  # Unix timestamp in ms
            }
        ]
        mock_response.status_code = 200

        with patch.object(client.http_client, "get", return_value=mock_response):
            alerts = client.sync_alerts()

        assert len(alerts) > 0
        assert alerts[0]["alert_id"] == "1"
        assert alerts[0]["severity"] == "critical"  # severity 8 maps to critical
        assert alerts[0]["source"] == "QRadar"

    def test_map_qradar_severity(self):
        """Test QRadar severity mapping."""
        connection = SIEMConnection.objects.create(
            name="QRadar Connection",
            siem_type=SIEMConnection.SIEMType.QRADAR,
            connection_config={},
        )

        client = QRadarSIEMClient(connection)

        assert client._map_qradar_severity(10) == "critical"
        assert client._map_qradar_severity(8) == "critical"
        assert client._map_qradar_severity(5) == "high"
        assert client._map_qradar_severity(3) == "medium"
        assert client._map_qradar_severity(1) == "low"


@pytest.mark.django_db
class TestElasticSIEMClient:
    """Test Elastic SIEM client."""

    def test_sync_alerts_success(self):
        """Test successful alert sync from Elastic."""
        connection = SIEMConnection.objects.create(
            name="Elastic Connection",
            siem_type=SIEMConnection.SIEMType.ELASTIC,
            connection_config={
                "api_url": "https://elastic.example.com",
                "api_key": "test-key",  # pragma: allowlist secret
            },
        )

        client = ElasticSIEMClient(connection)

        mock_response = Mock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "alert-1",
                        "_source": {
                            "signal": {
                                "rule": {
                                    "name": "Test Rule",
                                    "severity": "high",
                                    "description": "Test description",
                                }
                            },
                            "@timestamp": "2024-01-20T10:00:00Z",
                        },
                    }
                ]
            }
        }
        mock_response.status_code = 200

        with patch.object(client.http_client, "post", return_value=mock_response):
            alerts = client.sync_alerts()

        assert len(alerts) > 0
        assert alerts[0]["alert_id"] == "alert-1"
        assert alerts[0]["source"] == "Elastic"


@pytest.mark.django_db
class TestGetSIEMClient:
    """Test SIEM client factory function."""

    def test_get_sentinel_client(self):
        """Test getting Sentinel client."""
        connection = SIEMConnection.objects.create(
            name="Sentinel Connection",
            siem_type=SIEMConnection.SIEMType.SENTINEL,
            connection_config={},
        )

        client = get_siem_client(connection)
        assert isinstance(client, SentinelSIEMClient)

    def test_get_splunk_client(self):
        """Test getting Splunk client."""
        connection = SIEMConnection.objects.create(
            name="Splunk Connection",
            siem_type=SIEMConnection.SIEMType.SPLUNK,
            connection_config={},
        )

        client = get_siem_client(connection)
        assert isinstance(client, SplunkSIEMClient)

    def test_get_qradar_client(self):
        """Test getting QRadar client."""
        connection = SIEMConnection.objects.create(
            name="QRadar Connection",
            siem_type=SIEMConnection.SIEMType.QRADAR,
            connection_config={},
        )

        client = get_siem_client(connection)
        assert isinstance(client, QRadarSIEMClient)

    def test_get_elastic_client(self):
        """Test getting Elastic client."""
        connection = SIEMConnection.objects.create(
            name="Elastic Connection",
            siem_type=SIEMConnection.SIEMType.ELASTIC,
            connection_config={},
        )

        client = get_siem_client(connection)
        assert isinstance(client, ElasticSIEMClient)
