# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Request Synchronization Service.

Orchestrates synchronization of requests from ServiceNow,
including status change detection and stakeholder management.
"""
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from apps.cmdb_integration.models import CMDBConnection

from ..models import RequestStatusUpdate, TrackedRequest
from .servicenow_client import MockServiceNowRequestClient, ServiceNowRequestClient

logger = logging.getLogger(__name__)


class RequestSyncService:
    """
    Orchestrates request synchronization operations.

    Responsibilities:
    - Sync requests from ServiceNow
    - Detect status changes
    - Update SLA information
    - Track stakeholders
    """

    def __init__(
        self,
        connection: CMDBConnection,
        use_mock: bool = False,
    ):
        """
        Initialize sync service.

        Args:
            connection: CMDB connection configuration
            use_mock: Use mock client for development
        """
        self.connection = connection
        self.use_mock = use_mock or getattr(settings, "SERVICENOW_USE_MOCK", True)

        if self.use_mock:
            self.client = MockServiceNowRequestClient(connection)
        else:
            self.client = ServiceNowRequestClient(connection)

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()

    async def sync_request(self, servicenow_number: str) -> TrackedRequest:
        """
        Sync a single request from ServiceNow.

        Args:
            servicenow_number: ServiceNow request number (e.g., REQ0045678)

        Returns:
            TrackedRequest instance
        """
        # Find existing request or get from ServiceNow
        try:
            tracked_request = TrackedRequest.objects.get(servicenow_number=servicenow_number)
        except TrackedRequest.DoesNotExist:
            # Query ServiceNow to find by number
            requests = await self.client.query_requests(
                query=f"number={servicenow_number}",
                fields=[
                    "sys_id",
                    "number",
                    "short_description",
                    "requestor",
                    "assigned_to",
                    "assignment_group",
                    "state",
                    "priority",
                    "sys_updated_on",
                ],
            )
            if not requests:
                raise ValueError(f"Request {servicenow_number} not found in ServiceNow")

            sn_request = requests[0]
            tracked_request = TrackedRequest(
                servicenow_number=servicenow_number,
                servicenow_sys_id=sn_request["sys_id"],
            )

        # Get latest data from ServiceNow
        sn_request = await self.client.get_request(tracked_request.servicenow_sys_id)
        if not sn_request:
            raise ValueError(f"Request {servicenow_number} not found in ServiceNow")

        # Map ServiceNow state to our status
        state_map = {
            "1": TrackedRequest.Status.NEW,
            "2": TrackedRequest.Status.IN_PROGRESS,
            "3": TrackedRequest.Status.PENDING,
            "4": TrackedRequest.Status.RESOLVED,
            "7": TrackedRequest.Status.CLOSED,
            "8": TrackedRequest.Status.CANCELLED,
        }

        old_status = tracked_request.status
        new_status = state_map.get(sn_request.get("state", "1"), TrackedRequest.Status.NEW)

        # Update fields
        tracked_request.short_description = sn_request.get("short_description", "")[:255]
        tracked_request.requestor_email = sn_request.get("requestor", {}).get("email", "") or sn_request.get(
            "requestor_email", ""
        )
        tracked_request.requestor_name = sn_request.get("requestor", {}).get("name", "") or sn_request.get(
            "requestor_name", ""
        )
        tracked_request.assigned_to = sn_request.get("assigned_to", {}).get("name", "") or sn_request.get(
            "assigned_to_name", ""
        )
        tracked_request.assignment_group = sn_request.get("assignment_group", {}).get("name", "") or sn_request.get(
            "assignment_group_name", ""
        )
        tracked_request.status = new_status
        tracked_request.priority = sn_request.get("priority", "3")
        tracked_request.last_updated = timezone.now()

        # Get SLA info
        sla_info = await self.client.get_sla_info(tracked_request.servicenow_sys_id)
        if sla_info and sla_info.get("due_date"):
            from dateutil.parser import parse

            tracked_request.sla_due = parse(sla_info["due_date"])

        tracked_request.save()

        # Record status change if different
        if old_status != new_status:
            RequestStatusUpdate.objects.create(
                request=tracked_request,
                old_status=old_status,
                new_status=new_status,
                updated_by=sn_request.get("sys_updated_by", "system"),
            )

        return tracked_request

    async def sync_all_requests(self, limit: int = 100) -> List[TrackedRequest]:
        """
        Sync all active requests from ServiceNow.

        Args:
            limit: Maximum number of requests to sync

        Returns:
            List of synced TrackedRequest instances
        """
        # Query active requests from ServiceNow
        requests = await self.client.query_requests(
            query="state!=7^state!=8",  # Not closed or cancelled
            fields=[
                "sys_id",
                "number",
                "short_description",
                "requestor",
                "assigned_to",
                "assignment_group",
                "state",
                "priority",
                "sys_updated_on",
            ],
            limit=limit,
        )

        synced = []
        for sn_request in requests:
            try:
                tracked = await self.sync_request(sn_request["number"])
                synced.append(tracked)
            except Exception as e:
                logger.error(f"Failed to sync request {sn_request.get('number')}: {e}")

        return synced
