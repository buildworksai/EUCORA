# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AWX/Ansible Tower API client for Linux automation.

Provides integration with AWX/Tower for:
- Job template management and execution
- Inventory synchronization
- Playbook-based package deployment
- Remediation workflows
- Compliance enforcement

API Reference: https://docs.ansible.com/ansible-tower/latest/html/towerapi/
"""
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import requests

from apps.core.structured_logging import StructuredLogger

from .auth import AnsibleAuth

logger = logging.getLogger(__name__)


class AnsibleConnectorError(Exception):
    """Exception raised for Ansible/AWX connector errors."""

    def __init__(
        self,
        message: str,
        is_transient: bool = False,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        """
        Initialize AnsibleConnectorError.

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


class AnsibleConnector:
    """
    AWX/Ansible Tower connector for Linux automation.

    Implements idempotent operations with correlation ID tracking
    for audit trail and reconciliation support.
    """

    # Job status constants
    JOB_STATUS_PENDING = "pending"
    JOB_STATUS_WAITING = "waiting"
    JOB_STATUS_RUNNING = "running"
    JOB_STATUS_SUCCESSFUL = "successful"
    JOB_STATUS_FAILED = "failed"
    JOB_STATUS_ERROR = "error"
    JOB_STATUS_CANCELED = "canceled"

    TERMINAL_STATUSES = {JOB_STATUS_SUCCESSFUL, JOB_STATUS_FAILED, JOB_STATUS_ERROR, JOB_STATUS_CANCELED}

    # Cache for idempotent operations (TTL: 1 hour)
    _idempotency_cache: dict[str, tuple[dict, float]] = {}
    CACHE_TTL_SECONDS = 3600

    def __init__(self, auth: Optional[AnsibleAuth] = None):
        """
        Initialize Ansible connector.

        Args:
            auth: AnsibleAuth instance. If None, creates from environment.
        """
        self.auth = auth or AnsibleAuth()
        self.server_url = self.auth.server_url
        self.api_base = f"{self.server_url}/api/v2"
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
        Make authenticated request to AWX API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body data
            correlation_id: Correlation ID for audit trail

        Returns:
            Response JSON data

        Raises:
            AnsibleConnectorError: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        correlation_id = correlation_id or str(uuid4())

        session = self.auth.get_session()
        headers = {"X-Correlation-ID": correlation_id}
        headers = self.auth.sign_request(method, url, headers)

        self.logger.info(
            "awx_api_request",
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

            self.logger.info(
                "awx_api_response",
                status_code=response.status_code,
                correlation_id=correlation_id,
            )

            # Handle rate limiting
            if response.status_code == 429:
                raise AnsibleConnectorError(
                    "Rate limit exceeded",
                    is_transient=True,
                    status_code=429,
                )

            # Handle server errors
            if response.status_code >= 500:
                raise AnsibleConnectorError(
                    f"Server error: {response.status_code}",
                    is_transient=True,
                    status_code=response.status_code,
                    response_body=response.text,
                )

            response.raise_for_status()

            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            # Handle empty responses
            if not response.text:
                return {}

            return response.json()

        except requests.exceptions.Timeout:
            raise AnsibleConnectorError(
                "Request timeout",
                is_transient=True,
            )

        except requests.exceptions.ConnectionError as e:
            raise AnsibleConnectorError(
                f"Connection error: {e}",
                is_transient=True,
            )

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            is_transient = status_code in (408, 429, 502, 503, 504) if status_code else False

            raise AnsibleConnectorError(
                f"HTTP error: {e}",
                is_transient=is_transient,
                status_code=status_code,
                response_body=e.response.text if e.response else None,
            )

    def _paginate(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        max_results: int = 10000,
        correlation_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Handle pagination for list endpoints.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_results: Maximum results to fetch
            correlation_id: Correlation ID

        Returns:
            List of all results
        """
        results: list[Any] = []
        params = params or {}
        params["page_size"] = min(200, max_results)  # AWX max page size

        while len(results) < max_results:
            response = self._make_request(
                "GET",
                endpoint,
                params=params,
                correlation_id=correlation_id,
            )

            results.extend(response.get("results", []))

            # Check for next page
            next_url = response.get("next")
            if not next_url:
                break

            # Extract page number from next URL
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(next_url)
            query_params = parse_qs(parsed.query)
            if "page" in query_params:
                params["page"] = query_params["page"][0]
            else:
                break

        return results[:max_results]

    def get_idempotency_key(self, operation: str, params: dict) -> str:
        """Generate idempotency key for an operation."""
        key_data = json.dumps({"operation": operation, "params": params}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached_result(self, idempotency_key: str) -> Optional[dict]:
        """Get cached result if exists and not expired."""
        if idempotency_key in self._idempotency_cache:
            result, timestamp = self._idempotency_cache[idempotency_key]
            if datetime.now().timestamp() - timestamp < self.CACHE_TTL_SECONDS:
                return result
            del self._idempotency_cache[idempotency_key]
        return None

    def _cache_result(self, idempotency_key: str, result: dict) -> None:
        """Cache operation result."""
        self._idempotency_cache[idempotency_key] = (result, datetime.now().timestamp())

    async def test_connection(self) -> tuple[bool, str]:
        """Test connection to AWX server."""
        return self.auth.test_connection()

    # =========================================================================
    # Inventory Management
    # =========================================================================

    async def list_inventories(
        self,
        search: Optional[str] = None,
        organization_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List inventories.

        Args:
            search: Search query
            organization_id: Filter by organization
            correlation_id: Correlation ID

        Returns:
            List of inventories
        """
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if organization_id:
            params["organization"] = organization_id

        results = self._paginate(
            "/inventories/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "inventories": results,
            "count": len(results),
        }

    async def get_inventory(
        self,
        inventory_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get inventory details.

        Args:
            inventory_id: Inventory ID
            correlation_id: Correlation ID

        Returns:
            Inventory details
        """
        response = self._make_request(
            "GET",
            f"/inventories/{inventory_id}/",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "inventory": response,
        }

    async def get_inventory_hosts(
        self,
        inventory_id: int,
        enabled_only: bool = False,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get hosts in an inventory.

        Args:
            inventory_id: Inventory ID
            enabled_only: Only return enabled hosts
            correlation_id: Correlation ID

        Returns:
            List of hosts
        """
        params: dict[str, Any] = {}
        if enabled_only:
            params["enabled"] = "true"

        results = self._paginate(
            f"/inventories/{inventory_id}/hosts/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "hosts": results,
            "count": len(results),
            "inventory_id": inventory_id,
        }

    async def sync_inventory_source(
        self,
        inventory_source_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Trigger inventory source sync.

        Args:
            inventory_source_id: Inventory source ID
            correlation_id: Correlation ID

        Returns:
            Sync job details
        """
        response = self._make_request(
            "POST",
            f"/inventory_sources/{inventory_source_id}/update/",
            correlation_id=correlation_id,
        )

        self.logger.info(
            "awx_sync_inventory",
            inventory_source_id=inventory_source_id,
            job_id=response.get("id"),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_id": response.get("id"),
            "inventory_source_id": inventory_source_id,
            "correlation_id": correlation_id,
        }

    async def create_host(
        self,
        inventory_id: int,
        name: str,
        description: str = "",
        variables: Optional[dict] = None,
        enabled: bool = True,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a host in an inventory.

        Args:
            inventory_id: Target inventory ID
            name: Host name
            description: Host description
            variables: Host variables (YAML or JSON)
            enabled: Whether host is enabled
            correlation_id: Correlation ID

        Returns:
            Created host details
        """
        correlation_id = correlation_id or str(uuid4())

        # Idempotency check
        idempotency_key = self.get_idempotency_key(
            "create_host",
            {"inventory_id": inventory_id, "name": name},
        )
        cached = self._get_cached_result(idempotency_key)
        if cached:
            return cached

        json_data = {
            "name": name,
            "description": description,
            "inventory": inventory_id,
            "enabled": enabled,
        }
        if variables:
            json_data["variables"] = json.dumps(variables)

        try:
            response = self._make_request(
                "POST",
                "/hosts/",
                json_data=json_data,
                correlation_id=correlation_id,
            )

            result = {
                "success": True,
                "created": True,
                "host": response,
                "correlation_id": correlation_id,
            }

        except AnsibleConnectorError as e:
            if e.status_code == 400 and "already exists" in str(e.response_body or ""):
                # Host already exists - idempotent success
                result = {
                    "success": True,
                    "created": False,
                    "message": "Host already exists",
                    "correlation_id": correlation_id,
                }
            else:
                raise

        self._cache_result(idempotency_key, result)
        return result

    # =========================================================================
    # Job Template Management
    # =========================================================================

    async def list_job_templates(
        self,
        search: Optional[str] = None,
        project_id: Optional[int] = None,
        inventory_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List job templates.

        Args:
            search: Search query
            project_id: Filter by project
            inventory_id: Filter by inventory
            correlation_id: Correlation ID

        Returns:
            List of job templates
        """
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if project_id:
            params["project"] = project_id
        if inventory_id:
            params["inventory"] = inventory_id

        results = self._paginate(
            "/job_templates/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_templates": results,
            "count": len(results),
        }

    async def get_job_template(
        self,
        template_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get job template details.

        Args:
            template_id: Job template ID
            correlation_id: Correlation ID

        Returns:
            Job template details
        """
        response = self._make_request(
            "GET",
            f"/job_templates/{template_id}/",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_template": response,
        }

    async def launch_job_template(
        self,
        template_id: int,
        extra_vars: Optional[dict] = None,
        limit: Optional[str] = None,
        tags: Optional[str] = None,
        skip_tags: Optional[str] = None,
        inventory_id: Optional[int] = None,
        credential_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Launch a job from a template.

        Args:
            template_id: Job template ID
            extra_vars: Extra variables to pass
            limit: Host pattern to limit execution
            tags: Run only these tags
            skip_tags: Skip these tags
            inventory_id: Override inventory
            credential_id: Override credential
            correlation_id: Correlation ID

        Returns:
            Launched job details
        """
        correlation_id = correlation_id or str(uuid4())

        json_data: dict[str, Any] = {}
        if extra_vars:
            json_data["extra_vars"] = json.dumps(extra_vars)
        if limit:
            json_data["limit"] = limit
        if tags:
            json_data["job_tags"] = tags
        if skip_tags:
            json_data["skip_tags"] = skip_tags
        if inventory_id:
            json_data["inventory"] = inventory_id
        if credential_id:
            json_data["credentials"] = [credential_id]

        response = self._make_request(
            "POST",
            f"/job_templates/{template_id}/launch/",
            json_data=json_data if json_data else None,
            correlation_id=correlation_id,
        )

        job_id = response.get("id") or response.get("job")

        self.logger.info(
            "awx_launch_job",
            template_id=template_id,
            job_id=job_id,
            limit=limit,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_id": job_id,
            "template_id": template_id,
            "status": response.get("status", "pending"),
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Job Management
    # =========================================================================

    async def get_job(
        self,
        job_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get job details.

        Args:
            job_id: Job ID
            correlation_id: Correlation ID

        Returns:
            Job details
        """
        response = self._make_request(
            "GET",
            f"/jobs/{job_id}/",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job": response,
        }

    async def get_job_stdout(
        self,
        job_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get job stdout output.

        Args:
            job_id: Job ID
            correlation_id: Correlation ID

        Returns:
            Job stdout
        """
        response = self._make_request(
            "GET",
            f"/jobs/{job_id}/stdout/",
            params={"format": "txt"},
            correlation_id=correlation_id,
        )

        # Response might be plain text
        if isinstance(response, str):
            return {
                "success": True,
                "stdout": response,
                "job_id": job_id,
            }

        return {
            "success": True,
            "stdout": response.get("content", ""),
            "job_id": job_id,
        }

    async def cancel_job(
        self,
        job_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Cancel a running job.

        Args:
            job_id: Job ID
            correlation_id: Correlation ID

        Returns:
            Cancellation result
        """
        self._make_request(
            "POST",
            f"/jobs/{job_id}/cancel/",
            correlation_id=correlation_id,
        )

        self.logger.info(
            "awx_cancel_job",
            job_id=job_id,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_id": job_id,
            "cancelled": True,
        }

    async def wait_for_job(
        self,
        job_id: int,
        timeout: int = 600,
        poll_interval: int = 5,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Wait for a job to complete.

        Args:
            job_id: Job ID to wait for
            timeout: Maximum wait time in seconds
            poll_interval: Poll interval in seconds
            correlation_id: Correlation ID

        Returns:
            Final job status
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = await self.get_job(job_id, correlation_id=correlation_id)
            job = result.get("job", {})
            status = job.get("status")

            if status in self.TERMINAL_STATUSES:
                return {
                    "success": status == self.JOB_STATUS_SUCCESSFUL,
                    "job": job,
                    "status": status,
                    "elapsed": time.time() - start_time,
                }

            time.sleep(poll_interval)

        return {
            "success": False,
            "status": "timeout",
            "job_id": job_id,
            "message": f"Job did not complete within {timeout} seconds",
        }

    async def list_jobs(
        self,
        status: Optional[str] = None,
        job_template_id: Optional[int] = None,
        limit: int = 100,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List jobs.

        Args:
            status: Filter by status
            job_template_id: Filter by template
            limit: Maximum results
            correlation_id: Correlation ID

        Returns:
            List of jobs
        """
        params: dict[str, Any] = {"page_size": min(limit, 200)}
        if status:
            params["status"] = status
        if job_template_id:
            params["job_template"] = job_template_id

        response = self._make_request(
            "GET",
            "/jobs/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "jobs": response.get("results", []),
            "count": response.get("count", 0),
        }

    # =========================================================================
    # Workflow Job Templates
    # =========================================================================

    async def list_workflow_templates(
        self,
        search: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List workflow job templates.

        Args:
            search: Search query
            correlation_id: Correlation ID

        Returns:
            List of workflow templates
        """
        params: dict[str, Any] = {}
        if search:
            params["search"] = search

        results = self._paginate(
            "/workflow_job_templates/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "workflow_templates": results,
            "count": len(results),
        }

    async def launch_workflow(
        self,
        workflow_id: int,
        extra_vars: Optional[dict] = None,
        inventory_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Launch a workflow job.

        Args:
            workflow_id: Workflow template ID
            extra_vars: Extra variables
            inventory_id: Override inventory
            correlation_id: Correlation ID

        Returns:
            Launched workflow job details
        """
        correlation_id = correlation_id or str(uuid4())

        json_data: dict[str, Any] = {}
        if extra_vars:
            json_data["extra_vars"] = json.dumps(extra_vars)
        if inventory_id:
            json_data["inventory"] = inventory_id

        response = self._make_request(
            "POST",
            f"/workflow_job_templates/{workflow_id}/launch/",
            json_data=json_data if json_data else None,
            correlation_id=correlation_id,
        )

        self.logger.info(
            "awx_launch_workflow",
            workflow_id=workflow_id,
            job_id=response.get("id"),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_id": response.get("id"),
            "workflow_id": workflow_id,
            "status": response.get("status", "pending"),
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Project Management
    # =========================================================================

    async def list_projects(
        self,
        search: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List projects.

        Args:
            search: Search query
            correlation_id: Correlation ID

        Returns:
            List of projects
        """
        params: dict[str, Any] = {}
        if search:
            params["search"] = search

        results = self._paginate(
            "/projects/",
            params=params,
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "projects": results,
            "count": len(results),
        }

    async def sync_project(
        self,
        project_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Sync a project from SCM.

        Args:
            project_id: Project ID
            correlation_id: Correlation ID

        Returns:
            Sync job details
        """
        response = self._make_request(
            "POST",
            f"/projects/{project_id}/update/",
            correlation_id=correlation_id,
        )

        self.logger.info(
            "awx_sync_project",
            project_id=project_id,
            job_id=response.get("id"),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "job_id": response.get("id"),
            "project_id": project_id,
            "correlation_id": correlation_id,
        }

    # =========================================================================
    # Package Deployment (EUCORA-specific)
    # =========================================================================

    async def deploy_packages(
        self,
        template_id: int,
        hosts: list[str],
        packages: list[str],
        action: str = "install",
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Deploy packages using a job template.

        This is a convenience method that launches a job template
        with package deployment variables.

        Args:
            template_id: Job template ID (must accept package vars)
            hosts: Target host pattern
            packages: List of packages to install/remove
            action: 'install', 'remove', or 'upgrade'
            correlation_id: Correlation ID

        Returns:
            Deployment job details
        """
        correlation_id = correlation_id or str(uuid4())

        # Check idempotency for install/remove
        if action in ("install", "remove"):
            idempotency_key = self.get_idempotency_key(
                f"deploy_packages_{action}",
                {"template_id": template_id, "hosts": sorted(hosts), "packages": sorted(packages)},
            )
            cached = self._get_cached_result(idempotency_key)
            if cached:
                self.logger.info(
                    "awx_deploy_packages_cached",
                    action=action,
                    correlation_id=correlation_id,
                )
                return cached

        extra_vars = {
            "packages": packages,
            "package_action": action,
        }

        result = await self.launch_job_template(
            template_id=template_id,
            extra_vars=extra_vars,
            limit=",".join(hosts) if isinstance(hosts, list) else hosts,
            correlation_id=correlation_id,
        )

        result["action"] = action
        result["packages"] = packages
        result["hosts"] = hosts

        if action in ("install", "remove"):
            self._cache_result(idempotency_key, result)

        self.logger.info(
            "awx_deploy_packages",
            action=action,
            package_count=len(packages),
            host_count=len(hosts) if isinstance(hosts, list) else 1,
            job_id=result.get("job_id"),
            correlation_id=correlation_id,
        )

        return result

    async def run_remediation(
        self,
        template_id: int,
        hosts: list[str],
        remediation_type: str,
        parameters: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run a remediation playbook.

        Args:
            template_id: Remediation job template ID
            hosts: Target hosts
            remediation_type: Type of remediation
            parameters: Remediation parameters
            correlation_id: Correlation ID

        Returns:
            Remediation job details
        """
        correlation_id = correlation_id or str(uuid4())

        extra_vars = {
            "remediation_type": remediation_type,
            **(parameters or {}),
        }

        result = await self.launch_job_template(
            template_id=template_id,
            extra_vars=extra_vars,
            limit=",".join(hosts) if isinstance(hosts, list) else hosts,
            correlation_id=correlation_id,
        )

        result["remediation_type"] = remediation_type

        self.logger.info(
            "awx_run_remediation",
            remediation_type=remediation_type,
            host_count=len(hosts) if isinstance(hosts, list) else 1,
            job_id=result.get("job_id"),
            correlation_id=correlation_id,
        )

        return result

    # =========================================================================
    # Compliance & Reporting
    # =========================================================================

    async def get_host_facts(
        self,
        host_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get gathered facts for a host.

        Args:
            host_id: Host ID
            correlation_id: Correlation ID

        Returns:
            Host facts
        """
        response = self._make_request(
            "GET",
            f"/hosts/{host_id}/ansible_facts/",
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "host_id": host_id,
            "facts": response,
        }

    async def get_job_host_summaries(
        self,
        job_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get per-host summaries for a job.

        Args:
            job_id: Job ID
            correlation_id: Correlation ID

        Returns:
            Host summaries with success/failure counts
        """
        results = self._paginate(
            f"/jobs/{job_id}/job_host_summaries/",
            correlation_id=correlation_id,
        )

        # Calculate summary stats
        total_hosts = len(results)
        successful = sum(1 for r in results if r.get("failed", False) is False)
        failed = sum(1 for r in results if r.get("failed", False) is True)

        return {
            "success": True,
            "job_id": job_id,
            "host_summaries": results,
            "total_hosts": total_hosts,
            "successful_hosts": successful,
            "failed_hosts": failed,
            "success_rate": (successful / total_hosts * 100) if total_hosts > 0 else 0,
        }

    # =========================================================================
    # Inventory Sync for Control Plane
    # =========================================================================

    async def sync_inventory(
        self,
        inventory_id: int,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Synchronize inventory data to Control Plane.

        Args:
            inventory_id: Inventory ID to sync
            correlation_id: Correlation ID

        Returns:
            Full inventory data for reconciliation
        """
        correlation_id = correlation_id or str(uuid4())

        # Get inventory details
        inventory_result = await self.get_inventory(inventory_id, correlation_id)
        inventory = inventory_result.get("inventory", {})

        # Get all hosts
        hosts_result = await self.get_inventory_hosts(inventory_id, correlation_id=correlation_id)
        hosts = hosts_result.get("hosts", [])

        self.logger.info(
            "awx_sync_inventory",
            inventory_id=inventory_id,
            host_count=len(hosts),
            correlation_id=correlation_id,
        )

        return {
            "success": True,
            "inventory": inventory,
            "hosts": hosts,
            "host_count": len(hosts),
            "synced_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }
