# Integration Setup Runbook

**SPDX-License-Identifier: Apache-2.0**  
**Copyright (c) 2026 BuildWorks.AI**

## Overview

This runbook provides step-by-step instructions for setting up external system integrations in EUCORA.

---

## ServiceNow CMDB Integration

### Prerequisites
- ServiceNow instance URL
- Service account with read access to `cmdb_ci_computer` table
- Basic authentication credentials or OAuth2 app registration

### Setup Steps

1. **Create Integration Record**
   ```bash
   POST /api/v1/integrations/
   {
     "name": "ServiceNow CMDB",
     "type": "servicenow_cmdb",
     "api_url": "https://your-instance.service-now.com",
     "auth_type": "basic",
     "credentials": {
       "username": "service_account",
       "password": "password"
     },
     "sync_interval_minutes": 30
   }
   ```

2. **Test Connection**
   ```bash
   POST /api/v1/integrations/{id}/test/
   ```

3. **Enable Integration**
   ```bash
   PATCH /api/v1/integrations/{id}/
   {
     "is_enabled": true
   }
   ```

4. **Trigger Manual Sync**
   ```bash
   POST /api/v1/integrations/{id}/sync/
   ```

### Field Mapping

ServiceNow fields are automatically mapped to Asset model:
- `name` → `name`
- `serial_number` → `serial_number`
- `location.display_value` → `location`
- `assigned_to.display_value` → `owner`
- `install_status` → `status` (mapped)
- `category` → `type` (mapped)

---

## Microsoft Entra ID Integration

### Prerequisites
- Azure AD tenant ID
- App registration with Microsoft Graph API permissions:
  - `User.Read.All`
  - `Directory.Read.All`
  - `DeviceManagementManagedDevices.Read.All`
- OAuth2 client credentials (client ID, client secret, tenant ID)

### Setup Steps

1. **Register App in Azure Portal**
   - Create app registration
   - Grant required API permissions
   - Create client secret
   - Note: Client ID, Tenant ID, Client Secret

2. **Create Integration Record**
   ```bash
   POST /api/v1/integrations/
   {
     "name": "Entra ID",
     "type": "entra_id",
     "api_url": "https://graph.microsoft.com/v1.0",
     "auth_type": "oauth2",
     "credentials": {
       "client_id": "your-client-id",
       "client_secret": "your-client-secret",
       "tenant_id": "your-tenant-id",
       "access_token": "initial-token"  # Will be refreshed automatically
     },
     "sync_interval_minutes": 60,
     "metadata": {
       "api_url": "https://graph.microsoft.com/v1.0"
     }
   }
   ```

3. **Test Connection**
   ```bash
   POST /api/v1/integrations/{id}/test/
   ```

4. **Enable Integration**
   ```bash
   PATCH /api/v1/integrations/{id}/
   {
     "is_enabled": true
   }
   ```

### Data Synced
- Users → Django User model
- Groups → Django Group model (for RBAC)
- Managed Devices → Asset model (with compliance scores)

---

## ServiceNow ITSM Integration

### Prerequisites
- ServiceNow instance URL
- Service account with create/read access to `change_request` table
- Basic authentication or OAuth2

### Setup Steps

1. **Create Integration Record**
   ```bash
   POST /api/v1/integrations/
   {
     "name": "ServiceNow ITSM",
     "type": "servicenow_itsm",
     "api_url": "https://your-instance.service-now.com",
     "auth_type": "basic",
     "credentials": {
       "username": "service_account",
       "password": "password"
     },
     "metadata": {
       "custom_fields": {
         "u_deployment_intent_id": "correlation_id"
       }
     }
   }
   ```

2. **Link to CAB Workflow**
   - When creating CAB approval, external CR will be automatically created
   - Approval status synced from ServiceNow

---

## Datadog Integration

### Prerequisites
- Datadog account
- API key and Application key

### Setup Steps

1. **Get API Keys**
   - Navigate to Datadog → Organization Settings → API Keys
   - Create API key and Application key

2. **Create Integration Record**
   ```bash
   POST /api/v1/integrations/
   {
     "name": "Datadog",
     "type": "datadog",
     "api_url": "https://api.datadoghq.com/api/v1",
     "auth_type": "token",
     "credentials": {
       "api_key": "your-api-key",
       "app_key": "your-app-key"
     }
   }
   ```

3. **Push Metrics**
   - Deployment metrics automatically pushed via Celery tasks
   - Custom metrics can be pushed via service methods

---

## Troubleshooting

### Connection Test Fails

1. **Check Credentials**
   - Verify credentials are correct
   - Check credential expiration (OAuth2 tokens)

2. **Check Network Connectivity**
   - Verify API URL is accessible
   - Check firewall rules

3. **Check API Permissions**
   - Verify service account has required permissions
   - Check API rate limits

### Sync Fails

1. **Check Sync Logs**
   ```bash
   GET /api/v1/integrations/{id}/logs/
   ```

2. **Review Error Messages**
   - Check `error_message` and `error_details` in sync log
   - Verify field mappings are correct

3. **Check Rate Limits**
   - Some APIs have rate limits
   - Adjust `sync_interval_minutes` if needed

### Performance Issues

1. **Optimize Sync Interval**
   - Increase interval for large datasets
   - Use incremental sync where supported

2. **Filter Data**
   - Use metadata filters to reduce data volume
   - Sync only active records

---

## Security Best Practices

1. **Credential Storage**
   - Never store credentials in plaintext
   - Use vault references in production
   - Rotate credentials regularly

2. **API Permissions**
   - Follow principle of least privilege
   - Use service accounts, not user accounts
   - Scope permissions to minimum required

3. **Audit Logging**
   - All sync operations logged
   - Correlation IDs for traceability
   - Review sync logs regularly

---

**Last Updated**: 2026-01-06  
**Version**: 1.0


