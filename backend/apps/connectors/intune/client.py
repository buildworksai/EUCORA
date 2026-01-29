# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Intune connector client using Microsoft Graph API.

Implements core operations for Windows application deployment:
- List managed devices
- Create Win32 application
- Assign application to groups
- Query application assignment status
- Get deployment status

API Reference: https://learn.microsoft.com/en-us/graph/api/resources/intune-graph-overview
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from apps.core.resilient_http import CircuitBreakerOpen, ResilientAPIClient, ResilientAPIError
from apps.core.structured_logging import StructuredLogger

from .auth import IntuneAuth, IntuneAuthError

logger = logging.getLogger(__name__)


class IntuneConnectorError(Exception):
    """Intune connector error."""

    def __init__(self, message: str, correlation_id: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.correlation_id = correlation_id
        self.details = details or {}
        super().__init__(message)


class IntuneConnector:
    """
    Microsoft Intune connector for Windows application deployment.

    Uses Microsoft Graph API with OAuth 2.0 authentication.
    """

    # Microsoft Graph API base URL
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        """Initialize Intune connector."""
        # Initialize authentication
        try:
            self.auth = IntuneAuth()
        except IntuneAuthError as e:
            raise IntuneConnectorError(f"Intune authentication initialization failed: {e.message}")

        # Initialize API client
        self.client = ResilientAPIClient(
            service_name="intune",
            base_url=self.GRAPH_API_BASE,
            timeout=30,
        )

        self.structured_logger = StructuredLogger(__name__, user="system")

    def _get_auth_headers(self, correlation_id: Optional[str] = None) -> Dict[str, str]:
        """Get authorization headers with access token."""
        try:
            access_token = self.auth.get_access_token(correlation_id=correlation_id)
            return {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        except IntuneAuthError as e:
            raise IntuneConnectorError(
                f"Failed to get access token: {e.message}", correlation_id=correlation_id, details=e.details
            )

    def list_managed_devices(
        self, top: int = 100, filter_query: Optional[str] = None, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List managed devices in Intune.

        Args:
            top: Maximum number of devices to return (default: 100, max: 999)
            filter_query: OData filter query (e.g., "operatingSystem eq 'Windows'")
            correlation_id: Correlation ID for tracing

        Returns:
            List of managed device objects

        Raises:
            IntuneConnectorError: If API call fails
            CircuitBreakerOpen: If Intune service is unavailable
        """
        self.structured_logger.connector_event(
            connector_type="intune",
            operation="LIST_MANAGED_DEVICES",
            correlation_id=correlation_id or "UNKNOWN",
            outcome="STARTED",
        )

        try:
            headers = self._get_auth_headers(correlation_id)
            params = {"$top": str(min(top, 999))}

            if filter_query:
                params["$filter"] = filter_query

            response = self.client.get(
                endpoint="/deviceManagement/managedDevices",
                headers=headers,
                params=params,
                correlation_id=correlation_id,
            )

            devices = response.get("value", [])

            self.structured_logger.connector_event(
                connector_type="intune",
                operation="LIST_MANAGED_DEVICES",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="SUCCESS",
                details={"device_count": len(devices)},
            )

            return devices

        except CircuitBreakerOpen as e:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="LIST_MANAGED_DEVICES",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="CIRCUIT_OPEN",
            )
            raise

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="LIST_MANAGED_DEVICES",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="FAILURE",
                details={"error": e.message, "status_code": e.status_code},
            )
            raise IntuneConnectorError(
                f"Failed to list managed devices: {e.message}",
                correlation_id=correlation_id,
                details={"status_code": e.status_code},
            )

    def create_win32_app(
        self,
        display_name: str,
        description: str,
        publisher: str,
        file_name: str,
        setup_file_path: str,
        install_command: str,
        uninstall_command: str,
        detection_rules: List[Dict],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create Win32 application in Intune.

        Args:
            display_name: Application display name
            description: Application description
            publisher: Publisher name
            file_name: Installation file name (e.g., 'app.intunewin')
            setup_file_path: Path to setup file within package
            install_command: Install command line
            uninstall_command: Uninstall command line
            detection_rules: List of detection rules (file/registry/script)
            correlation_id: Correlation ID for tracing

        Returns:
            Created application object with ID

        Raises:
            IntuneConnectorError: If API call fails
            CircuitBreakerOpen: If Intune service is unavailable
        """
        self.structured_logger.connector_event(
            connector_type="intune",
            operation="CREATE_WIN32_APP",
            correlation_id=correlation_id or "UNKNOWN",
            outcome="STARTED",
            details={"display_name": display_name},
        )

        # Build app payload
        app_payload = {
            "@odata.type": "#microsoft.graph.win32LobApp",
            "displayName": display_name,
            "description": description,
            "publisher": publisher,
            "fileName": file_name,
            "setupFilePath": setup_file_path,
            "installCommandLine": install_command,
            "uninstallCommandLine": uninstall_command,
            "detectionRules": detection_rules,
            "installExperience": {
                "runAsAccount": "system",  # Run as SYSTEM
            },
            "returnCodes": [
                {"returnCode": 0, "type": "success"},
                {"returnCode": 1707, "type": "success"},  # Already installed
                {"returnCode": 3010, "type": "softReboot"},  # Reboot required
                {"returnCode": 1641, "type": "hardReboot"},  # Reboot initiated
            ],
        }

        try:
            headers = self._get_auth_headers(correlation_id)

            response = self.client.post(
                endpoint="/deviceAppManagement/mobileApps",
                json_data=app_payload,
                headers=headers,
                correlation_id=correlation_id,
            )

            app_id = response.get("id")

            self.structured_logger.connector_event(
                connector_type="intune",
                operation="CREATE_WIN32_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="SUCCESS",
                details={"app_id": app_id, "display_name": display_name},
            )

            self.structured_logger.audit_event(
                action="INTUNE_APP_CREATED",
                resource_type="Win32LobApp",
                resource_id=app_id,
                outcome="SUCCESS",
                details={"display_name": display_name, "publisher": publisher},
            )

            return response

        except CircuitBreakerOpen:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="CREATE_WIN32_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="CIRCUIT_OPEN",
            )
            raise

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="CREATE_WIN32_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="FAILURE",
                details={"error": e.message, "status_code": e.status_code},
            )

            # Check for conflict (app already exists)
            if e.status_code == 409:
                self.structured_logger.info("App already exists (idempotent)", extra={"display_name": display_name})
                # Query existing app
                existing_app = self._find_app_by_name(display_name, correlation_id)
                if existing_app:
                    return existing_app

            raise IntuneConnectorError(
                f"Failed to create Win32 app: {e.message}",
                correlation_id=correlation_id,
                details={"status_code": e.status_code},
            )

    def assign_app_to_group(
        self, app_id: str, group_id: str, intent: str = "required", correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign application to Azure AD group.

        Args:
            app_id: Application ID
            group_id: Azure AD group ID
            intent: Assignment intent ('required', 'available', 'uninstall')
            correlation_id: Correlation ID for tracing

        Returns:
            Assignment object

        Raises:
            IntuneConnectorError: If API call fails
            CircuitBreakerOpen: If Intune service is unavailable
        """
        self.structured_logger.connector_event(
            connector_type="intune",
            operation="ASSIGN_APP",
            correlation_id=correlation_id or "UNKNOWN",
            outcome="STARTED",
            details={"app_id": app_id, "group_id": group_id, "intent": intent},
        )

        # Build assignment payload
        assignment_payload = {
            "mobileAppAssignments": [
                {
                    "@odata.type": "#microsoft.graph.mobileAppAssignment",
                    "intent": intent,
                    "target": {
                        "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                        "groupId": group_id,
                    },
                }
            ]
        }

        try:
            headers = self._get_auth_headers(correlation_id)

            response = self.client.post(
                endpoint=f"/deviceAppManagement/mobileApps/{app_id}/assign",
                json_data=assignment_payload,
                headers=headers,
                correlation_id=correlation_id,
            )

            self.structured_logger.connector_event(
                connector_type="intune",
                operation="ASSIGN_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="SUCCESS",
                details={"app_id": app_id, "group_id": group_id},
            )

            self.structured_logger.audit_event(
                action="INTUNE_APP_ASSIGNED",
                resource_type="MobileAppAssignment",
                resource_id=app_id,
                outcome="SUCCESS",
                details={"group_id": group_id, "intent": intent},
            )

            return response

        except CircuitBreakerOpen:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="ASSIGN_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="CIRCUIT_OPEN",
            )
            raise

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="ASSIGN_APP",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="FAILURE",
                details={"error": e.message, "status_code": e.status_code},
            )
            raise IntuneConnectorError(
                f"Failed to assign app: {e.message}",
                correlation_id=correlation_id,
                details={"status_code": e.status_code},
            )

    def get_app_install_status(
        self, app_id: str, top: int = 100, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get application installation status across devices.

        Args:
            app_id: Application ID
            top: Maximum number of statuses to return
            correlation_id: Correlation ID for tracing

        Returns:
            List of install status objects

        Raises:
            IntuneConnectorError: If API call fails
            CircuitBreakerOpen: If Intune service is unavailable
        """
        self.structured_logger.connector_event(
            connector_type="intune",
            operation="GET_APP_STATUS",
            correlation_id=correlation_id or "UNKNOWN",
            outcome="STARTED",
            details={"app_id": app_id},
        )

        try:
            headers = self._get_auth_headers(correlation_id)
            params = {"$top": str(min(top, 999))}

            response = self.client.get(
                endpoint=f"/deviceAppManagement/mobileApps/{app_id}/deviceStatuses",
                headers=headers,
                params=params,
                correlation_id=correlation_id,
            )

            statuses = response.get("value", [])

            self.structured_logger.connector_event(
                connector_type="intune",
                operation="GET_APP_STATUS",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="SUCCESS",
                details={"status_count": len(statuses)},
            )

            return statuses

        except CircuitBreakerOpen:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="GET_APP_STATUS",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="CIRCUIT_OPEN",
            )
            raise

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                connector_type="intune",
                operation="GET_APP_STATUS",
                correlation_id=correlation_id or "UNKNOWN",
                outcome="FAILURE",
                details={"error": e.message, "status_code": e.status_code},
            )
            raise IntuneConnectorError(
                f"Failed to get app install status: {e.message}",
                correlation_id=correlation_id,
                details={"status_code": e.status_code},
            )

    def _find_app_by_name(self, display_name: str, correlation_id: Optional[str] = None) -> Optional[Dict]:
        """Find application by display name (for idempotent operations)."""
        try:
            headers = self._get_auth_headers(correlation_id)
            params = {"$filter": f"displayName eq '{display_name}'"}

            response = self.client.get(
                endpoint="/deviceAppManagement/mobileApps",
                headers=headers,
                params=params,
                correlation_id=correlation_id,
            )

            apps = response.get("value", [])
            return apps[0] if apps else None

        except Exception as e:
            self.structured_logger.warning(f"Failed to find app by name: {e}")
            return None

    def close(self) -> None:
        """Close clients and release resources."""
        self.client.close()
        self.auth.close()
