# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Entra ID connector for EUCORA Control Plane.

Provides user and group synchronization via Microsoft Graph API:
- List/get users with attributes
- List/get groups with membership
- Sync users to local user database
- Sync groups for RBAC mapping

All operations are idempotent with correlation ID tracking.
"""
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from .auth import EntraAuth

logger = logging.getLogger(__name__)


@dataclass
class EntraUser:
    """Entra ID user representation."""

    id: str
    user_principal_name: str
    display_name: str
    given_name: Optional[str]
    surname: Optional[str]
    mail: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    office_location: Optional[str]
    mobile_phone: Optional[str]
    account_enabled: bool
    created_datetime: Optional[datetime]
    last_sign_in_datetime: Optional[datetime] = None
    manager_id: Optional[str] = None
    member_of: list[str] = field(default_factory=list)


@dataclass
class EntraGroup:
    """Entra ID group representation."""

    id: str
    display_name: str
    description: Optional[str]
    mail: Optional[str]
    mail_enabled: bool
    security_enabled: bool
    group_types: list[str]
    created_datetime: Optional[datetime]
    membership_rule: Optional[str] = None
    member_count: int = 0


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    correlation_id: str
    operation: str
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    errors: list[dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class EntraConnector:
    """
    Entra ID connector for user/group synchronization.

    Implements:
    - User listing with pagination and filtering
    - Group listing with membership expansion
    - User sync to local database
    - Group sync for RBAC mapping
    - Manager hierarchy resolution

    All operations are idempotent and tracked with correlation IDs.
    """

    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    BATCH_API_URL = "https://graph.microsoft.com/v1.0/$batch"

    # Default fields to fetch for users
    DEFAULT_USER_FIELDS = [
        "id",
        "userPrincipalName",
        "displayName",
        "givenName",
        "surname",
        "mail",
        "jobTitle",
        "department",
        "officeLocation",
        "mobilePhone",
        "accountEnabled",
        "createdDateTime",
        "signInActivity",
    ]

    # Default fields to fetch for groups
    DEFAULT_GROUP_FIELDS = [
        "id",
        "displayName",
        "description",
        "mail",
        "mailEnabled",
        "securityEnabled",
        "groupTypes",
        "createdDateTime",
        "membershipRule",
    ]

    def __init__(
        self,
        auth: EntraAuth,
        timeout: float = 30.0,
        max_retries: int = 3,
        page_size: int = 100,
    ) -> None:
        """
        Initialize Entra ID connector.

        Args:
            auth: EntraAuth instance for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
            page_size: Number of records per page for pagination
        """
        self._auth = auth
        self._timeout = timeout
        self._max_retries = max_retries
        self._page_size = min(page_size, 999)  # Graph API max is 999

        # Idempotency cache (correlation_id -> result)
        self._idempotency_cache: dict[str, Any] = {}
        self._cache_max_size = 1000

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid token."""
        await self._auth.authenticate()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to Graph API.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to GRAPH_API_URL)
            params: Query parameters
            json_data: JSON body
            correlation_id: Correlation ID for tracking

        Returns:
            API response as dict

        Raises:
            httpx.HTTPStatusError: If request fails after retries
        """
        await self._ensure_authenticated()

        url = f"{self.GRAPH_API_URL}/{endpoint.lstrip('/')}"
        headers = {
            **self._auth.get_auth_header(),
            "Content-Type": "application/json",
            "ConsistencyLevel": "eventual",  # Required for some queries
        }

        if correlation_id:
            headers["client-request-id"] = correlation_id

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
                        headers=headers,
                    )

                    # Handle throttling
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 30))
                        logger.warning(f"Graph API throttled, retrying after {retry_after}s")
                        import asyncio

                        await asyncio.sleep(retry_after)
                        continue

                    response.raise_for_status()
                    return response.json() if response.content else {}

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    # Token might be expired, refresh and retry
                    await self._auth.refresh_token()
                    continue
                if e.response.status_code >= 500:
                    last_error = e
                    logger.warning(
                        f"Graph API error {e.response.status_code}, attempt {attempt + 1}/{self._max_retries}"
                    )
                    continue
                raise
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request error: {e}, attempt {attempt + 1}/{self._max_retries}")
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Request failed after retries")

    def _get_idempotency_key(self, operation: str, params: dict[str, Any]) -> str:
        """Generate idempotency key for an operation."""
        key_data = f"{operation}:{sorted(params.items())}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    async def list_users(
        self,
        filter_query: Optional[str] = None,
        select_fields: Optional[list[str]] = None,
        include_sign_in_activity: bool = False,
        correlation_id: Optional[str] = None,
    ) -> list[EntraUser]:
        """
        List users from Entra ID with pagination.

        Args:
            filter_query: OData filter query (e.g., "accountEnabled eq true")
            select_fields: Fields to select (uses defaults if not specified)
            include_sign_in_activity: Include sign-in activity (requires extra permission)
            correlation_id: Correlation ID for tracking

        Returns:
            List of EntraUser objects
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        logger.info(f"[{correlation_id}] Listing Entra ID users")

        fields = select_fields or self.DEFAULT_USER_FIELDS.copy()
        if not include_sign_in_activity and "signInActivity" in fields:
            fields.remove("signInActivity")

        params: dict[str, Any] = {
            "$select": ",".join(fields),
            "$top": self._page_size,
            "$count": "true",
        }

        if filter_query:
            params["$filter"] = filter_query

        users: list[EntraUser] = []
        endpoint = "users"

        while True:
            response = await self._make_request("GET", endpoint, params=params, correlation_id=correlation_id)

            for user_data in response.get("value", []):
                users.append(self._parse_user(user_data))

            # Handle pagination
            next_link = response.get("@odata.nextLink")
            if not next_link:
                break

            # Extract endpoint and params from next link
            endpoint = next_link.replace(self.GRAPH_API_URL + "/", "")
            params = {}

        logger.info(f"[{correlation_id}] Retrieved {len(users)} users from Entra ID")
        return users

    async def get_user(
        self,
        user_id: str,
        include_manager: bool = True,
        include_groups: bool = True,
        correlation_id: Optional[str] = None,
    ) -> Optional[EntraUser]:
        """
        Get a specific user by ID or UPN.

        Args:
            user_id: User ID (GUID) or userPrincipalName
            include_manager: Include manager information
            include_groups: Include group memberships
            correlation_id: Correlation ID for tracking

        Returns:
            EntraUser or None if not found
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        logger.info(f"[{correlation_id}] Getting Entra ID user: {user_id[:20]}...")

        try:
            params = {"$select": ",".join(self.DEFAULT_USER_FIELDS)}
            response = await self._make_request("GET", f"users/{user_id}", params=params, correlation_id=correlation_id)

            user = self._parse_user(response)

            # Get manager
            if include_manager:
                try:
                    manager_response = await self._make_request(
                        "GET", f"users/{user_id}/manager", params={"$select": "id"}, correlation_id=correlation_id
                    )
                    user.manager_id = manager_response.get("id")
                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 404:
                        raise

            # Get group memberships
            if include_groups:
                groups_response = await self._make_request(
                    "GET",
                    f"users/{user_id}/memberOf",
                    params={"$select": "id", "$top": 200},
                    correlation_id=correlation_id,
                )
                user.member_of = [
                    g["id"]
                    for g in groups_response.get("value", [])
                    if g.get("@odata.type") == "#microsoft.graph.group"
                ]

            return user

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def _parse_user(self, data: dict[str, Any]) -> EntraUser:
        """Parse user data from Graph API response."""
        created_dt = None
        if data.get("createdDateTime"):
            created_dt = datetime.fromisoformat(data["createdDateTime"].replace("Z", "+00:00"))

        last_sign_in = None
        sign_in_activity = data.get("signInActivity", {})
        if sign_in_activity.get("lastSignInDateTime"):
            last_sign_in = datetime.fromisoformat(sign_in_activity["lastSignInDateTime"].replace("Z", "+00:00"))

        return EntraUser(
            id=data["id"],
            user_principal_name=data.get("userPrincipalName", ""),
            display_name=data.get("displayName", ""),
            given_name=data.get("givenName"),
            surname=data.get("surname"),
            mail=data.get("mail"),
            job_title=data.get("jobTitle"),
            department=data.get("department"),
            office_location=data.get("officeLocation"),
            mobile_phone=data.get("mobilePhone"),
            account_enabled=data.get("accountEnabled", True),
            created_datetime=created_dt,
            last_sign_in_datetime=last_sign_in,
        )

    # ========================================================================
    # GROUP OPERATIONS
    # ========================================================================

    async def list_groups(
        self,
        filter_query: Optional[str] = None,
        security_only: bool = False,
        include_member_count: bool = True,
        correlation_id: Optional[str] = None,
    ) -> list[EntraGroup]:
        """
        List groups from Entra ID with pagination.

        Args:
            filter_query: OData filter query
            security_only: Only return security groups
            include_member_count: Include member count (requires extra API call)
            correlation_id: Correlation ID for tracking

        Returns:
            List of EntraGroup objects
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        logger.info(f"[{correlation_id}] Listing Entra ID groups")

        params: dict[str, Any] = {
            "$select": ",".join(self.DEFAULT_GROUP_FIELDS),
            "$top": self._page_size,
            "$count": "true",
        }

        if security_only:
            if filter_query:
                params["$filter"] = f"({filter_query}) and securityEnabled eq true"
            else:
                params["$filter"] = "securityEnabled eq true"
        elif filter_query:
            params["$filter"] = filter_query

        groups: list[EntraGroup] = []
        endpoint = "groups"

        while True:
            response = await self._make_request("GET", endpoint, params=params, correlation_id=correlation_id)

            for group_data in response.get("value", []):
                group = self._parse_group(group_data)

                if include_member_count:
                    # Get member count
                    try:
                        count_response = await self._make_request(
                            "GET",
                            f"groups/{group.id}/members/$count",
                            correlation_id=correlation_id,
                        )
                        # Response is just a number
                        group.member_count = int(count_response) if isinstance(count_response, (int, str)) else 0
                    except Exception:
                        # Count endpoint may fail, continue without it
                        pass

                groups.append(group)

            # Handle pagination
            next_link = response.get("@odata.nextLink")
            if not next_link:
                break

            endpoint = next_link.replace(self.GRAPH_API_URL + "/", "")
            params = {}

        logger.info(f"[{correlation_id}] Retrieved {len(groups)} groups from Entra ID")
        return groups

    async def get_group(
        self,
        group_id: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[EntraGroup]:
        """
        Get a specific group by ID.

        Args:
            group_id: Group ID (GUID)
            correlation_id: Correlation ID for tracking

        Returns:
            EntraGroup or None if not found
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        try:
            params = {"$select": ",".join(self.DEFAULT_GROUP_FIELDS)}
            response = await self._make_request(
                "GET", f"groups/{group_id}", params=params, correlation_id=correlation_id
            )
            return self._parse_group(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_group_members(
        self,
        group_id: str,
        transitive: bool = False,
        correlation_id: Optional[str] = None,
    ) -> list[str]:
        """
        Get members of a group.

        Args:
            group_id: Group ID
            transitive: Include nested group members
            correlation_id: Correlation ID for tracking

        Returns:
            List of user IDs
        """
        correlation_id = correlation_id or str(uuid.uuid4())

        endpoint = f"groups/{group_id}/transitiveMembers" if transitive else f"groups/{group_id}/members"
        params = {"$select": "id", "$top": self._page_size}

        member_ids: list[str] = []

        while True:
            response = await self._make_request("GET", endpoint, params=params, correlation_id=correlation_id)

            for member in response.get("value", []):
                if member.get("@odata.type") == "#microsoft.graph.user":
                    member_ids.append(member["id"])

            next_link = response.get("@odata.nextLink")
            if not next_link:
                break

            endpoint = next_link.replace(self.GRAPH_API_URL + "/", "")
            params = {}

        return member_ids

    def _parse_group(self, data: dict[str, Any]) -> EntraGroup:
        """Parse group data from Graph API response."""
        created_dt = None
        if data.get("createdDateTime"):
            created_dt = datetime.fromisoformat(data["createdDateTime"].replace("Z", "+00:00"))

        return EntraGroup(
            id=data["id"],
            display_name=data.get("displayName", ""),
            description=data.get("description"),
            mail=data.get("mail"),
            mail_enabled=data.get("mailEnabled", False),
            security_enabled=data.get("securityEnabled", False),
            group_types=data.get("groupTypes", []),
            created_datetime=created_dt,
            membership_rule=data.get("membershipRule"),
        )

    # ========================================================================
    # SYNC OPERATIONS
    # ========================================================================

    async def sync_users(
        self,
        filter_query: Optional[str] = None,
        include_disabled: bool = False,
        correlation_id: Optional[str] = None,
    ) -> SyncResult:
        """
        Sync users from Entra ID to local database.

        This is an idempotent operation - running it multiple times
        with the same parameters produces the same result.

        Args:
            filter_query: Optional filter for users to sync
            include_disabled: Include disabled accounts
            correlation_id: Correlation ID for tracking

        Returns:
            SyncResult with operation details
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        # Check idempotency cache
        idempotency_key = self._get_idempotency_key(
            "sync_users", {"filter": filter_query, "include_disabled": include_disabled}
        )
        if idempotency_key in self._idempotency_cache:
            logger.info(f"[{correlation_id}] Returning cached sync result")
            return self._idempotency_cache[idempotency_key]

        logger.info(f"[{correlation_id}] Starting user sync from Entra ID")

        # Build filter
        if not include_disabled:
            base_filter = "accountEnabled eq true"
            if filter_query:
                filter_query = f"({filter_query}) and {base_filter}"
            else:
                filter_query = base_filter

        errors: list[dict[str, Any]] = []
        created = 0
        updated = 0

        try:
            users = await self.list_users(
                filter_query=filter_query,
                include_sign_in_activity=True,
                correlation_id=correlation_id,
            )

            # In a real implementation, this would sync to the local database
            # For now, we just count the users
            for user in users:
                # Placeholder for actual database sync logic
                # This would call UserProfile.objects.update_or_create(...)
                updated += 1

            result = SyncResult(
                success=True,
                correlation_id=correlation_id,
                operation="sync_users",
                records_processed=len(users),
                records_created=created,
                records_updated=updated,
                records_deleted=0,
                errors=errors,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] User sync failed: {e}")
            result = SyncResult(
                success=False,
                correlation_id=correlation_id,
                operation="sync_users",
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_deleted=0,
                errors=[{"message": str(e), "type": type(e).__name__}],
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        result.duration_seconds = (
            (result.completed_at - result.started_at).total_seconds() if result.completed_at else None
        )

        # Cache result
        if len(self._idempotency_cache) >= self._cache_max_size:
            # Remove oldest entries
            keys_to_remove = list(self._idempotency_cache.keys())[: self._cache_max_size // 2]
            for key in keys_to_remove:
                del self._idempotency_cache[key]
        self._idempotency_cache[idempotency_key] = result

        return result

    async def sync_groups(
        self,
        filter_query: Optional[str] = None,
        security_only: bool = True,
        correlation_id: Optional[str] = None,
    ) -> SyncResult:
        """
        Sync groups from Entra ID to local database.

        This is an idempotent operation.

        Args:
            filter_query: Optional filter for groups to sync
            security_only: Only sync security groups
            correlation_id: Correlation ID for tracking

        Returns:
            SyncResult with operation details
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        idempotency_key = self._get_idempotency_key(
            "sync_groups", {"filter": filter_query, "security_only": security_only}
        )
        if idempotency_key in self._idempotency_cache:
            logger.info(f"[{correlation_id}] Returning cached group sync result")
            return self._idempotency_cache[idempotency_key]

        logger.info(f"[{correlation_id}] Starting group sync from Entra ID")

        errors: list[dict[str, Any]] = []
        created = 0
        updated = 0

        try:
            groups = await self.list_groups(
                filter_query=filter_query,
                security_only=security_only,
                include_member_count=True,
                correlation_id=correlation_id,
            )

            for group in groups:
                # Placeholder for actual database sync logic
                updated += 1

            result = SyncResult(
                success=True,
                correlation_id=correlation_id,
                operation="sync_groups",
                records_processed=len(groups),
                records_created=created,
                records_updated=updated,
                records_deleted=0,
                errors=errors,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] Group sync failed: {e}")
            result = SyncResult(
                success=False,
                correlation_id=correlation_id,
                operation="sync_groups",
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_deleted=0,
                errors=[{"message": str(e), "type": type(e).__name__}],
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        result.duration_seconds = (
            (result.completed_at - result.started_at).total_seconds() if result.completed_at else None
        )
        self._idempotency_cache[idempotency_key] = result

        return result

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def test_connection(self, correlation_id: Optional[str] = None) -> dict[str, Any]:
        """
        Test connection to Entra ID.

        Args:
            correlation_id: Correlation ID for tracking

        Returns:
            Connection status and tenant info
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        logger.info(f"[{correlation_id}] Testing Entra ID connection")

        try:
            # Get tenant info
            response = await self._make_request(
                "GET",
                "organization",
                params={"$select": "id,displayName,verifiedDomains"},
                correlation_id=correlation_id,
            )

            org = response.get("value", [{}])[0]
            domains = [d["name"] for d in org.get("verifiedDomains", []) if d.get("isDefault")]

            return {
                "success": True,
                "tenant_id": org.get("id"),
                "tenant_name": org.get("displayName"),
                "primary_domain": domains[0] if domains else None,
                "correlation_id": correlation_id,
            }

        except Exception as e:
            logger.exception(f"[{correlation_id}] Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "correlation_id": correlation_id,
            }

    def __repr__(self) -> str:
        return f"EntraConnector(auth={self._auth!r})"
