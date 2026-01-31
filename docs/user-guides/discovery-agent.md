# Discovery Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Discovery Agent helps application managers discover applications across multiple sources, normalize application data, identify license gaps, and detect patch gaps. It provides a unified view of your application portfolio.

## Key Features

- **Multi-Source Discovery**: Discovers applications from SCCM, Intune, AD, CMDB, and spreadsheets
- **Application Normalization**: Normalizes application names across sources into canonical records
- **License Gap Detection**: Identifies unlicensed, over-licensed, and version mismatch issues
- **Patch Gap Detection**: Detects applications with outdated versions
- **Discovery Reports**: Generates comprehensive discovery reports

## Getting Started

### Accessing the Agent

1. Navigate to **Discovery** from the main dashboard
2. You'll see the Discovery Dashboard with discovery sources, normalized applications, and gap analysis

### Prerequisites

- Access to discovery sources (SCCM, Intune, AD, CMDB)
- Discovery Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Configuring Discovery Sources

**Step 1**: Navigate to **Sources** tab
**Step 2**: Click **Add Source**
**Step 3**: Select source type:
- SCCM
- Intune
- Active Directory
- CMDB
- Spreadsheet

**Step 4**: Enter connection details:
- Source name
- Connection configuration (varies by source type)
- Test connection

**Step 5**: Configure sync schedule (default: daily)
**Step 6**: Save and activate source

### 2. Running Discovery

**Automatic Discovery**: Sources run automatically based on configured schedule

**Manual Discovery**:
1. Go to **Runs** tab
2. Click **Start Discovery**
3. Select source(s)
4. Choose discovery type:
   - **Full Discovery**: Discovers all applications
   - **Incremental Discovery**: Discovers only changes

**Step 5**: Monitor discovery progress
**Step 6**: Review discovery results

### 3. Viewing Discovered Applications

**Step 1**: Go to **Applications** → **Discovered**
**Step 2**: View discovered applications:
- Application name
- Vendor
- Version
- Source
- Device count

**Step 3**: Filter by:
- Source
- Vendor
- Search by name

**Step 4**: Click on application to view details

### 4. Normalizing Applications

**Step 1**: Navigate to **Applications** → **Normalized**
**Step 2**: View normalized applications:
- Normalized name
- Vendor
- Version
- Source applications (linked discovered apps)
- Confidence score

**Step 3**: Review normalization suggestions:
- Applications with low confidence scores
- Potential duplicates
- Merge suggestions

**Step 4**: Merge applications:
- Select applications to merge
- Click **Merge**
- Review merge preview
- Confirm merge

### 5. Managing License Gaps

**Step 1**: Go to **License Gaps** tab
**Step 2**: View gap list:
- Application name
- Gap type:
  - Unlicensed: Application installed but no license
  - Over-licensed: More licenses than installations
  - Version Mismatch: License version doesn't match installed version
- Affected devices
- Status (Open, Resolved, Accepted)

**Step 3**: Resolve gaps:
- **Purchase License**: Mark as resolved after purchasing
- **Remove Application**: Mark as resolved after removal
- **Accept Gap**: Accept gap with justification

**Step 4**: Filter by gap type and status

### 6. Managing Patch Gaps

**Step 1**: Navigate to **Patch Gaps** tab
**Step 2**: View patch gap list:
- Application name
- Current version
- Latest version
- Affected devices
- Status (Open, Patched, Accepted)

**Step 3**: Review patch gaps:
- Priority (based on affected device count)
- Security implications
- Patch availability

**Step 4**: Resolve gaps:
- **Deploy Patch**: Create deployment plan for patching
- **Accept Gap**: Accept gap with justification
- **Mark as Patched**: After patch deployment

### 7. Generating Discovery Reports

**Step 1**: Go to **Reports** → **Generate Report**
**Step 2**: Select report type:
- **Application Inventory**: Complete application list
- **License Gap Report**: License gap analysis
- **Patch Gap Report**: Patch gap analysis
- **Normalization Report**: Normalization statistics

**Step 3**: Configure report parameters:
- Date range
- Sources to include
- Filters (vendor, status, etc.)

**Step 4**: Generate report
**Step 5**: Review and export report

### 8. Viewing Discovery Dashboard

**Step 1**: Navigate to **Dashboard** → **Summary**
**Step 2**: Review summary statistics:
- Total applications discovered
- Normalized applications
- License gaps
- Patch gaps
- Discovery sources status

**Step 3**: View trends:
- Applications discovered over time
- Gap trends
- Normalization progress

## Configuration Options

### Discovery Configuration

- **Sync Schedule**: Configure automatic discovery frequency
- **Application Filters**: Filter applications by criteria
- **Normalization Rules**: Configure normalization matching rules

### Gap Detection

- **License Gap Rules**: Configure license gap detection rules
- **Patch Gap Rules**: Configure patch gap detection rules
- **Gap Thresholds**: Set thresholds for gap alerts

## Best Practices

1. **Run Regular Discoveries**: Schedule daily or weekly discoveries
2. **Review Normalizations**: Regularly review normalization suggestions
3. **Resolve Gaps Promptly**: Address license and patch gaps quickly
4. **Maintain Source Configuration**: Keep source connections updated
5. **Use Reports**: Generate reports for compliance and planning
6. **Document Resolutions**: Document gap resolution decisions

## Troubleshooting

### Discovery Issues

**Problem**: Discovery fails with connection error
**Solution**: Verify source connection configuration and credentials

**Problem**: No applications discovered
**Solution**: Check source configuration and application filters

### Normalization Issues

**Problem**: Applications not normalizing correctly
**Solution**: Review normalization rules and confidence scores

**Problem**: Too many duplicate suggestions
**Solution**: Adjust normalization matching rules

### Gap Detection Issues

**Problem**: Gaps not detected
**Solution**: Verify gap detection rules and license/patch data

**Problem**: False positive gaps
**Solution**: Review gap detection rules and update if needed

## Related Documentation

- [Discovery Agent API Reference](../api/discovery-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/23-discovery-agent.md)
