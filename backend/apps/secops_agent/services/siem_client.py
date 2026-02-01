# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
SIEM Client.

Provides interface for integrating with SIEM platforms
(Sentinel, Splunk, QRadar, Elastic).
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apps.core.http import ResilientHTTPClient
from apps.secops_agent.models import SIEMConnection

logger = logging.getLogger(__name__)


class SIEMClient:
    """
    Base client for SIEM platforms.

    Subclasses implement platform-specific logic.
    """

    def __init__(self, connection: SIEMConnection):
        """
        Initialize SIEM client.

        Args:
            connection: SIEMConnection model instance
        """
        self.connection = connection
        self.config = connection.connection_config
        # Use generic service name based on SIEM type, fallback to known services
        siem_service_map = {
            SIEMConnection.SIEMType.SENTINEL: "defender",  # Azure services
            SIEMConnection.SIEMType.SPLUNK: "splunk",
            SIEMConnection.SIEMType.ELASTIC: "elastic",
            SIEMConnection.SIEMType.QRADAR: "external_api",  # Generic external API
        }
        service_name = siem_service_map.get(connection.siem_type, "external_api")
        self.http_client = ResilientHTTPClient(
            service_name=service_name,
            timeout=self.config.get("timeout", 30),
            max_retries=self.config.get("max_retries", 3),
        )

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Sync security alerts from SIEM.

        Args:
            since: Only fetch alerts since this datetime

        Returns:
            List of alert records
        """
        raise NotImplementedError("Subclasses must implement sync_alerts")

    def test_connection(self) -> bool:
        """
        Test SIEM connection.

        Returns:
            True if connection successful
        """
        raise NotImplementedError("Subclasses must implement test_connection")


class SentinelSIEMClient(SIEMClient):
    """Azure Sentinel SIEM client."""

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Sync alerts from Azure Sentinel.

        Args:
            since: Only fetch alerts since this datetime

        Returns:
            List of alert records
        """
        try:
            workspace_id = self.config.get("workspace_id")
            tenant_id = self.config.get("tenant_id")
            client_id = self.config.get("client_id")
            client_secret = self.config.get("client_secret")

            if not all([workspace_id, tenant_id, client_id, client_secret]):
                logger.error("Azure Sentinel credentials not configured")
                return []

            # Get access token
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://api.loganalytics.io/.default",
                "grant_type": "client_credentials",
            }

            token_response = self.http_client.post(token_url, data=token_data)
            access_token = token_response.json().get("access_token")

            if not access_token:
                logger.error("Failed to get Azure Sentinel access token")
                return []

            # Query Sentinel alerts
            if since is None:
                since = datetime.now() - timedelta(hours=24)

            query = f"""
            SecurityAlert
            | where TimeGenerated >= datetime('{since.isoformat()}')
            | order by TimeGenerated desc
            | take 100
            """

            query_url = f"https://api.loganalytics.io/v1/workspaces/{workspace_id}/query"
            headers = {"Authorization": f"Bearer {access_token}"}
            query_params = {"query": query}

            response = self.http_client.post(query_url, headers=headers, json=query_params)
            data = response.json()

            alerts = []
            for row in data.get("tables", [{}])[0].get("rows", []):
                alerts.append(
                    {
                        "alert_id": row[0] if len(row) > 0 else "",
                        "title": row[1] if len(row) > 1 else "",
                        "severity": self._map_sentinel_severity(row[2] if len(row) > 2 else ""),
                        "description": row[3] if len(row) > 3 else "",
                        "source": "Azure Sentinel",
                        "affected_assets": [],
                        "alert_time": row[4] if len(row) > 4 else datetime.now().isoformat(),
                    }
                )

            logger.info(f"Synced {len(alerts)} alerts from Azure Sentinel")
            return alerts

        except Exception as e:
            logger.error(f"Failed to sync alerts from Azure Sentinel: {e}", exc_info=True)
            return []

    def _map_sentinel_severity(self, severity: str) -> str:
        """Map Sentinel severity to standard severity."""
        severity_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "low",
        }
        return severity_map.get(severity, "medium")

    def test_connection(self) -> bool:
        """Test Azure Sentinel connection."""
        try:
            workspace_id = self.config.get("workspace_id")
            tenant_id = self.config.get("tenant_id")
            client_id = self.config.get("client_id")
            client_secret = self.config.get("client_secret")

            if not all([workspace_id, tenant_id, client_id, client_secret]):
                return False

            # Test token acquisition
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://api.loganalytics.io/.default",
                "grant_type": "client_credentials",
            }

            response = self.http_client.post(token_url, data=token_data)
            return response.status_code == 200 and "access_token" in response.json()
        except Exception as e:
            logger.error(f"Azure Sentinel connection test failed: {e}")
            return False


class SplunkSIEMClient(SIEMClient):
    """Splunk SIEM client."""

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Sync alerts from Splunk.

        Args:
            since: Only fetch alerts since this datetime

        Returns:
            List of alert records
        """
        try:
            api_url = self.config.get("api_url")
            username = self.config.get("username")
            password = self.config.get("password")

            if not api_url or not username or not password:
                logger.error("Splunk credentials not configured")
                return []

            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(username, password)

            if since is None:
                since = datetime.now() - timedelta(hours=24)

            # Splunk search query
            search_query = f'search index=security earliest="{since.strftime("%Y-%m-%dT%H:%M:%S")}" | head 100'

            search_url = f"{api_url}/services/search/jobs"
            search_data = {"search": search_query, "output_mode": "json"}

            # Start search job
            response = self.http_client.post(search_url, auth=auth, data=search_data)
            sid = response.json().get("sid")

            if not sid:
                return []

            # Wait for results and get them
            results_url = f"{api_url}/services/search/jobs/{sid}/results"
            results_response = self.http_client.get(results_url, auth=auth, params={"output_mode": "json"})
            results = results_response.json().get("results", [])

            alerts = []
            for result in results:
                alerts.append(
                    {
                        "alert_id": result.get("_key", ""),
                        "title": result.get("title", ""),
                        "severity": result.get("severity", "medium"),
                        "description": result.get("description", ""),
                        "source": "Splunk",
                        "affected_assets": [],
                        "alert_time": result.get("_time", datetime.now().isoformat()),
                    }
                )

            logger.info(f"Synced {len(alerts)} alerts from Splunk")
            return alerts

        except Exception as e:
            logger.error(f"Failed to sync alerts from Splunk: {e}", exc_info=True)
            return []

    def test_connection(self) -> bool:
        """Test Splunk connection."""
        try:
            api_url = self.config.get("api_url")
            username = self.config.get("username")
            password = self.config.get("password")

            if not api_url or not username or not password:
                return False

            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(username, password)
            test_url = f"{api_url}/services/auth/login"

            response = self.http_client.post(test_url, auth=auth, data={"username": username, "password": password})
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Splunk connection test failed: {e}")
            return False


class QRadarSIEMClient(SIEMClient):
    """IBM QRadar SIEM client."""

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Sync alerts from QRadar.

        Args:
            since: Only fetch alerts since this datetime

        Returns:
            List of alert records
        """
        try:
            api_url = self.config.get("api_url")
            api_token = self.config.get("api_token")

            if not api_url or not api_token:
                logger.error("QRadar API credentials not configured")
                return []

            headers = {"SEC": api_token, "Content-Type": "application/json"}

            if since is None:
                since = datetime.now() - timedelta(hours=24)

            since_epoch = int(since.timestamp() * 1000)

            # Get offenses (alerts)
            offenses_url = f"{api_url}/api/siem/offenses"
            params = {"start_time": since_epoch}

            response = self.http_client.get(offenses_url, headers=headers, params=params)
            offenses = response.json()

            alerts = []
            for offense in offenses[:100]:
                alerts.append(
                    {
                        "alert_id": str(offense.get("id", "")),
                        "title": offense.get("description", ""),
                        "severity": self._map_qradar_severity(offense.get("severity", 0)),
                        "description": offense.get("description", ""),
                        "source": "QRadar",
                        "affected_assets": [],
                        "alert_time": datetime.fromtimestamp(offense.get("start_time", 0) / 1000).isoformat(),
                    }
                )

            logger.info(f"Synced {len(alerts)} alerts from QRadar")
            return alerts

        except Exception as e:
            logger.error(f"Failed to sync alerts from QRadar: {e}", exc_info=True)
            return []

    def _map_qradar_severity(self, severity: int) -> str:
        """Map QRadar severity (0-10) to standard severity."""
        if severity >= 8:
            return "critical"
        elif severity >= 5:
            return "high"
        elif severity >= 3:
            return "medium"
        else:
            return "low"

    def test_connection(self) -> bool:
        """Test QRadar connection."""
        try:
            api_url = self.config.get("api_url")
            api_token = self.config.get("api_token")

            if not api_url or not api_token:
                return False

            headers = {"SEC": api_token}
            test_url = f"{api_url}/api/system/about"

            response = self.http_client.get(test_url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"QRadar connection test failed: {e}")
            return False


class ElasticSIEMClient(SIEMClient):
    """Elastic SIEM client."""

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Sync alerts from Elastic.

        Args:
            since: Only fetch alerts since this datetime

        Returns:
            List of alert records
        """
        try:
            api_url = self.config.get("api_url")
            api_key = self.config.get("api_key")

            if not api_url or not api_key:
                logger.error("Elastic API credentials not configured")
                return []

            headers = {"Authorization": f"ApiKey {api_key}", "Content-Type": "application/json"}

            if since is None:
                since = datetime.now() - timedelta(hours=24)

            # Elasticsearch query
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": since.isoformat(),
                        }
                    }
                },
                "size": 100,
            }

            search_url = f"{api_url}/.siem-signals-*/_search"
            response = self.http_client.post(search_url, headers=headers, json=query)
            hits = response.json().get("hits", {}).get("hits", [])

            alerts = []
            for hit in hits:
                source = hit.get("_source", {})
                alerts.append(
                    {
                        "alert_id": hit.get("_id", ""),
                        "title": source.get("signal", {}).get("rule", {}).get("name", ""),
                        "severity": source.get("signal", {}).get("rule", {}).get("severity", "medium"),
                        "description": source.get("signal", {}).get("rule", {}).get("description", ""),
                        "source": "Elastic",
                        "affected_assets": [],
                        "alert_time": source.get("@timestamp", datetime.now().isoformat()),
                    }
                )

            logger.info(f"Synced {len(alerts)} alerts from Elastic")
            return alerts

        except Exception as e:
            logger.error(f"Failed to sync alerts from Elastic: {e}", exc_info=True)
            return []

    def test_connection(self) -> bool:
        """Test Elastic connection."""
        try:
            api_url = self.config.get("api_url")
            api_key = self.config.get("api_key")

            if not api_url or not api_key:
                return False

            headers = {"Authorization": f"ApiKey {api_key}"}
            test_url = f"{api_url}/_cluster/health"

            response = self.http_client.get(test_url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Elastic connection test failed: {e}")
            return False


class MockSIEMClient(SIEMClient):
    """Mock SIEM client for development/testing."""

    def __init__(self, connection: SIEMConnection):
        """Initialize mock SIEM client without HTTP client."""
        self.connection = connection
        self.config = connection.connection_config
        # Don't initialize HTTP client for mock

    def sync_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Return mock alert data."""
        if since is None:
            since = datetime.now() - timedelta(hours=24)

        return [
            {
                "alert_id": "ALERT-001",
                "title": "Suspicious Login Activity",
                "severity": "high",
                "description": "Multiple failed login attempts detected",
                "source": "Active Directory",
                "affected_assets": ["DEVICE-001", "DEVICE-002"],
                "alert_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
            {
                "alert_id": "ALERT-002",
                "title": "Malware Detection",
                "severity": "critical",
                "description": "Malware detected on endpoint",
                "source": "Defender",
                "affected_assets": ["DEVICE-003"],
                "alert_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            },
        ]

    def test_connection(self) -> bool:
        """Return True for mock connection test."""
        return True


def get_siem_client(connection: SIEMConnection) -> SIEMClient:
    """
    Factory function to get appropriate SIEM client.

    Args:
        connection: SIEMConnection instance

    Returns:
        SIEM client instance
    """
    siem_type = connection.siem_type

    if siem_type == SIEMConnection.SIEMType.SENTINEL:
        return SentinelSIEMClient(connection)
    elif siem_type == SIEMConnection.SIEMType.SPLUNK:
        return SplunkSIEMClient(connection)
    elif siem_type == SIEMConnection.SIEMType.QRADAR:
        return QRadarSIEMClient(connection)
    elif siem_type == SIEMConnection.SIEMType.ELASTIC:
        return ElasticSIEMClient(connection)
    else:
        # Fallback to mock for unknown types
        logger.warning(f"Unknown SIEM type: {siem_type}, using mock client")
        return MockSIEMClient(connection)
