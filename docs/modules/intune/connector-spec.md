# Intune Connector Specification

**Version**: 2.0
**Platform**: Windows (Intune-managed devices)
**API**: Microsoft Graph API v1.0
**Authentication**: OAuth2 Client Credentials Flow
**Status**: Production-Ready

---

## Overview

The Intune connector integrates with Microsoft Intune via the Microsoft Graph API to publish Win32 LOB applications, create assignments to Entra ID groups, and query deployment status. It supports ring-based rollout targeting and provides detailed install metrics.

---

## Prerequisites

### Azure AD App Registration

1. **Create App Registration** in Azure Portal
   - Navigate to: Azure Active Directory → App registrations → New registration
   - Name: `EUCORA-Intune-Connector`
   - Supported account types: Single tenant
   - Redirect URI: Not required (client credentials flow)

2. **API Permissions** (Application permissions, not delegated)
   - `DeviceManagementApps.ReadWrite.All` - Manage Intune apps
   - `Group.Read.All` - Read group membership
   - `Device.Read.All` - Read device information

3. **Grant Admin Consent** for all permissions

4. **Create Client Secret**
   - Navigate to: Certificates & secrets → New client secret
   - Description: `EUCORA Connector Secret`
   - Expiration: 24 months (recommended)
   - **Copy secret value immediately** (not retrievable later)

### Entra ID Groups (Ring-Based Targeting)

Create Entra ID groups for each ring:
- `EUCORA-Ring-Lab` - Lab devices
- `EUCORA-Ring-Canary` - Canary devices (early adopters)
- `EUCORA-Ring-Pilot` - Pilot devices (broader testing)
- `EUCORA-Ring-Department` - Department-wide rollout
- `EUCORA-Ring-Global` - Global rollout

**Note**: Groups can be dynamic (query-based) or assigned (manual membership).

---

## Configuration

**File**: `scripts/config/settings.json`

```json
{
  "connectors": {
    "intune": {
      "tenant_id": "your-tenant-id-guid",
      "client_id": "your-app-registration-client-id-guid",
      "client_secret": "your-client-secret-value",
      "ring_groups": {
        "lab": "lab-group-id-guid",
        "canary": "canary-group-id-guid",
        "pilot": "pilot-group-id-guid",
        "department": "department-group-id-guid",
        "global": "global-group-id-guid"
      }
    }
  }
}
```

**Environment Variables** (Alternative):
```bash
export INTUNE_TENANT_ID="your-tenant-id"
export INTUNE_CLIENT_ID="your-client-id"
export INTUNE_CLIENT_SECRET="your-client-secret"
export INTUNE_LAB_GROUP_ID="lab-group-id"
export INTUNE_CANARY_GROUP_ID="canary-group-id"
# ... etc
```

---

## API Functions

### `Publish-IntuneApplication`

**Purpose**: Publish Win32 LOB application to Intune with ring-based assignment.

**Parameters**:
- `DeploymentIntent` (hashtable) - Deployment metadata
  - `AppName` (string, required) - Application display name
  - `Description` (string, optional) - Application description
  - `Publisher` (string, required) - Publisher name
  - `Version` (string, optional) - Application version
  - `FileName` (string, required) - `.intunewin` file name
  - `InstallCommand` (string, required) - Silent install command
  - `UninstallCommand` (string, required) - Silent uninstall command
  - `RequiresAdmin` (bool, optional) - Run as system (default: `$true`)
  - `RestartBehavior` (string, optional) - `suppress`, `allow`, `force` (default: `suppress`)
  - `DetectionPath` (string, required) - File system path for detection
  - `DetectionFile` (string, required) - File name for detection
  - `Ring` (string, required) - Target ring (`Lab`, `Canary`, `Pilot`, `Department`, `Global`)
- `CorrelationId` (string, required) - Correlation ID for audit trail

**Returns**: Hashtable
```powershell
@{
    status = 'published'
    correlation_id = 'cid-123'
    app_id = 'guid-app-id'
    app_name = 'Application Name'
    assignment_id = 'guid-assignment-id'
    connector = 'intune'
}
```

**Example**:
```powershell
$intent = @{
    AppName = 'Notepad++ 8.5.1'
    Description = 'Text editor for Windows'
    Publisher = 'Notepad++ Team'
    Version = '8.5.1'
    FileName = 'notepadplusplus-8.5.1.intunewin'
    InstallCommand = 'notepadplusplus-8.5.1.exe /S'
    UninstallCommand = 'C:\Program Files\Notepad++\uninstall.exe /S'
    RequiresAdmin = $true
    RestartBehavior = 'suppress'
    DetectionPath = 'C:\Program Files\Notepad++'
    DetectionFile = 'notepad++.exe'
    Ring = 'Canary'
}

$result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId 'deploy-001'
```

---

### `Remove-IntuneApplication`

**Purpose**: Soft delete application from Intune.

**Parameters**:
- `ApplicationId` (string, required) - Intune app ID (GUID)
- `CorrelationId` (string, required) - Correlation ID for audit trail

**Returns**: Hashtable
```powershell
@{
    status = 'removed'
    correlation_id = 'cid-456'
    app_id = 'guid-app-id'
    connector = 'intune'
}
```

**Example**:
```powershell
$result = Remove-IntuneApplication -ApplicationId 'app-guid-123' -CorrelationId 'remove-001'
```

---

### `Get-IntuneDeploymentStatus`

**Purpose**: Query deployment status by correlation ID.

**Parameters**:
- `CorrelationId` (string, required) - Correlation ID to search for

**Returns**: Hashtable
```powershell
@{
    status = 'queried'
    correlation_id = 'cid-789'
    app_id = 'guid-app-id'
    app_name = 'Application Name'
    success_count = 95
    failure_count = 5
    pending_count = 10
    total_devices = 110
    success_rate = 86.36
    connector = 'intune'
}
```

**Example**:
```powershell
$status = Get-IntuneDeploymentStatus -CorrelationId 'deploy-001'
Write-Host "Success Rate: $($status.success_rate)%"
```

---

### `Test-IntuneConnection`

**Purpose**: Health check for Microsoft Graph API connectivity.

**Parameters**:
- `AuthToken` (string, required) - Not used (OAuth2 token acquired internally)

**Returns**: Hashtable
```powershell
@{
    connector = 'Intune'
    status = 'healthy'
    checked_at = '2026-01-04T23:30:00Z'
    tenant_id = 'your-tenant-id'
}
```

**Example**:
```powershell
$health = Test-IntuneConnection -AuthToken 'dummy'
if ($health.status -eq 'healthy') {
    Write-Host "Intune connector is healthy"
}
```

---

### `Get-IntuneTargetDevices`

**Purpose**: Query ring-based group membership.

**Parameters**:
- `Ring` (string, required) - Target ring (`Lab`, `Canary`, `Pilot`, `Department`, `Global`)

**Returns**: Array of hashtables
```powershell
@(
    @{
        device_id = 'device-guid-001'
        device_name = 'DESKTOP-ABC123'
        ring = 'Canary'
        os = 'Windows'
        last_seen = '2026-01-04T10:00:00Z'
    },
    # ... more devices
)
```

**Example**:
```powershell
$devices = Get-IntuneTargetDevices -Ring 'Canary'
Write-Host "Canary ring has $($devices.Count) devices"
```

---

## Microsoft Graph API Endpoints

### Authentication
- **POST** `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
  - Grant type: `client_credentials`
  - Scope: `https://graph.microsoft.com/.default`

### Application Management
- **POST** `https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps`
  - Create Win32 LOB app
  - Payload: `@odata.type = '#microsoft.graph.win32LobApp'`

- **POST** `https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/{id}/assignments`
  - Create assignment to group
  - Payload: `intent = 'required'`, `target.groupId = 'group-guid'`

- **DELETE** `https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/{id}`
  - Soft delete application

- **GET** `https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps?$filter=contains(notes,'...')`
  - Search apps by correlation ID (stored in `notes` field)

- **GET** `https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/{id}/deviceStatuses`
  - Get install status per device
  - Returns: `installState` (`installed`, `failed`, `notInstalled`, `installing`)

### Group Management
- **GET** `https://graph.microsoft.com/v1.0/groups/{id}/members`
  - Get group members (devices)
  - Filter: `@odata.type = '#microsoft.graph.device'`

---

## Error Handling

### Transient Errors (Retry-able)
- `429 Too Many Requests` - Rate limit exceeded (exponential backoff)
- `500 Internal Server Error` - Microsoft Graph temporary issue
- `503 Service Unavailable` - Microsoft Graph maintenance

### Permanent Errors (Non-retry-able)
- `400 Bad Request` - Invalid payload (fix request)
- `401 Unauthorized` - Invalid credentials (check app registration)
- `403 Forbidden` - Insufficient permissions (check API permissions)
- `404 Not Found` - Resource doesn't exist

### Policy Violations
- `403 Forbidden` with `"policy"` in message - CAB approval required
- `403 Forbidden` with `"compliance"` in message - Compliance policy violation

---

## Idempotency

All operations use correlation IDs to prevent duplicate actions:
- **Publish**: Checks if app with correlation ID already exists (via `notes` field search)
- **Remove**: Safe to retry (DELETE is idempotent)
- **Status**: Read-only operation (always safe)

**Idempotency Key**: Correlation ID is used as idempotency key for all POST/PUT/PATCH operations.

---

## Rate Limits

Microsoft Graph API rate limits:
- **Per-app limit**: 2,000 requests per second per tenant
- **Per-user limit**: Not applicable (client credentials flow)

**Mitigation**:
- Exponential backoff on `429` responses
- Retry-After header respected
- Maximum 3 retries with 2-second base delay

---

## Troubleshooting

### "Authentication failed"
- **Cause**: Invalid client credentials or expired secret
- **Solution**: Verify `client_id`, `client_secret`, and `tenant_id` in config
- **Check**: App registration exists and secret is not expired

### "Insufficient permissions"
- **Cause**: Missing API permissions or admin consent not granted
- **Solution**: Grant admin consent for `DeviceManagementApps.ReadWrite.All`

### "Group not found"
- **Cause**: Invalid group ID in `ring_groups` configuration
- **Solution**: Verify group IDs in Azure Portal (Azure AD → Groups → Object ID)

### "App already exists"
- **Cause**: Duplicate correlation ID (idempotency check)
- **Solution**: Use unique correlation IDs or query existing app

---

## Related Documentation

- [Microsoft Graph API - Intune Apps](https://learn.microsoft.com/en-us/graph/api/resources/intune-apps-win32lobapp)
- [Win32 LOB App Deployment](https://learn.microsoft.com/en-us/mem/intune/apps/apps-win32-app-management)
- [.agents/rules/08-connector-rules.md](../../../.agents/rules/08-connector-rules.md)
- [docs/architecture/execution-plane-connectors.md](../../architecture/execution-plane-connectors.md)

---

**Intune Connector Specification v2.0 - Production-Ready**
