---
name: servicenow-integration
description: ServiceNow integration patterns for EUCORA including CMDB sync, ITSM workflows, change request management, and CAB approval integration. Use when integrating with ServiceNow CMDB, creating change requests, or syncing assets.
status: ✅ Working
last-validated: 2026-01-30
---

# ServiceNow Integration Patterns

ServiceNow CMDB and ITSM integration for EUCORA platform.

---

## Quick Reference

| Integration | Endpoint | Purpose |
|-------------|----------|---------|
| CMDB | `/api/now/table/cmdb_ci` | Asset inventory sync |
| Change Management | `/api/now/table/change_request` | CAB workflow integration |
| Incidents | `/api/now/table/incident` | Incident creation |
| Service Catalog | `/api/now/table/sc_request` | Request management |

---

## Configuration

### ServiceNow Client

```python
# backend/apps/integrations/servicenow/client.py
import httpx
from typing import AsyncGenerator

class ServiceNowClient:
    """ServiceNow REST API client."""

    def __init__(self, instance: str, username: str, password: str):
        self.base_url = f"https://{instance}.service-now.com"
        self.auth = (username, password)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json: dict = None,
    ) -> dict:
        """Make authenticated request to ServiceNow."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                auth=self.auth,
                params=params,
                json=json,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    async def get_table(
        self,
        table: str,
        query: str = None,
        fields: list[str] = None,
        limit: int = 100,
    ) -> AsyncGenerator[dict, None]:
        """Query ServiceNow table with pagination."""
        offset = 0

        while True:
            params = {
                "sysparm_limit": limit,
                "sysparm_offset": offset,
            }

            if query:
                params["sysparm_query"] = query
            if fields:
                params["sysparm_fields"] = ",".join(fields)

            result = await self._request(
                "GET",
                f"/api/now/table/{table}",
                params=params,
            )

            records = result.get("result", [])
            if not records:
                break

            for record in records:
                yield record

            offset += limit

    async def create_record(self, table: str, data: dict) -> dict:
        """Create record in ServiceNow table."""
        result = await self._request(
            "POST",
            f"/api/now/table/{table}",
            json=data,
        )
        return result.get("result", {})

    async def update_record(
        self,
        table: str,
        sys_id: str,
        data: dict,
    ) -> dict:
        """Update record in ServiceNow table."""
        result = await self._request(
            "PATCH",
            f"/api/now/table/{table}/{sys_id}",
            json=data,
        )
        return result.get("result", {})
```

---

## CMDB Integration

### Asset Sync Service

```python
# backend/apps/integrations/servicenow/cmdb.py

class CMDBSyncService:
    """Sync assets from ServiceNow CMDB."""

    def __init__(self, client: ServiceNowClient):
        self.client = client

    async def sync_computers(self) -> int:
        """Sync computer CIs from CMDB."""
        synced = 0

        async for ci in self.client.get_table(
            table="cmdb_ci_computer",
            fields=["sys_id", "name", "serial_number", "os", "os_version",
                    "manufacturer", "model_id", "assigned_to", "department"],
        ):
            await self._upsert_asset(ci)
            synced += 1

        return synced

    async def _upsert_asset(self, ci: dict) -> Asset:
        """Create or update asset from CMDB CI."""
        asset, created = await Asset.objects.aupdate_or_create(
            external_id=ci["sys_id"],
            source="servicenow",
            defaults={
                "name": ci.get("name", ""),
                "serial_number": ci.get("serial_number", ""),
                "os": ci.get("os", ""),
                "os_version": ci.get("os_version", ""),
                "manufacturer": ci.get("manufacturer", ""),
                "model": ci.get("model_id", {}).get("display_value", ""),
                "assigned_to": ci.get("assigned_to", {}).get("display_value", ""),
                "department": ci.get("department", {}).get("display_value", ""),
            },
        )
        return asset

    async def query_cmdb(
        self,
        ci_class: str,
        query: str,
    ) -> list[dict]:
        """Query CMDB for CIs matching criteria."""
        results = []
        async for ci in self.client.get_table(
            table=ci_class,
            query=query,
        ):
            results.append(ci)
        return results
```

### CMDB CI Classes

| CI Class | Table | Description |
|----------|-------|-------------|
| Computer | `cmdb_ci_computer` | Workstations, laptops |
| Server | `cmdb_ci_server` | Physical/virtual servers |
| Application | `cmdb_ci_appl` | Business applications |
| Service | `cmdb_ci_service` | IT services |
| Software | `cmdb_ci_spkg` | Software packages |

---

## Change Management Integration

### Change Request Service

```python
# backend/apps/integrations/servicenow/change.py

class ChangeRequestService:
    """ServiceNow Change Management integration."""

    def __init__(self, client: ServiceNowClient):
        self.client = client

    async def create_change_request(
        self,
        deployment,
        correlation_id: str,
    ) -> dict:
        """Create change request for deployment."""
        change_data = {
            "short_description": f"Deployment: {deployment.name}",
            "description": f"""
                Application: {deployment.application.name}
                Version: {deployment.version}
                Target Ring: {deployment.get_target_ring_display()}
                Risk Score: {deployment.risk_score}

                Correlation ID: {correlation_id}
            """,
            "type": "normal" if deployment.risk_score > 50 else "standard",
            "risk": self._map_risk_level(deployment.risk_score),
            "impact": self._map_impact(deployment.blast_radius),
            "category": "Software",
            "assignment_group": "CAB",
            "u_correlation_id": correlation_id,  # Custom field
        }

        result = await self.client.create_record(
            table="change_request",
            data=change_data,
        )

        return result

    async def get_change_status(self, change_number: str) -> dict:
        """Get change request status."""
        async for change in self.client.get_table(
            table="change_request",
            query=f"number={change_number}",
            fields=["sys_id", "number", "state", "approval", "close_code"],
        ):
            return change
        return None

    async def sync_approval_status(self, change_number: str) -> bool:
        """Sync approval status from ServiceNow back to EUCORA."""
        change = await self.get_change_status(change_number)

        if not change:
            return False

        # Map ServiceNow approval states
        approval_map = {
            "approved": "approved",
            "rejected": "rejected",
            "requested": "pending",
        }

        status = approval_map.get(change.get("approval"), "pending")

        # Update EUCORA CAB submission
        correlation_id = change.get("u_correlation_id")
        if correlation_id:
            submission = await CABSubmission.objects.filter(
                correlation_id=correlation_id
            ).afirst()

            if submission:
                submission.external_status = status
                submission.external_change_number = change_number
                await submission.asave()

        return True

    def _map_risk_level(self, risk_score: float) -> str:
        if risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "moderate"
        return "low"

    def _map_impact(self, blast_radius: int) -> str:
        if blast_radius >= 10000:
            return "1"  # High
        elif blast_radius >= 1000:
            return "2"  # Medium
        return "3"  # Low
```

### Bidirectional Sync

```python
# backend/apps/integrations/servicenow/tasks.py
from celery import shared_task

@shared_task
def sync_change_approvals():
    """Sync change request approvals from ServiceNow."""
    client = ServiceNowClient(
        instance=settings.SERVICENOW_INSTANCE,
        username=settings.SERVICENOW_USERNAME,
        password=settings.SERVICENOW_PASSWORD,
    )
    service = ChangeRequestService(client)

    # Get pending EUCORA submissions with ServiceNow change numbers
    submissions = CABSubmission.objects.filter(
        status=CABSubmission.Status.PENDING,
        external_change_number__isnull=False,
    )

    for submission in submissions:
        asyncio.run(
            service.sync_approval_status(submission.external_change_number)
        )

@shared_task
def create_change_for_deployment(deployment_id: str, correlation_id: str):
    """Create ServiceNow change request for deployment."""
    deployment = Deployment.objects.get(id=deployment_id)

    client = ServiceNowClient(...)
    service = ChangeRequestService(client)

    change = asyncio.run(
        service.create_change_request(deployment, correlation_id)
    )

    # Store change number
    deployment.external_change_number = change["number"]
    deployment.save()
```

---

## Incident Management

### Incident Creation

```python
class IncidentService:
    """ServiceNow Incident Management integration."""

    async def create_incident(
        self,
        deployment,
        error_details: str,
        correlation_id: str,
    ) -> dict:
        """Create incident for failed deployment."""
        incident_data = {
            "short_description": f"Deployment failed: {deployment.name}",
            "description": f"""
                Deployment: {deployment.name}
                Application: {deployment.application.name}
                Version: {deployment.version}
                Ring: {deployment.get_target_ring_display()}

                Error: {error_details}

                Correlation ID: {correlation_id}
            """,
            "category": "Software",
            "subcategory": "Deployment",
            "impact": "2",  # Medium
            "urgency": "2",  # Medium
            "assignment_group": "Application Support",
            "u_correlation_id": correlation_id,
        }

        return await self.client.create_record(
            table="incident",
            data=incident_data,
        )

    async def update_incident(
        self,
        incident_number: str,
        work_notes: str,
        state: str = None,
    ) -> dict:
        """Update incident with progress."""
        update_data = {"work_notes": work_notes}

        if state:
            update_data["state"] = state

        # Find incident by number
        async for inc in self.client.get_table(
            table="incident",
            query=f"number={incident_number}",
            fields=["sys_id"],
        ):
            return await self.client.update_record(
                table="incident",
                sys_id=inc["sys_id"],
                data=update_data,
            )

        return None
```

---

## API Endpoints

```python
# backend/apps/integrations/servicenow/urls.py

# Configuration
GET    /api/v1/integrations/servicenow/config/       # Get config
PUT    /api/v1/integrations/servicenow/config/       # Update config
POST   /api/v1/integrations/servicenow/test/         # Test connection

# CMDB
POST   /api/v1/integrations/servicenow/cmdb/sync/    # Trigger CMDB sync
GET    /api/v1/integrations/servicenow/cmdb/query/   # Query CMDB

# Change Management
POST   /api/v1/integrations/servicenow/change/       # Create change
GET    /api/v1/integrations/servicenow/change/{id}/  # Get change status
POST   /api/v1/integrations/servicenow/change/sync/  # Sync approvals

# Incidents
POST   /api/v1/integrations/servicenow/incident/     # Create incident
```

---

## Configuration Model

```python
class ServiceNowConfig(TimeStampedModel):
    """ServiceNow integration configuration."""

    class IntegrationType(models.TextChoices):
        CMDB = "cmdb", "CMDB Asset Sync"
        ITSM = "itsm", "ITSM Workflows"
        BOTH = "both", "CMDB + ITSM"

    instance = models.CharField(max_length=128)  # e.g., "company-name"
    integration_type = models.CharField(
        max_length=16,
        choices=IntegrationType.choices,
        default=IntegrationType.BOTH,
    )

    # Authentication
    username = EncryptedCharField(max_length=128)
    password = EncryptedCharField(max_length=256)

    # CMDB Settings
    cmdb_sync_enabled = models.BooleanField(default=True)
    cmdb_sync_interval_minutes = models.IntegerField(default=60)
    cmdb_ci_classes = models.JSONField(default=list)  # ["cmdb_ci_computer"]

    # Change Management Settings
    change_auto_create = models.BooleanField(default=True)
    change_approval_sync = models.BooleanField(default=True)
    change_assignment_group = models.CharField(max_length=128, default="CAB")

    # Status
    is_enabled = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True)
    last_sync_status = models.CharField(max_length=32, blank=True)
```

---

## Error Handling

```python
class ServiceNowError(Exception):
    """Base ServiceNow error."""
    pass

class ServiceNowAuthError(ServiceNowError):
    """Authentication failed."""
    pass

class ServiceNowRateLimitError(ServiceNowError):
    """Rate limit exceeded."""
    pass

async def handle_servicenow_error(response: httpx.Response):
    """Handle ServiceNow API errors."""
    if response.status_code == 401:
        raise ServiceNowAuthError("Invalid credentials")

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", 60)
        raise ServiceNowRateLimitError(f"Rate limited. Retry after {retry_after}s")

    if response.status_code >= 400:
        error = response.json().get("error", {})
        raise ServiceNowError(error.get("message", "Unknown error"))
```

---

## Checklist

### Setup

```
☐ ServiceNow instance configured
☐ Integration user created with API access
☐ Custom field u_correlation_id added to change_request
☐ Assignment groups configured
```

### CMDB Sync

```
☐ CI classes selected for sync
☐ Sync schedule configured
☐ Asset mapping validated
☐ Incremental sync tested
```

### Change Management

```
☐ Change types mapped (standard/normal)
☐ Risk mapping configured
☐ Approval sync working
☐ CAB assignment group set
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Hardcoded credentials | Use secrets manager |
| Full CMDB sync every time | Incremental sync with delta |
| Missing correlation IDs | Include in all records |
| No error handling | Handle rate limits, auth errors |
| Polling without limit | Respect API rate limits |
