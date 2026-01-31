# CMDB Integration Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The CMDB Integration Agent automatically keeps your ServiceNow CMDB up to date by synchronizing data from multiple sources including SCCM, Intune, Discovery tools, and deployment pipelines. It identifies data discrepancies and helps maintain data quality.

## Key Features

- **Automated Data Synchronization**: Syncs CMDB data from multiple sources on a schedule
- **Data Quality Monitoring**: Validates CMDB data against business rules
- **Discrepancy Detection**: Identifies missing or inconsistent data across sources
- **Bidirectional Sync**: Supports both source-to-CMDB and CMDB-to-source synchronization

## Getting Started

### Accessing the Agent

1. Navigate to **CMDB Integration** from the main dashboard
2. You'll see the CMDB Dashboard with connection status and sync statistics

### Prerequisites

- ServiceNow CMDB access credentials
- At least one configured data source (SCCM, Intune, Discovery)
- CMDB Integration Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Setting Up CMDB Connection

**Step 1**: Navigate to **Connections** tab
**Step 2**: Click **Add Connection**
**Step 3**: Enter ServiceNow instance details:
- Instance URL (e.g., `https://yourinstance.service-now.com`)
- Username and password (or OAuth credentials)
- Test connection to verify access

**Step 4**: Configure table mappings:
- Map source tables to CMDB tables
- Configure field mappings (source field → CMDB attribute)
- Set sync direction (source → CMDB, CMDB → source, or bidirectional)

**Step 5**: Save and activate the connection

### 2. Running a Manual Sync

**Step 1**: Go to **Sync Records** tab
**Step 2**: Select your connection
**Step 3**: Click **Start Sync**
**Step 4**: Choose sync type:
- **Full Sync**: Syncs all records (use for initial setup)
- **Incremental Sync**: Syncs only changes since last sync

**Step 5**: Monitor sync progress in real-time
**Step 6**: Review sync results and discrepancy report

### 3. Reviewing Data Discrepancies

**Step 1**: Navigate to **Discrepancies** tab
**Step 2**: Filter by:
- Sync record
- Discrepancy type (missing in CMDB, missing in source, data mismatch)
- Status (open, resolved, ignored)

**Step 3**: Review discrepancy details:
- Source value vs CMDB value
- Affected records
- Field-level differences

**Step 4**: Resolve discrepancies:
- **Auto-resolve**: Accept source value (for R1 operations)
- **Manual review**: Requires approval (for R2/R3 operations)
- **Ignore**: Mark as false positive

### 4. Viewing Data Quality Reports

**Step 1**: Go to **Reports** → **Data Quality**
**Step 2**: Select connection and date range
**Step 3**: Review metrics:
- Total records synced
- Valid vs invalid records
- Discrepancy count by type
- Data quality score

**Step 4**: Export report for audit purposes

## Configuration Options

### Sync Schedule

Configure automatic sync schedules:
- **Hourly**: For high-frequency changes
- **Daily**: Standard schedule for most sources
- **On-demand**: Manual trigger only

### Validation Rules

Configure validation rules to enforce data quality:
- **Required Fields**: Ensure critical fields are populated
- **Data Format**: Validate data types and formats
- **Referential Integrity**: Check CI relationships
- **Business Rules**: Custom validation logic

### Field Mappings

Map source fields to CMDB attributes:
- One-to-one mappings
- Transformations (e.g., date format conversion)
- Default values for missing fields
- Conditional mappings based on source data

## Best Practices

1. **Start with Incremental Syncs**: Use full syncs only for initial setup
2. **Review Discrepancies Regularly**: Set up alerts for high-priority discrepancies
3. **Validate Before Resolving**: Always verify discrepancy details before auto-resolving
4. **Maintain Audit Trail**: Keep sync records for compliance and troubleshooting
5. **Test Mapping Changes**: Test field mapping changes in a non-production environment first

## Troubleshooting

### Sync Failures

**Problem**: Sync fails with authentication error
**Solution**: Verify ServiceNow credentials and permissions

**Problem**: Sync completes but no records updated
**Solution**: Check table mappings and field mappings configuration

**Problem**: High discrepancy count
**Solution**: Review validation rules and source data quality

### Data Quality Issues

**Problem**: Low data quality score
**Solution**:
- Review validation rule failures
- Check source data completeness
- Update field mappings if needed

**Problem**: Missing relationships
**Solution**: Verify referential integrity rules and CI relationship mappings

## Related Documentation

- [CMDB Integration API Reference](../api/cmdb-integration-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/19-cmdb-integration-agent.md)
