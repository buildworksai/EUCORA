# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft SCCM (Configuration Manager) connector client.

Implements SCCM AdminService REST API operations for:
- Application management (create, update, delete)
- Package distribution to Distribution Points
- Collection targeting and deployment
- Compliance status queries
- Rollback operations

AdminService API Documentation:
https://learn.microsoft.com/en-us/mem/configmgr/develop/adminservice/overview
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from decouple import config

from apps.core.structured_logging import StructuredLogger

from .auth import SCCMAuth, SCCMAuthError

logger = logging.getLogger(__name__)


class SCCMConnectorError(Exception):
    """SCCM connector error."""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        is_transient: bool = False,
        details: Optional[Dict] = None,
    ):
        self.message = message
        self.error_type = error_type  # transient, permanent, policy_violation
        self.is_transient = is_transient  # True = retry, False = fail
        self.details = details or {}
        super().__init__(message)


class SCCMConnector:
    """
    Microsoft SCCM connector for application deployment.

    Provides idempotent operations for application management,
    distribution point management, and deployment targeting.
    """

    # AdminService API endpoints
    API_APPLICATIONS = "/wmi/SMS_Application"
    API_PACKAGES = "/wmi/SMS_Package"
    API_COLLECTIONS = "/wmi/SMS_Collection"
    API_DISTRIBUTION_POINTS = "/wmi/SMS_DistributionPoint"
    API_DEPLOYMENTS = "/wmi/SMS_ApplicationAssignment"
    API_COMPLIANCE = "/wmi/SMS_AppDeploymentAssetDetails"

    # Idempotency key cache (in production, use Redis)
    _idempotency_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, auth: Optional[SCCMAuth] = None):
        """
        Initialize SCCM connector.

        Args:
            auth: SCCMAuth instance (creates new one if not provided)
        """
        self.auth = auth or SCCMAuth()
        self.server_url = self.auth.server_url
        self.site_code = self.auth.site_code
        self.structured_logger = StructuredLogger(__name__, user="system")
        self._default_timeout = 60

    def get_idempotency_key(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Generate idempotency key for operation.

        Args:
            operation: Operation name (e.g., "create_application")
            params: Operation parameters

        Returns:
            Idempotency key string
        """
        key_data = json.dumps({"operation": operation, "params": params}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _check_idempotency(self, key: str, correlation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check if operation was already performed."""
        cached = self._idempotency_cache.get(key)
        if cached:
            self.structured_logger.log_info(
                "Idempotent operation - returning cached result",
                extra={"idempotency_key": key, "correlation_id": correlation_id},
            )
        return cached

    def _store_idempotency(self, key: str, result: Dict[str, Any], correlation_id: Optional[str] = None) -> None:
        """Store operation result for idempotency."""
        self._idempotency_cache[key] = result
        self.structured_logger.log_debug(
            "Stored idempotency result",
            extra={"idempotency_key": key, "correlation_id": correlation_id},
        )

    async def test_connection(self, correlation_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Test connection to SCCM.

        Args:
            correlation_id: Correlation ID for logging

        Returns:
            Tuple of (success: bool, message: str)
        """
        return self.auth.test_connection(correlation_id)

    async def sync_inventory(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync application inventory from SCCM.

        Args:
            correlation_id: Correlation ID for logging

        Returns:
            Dictionary with sync results
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        try:
            session = self.auth.get_session(correlation_id)

            # Get all applications
            url = f"{self.server_url}{self.API_APPLICATIONS}"
            response = session.get(url, timeout=self._default_timeout)
            response.raise_for_status()

            data = response.json()
            applications = data.get("value", [])

            self.structured_logger.log_info(
                "SCCM inventory synced",
                extra={
                    "correlation_id": correlation_id,
                    "application_count": len(applications),
                },
            )

            return {
                "success": True,
                "applications": applications,
                "count": len(applications),
                "synced_at": datetime.utcnow().isoformat(),
            }

        except requests.exceptions.HTTPError as e:
            raise SCCMConnectorError(
                f"Failed to sync inventory: {e}",
                error_type="transient" if e.response.status_code >= 500 else "permanent",
                is_transient=e.response.status_code >= 500,
                details={"status_code": e.response.status_code},
            )
        except Exception as e:
            raise SCCMConnectorError(
                f"Inventory sync error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def create_application(
        self,
        name: str,
        version: str,
        publisher: str,
        content_location: str,
        install_command: str,
        uninstall_command: str,
        detection_script: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create application in SCCM.

        Args:
            name: Application name
            version: Application version
            publisher: Application publisher
            content_location: UNC path to content
            install_command: Installation command line
            uninstall_command: Uninstallation command line
            detection_script: Optional PowerShell detection script
            correlation_id: Correlation ID for logging

        Returns:
            Created application details
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        # Check idempotency
        idem_key = self.get_idempotency_key("create_application", {"name": name, "version": version})
        cached = self._check_idempotency(idem_key, correlation_id)
        if cached:
            return cached

        try:
            session = self.auth.get_session(correlation_id)

            # Check if application already exists
            existing = await self._find_application_by_name(name, version, session)
            if existing:
                self.structured_logger.log_info(
                    "Application already exists",
                    extra={
                        "name": name,
                        "version": version,
                        "ci_unique_id": existing.get("CI_UniqueID"),
                    },
                )
                result = {
                    "success": True,
                    "created": False,
                    "application": existing,
                    "message": "Application already exists",
                }
                self._store_idempotency(idem_key, result, correlation_id)
                return result

            # Create application via AdminService
            # Note: Full implementation requires XML-based Application Model
            # This is a simplified version using WMI wrapper
            app_data = {
                "LocalizedDisplayName": name,
                "SoftwareVersion": version,
                "Manufacturer": publisher,
                "LocalizedDescription": f"Deployed via EUCORA Control Plane",
            }

            url = f"{self.server_url}{self.API_APPLICATIONS}"
            response = session.post(url, json=app_data, timeout=self._default_timeout)

            if response.status_code == 409:
                # Application already exists - find and return it
                existing = await self._find_application_by_name(name, version, session)
                result = {
                    "success": True,
                    "created": False,
                    "application": existing,
                    "message": "Application already exists (conflict)",
                }
                self._store_idempotency(idem_key, result, correlation_id)
                return result

            response.raise_for_status()
            created_app = response.json()

            self.structured_logger.log_info(
                "SCCM application created",
                extra={
                    "name": name,
                    "version": version,
                    "ci_unique_id": created_app.get("CI_UniqueID"),
                },
            )

            result = {
                "success": True,
                "created": True,
                "application": created_app,
                "message": "Application created successfully",
            }
            self._store_idempotency(idem_key, result, correlation_id)
            return result

        except SCCMConnectorError:
            raise
        except requests.exceptions.HTTPError as e:
            raise SCCMConnectorError(
                f"Failed to create application: {e}",
                error_type="transient" if e.response.status_code >= 500 else "permanent",
                is_transient=e.response.status_code >= 500,
                details={"status_code": e.response.status_code, "name": name},
            )
        except Exception as e:
            raise SCCMConnectorError(
                f"Application creation error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def _find_application_by_name(
        self,
        name: str,
        version: Optional[str],
        session: requests.Session,
    ) -> Optional[Dict[str, Any]]:
        """Find application by name and optionally version."""
        try:
            filter_query = f"LocalizedDisplayName eq '{name}'"
            if version:
                filter_query += f" and SoftwareVersion eq '{version}'"

            url = f"{self.server_url}{self.API_APPLICATIONS}?$filter={filter_query}"
            response = session.get(url, timeout=self._default_timeout)
            response.raise_for_status()

            data = response.json()
            apps = data.get("value", [])
            return apps[0] if apps else None
        except Exception as e:
            self.structured_logger.log_warning(f"Error finding application: {e}", extra={"name": name})
            return None

    async def distribute_content(
        self,
        application_id: str,
        distribution_point_groups: List[str],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Distribute application content to Distribution Points.

        Args:
            application_id: SCCM application CI_UniqueID
            distribution_point_groups: List of DP group names
            correlation_id: Correlation ID for logging

        Returns:
            Distribution status
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        # Check idempotency
        idem_key = self.get_idempotency_key(
            "distribute_content",
            {"application_id": application_id, "dp_groups": distribution_point_groups},
        )
        cached = self._check_idempotency(idem_key, correlation_id)
        if cached:
            return cached

        try:
            session = self.auth.get_session(correlation_id)

            # Distribute to each DP group
            results = []
            for dp_group in distribution_point_groups:
                # AdminService distribute content call
                url = f"{self.server_url}/wmi/SMS_DistributionPointGroup('{dp_group}')/AdminService.DistributeContent"
                payload = {"PackageIDs": [application_id]}

                response = session.post(url, json=payload, timeout=self._default_timeout)

                if response.status_code in [200, 201, 204]:
                    results.append({"dp_group": dp_group, "status": "initiated"})
                else:
                    results.append({"dp_group": dp_group, "status": "failed", "code": response.status_code})

            self.structured_logger.log_info(
                "Content distribution initiated",
                extra={
                    "application_id": application_id,
                    "dp_groups": distribution_point_groups,
                    "results": results,
                },
            )

            result = {
                "success": all(r["status"] == "initiated" for r in results),
                "distribution_results": results,
                "message": "Content distribution initiated",
            }
            self._store_idempotency(idem_key, result, correlation_id)
            return result

        except Exception as e:
            raise SCCMConnectorError(
                f"Content distribution error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def deploy_to_collection(
        self,
        application_id: str,
        collection_id: str,
        deployment_action: str = "Install",
        deployment_purpose: str = "Required",
        schedule: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deploy application to a collection.

        Args:
            application_id: SCCM application CI_UniqueID
            collection_id: Target collection ID
            deployment_action: Install or Uninstall
            deployment_purpose: Required or Available
            schedule: Optional deployment schedule
            correlation_id: Correlation ID for logging

        Returns:
            Deployment details
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        # Check idempotency
        idem_key = self.get_idempotency_key(
            "deploy_to_collection",
            {
                "application_id": application_id,
                "collection_id": collection_id,
                "action": deployment_action,
            },
        )
        cached = self._check_idempotency(idem_key, correlation_id)
        if cached:
            return cached

        try:
            session = self.auth.get_session(correlation_id)

            # Create deployment (ApplicationAssignment)
            deployment_data = {
                "ApplicationName": application_id,
                "AssignmentName": f"EUCORA_{application_id}_{collection_id}",
                "CollectionName": collection_id,
                "DesiredConfigType": 1 if deployment_action == "Install" else 2,
                "OfferTypeID": 0 if deployment_purpose == "Required" else 2,
                "WoLEnabled": False,
                "RebootOutsideOfServiceWindows": False,
                "OverrideServiceWindows": False,
            }

            if schedule:
                deployment_data["AssignedCIs"] = schedule

            url = f"{self.server_url}{self.API_DEPLOYMENTS}"
            response = session.post(url, json=deployment_data, timeout=self._default_timeout)

            if response.status_code == 409:
                # Deployment already exists
                result = {
                    "success": True,
                    "created": False,
                    "message": "Deployment already exists",
                }
                self._store_idempotency(idem_key, result, correlation_id)
                return result

            response.raise_for_status()
            deployment = response.json()

            self.structured_logger.log_info(
                "SCCM deployment created",
                extra={
                    "application_id": application_id,
                    "collection_id": collection_id,
                    "assignment_id": deployment.get("AssignmentID"),
                },
            )

            result = {
                "success": True,
                "created": True,
                "deployment": deployment,
                "message": "Deployment created successfully",
            }
            self._store_idempotency(idem_key, result, correlation_id)
            return result

        except SCCMConnectorError:
            raise
        except requests.exceptions.HTTPError as e:
            raise SCCMConnectorError(
                f"Failed to create deployment: {e}",
                error_type="transient" if e.response.status_code >= 500 else "permanent",
                is_transient=e.response.status_code >= 500,
                details={"status_code": e.response.status_code},
            )
        except Exception as e:
            raise SCCMConnectorError(
                f"Deployment creation error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def get_compliance_status(
        self,
        application_id: str,
        collection_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get deployment compliance status.

        Args:
            application_id: SCCM application CI_UniqueID
            collection_id: Optional collection filter
            correlation_id: Correlation ID for logging

        Returns:
            Compliance status summary
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        try:
            session = self.auth.get_session(correlation_id)

            # Query compliance status
            filter_query = f"AppCI eq '{application_id}'"
            if collection_id:
                filter_query += f" and CollectionID eq '{collection_id}'"

            url = f"{self.server_url}{self.API_COMPLIANCE}?$filter={filter_query}"
            response = session.get(url, timeout=self._default_timeout)
            response.raise_for_status()

            data = response.json()
            assets = data.get("value", [])

            # Aggregate compliance status
            status_counts = {
                "installed": 0,
                "failed": 0,
                "pending": 0,
                "unknown": 0,
            }

            for asset in assets:
                status = asset.get("StatusType", 0)
                if status == 1:
                    status_counts["installed"] += 1
                elif status == 2:
                    status_counts["failed"] += 1
                elif status == 3:
                    status_counts["pending"] += 1
                else:
                    status_counts["unknown"] += 1

            total = sum(status_counts.values())
            success_rate = status_counts["installed"] / total * 100 if total > 0 else 0

            self.structured_logger.log_info(
                "SCCM compliance status retrieved",
                extra={
                    "application_id": application_id,
                    "collection_id": collection_id,
                    "total_devices": total,
                    "success_rate": success_rate,
                },
            )

            return {
                "success": True,
                "application_id": application_id,
                "collection_id": collection_id,
                "total_devices": total,
                "status_counts": status_counts,
                "success_rate": round(success_rate, 2),
                "queried_at": datetime.utcnow().isoformat(),
            }

        except requests.exceptions.HTTPError as e:
            raise SCCMConnectorError(
                f"Failed to get compliance status: {e}",
                error_type="transient" if e.response.status_code >= 500 else "permanent",
                is_transient=e.response.status_code >= 500,
            )
        except Exception as e:
            raise SCCMConnectorError(
                f"Compliance query error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def rollback(
        self,
        deployment_id: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rollback a deployment (delete deployment assignment).

        Args:
            deployment_id: SCCM deployment assignment ID
            correlation_id: Correlation ID for logging

        Returns:
            Rollback result
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        try:
            session = self.auth.get_session(correlation_id)

            # Delete deployment assignment
            url = f"{self.server_url}{self.API_DEPLOYMENTS}('{deployment_id}')"
            response = session.delete(url, timeout=self._default_timeout)

            if response.status_code == 404:
                self.structured_logger.log_warning(
                    "Deployment not found for rollback",
                    extra={"deployment_id": deployment_id},
                )
                return {
                    "success": True,
                    "message": "Deployment not found (already deleted)",
                }

            response.raise_for_status()

            self.structured_logger.log_info(
                "SCCM deployment rolled back",
                extra={"deployment_id": deployment_id},
            )

            return {
                "success": True,
                "deployment_id": deployment_id,
                "message": "Deployment rolled back successfully",
            }

        except requests.exceptions.HTTPError as e:
            raise SCCMConnectorError(
                f"Failed to rollback deployment: {e}",
                error_type="transient" if e.response.status_code >= 500 else "permanent",
                is_transient=e.response.status_code >= 500,
            )
        except Exception as e:
            raise SCCMConnectorError(
                f"Rollback error: {e}",
                error_type="transient",
                is_transient=True,
            )

    async def list_collections(
        self,
        collection_type: str = "Device",
        correlation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List available collections.

        Args:
            collection_type: Device or User
            correlation_id: Correlation ID for logging

        Returns:
            List of collections
        """
        if correlation_id:
            self.structured_logger.correlation_id = correlation_id

        try:
            session = self.auth.get_session(correlation_id)

            # Collection type: 1 = User, 2 = Device
            type_filter = 2 if collection_type == "Device" else 1
            url = f"{self.server_url}{self.API_COLLECTIONS}?$filter=CollectionType eq {type_filter}"

            response = session.get(url, timeout=self._default_timeout)
            response.raise_for_status()

            data = response.json()
            collections = data.get("value", [])

            self.structured_logger.log_info(
                "SCCM collections retrieved",
                extra={"collection_type": collection_type, "count": len(collections)},
            )

            return collections

        except Exception as e:
            raise SCCMConnectorError(
                f"Failed to list collections: {e}",
                error_type="transient",
                is_transient=True,
            )
