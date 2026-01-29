# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Landscape API client for Ubuntu/Linux endpoint management.

Provides integration with Canonical Landscape for:
- Computer inventory and management
- Package deployment and compliance
- Repository management
- Script execution
- Activity monitoring

API Reference: https://landscape.canonical.com/api
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import requests

from apps.core.structured_logging import StructuredLogger

from .auth import LandscapeAuth

logger = logging.getLogger(__name__)


class LandscapeConnectorError(Exception):
    """Exception raised for Landscape connector errors."""

    def __init__(
        self,
        message: str,
        is_transient: bool = False,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        """
        Initialize LandscapeConnectorError.

        Args:
            message: Error description
            is_transient: Whether the error is transient and retryable
            status_code: HTTP status code if applicable
            response_body: Response body if available
        """
        super().__init__(message)
        self.is_transient = is_transient
        self.status_code = status_code
        self.response_body = response_body


class LandscapeConnector:
    """
    Landscape API connector for Linux endpoint management.

    Implements idempotent operations with correlation ID tracking
    for audit trail and reconciliation support.
    """

    # Cache for idempotent operations (TTL: 1 hour)
    _idempotency_cache: dict[str, tuple[dict, float]] = {}
    CACHE_TTL_SECONDS = 3600

    def __init__(self, auth: Optional[LandscapeAuth] = None):
        """
        Initialize Landscape connector.

        Args:
            auth: LandscapeAuth instance. If None, creates from environment.
        """
        self.auth = auth or LandscapeAuth()
        self.server_url = self.auth.server_url
        self.logger = StructuredLogger(__name__)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to Landscape API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body data
            correlation_id: Correlation ID for audit trail

        Returns:
            Response JSON data

        Raises:
            LandscapeConnectorError: If request fails
        """
        url = f"{self.server_url}{endpoint}"
        correlation_id = correlation_id or str(uuid4())

        session = self.auth.get_session()
        headers = {"X-Correlation-ID": correlation_id}

        # Prepare body for signing
        body = json.dumps(json_data) if json_data else ""
        headers = self.auth.sign_request(method, url, headers, body)

        self.logger.info(
            "landscape_api_request",
            method=method,
            endpoint=endpoint,
            correlation_id=correlation_id,
        )

        try:
            response = session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=60,
            )

            # Log response
            self.logger.info(
                "landscape_api_response",
                status_code=response.status_code,
                correlation_id=correlation_id,
            )

            # Handle specific status codes
            if response.status_code == 429:
                raise LandscapeConnectorError(
                    "Rate limit exceeded",
                    is_transient=True,
                    status_code=429,
                )

            if response.status_code >= 500:
                raise LandscapeConnectorError(
                    f"Server error: {response.status_code}",
                    is_transient=True,
                    status_code=response.status_code,
                    response_body=response.text,
                )

            response.raise_for_status()

            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.Timeout:
            raise LandscapeConnectorError(
                "Request timeout",
                is_transient=True,
            )

        except requests.exceptions.ConnectionError as e:
            raise LandscapeConnectorError(
                f"Connection error: {e}",
                is_transient=True,
            )

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            is_transient = status_code in (408, 429, 502, 503, 504) if status_code else False

            raise LandscapeConnectorError(
                f"HTTP error: {e}",
                is_transient=is_transient,
                status_code=status_code,
                response_body=e.response.text if e.response else None,
            )

    def get_idempotency_key(self, operation: str, params: dict) -> str:
        """
        Generate idempotency key for an operation.

        Args:
            operation: Operation name
            params: Operation parameters

        Returns:
            SHA-256 hash of operation + params
        """
        key_data = json.dumps({"operation": operation, "params": params}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached_result(self, idempotency_key: str) -> Optional[dict]:
        """Get cached result if exists and not expired."""
        if idempotency_key in self._idempotency_cache:
            result, timestamp = self._idempotency_cache[idempotency_key]
            if datetime.now().timestamp() - timestamp < self.CACHE_TTL_SECONDS:
                return result
            # Expired, remove from cache
            del self._idempotency_cache[idempotency_key]
        return None

    def _cache_result(self, idempotency_key: str, result: dict) -> None:
        """Cache operation result."""
        self._idempotency_cache[idempotency_key] = (result, datetime.now().timestamp())

    async def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to Landscape server.

        Returns:
            Tuple of (success, message)
        """
        return self.auth.test_connection()

    # =========================================================================
    # Computer Management
    # =========================================================================

    async def list_computers(
        self,
        query: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 1000,
        offset: int = 0,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List computers managed by Landscape.

        Args:
            query: Search query (hostname, IP, etc.)
            tags: Filter by tags
            limit: Maximum results to return
            offset: Pagination offset
            correlation_id: Correlation ID for audit

        Returns:
            Dict with computers list and pagination info
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if query:
            params["query"] = query
        if tags:
            params["tags"] = ",".join(tags)

        response = self._make_request(
            "GET",
            "/api/v2/computers",
            params=params,
            correlation_id=correlation_id,
        )

        computers = response.get("computers", [])

        self.logger.info(
            "landscape_list_computers",
            count=len(computers),
            query=query,
            tags=tags,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "computers": computers,
            "total": response.get("total", len(computers)),
            "limit": limit,
            "offset": offset,
        }

    async def get_computer(
        self,
        computer_id: str,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get detailed information about a computer.

        Args:
            computer_id: Landscape computer ID
            correlation_id: Correlation ID for audit

        Returns:
            Computer details
        """
        response = self._make_request(
            "GET",
            f"/api/v2/computers/{computer_id}",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "computer": response,
        }

    async def get_computer_packages(
        self,
        computer_id: str,
        installed_only: bool = True,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get packages installed on a computer.

        Args:
            computer_id: Landscape computer ID
            installed_only: Only return installed packages
            correlation_id: Correlation ID for audit

        Returns:
            List of packages
        """
        params: dict[str, Any] = {}
        if installed_only:
            params["installed"] = "true"

        response = self._make_request(
            "GET",
            f"/api/v2/computers/{computer_id}/packages",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "packages": response.get("packages", []),
            "computer_id": computer_id,
        }

    async def add_computer_tags(
        self,
        computer_id: str,
        tags: list[str],
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Add tags to a computer.

        Args:
            computer_id: Landscape computer ID
            tags: Tags to add
            correlation_id: Correlation ID for audit

        Returns:
            Operation result
        """
        self._make_request(
            "POST",
            f"/api/v2/computers/{computer_id}/tags",
            json_data={"tags": tags},
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_add_tags",
            computer_id=computer_id,
            tags=tags,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "computer_id": computer_id,
            "tags": tags,
        }

    async def remove_computer_tags(
        self,
        computer_id: str,
        tags: list[str],
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Remove tags from a computer.

        Args:
            computer_id: Landscape computer ID
            tags: Tags to remove
            correlation_id: Correlation ID for audit

        Returns:
            Operation result
        """
        self._make_request(
            "DELETE",
            f"/api/v2/computers/{computer_id}/tags",
            json_data={"tags": tags},
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_remove_tags",
            computer_id=computer_id,
            tags=tags,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "computer_id": computer_id,
            "removed_tags": tags,
        }

    # =========================================================================
    # Package Management
    # =========================================================================

    async def list_packages(
        self,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List available packages in repositories.

        Args:
            search: Search term for package name
            limit: Maximum results
            offset: Pagination offset
            correlation_id: Correlation ID for audit

        Returns:
            List of packages
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search

        response = self._make_request(
            "GET",
            "/api/v2/packages",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "packages": response.get("packages", []),
            "total": response.get("total", 0),
        }

    async def install_packages(
        self,
        computer_ids: list[str],
        packages: list[str],
        deliver_after: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Install packages on specified computers.

        This is an idempotent operation - repeated calls with the same
        parameters will return the cached result.

        Args:
            computer_ids: List of target computer IDs
            packages: List of package names to install
            deliver_after: Schedule installation for later
            correlation_id: Correlation ID for audit

        Returns:
            Activity ID for tracking
        """
        correlation_id = correlation_id or str(uuid4())

        # Check idempotency cache
        idempotency_key = self.get_idempotency_key(
            "install_packages",
            {"computer_ids": sorted(computer_ids), "packages": sorted(packages)},
        )
        cached = self._get_cached_result(idempotency_key)
        if cached:
            self.logger.info(
                "landscape_install_packages_cached",
                correlation_id=correlation_id,
            )
            return cached

        json_data: dict[str, Any] = {
            "computer_ids": computer_ids,
            "packages": packages,
        }
        if deliver_after:
            json_data["deliver_after"] = deliver_after.isoformat()

        response = self._make_request(
            "POST",
            "/api/v2/activities/install-packages",
            json_data=json_data,
            correlation_id=correlation_id,
        )

        result = {
            "success": True,
            "activity_id": response.get("activity_id"),
            "computer_ids": computer_ids,
            "packages": packages,
            "correlation_id": correlation_id,
        }

        self._cache_result(idempotency_key, result)

        self.logger.info(
            "landscape_install_packages",
            activity_id=response.get("activity_id"),
            computer_count=len(computer_ids),
            package_count=len(packages),
            correlation_id=correlation_id,
        )

        return result

    async def remove_packages(
        self,
        computer_ids: list[str],
        packages: list[str],
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Remove packages from specified computers.

        Args:
            computer_ids: List of target computer IDs
            packages: List of package names to remove
            correlation_id: Correlation ID for audit

        Returns:
            Activity ID for tracking
        """
        correlation_id = correlation_id or str(uuid4())

        # Check idempotency cache
        idempotency_key = self.get_idempotency_key(
            "remove_packages",
            {"computer_ids": sorted(computer_ids), "packages": sorted(packages)},
        )
        cached = self._get_cached_result(idempotency_key)
        if cached:
            return cached

        response = self._make_request(
            "POST",
            "/api/v2/activities/remove-packages",
            json_data={
                "computer_ids": computer_ids,
                "packages": packages,
            },
            correlation_id=correlation_id,
        )

        result = {
            "success": True,
            "activity_id": response.get("activity_id"),
            "computer_ids": computer_ids,
            "packages": packages,
            "correlation_id": correlation_id,
        }

        self._cache_result(idempotency_key, result)

        self.logger.info(
            "landscape_remove_packages",
            activity_id=response.get("activity_id"),
            computer_count=len(computer_ids),
            package_count=len(packages),
            correlation_id=correlation_id,
        )

        return result

    async def upgrade_packages(
        self,
        computer_ids: list[str],
        packages: Optional[list[str]] = None,
        security_only: bool = False,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Upgrade packages on specified computers.

        Args:
            computer_ids: List of target computer IDs
            packages: Specific packages to upgrade (None = all)
            security_only: Only apply security updates
            correlation_id: Correlation ID for audit

        Returns:
            Activity ID for tracking
        """
        correlation_id = correlation_id or str(uuid4())

        json_data = {
            "computer_ids": computer_ids,
            "security_only": security_only,
        }
        if packages:
            json_data["packages"] = packages

        response = self._make_request(
            "POST",
            "/api/v2/activities/upgrade-packages",
            json_data=json_data,
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_upgrade_packages",
            activity_id=response.get("activity_id"),
            computer_count=len(computer_ids),
            security_only=security_only,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity_id": response.get("activity_id"),
            "computer_ids": computer_ids,
            "packages": packages,
            "security_only": security_only,
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Repository Management
    # =========================================================================

    async def list_repositories(
        self,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List configured package repositories.

        Returns:
            List of repositories
        """
        response = self._make_request(
            "GET",
            "/api/v2/repositories",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "repositories": response.get("repositories", []),
        }

    async def create_repository(
        self,
        name: str,
        uri: str,
        distribution: str,
        components: list[str],
        architectures: list[str],
        gpg_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new package repository.

        Args:
            name: Repository name
            uri: Repository URI
            distribution: Distribution codename (e.g., 'jammy')
            components: Repository components (e.g., ['main', 'universe'])
            architectures: Supported architectures (e.g., ['amd64', 'arm64'])
            gpg_key: GPG key for repository signing
            correlation_id: Correlation ID for audit

        Returns:
            Created repository details
        """
        correlation_id = correlation_id or str(uuid4())

        # Idempotency check
        idempotency_key = self.get_idempotency_key(
            "create_repository",
            {"name": name, "uri": uri, "distribution": distribution},
        )
        cached = self._get_cached_result(idempotency_key)
        if cached:
            return cached

        json_data = {
            "name": name,
            "uri": uri,
            "distribution": distribution,
            "components": components,
            "architectures": architectures,
        }
        if gpg_key:
            json_data["gpg_key"] = gpg_key

        try:
            response = self._make_request(
                "POST",
                "/api/v2/repositories",
                json_data=json_data,
                correlation_id=correlation_id,
            )

            result = {
                "success": True,
                "created": True,
                "repository": response,
                "correlation_id": correlation_id,
            }

        except LandscapeConnectorError as e:
            if e.status_code == 409:
                # Already exists - idempotent success
                result = {
                    "success": True,
                    "created": False,
                    "message": "Repository already exists",
                    "correlation_id": correlation_id,
                }
            else:
                raise

        self._cache_result(idempotency_key, result)

        self.logger.info(
            "landscape_create_repository",
            name=name,
            uri=uri,
            created=result.get("created", False),
            correlation_id=correlation_id,
        )

        return result

    async def sync_repository(
        self,
        repository_id: str,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Trigger repository synchronization.

        Args:
            repository_id: Repository ID to sync
            correlation_id: Correlation ID for audit

        Returns:
            Sync activity details
        """
        response = self._make_request(
            "POST",
            f"/api/v2/repositories/{repository_id}/sync",
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_sync_repository",
            repository_id=repository_id,
            activity_id=response.get("activity_id"),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity_id": response.get("activity_id"),
            "repository_id": repository_id,
        }

    # =========================================================================
    # Script Execution
    # =========================================================================

    async def run_script(
        self,
        computer_ids: list[str],
        script: str,
        interpreter: str = "/bin/bash",
        timeout: int = 300,
        username: str = "root",
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a script on specified computers.

        Args:
            computer_ids: Target computer IDs
            script: Script content to execute
            interpreter: Script interpreter path
            timeout: Execution timeout in seconds
            username: User to run script as
            correlation_id: Correlation ID for audit

        Returns:
            Activity ID for tracking
        """
        correlation_id = correlation_id or str(uuid4())

        response = self._make_request(
            "POST",
            "/api/v2/activities/run-script",
            json_data={
                "computer_ids": computer_ids,
                "script": script,
                "interpreter": interpreter,
                "timeout": timeout,
                "username": username,
            },
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_run_script",
            activity_id=response.get("activity_id"),
            computer_count=len(computer_ids),
            interpreter=interpreter,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity_id": response.get("activity_id"),
            "computer_ids": computer_ids,
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Activity Tracking
    # =========================================================================

    async def get_activity(
        self,
        activity_id: str,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get activity status and details.

        Args:
            activity_id: Activity ID to query
            correlation_id: Correlation ID for audit

        Returns:
            Activity details including status and results
        """
        response = self._make_request(
            "GET",
            f"/api/v2/activities/{activity_id}",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity": response,
        }

    async def list_activities(
        self,
        status: Optional[str] = None,
        activity_type: Optional[str] = None,
        limit: int = 100,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List activities with optional filters.

        Args:
            status: Filter by status (pending, running, completed, failed)
            activity_type: Filter by type
            limit: Maximum results
            correlation_id: Correlation ID for audit

        Returns:
            List of activities
        """
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if activity_type:
            params["type"] = activity_type

        response = self._make_request(
            "GET",
            "/api/v2/activities",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activities": response.get("activities", []),
            "total": response.get("total", 0),
        }

    async def cancel_activity(
        self,
        activity_id: str,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Cancel a pending or running activity.

        Args:
            activity_id: Activity to cancel
            correlation_id: Correlation ID for audit

        Returns:
            Cancellation result
        """
        self._make_request(
            "POST",
            f"/api/v2/activities/{activity_id}/cancel",
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_cancel_activity",
            activity_id=activity_id,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity_id": activity_id,
            "cancelled": True,
        }

    # =========================================================================
    # Compliance & Reporting
    # =========================================================================

    async def get_compliance_status(
        self,
        computer_ids: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get package compliance status for computers.

        Args:
            computer_ids: Specific computers to check
            tags: Filter by tags
            correlation_id: Correlation ID for audit

        Returns:
            Compliance summary with details
        """
        params: dict[str, Any] = {}
        if computer_ids:
            params["computer_ids"] = ",".join(computer_ids)
        if tags:
            params["tags"] = ",".join(tags)

        response = self._make_request(
            "GET",
            "/api/v2/compliance/packages",
            params=params,
            correlation_id=correlation_id,
        )

        # Calculate compliance rate
        total = response.get("total_computers", 0)
        compliant = response.get("compliant_computers", 0)
        compliance_rate = (compliant / total * 100) if total > 0 else 0

        return {
            "success": True,
            "total_computers": total,
            "compliant_computers": compliant,
            "non_compliant_computers": total - compliant,
            "compliance_rate": round(compliance_rate, 2),
            "pending_updates": response.get("pending_updates", 0),
            "security_updates": response.get("security_updates", 0),
            "details": response.get("details", []),
        }

    async def get_security_updates(
        self,
        computer_ids: Optional[list[str]] = None,
        severity: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get pending security updates.

        Args:
            computer_ids: Specific computers to check
            severity: Filter by severity (critical, high, medium, low)
            correlation_id: Correlation ID for audit

        Returns:
            List of pending security updates
        """
        params: dict[str, Any] = {}
        if computer_ids:
            params["computer_ids"] = ",".join(computer_ids)
        if severity:
            params["severity"] = severity

        response = self._make_request(
            "GET",
            "/api/v2/security/updates",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "updates": response.get("updates", []),
            "total": response.get("total", 0),
            "by_severity": response.get("by_severity", {}),
        }

    # =========================================================================
    # Rollback Support
    # =========================================================================

    async def rollback_packages(
        self,
        computer_ids: list[str],
        packages: list[dict[str, str]],
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Rollback packages to specific versions.

        Args:
            computer_ids: Target computer IDs
            packages: List of {"name": "pkg", "version": "1.0.0"}
            correlation_id: Correlation ID for audit

        Returns:
            Activity ID for tracking
        """
        correlation_id = correlation_id or str(uuid4())

        response = self._make_request(
            "POST",
            "/api/v2/activities/install-packages",
            json_data={
                "computer_ids": computer_ids,
                "packages": [f"{p['name']}={p['version']}" for p in packages],
                "allow_downgrade": True,
            },
            correlation_id=correlation_id,
        )

        self.logger.info(
            "landscape_rollback_packages",
            activity_id=response.get("activity_id"),
            computer_count=len(computer_ids),
            package_count=len(packages),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "activity_id": response.get("activity_id"),
            "computer_ids": computer_ids,
            "packages": packages,
            "rollback": True,
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Inventory Sync for Control Plane
    # =========================================================================

    async def sync_inventory(
        self,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Synchronize full computer inventory to Control Plane.

        Returns all computers with packages for reconciliation.

        Args:
            correlation_id: Correlation ID for audit

        Returns:
            Full inventory data
        """
        correlation_id = correlation_id or str(uuid4())

        # Get all computers
        computers_response = await self.list_computers(
            limit=10000,
            correlation_id=correlation_id,
        )
        computers = computers_response.get("computers", [])

        self.logger.info(
            "landscape_sync_inventory",
            computer_count=len(computers),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "count": len(computers),
            "computers": computers,
            "synced_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }
