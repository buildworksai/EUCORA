---
name: connector-development
description: Execution plane connector patterns for EUCORA including Intune, Jamf Pro, SCCM, Landscape, and Ansible integration. Use when building connectors, implementing idempotent operations, or integrating with MDM/UEM platforms.
status: ✅ Working
last-validated: 2026-01-30
---

# Connector Development Patterns

Execution plane connector patterns for EUCORA platform integrations.

---

## Quick Reference

| Connector | API | Auth | Status |
|-----------|-----|------|--------|
| Intune | Microsoft Graph | OAuth 2.0 (cert) | Production |
| Jamf Pro | Jamf Pro API | OAuth 2.0 | Production |
| SCCM | AdminService REST | Windows Auth | Planned |
| Landscape | Landscape API | API Token | Planned |
| Ansible/AWX | AWX API | OAuth | Planned |

---

## Connector Base Pattern

### Abstract Base Class

```python
# backend/apps/connectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ErrorClass(str, Enum):
    TRANSIENT = "transient"  # Retry
    PERMANENT = "permanent"  # Don't retry
    POLICY_VIOLATION = "policy_violation"  # Security/policy issue

@dataclass
class ConnectorResult:
    success: bool
    correlation_id: str
    error_class: Optional[ErrorClass] = None
    error_message: Optional[str] = None
    data: Optional[dict] = None
    was_existing: bool = False  # For idempotency

class BaseConnector(ABC):
    """Abstract base for execution plane connectors."""

    def __init__(self, config: dict):
        self.config = config
        self._client = None

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the execution plane."""
        pass

    @abstractmethod
    async def publish(
        self,
        artifact,
        correlation_id: str,
    ) -> ConnectorResult:
        """Publish artifact to execution plane."""
        pass

    @abstractmethod
    async def get_deployment_status(
        self,
        deployment_id: str,
    ) -> ConnectorResult:
        """Get deployment status from execution plane."""
        pass

    @abstractmethod
    async def rollback(
        self,
        deployment_id: str,
        target_version: str,
    ) -> ConnectorResult:
        """Rollback deployment to target version."""
        pass

    def classify_error(self, exception: Exception) -> ErrorClass:
        """Classify error for retry decisions."""
        message = str(exception).lower()

        # Transient errors (retry)
        if any(code in message for code in ["429", "503", "504", "timeout"]):
            return ErrorClass.TRANSIENT

        # Policy violations (don't retry)
        if any(code in message for code in ["401", "403", "forbidden"]):
            return ErrorClass.POLICY_VIOLATION

        # Default to permanent
        return ErrorClass.PERMANENT
```

---

## Intune Connector

### Configuration

```python
# backend/apps/connectors/intune/config.py
from pydantic import BaseModel

class IntuneConfig(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str  # Or certificate path
    scope: str = "https://graph.microsoft.com/.default"
    api_version: str = "v1.0"
```

### Implementation

```python
# backend/apps/connectors/intune/connector.py
import httpx
from azure.identity import ClientSecretCredential
from ..base import BaseConnector, ConnectorResult, ErrorClass

class IntuneConnector(BaseConnector):
    """Microsoft Intune connector via Graph API."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    async def authenticate(self):
        """Authenticate with Microsoft Graph."""
        credential = ClientSecretCredential(
            tenant_id=self.config["tenant_id"],
            client_id=self.config["client_id"],
            client_secret=self.config["client_secret"],
        )
        self._token = credential.get_token(
            "https://graph.microsoft.com/.default"
        ).token

    async def publish(
        self,
        artifact,
        correlation_id: str,
    ) -> ConnectorResult:
        """Publish Win32 app to Intune."""
        try:
            # Check idempotency - has this already been published?
            existing = await self._find_by_correlation_id(correlation_id)
            if existing:
                return ConnectorResult(
                    success=True,
                    correlation_id=correlation_id,
                    data=existing,
                    was_existing=True,
                )

            # Create Win32 LOB app
            app_data = {
                "displayName": artifact.name,
                "description": artifact.description,
                "publisher": artifact.publisher,
                "fileName": artifact.filename,
                "installCommandLine": artifact.install_command,
                "uninstallCommandLine": artifact.uninstall_command,
                "notes": f"Correlation ID: {correlation_id}",
                # Detection rules, requirements, etc.
            }

            async with httpx.AsyncClient() as client:
                # Create app object
                response = await client.post(
                    f"{self.GRAPH_BASE_URL}/deviceAppManagement/mobileApps",
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                        "X-Correlation-ID": correlation_id,
                    },
                    json={"@odata.type": "#microsoft.graph.win32LobApp", **app_data},
                )
                response.raise_for_status()
                app = response.json()

                # Upload content file
                await self._upload_content(client, app["id"], artifact.file_path)

                # Commit the app
                await self._commit_app(client, app["id"])

            return ConnectorResult(
                success=True,
                correlation_id=correlation_id,
                data={"intune_app_id": app["id"]},
            )

        except Exception as e:
            return ConnectorResult(
                success=False,
                correlation_id=correlation_id,
                error_class=self.classify_error(e),
                error_message=str(e),
            )

    async def _find_by_correlation_id(self, correlation_id: str) -> dict | None:
        """Check if app already exists (idempotency check)."""
        # SECURITY: Escape single quotes in correlation_id for OData filter safety
        # OData uses single quotes for string literals; escape by doubling them
        safe_correlation_id = correlation_id.replace("'", "''")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GRAPH_BASE_URL}/deviceAppManagement/mobileApps",
                headers={"Authorization": f"Bearer {self._token}"},
                params={"$filter": f"contains(notes, '{safe_correlation_id}')"},
            )
            apps = response.json().get("value", [])
            return apps[0] if apps else None

    async def create_assignment(
        self,
        app_id: str,
        group_id: str,
        correlation_id: str,
        intent: str = "required",
    ) -> ConnectorResult:
        """Create app assignment to Entra ID group."""
        assignment = {
            "@odata.type": "#microsoft.graph.mobileAppAssignment",
            "intent": intent,
            "target": {
                "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                "groupId": group_id,
            },
            "settings": {
                "@odata.type": "#microsoft.graph.win32LobAppAssignmentSettings",
                "notifications": "showAll",
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GRAPH_BASE_URL}/deviceAppManagement/mobileApps/{app_id}/assignments",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                json=assignment,
            )
            response.raise_for_status()

        return ConnectorResult(success=True, correlation_id=correlation_id, data=response.json())

    async def get_deployment_status(
        self,
        deployment_id: str,
        correlation_id: str,
    ) -> ConnectorResult:
        """Get install status for an app."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GRAPH_BASE_URL}/deviceAppManagement/mobileApps/{deployment_id}/deviceStatuses",
                headers={"Authorization": f"Bearer {self._token}"},
            )
            response.raise_for_status()

            statuses = response.json().get("value", [])

            return ConnectorResult(
                success=True,
                correlation_id=correlation_id,
                data={
                    "total": len(statuses),
                    "installed": sum(1 for s in statuses if s["installState"] == "installed"),
                    "failed": sum(1 for s in statuses if s["installState"] == "failed"),
                    "pending": sum(1 for s in statuses if s["installState"] == "notInstalled"),
                },
            )
```

---

## Jamf Pro Connector

```python
# backend/apps/connectors/jamf/connector.py

class JamfConnector(BaseConnector):
    """Jamf Pro connector for macOS deployments."""

    async def authenticate(self):
        """Authenticate with Jamf Pro API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['api_url']}/api/v1/auth/token",
                auth=(self.config["username"], self.config["password"]),
            )
            response.raise_for_status()
            self._token = response.json()["token"]

    async def publish(
        self,
        artifact,
        correlation_id: str,
    ) -> ConnectorResult:
        """Publish package to Jamf Pro."""
        try:
            # Upload package
            async with httpx.AsyncClient() as client:
                # Create package record
                package_data = {
                    "name": artifact.name,
                    "fileName": artifact.filename,
                    "notes": f"Correlation ID: {correlation_id}",
                }

                response = await client.post(
                    f"{self.config['api_url']}/api/v1/packages",
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                    },
                    json=package_data,
                )
                response.raise_for_status()
                package = response.json()

                # Upload package file
                with open(artifact.file_path, "rb") as f:
                    upload_response = await client.post(
                        f"{self.config['api_url']}/api/v1/packages/{package['id']}/upload",
                        headers={"Authorization": f"Bearer {self._token}"},
                        files={"file": f},
                    )
                    upload_response.raise_for_status()

            return ConnectorResult(
                success=True,
                correlation_id=correlation_id,
                data={"jamf_package_id": package["id"]},
            )

        except Exception as e:
            return ConnectorResult(
                success=False,
                correlation_id=correlation_id,
                error_class=self.classify_error(e),
                error_message=str(e),
            )

    async def create_policy(
        self,
        name: str,
        package_id: str,
        scope: dict,
        correlation_id: str,
    ) -> ConnectorResult:
        """Create Jamf policy for package deployment."""
        policy_xml = f"""
        <policy>
            <name>{name}</name>
            <enabled>true</enabled>
            <notes>Correlation ID: {correlation_id}</notes>
            <scope>{self._scope_to_xml(scope)}</scope>
            <package_configuration>
                <packages>
                    <package>
                        <id>{package_id}</id>
                        <action>Install</action>
                    </package>
                </packages>
            </package_configuration>
        </policy>
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['api_url']}/JSSResource/policies",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/xml",
                },
                content=policy_xml,
            )
            response.raise_for_status()

        return ConnectorResult(success=True, correlation_id=correlation_id, data={"policy_created": True})
```

---

## SCCM Connector (PowerShell)

```powershell
# scripts/connectors/SCCM/Publish-SCCMPackage.ps1

function Publish-SCCMPackage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$PackagePath,

        [Parameter(Mandatory)]
        [string]$PackageName,

        [Parameter(Mandatory)]
        [string]$CorrelationId,

        [Parameter()]
        [string]$SiteServer = $env:SCCM_SITE_SERVER,

        [Parameter()]
        [string]$SiteCode = $env:SCCM_SITE_CODE
    )

    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    # Import SCCM module
    Import-Module "$($env:SMS_ADMIN_UI_PATH)\..\ConfigurationManager.psd1"
    Set-Location "${SiteCode}:"

    try {
        # Check idempotency
        $existing = Get-CMPackage -Name $PackageName -Fast | Where-Object {
            $_.Comment -like "*$CorrelationId*"
        }

        if ($existing) {
            Write-StructuredLog -Message "Package already exists" -Level Info -CorrelationId $CorrelationId
            return @{
                success = $true
                was_existing = $true
                package_id = $existing.PackageID
            }
        }

        # Create package
        $package = New-CMPackage `
            -Name $PackageName `
            -Path (Split-Path $PackagePath) `
            -Description "Correlation ID: $CorrelationId"

        # Create program
        New-CMProgram `
            -PackageId $package.PackageID `
            -StandardProgramName "Install" `
            -CommandLine "msiexec /i `"$PackageName`" /qn"

        # Distribute to DPs
        Start-CMContentDistribution `
            -PackageId $package.PackageID `
            -DistributionPointGroupName "All Distribution Points"

        return @{
            success = $true
            was_existing = $false
            package_id = $package.PackageID
            correlation_id = $CorrelationId
        }
    }
    catch {
        $errorClass = Get-ErrorClassification -Exception $_.Exception

        return @{
            success = $false
            error_class = $errorClass
            error_message = $_.Exception.Message
            correlation_id = $CorrelationId
        }
    }
}
```

---

## Idempotency Pattern

### Key Principles

1. **Use correlation ID as idempotency key**
2. **Check before create**
3. **Return existing if found**
4. **Store correlation ID in notes/metadata**

```python
async def idempotent_operation(
    self,
    operation_fn,
    correlation_id: str,
    check_fn,
) -> ConnectorResult:
    """Wrap operation with idempotency check."""

    # Check if already done
    existing = await check_fn(correlation_id)
    if existing:
        return ConnectorResult(
            success=True,
            correlation_id=correlation_id,
            data=existing,
            was_existing=True,
        )

    # Perform operation
    result = await operation_fn()

    return ConnectorResult(
        success=True,
        correlation_id=correlation_id,
        data=result,
        was_existing=False,
    )
```

---

## Error Classification

| HTTP Status | Error Class | Retry? |
|-------------|-------------|--------|
| 429 | TRANSIENT | Yes (with backoff) |
| 503 | TRANSIENT | Yes |
| 504 | TRANSIENT | Yes |
| 401 | POLICY_VIOLATION | No |
| 403 | POLICY_VIOLATION | No |
| 400 | PERMANENT | No |
| 404 | PERMANENT | No |
| 500 | PERMANENT | No* |

*May retry once for 500 errors.

---

## Retry with Backoff

```python
import asyncio
from functools import wraps

def retry_transient(max_attempts=5, base_delay=2):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    error_class = self.classify_error(e)

                    if error_class != ErrorClass.TRANSIENT:
                        raise

                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)

            raise last_error
        return wrapper
    return decorator

# Usage
class IntuneConnector(BaseConnector):
    @retry_transient(max_attempts=5)
    async def publish(self, artifact, correlation_id):
        ...
```

---

## Checklist

### Connector Implementation

```
☐ Inherits from BaseConnector
☐ Implements authenticate()
☐ Implements publish() with idempotency
☐ Implements get_deployment_status()
☐ Implements rollback()
☐ Error classification implemented
☐ Correlation ID in all requests
☐ Retry logic for transient errors
```

### Testing

```
☐ Unit tests for all methods
☐ Idempotency tests
☐ Error classification tests
☐ Integration tests (mocked API)
☐ Rollback tests
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Non-idempotent operations | Always check before create |
| Missing correlation IDs | Include in all requests |
| No error classification | Classify all errors |
| Retry on 401/403 | Only retry transient errors |
| Hardcoded credentials | Use vault/secrets manager |
