# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Jamf Pro connector for macOS device and application management.

Provides integration with Jamf Pro API for:
- Device inventory management
- macOS application deployment (PKG packages)
- Policy-based deployments
- Application installation status tracking

Configuration (environment variables):
- JAMF_SERVER_URL: Jamf Pro server URL
- JAMF_CLIENT_ID: OAuth 2.0 client ID (preferred)
- JAMF_CLIENT_SECRET: OAuth 2.0 client secret (preferred)
- JAMF_USERNAME: Basic auth username (fallback)
- JAMF_PASSWORD: Basic auth password (fallback)

Example:
    connector = JamfConnector()
    computers = connector.list_computers(correlation_id='DEPLOY-123')
    package_id = connector.create_package('MyApp.pkg', 'MyApp', correlation_id='DEPLOY-456')
"""
import logging
from typing import Any, Dict, List, Optional

from apps.connectors.jamf.auth import JamfAuth, JamfAuthError
from apps.core.circuit_breaker import CircuitBreakerOpen
from apps.core.resilient_http import ResilientAPIClient, ResilientAPIError
from apps.core.structured_logging import StructuredLogger

logger = logging.getLogger(__name__)


class JamfConnectorError(Exception):
    """Exception raised for Jamf connector errors."""

    def __init__(self, message: str, correlation_id: Optional[str] = None, status_code: Optional[int] = None):
        self.message = message
        self.correlation_id = correlation_id
        self.status_code = status_code
        super().__init__(self.message)


class JamfConnector:
    """
    Jamf Pro connector for macOS device and application management.

    Integrates with Jamf Pro API for device management, package deployment,
    and policy-based application distribution.
    """

    def __init__(self):
        """
        Initialize Jamf connector.

        Raises:
            JamfAuthError: If authentication configuration is invalid
        """
        # Initialize auth
        self.auth = JamfAuth()

        # Initialize API client with Jamf server URL
        self.client = ResilientAPIClient(service_name="jamf", base_url=self.auth.server_url, timeout=30)

        # Initialize structured logger
        self.structured_logger = StructuredLogger(__name__, user="system")

        logger.info(f"Jamf connector initialized (server={self.auth.server_url})")

    def _get_auth_headers(self, correlation_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get authorization headers with access token.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Headers dict with Authorization and Accept headers
        """
        token = self.auth.get_access_token(correlation_id=correlation_id)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def list_computers(
        self,
        page: int = 0,
        page_size: int = 100,
        sort: Optional[str] = None,
        filter_query: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List managed computers (macOS devices) in Jamf Pro.

        Uses Jamf Pro API v1 for computer inventory.

        Args:
            page: Page number (0-indexed)
            page_size: Results per page (max 2000)
            sort: Sort expression (e.g., 'general.name:asc')
            filter_query: RSQL filter query (e.g., 'general.platform=="Mac"')
            correlation_id: Correlation ID for tracing

        Returns:
            Dict with 'totalCount' and 'results' list of computer objects

        Raises:
            JamfConnectorError: If API call fails
            CircuitBreakerOpen: If circuit breaker is open
        """
        self.structured_logger.connector_event("jamf", "LIST_COMPUTERS", "STARTED", correlation_id)

        try:
            headers = self._get_auth_headers(correlation_id)
            params: Dict[str, str] = {
                "page": str(page),
                "page-size": str(min(page_size, 2000)),
            }

            if sort:
                params["sort"] = sort

            if filter_query:
                params["filter"] = filter_query

            response = self.client.get(
                "/api/v1/computers-inventory", headers=headers, params=params, correlation_id=correlation_id
            )

            computers = response.get("results", [])
            total_count = response.get("totalCount", len(computers))

            self.structured_logger.connector_event(
                "jamf",
                "LIST_COMPUTERS",
                "SUCCESS",
                correlation_id,
                {"computer_count": len(computers), "total_count": total_count},
            )

            return response

        except CircuitBreakerOpen:
            self.structured_logger.connector_event("jamf", "LIST_COMPUTERS", "CIRCUIT_OPEN", correlation_id)
            raise

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                "jamf", "LIST_COMPUTERS", "FAILURE", correlation_id, {"error": e.message, "status_code": e.status_code}
            )
            raise JamfConnectorError(
                f"Failed to list computers: {e.message}", correlation_id=correlation_id, status_code=e.status_code
            ) from e

    def get_computer_by_id(self, computer_id: str, correlation_id: Optional[str] = None) -> Dict:
        """
        Get detailed information for a specific computer.

        Args:
            computer_id: Computer ID (UUID or integer ID)
            correlation_id: Correlation ID for tracing

        Returns:
            Computer details dict

        Raises:
            JamfConnectorError: If API call fails
        """
        self.structured_logger.connector_event(
            "jamf", "GET_COMPUTER", "STARTED", correlation_id, {"computer_id": computer_id}
        )

        try:
            headers = self._get_auth_headers(correlation_id)

            response = self.client.get(
                f"/api/v1/computers-inventory-detail/{computer_id}", headers=headers, correlation_id=correlation_id
            )

            self.structured_logger.connector_event(
                "jamf", "GET_COMPUTER", "SUCCESS", correlation_id, {"computer_id": computer_id}
            )

            return response

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                "jamf",
                "GET_COMPUTER",
                "FAILURE",
                correlation_id,
                {"computer_id": computer_id, "error": e.message, "status_code": e.status_code},
            )
            raise JamfConnectorError(
                f"Failed to get computer {computer_id}: {e.message}",
                correlation_id=correlation_id,
                status_code=e.status_code,
            ) from e

    def create_package(
        self,
        package_name: str,
        file_name: str,
        category: Optional[str] = None,
        info: Optional[str] = None,
        notes: Optional[str] = None,
        priority: int = 10,
        fill_user_template: bool = False,
        fill_existing_users: bool = False,
        boot_volume_required: bool = True,
        correlation_id: Optional[str] = None,
    ) -> Dict:
        """
        Create a package record in Jamf Pro.

        Note: This creates the package metadata only. The actual PKG file must be
        uploaded separately using Jamf Admin or the file upload API.

        Args:
            package_name: Package display name
            file_name: PKG file name (e.g., 'MyApp-1.0.pkg')
            category: Package category
            info: Package information/description
            notes: Package notes
            priority: Installation priority (1-20, default 10)
            fill_user_template: Fill user template
            fill_existing_users: Fill existing users
            boot_volume_required: Require boot volume
            correlation_id: Correlation ID for tracing

        Returns:
            Created package dict with 'id'

        Raises:
            JamfConnectorError: If API call fails
        """
        self.structured_logger.connector_event(
            "jamf", "CREATE_PACKAGE", "STARTED", correlation_id, {"package_name": package_name, "file_name": file_name}
        )

        try:
            headers = self._get_auth_headers(correlation_id)
            headers["Content-Type"] = "application/json"

            package_payload = {
                "packageName": package_name,
                "fileName": file_name,
                "categoryId": category if category else "-1",
                "info": info or "",
                "notes": notes or "",
                "priority": priority,
                "fillUserTemplate": fill_user_template,
                "fillExistingUsers": fill_existing_users,
                "bootVolumeRequired": boot_volume_required,
                "rebootRequired": False,
                "osRequirements": "",
            }

            response = self.client.post(
                "/api/v1/packages", json_data=package_payload, headers=headers, correlation_id=correlation_id
            )

            package_id = response.get("id")

            self.structured_logger.connector_event(
                "jamf",
                "CREATE_PACKAGE",
                "SUCCESS",
                correlation_id,
                {"package_id": package_id, "package_name": package_name},
            )

            self.structured_logger.audit_event(
                action="JAMF_PACKAGE_CREATED",
                resource_type="JamfPackage",
                resource_id=str(package_id),
                outcome="SUCCESS",
                details={"package_name": package_name, "file_name": file_name},
            )

            return response

        except ResilientAPIError as e:
            # Handle idempotent operation (409 conflict)
            if e.status_code == 409:
                existing_package = self._find_package_by_name(package_name, correlation_id)
                if existing_package:
                    self.structured_logger.connector_event(
                        "jamf",
                        "CREATE_PACKAGE",
                        "SUCCESS",
                        correlation_id,
                        {"package_id": existing_package["id"], "package_name": package_name, "idempotent": True},
                    )
                    return existing_package

            self.structured_logger.connector_event(
                "jamf",
                "CREATE_PACKAGE",
                "FAILURE",
                correlation_id,
                {"package_name": package_name, "error": e.message, "status_code": e.status_code},
            )
            raise JamfConnectorError(
                f"Failed to create package: {e.message}", correlation_id=correlation_id, status_code=e.status_code
            ) from e

    def _find_package_by_name(self, package_name: str, correlation_id: Optional[str] = None) -> Optional[Dict]:
        """
        Find existing package by name (for idempotent operations).

        Args:
            package_name: Package name to search for
            correlation_id: Correlation ID for tracing

        Returns:
            Package dict if found, None otherwise
        """
        try:
            headers = self._get_auth_headers(correlation_id)
            params = {"filter": f'packageName=="{package_name}"'}

            response = self.client.get(
                "/api/v1/packages", headers=headers, params=params, correlation_id=correlation_id
            )

            results = response.get("results", [])
            if results:
                return results[0]

            return None

        except Exception as e:
            logger.warning(f"Failed to find package by name: {str(e)}")
            return None

    def create_policy(
        self,
        policy_name: str,
        package_id: str,
        scope: Dict[str, Any],
        enabled: bool = True,
        frequency: str = "Once per computer",
        category: Optional[str] = None,
        trigger_checkin: bool = True,
        trigger_enrollment: bool = False,
        trigger_startup: bool = False,
        correlation_id: Optional[str] = None,
    ) -> Dict:
        """
        Create a policy for package deployment.

        Policies in Jamf Pro define deployment rules, scope, triggers, and execution frequency.

        Args:
            policy_name: Policy display name
            package_id: Package ID to deploy
            scope: Policy scope dict with 'computers', 'computerGroups', 'buildings', 'departments'
            enabled: Enable policy immediately
            frequency: Execution frequency ('Once per computer', 'Ongoing', etc.)
            category: Policy category
            trigger_checkin: Trigger on check-in
            trigger_enrollment: Trigger on enrollment
            trigger_startup: Trigger on startup
            correlation_id: Correlation ID for tracing

        Returns:
            Created policy dict with 'id'

        Raises:
            JamfConnectorError: If API call fails
        """
        self.structured_logger.connector_event(
            "jamf", "CREATE_POLICY", "STARTED", correlation_id, {"policy_name": policy_name, "package_id": package_id}
        )

        try:
            headers = self._get_auth_headers(correlation_id)
            headers["Content-Type"] = "application/xml"

            # Jamf Classic API uses XML for policies
            policy_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<policy>
    <general>
        <name>{policy_name}</name>
        <enabled>{str(enabled).lower()}</enabled>
        <frequency>{frequency}</frequency>
        <category>
            <name>{category or 'No category assigned'}</name>
        </category>
    </general>
    <scope>
        <all_computers>{str(not scope).lower()}</all_computers>
    </scope>
    <package_configuration>
        <packages>
            <package>
                <id>{package_id}</id>
                <action>Install</action>
            </package>
        </packages>
    </package_configuration>
    <self_service>
        <use_for_self_service>false</use_for_self_service>
    </self_service>
</policy>"""

            # Use Classic API for policy creation (XML-based)
            response = self.client.post(
                "/JSSResource/policies/id/0", data=policy_xml, headers=headers, correlation_id=correlation_id
            )

            # Parse XML response to get policy ID
            policy_id = self._extract_policy_id_from_xml(response)

            self.structured_logger.connector_event(
                "jamf",
                "CREATE_POLICY",
                "SUCCESS",
                correlation_id,
                {"policy_id": policy_id, "policy_name": policy_name, "package_id": package_id},
            )

            self.structured_logger.audit_event(
                action="JAMF_POLICY_CREATED",
                resource_type="JamfPolicy",
                resource_id=str(policy_id),
                outcome="SUCCESS",
                details={"policy_name": policy_name, "package_id": package_id, "enabled": enabled},
            )

            return {"id": policy_id, "name": policy_name}

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                "jamf",
                "CREATE_POLICY",
                "FAILURE",
                correlation_id,
                {"policy_name": policy_name, "error": e.message, "status_code": e.status_code},
            )
            raise JamfConnectorError(
                f"Failed to create policy: {e.message}", correlation_id=correlation_id, status_code=e.status_code
            ) from e

    def _extract_policy_id_from_xml(self, xml_response: Any) -> str:
        """
        Extract policy ID from XML response.

        Args:
            xml_response: XML response from Jamf API

        Returns:
            Policy ID string
        """
        # Simple XML parsing for policy ID
        # In production, use xml.etree.ElementTree for robust parsing
        try:
            import re

            match = re.search(r"<id>(\d+)</id>", str(xml_response))
            if match:
                return match.group(1)
            return "unknown"
        except Exception:
            return "unknown"

    def get_policy_logs(
        self,
        policy_id: str,
        page: int = 0,
        page_size: int = 100,
        correlation_id: Optional[str] = None,
    ) -> Dict:
        """
        Get policy execution logs for deployment status tracking.

        Args:
            policy_id: Policy ID
            page: Page number (0-indexed)
            page_size: Results per page
            correlation_id: Correlation ID for tracing

        Returns:
            Dict with policy log results

        Raises:
            JamfConnectorError: If API call fails
        """
        self.structured_logger.connector_event(
            "jamf", "GET_POLICY_LOGS", "STARTED", correlation_id, {"policy_id": policy_id}
        )

        try:
            headers = self._get_auth_headers(correlation_id)
            params = {
                "page": str(page),
                "page-size": str(min(page_size, 2000)),
            }

            response = self.client.get(
                f"/api/v1/policy-logs/{policy_id}", headers=headers, params=params, correlation_id=correlation_id
            )

            self.structured_logger.connector_event(
                "jamf",
                "GET_POLICY_LOGS",
                "SUCCESS",
                correlation_id,
                {"policy_id": policy_id, "log_count": len(response.get("results", []))},
            )

            return response

        except ResilientAPIError as e:
            self.structured_logger.connector_event(
                "jamf",
                "GET_POLICY_LOGS",
                "FAILURE",
                correlation_id,
                {"policy_id": policy_id, "error": e.message, "status_code": e.status_code},
            )
            raise JamfConnectorError(
                f"Failed to get policy logs: {e.message}", correlation_id=correlation_id, status_code=e.status_code
            ) from e

    def get_computer_applications(
        self,
        computer_id: str,
        correlation_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get installed applications for a specific computer.

        Args:
            computer_id: Computer ID
            correlation_id: Correlation ID for tracing

        Returns:
            List of installed application dicts

        Raises:
            JamfConnectorError: If API call fails
        """
        try:
            computer_details = self.get_computer_by_id(computer_id, correlation_id)
            applications = computer_details.get("applications", [])

            self.structured_logger.connector_event(
                "jamf",
                "GET_COMPUTER_APPS",
                "SUCCESS",
                correlation_id,
                {"computer_id": computer_id, "app_count": len(applications)},
            )

            return applications

        except JamfConnectorError:
            raise

        except Exception as e:
            self.structured_logger.connector_event(
                "jamf", "GET_COMPUTER_APPS", "FAILURE", correlation_id, {"computer_id": computer_id, "error": str(e)}
            )
            raise JamfConnectorError(
                f"Failed to get computer applications: {str(e)}", correlation_id=correlation_id
            ) from e
