# Integration Setup Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides instructions for setting up external integrations in EUCORA, including ServiceNow, SIEM platforms, monitoring systems, and other enterprise tools.

## Prerequisites

- Platform Admin role
- Access to external system credentials
- Network connectivity to external systems

---

## ServiceNow Integration

### CMDB Integration

**Step 1**: Navigate to **Settings** → **Integrations** → **ServiceNow**
**Step 2**: Click **Add CMDB Connection**
**Step 3**: Enter connection details:
- **Instance URL**: ServiceNow instance URL (e.g., `https://yourinstance.service-now.com`)
- **Username**: ServiceNow API username
- **Password**: ServiceNow API password (stored encrypted)
- **API Version**: API version (default: `v1`)

**Step 4**: Test connection
**Step 5**: Configure table mappings:
- Map source tables to CMDB tables
- Configure field mappings
- Set sync direction

**Step 6**: Save and activate connection

### Change Management Integration

**Step 1**: Navigate to **Settings** → **Integrations** → **ServiceNow**
**Step 2**: Click **Add Change Management Connection**
**Step 3**: Enter connection details (same as CMDB)
**Step 4**: Configure change sync:
- **Sync Schedule**: How often to sync changes (default: hourly)
- **Change States**: Which states to sync
- **Notification Rules**: When to send notifications

**Step 5**: Save and activate

### Request Management Integration

**Step 1**: Navigate to **Settings** → **Integrations** → **ServiceNow**
**Step 2**: Click **Add Request Management Connection**
**Step 3**: Enter connection details
**Step 4**: Configure request sync:
- **Sync Schedule**: How often to sync requests
- **Request Types**: Which types to sync
- **SLA Monitoring**: Enable SLA monitoring

**Step 5**: Save and activate

### Knowledge Base Integration

**Step 1**: Navigate to **Settings** → **Integrations** → **ServiceNow**
**Step 2**: Click **Add Knowledge Base Connection**
**Step 3**: Enter connection details
**Step 4**: Configure KB sync:
- **Sync Schedule**: How often to sync articles
- **Article Categories**: Which categories to sync
- **Content Filtering**: Filter articles by criteria

**Step 5**: Save and activate

---

## SIEM Integration

### Microsoft Sentinel

**Step 1**: Navigate to **Settings** → **Integrations** → **SIEM**
**Step 2**: Click **Add SIEM Connection**
**Step 3**: Select **Microsoft Sentinel**
**Step 4**: Enter connection details:
- **Workspace ID**: Azure Log Analytics workspace ID
- **Shared Key**: Workspace shared key
- **API Endpoint**: Sentinel API endpoint

**Step 5**: Configure alert sync:
- **Sync Schedule**: How often to sync alerts
- **Severity Filter**: Which severities to sync
- **Alert Types**: Which types to sync

**Step 6**: Test connection
**Step 7**: Save and activate

### Splunk

**Step 1**: Navigate to **Settings** → **Integrations** → **SIEM**
**Step 2**: Click **Add SIEM Connection**
**Step 3**: Select **Splunk**
**Step 4**: Enter connection details:
- **Splunk URL**: Splunk instance URL
- **Username**: Splunk API username
- **Password**: Splunk API password
- **API Token**: Splunk API token (alternative to username/password)

**Step 5**: Configure alert sync (similar to Sentinel)
**Step 6**: Save and activate

### IBM QRadar

**Step 1**: Navigate to **Settings** → **Integrations** → **SIEM**
**Step 2**: Click **Add SIEM Connection**
**Step 3**: Select **IBM QRadar**
**Step 4**: Enter connection details:
- **QRadar URL**: QRadar instance URL
- **API Token**: QRadar API token
- **API Version**: API version

**Step 5**: Configure alert sync
**Step 6**: Save and activate

---

## Monitoring Platform Integration

### Prometheus

**Step 1**: Navigate to **Settings** → **Integrations** → **Monitoring**
**Step 2**: Click **Add Monitoring Platform**
**Step 3**: Select **Prometheus**
**Step 4**: Enter connection details:
- **Prometheus URL**: Prometheus server URL
- **API Endpoint**: Prometheus API endpoint (default: `/api/v1`)
- **Authentication**: Basic auth or bearer token

**Step 5**: Configure metric collection:
- **Collection Interval**: How often to collect metrics
- **Metrics to Collect**: Select metrics to collect
- **Query Templates**: Configure PromQL queries

**Step 6**: Save and activate

### Datadog

**Step 1**: Navigate to **Settings** → **Integrations** → **Monitoring**
**Step 2**: Click **Add Monitoring Platform**
**Step 3**: Select **Datadog**
**Step 4**: Enter connection details:
- **API Key**: Datadog API key
- **Application Key**: Datadog application key
- **Site**: Datadog site (e.g., `datadoghq.com`)

**Step 5**: Configure metric collection
**Step 6**: Save and activate

### Azure Monitor

**Step 1**: Navigate to **Settings** → **Integrations** → **Monitoring**
**Step 2**: Click **Add Monitoring Platform**
**Step 3**: Select **Azure Monitor**
**Step 4**: Enter connection details:
- **Tenant ID**: Azure tenant ID
- **Client ID**: Azure application client ID
- **Client Secret**: Azure application client secret
- **Subscription ID**: Azure subscription ID

**Step 5**: Configure metric collection
**Step 6**: Save and activate

---

## Vulnerability Scanner Integration

### Qualys

**Step 1**: Navigate to **Settings** → **Integrations** → **Vulnerability Scanners**
**Step 2**: Click **Add Scanner**
**Step 3**: Select **Qualys**
**Step 4**: Enter connection details:
- **Qualys URL**: Qualys platform URL
- **Username**: Qualys API username
- **Password**: Qualys API password

**Step 5**: Configure scan sync:
- **Sync Schedule**: How often to sync scan results
- **Scan Types**: Which scan types to sync
- **Severity Filter**: Which severities to sync

**Step 6**: Save and activate

### Nessus

**Step 1**: Navigate to **Settings** → **Integrations** → **Vulnerability Scanners**
**Step 2**: Click **Add Scanner**
**Step 3**: Select **Nessus**
**Step 4**: Enter connection details:
- **Nessus URL**: Nessus server URL
- **API Key**: Nessus API key
- **Secret Key**: Nessus secret key

**Step 5**: Configure scan sync
**Step 6**: Save and activate

---

## Knowledge Source Integration

### Confluence

**Step 1**: Navigate to **Settings** → **Integrations** → **Knowledge Sources**
**Step 2**: Click **Add Source**
**Step 3**: Select **Confluence**
**Step 4**: Enter connection details:
- **Confluence URL**: Confluence instance URL
- **Username**: Confluence username
- **API Token**: Confluence API token

**Step 5**: Configure content sync:
- **Spaces to Sync**: Select Confluence spaces
- **Sync Schedule**: How often to sync
- **Content Filter**: Filter by labels or categories

**Step 6**: Save and activate

### SharePoint

**Step 1**: Navigate to **Settings** → **Integrations** → **Knowledge Sources**
**Step 2**: Click **Add Source**
**Step 3**: Select **SharePoint**
**Step 4**: Enter connection details:
- **SharePoint URL**: SharePoint site URL
- **Client ID**: Azure app client ID
- **Client Secret**: Azure app client secret
- **Tenant ID**: Azure tenant ID

**Step 5**: Configure content sync:
- **Sites to Sync**: Select SharePoint sites
- **Libraries to Sync**: Select document libraries
- **Sync Schedule**: How often to sync

**Step 6**: Save and activate

---

## Testing Integrations

### Connection Testing

**Step 1**: Navigate to integration configuration
**Step 2**: Click **Test Connection**
**Step 3**: Review test results:
- Connection status
- Authentication status
- API access verification

**Step 4**: Fix any issues and retest

### Sync Testing

**Step 1**: Navigate to integration configuration
**Step 2**: Click **Test Sync**
**Step 3**: Review sync results:
- Records synced
- Errors encountered
- Sync duration

**Step 4**: Review synced data in EUCORA

---

## Troubleshooting

### Connection Failures

**Problem**: Integration connection fails
**Solution**:
1. Verify network connectivity
2. Check credentials
3. Verify API permissions
4. Check firewall rules

### Sync Failures

**Problem**: Data sync fails
**Solution**:
1. Check sync logs
2. Verify API rate limits
3. Check data format compatibility
4. Review error messages

### Authentication Issues

**Problem**: Authentication fails
**Solution**:
1. Verify credentials
2. Check token expiration
3. Verify OAuth configuration
4. Review authentication logs

---

## Related Documentation

- [Agent Configuration Guide](agent-configuration.md)
- [Workflow Management Guide](workflow-management.md)
- [Monitoring Agents Guide](monitoring-agents.md)
