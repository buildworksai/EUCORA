# SecOps Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The SecOps Agent provides automated vulnerability management, security compliance monitoring, and remediation workflows. It integrates with vulnerability scanners, SIEM platforms, and compliance frameworks to help security teams manage security risks efficiently.

## Key Features

- **Vulnerability Scanning**: Integrates with Qualys, Nessus, Rapid7, and Microsoft Defender
- **CVE Tracking**: Monitors CVEs and maps them to installed applications
- **Automated Remediation**: Creates and executes remediation plans based on risk levels
- **SIEM Integration**: Correlates security alerts with vulnerabilities
- **Compliance Monitoring**: Tracks compliance against CIS, NIST, SOC2, and ISO27001

## Getting Started

### Accessing the Agent

1. Navigate to **SecOps** from the main dashboard
2. You'll see the SecOps Dashboard with vulnerability summary and compliance status

### Prerequisites

- Vulnerability scanner credentials (if using external scanners)
- SIEM platform access (optional, for alert correlation)
- SecOps Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Configuring Vulnerability Scanners

**Step 1**: Navigate to **Scanners** tab
**Step 2**: Click **Add Scanner**
**Step 3**: Select scanner type:
- Qualys
- Nessus
- Rapid7
- Microsoft Defender

**Step 4**: Enter connection details:
- API endpoint URL
- API credentials (API key, username/password)
- Test connection

**Step 5**: Configure sync schedule (default: every 6 hours)
**Step 6**: Save and activate scanner

### 2. Syncing Vulnerabilities

**Automatic Sync**: Scanners sync automatically based on configured schedule

**Manual Sync**:
1. Go to **Scanners** tab
2. Select scanner
3. Click **Sync** button
4. Monitor sync progress
5. Review newly discovered vulnerabilities

### 3. Reviewing Vulnerabilities

**Step 1**: Navigate to **Vulnerabilities** tab
**Step 2**: Filter by:
- Severity (Critical, High, Medium, Low)
- CVE ID
- Search by title or description

**Step 3**: View vulnerability details:
- CVE information
- CVSS score and vector
- Affected products
- Instances on assets

**Step 4**: Review instances:
- Click on vulnerability
- View **Instances** tab
- See affected assets and applications

### 4. Managing Vulnerability Instances

**Remediate Instance**:
1. Go to **Instances** tab
2. Select instance
3. Click **Remediate**
4. Add remediation notes
5. Instance status changes to "Remediated"

**Accept Risk**:
1. Select instance
2. Click **Accept Risk**
3. Provide justification notes
4. Instance status changes to "Accepted"

**Mark as False Positive**:
1. Select instance
2. Click **False Positive**
3. Add explanation notes
4. Instance status changes to "False Positive"

### 5. Creating Remediation Plans

**Step 1**: Navigate to **Remediation Plans** tab
**Step 2**: Click **Create Plan**
**Step 3**: Select vulnerability or multiple instances
**Step 4**: Define remediation steps:
- Patch deployment
- Configuration changes
- Compensating controls

**Step 5**: Set risk level:
- **R1**: Informational (auto-approved)
- **R2**: Requires approval
- **R3**: Critical (mandatory approval)

**Step 6**: Submit for approval (if R2/R3)
**Step 7**: Execute plan after approval

### 6. SIEM Integration

**Configure SIEM Connection**:
1. Go to **SIEM** tab
2. Click **Add Connection**
3. Select SIEM type:
- Splunk
- Microsoft Sentinel
- IBM QRadar
- ArcSight

**Step 4**: Enter connection details and test
**Step 5**: Configure alert sync schedule

**Sync Alerts**:
1. Select SIEM connection
2. Click **Sync Alerts**
3. Review synced alerts
4. Correlate with vulnerabilities

### 7. Compliance Monitoring

**View Compliance Baselines**:
1. Navigate to **Compliance** → **Baselines**
2. Review active baselines (CIS, NIST, SOC2, ISO27001)
3. Check compliance status

**Run Compliance Check**:
1. Go to **Compliance** → **Checks**
2. Click **Run Check**
3. Select baseline and asset
4. Review compliance results:
- Overall score
- Passed/failed controls
- Control-level details

**View Compliance Status**:
1. Go to **Reports** → **Compliance Status**
2. Review compliance by framework
3. Identify non-compliant assets

## Configuration Options

### Scanner Configuration

- **Sync Schedule**: Configure automatic sync frequency
- **Severity Filtering**: Filter vulnerabilities by severity
- **Asset Mapping**: Map scanner assets to EUCORA applications

### Remediation Workflows

- **Auto-remediation**: Enable for low-risk vulnerabilities (R1)
- **Approval Thresholds**: Configure risk levels requiring approval
- **Remediation Scripts**: Define automated remediation steps

### Compliance Baselines

- **Framework Selection**: Choose compliance frameworks
- **Control Definitions**: Configure control requirements
- **Scoring Methodology**: Set compliance scoring rules

## Best Practices

1. **Regular Vulnerability Scans**: Schedule daily or weekly scans
2. **Prioritize Critical CVEs**: Focus on Critical and High severity vulnerabilities
3. **Track Remediation Progress**: Monitor remediation plan execution
4. **Maintain Compliance Baselines**: Keep baselines updated with framework changes
5. **Correlate with SIEM**: Use SIEM alerts to prioritize vulnerabilities
6. **Document Exceptions**: Always document risk acceptance decisions

## Troubleshooting

### Scanner Connection Issues

**Problem**: Scanner connection test fails
**Solution**: Verify API credentials and network connectivity

**Problem**: Sync completes but no vulnerabilities found
**Solution**: Check scanner scan configuration and asset coverage

### Remediation Plan Issues

**Problem**: Remediation plan fails to execute
**Solution**: Verify remediation scripts and target asset access

**Problem**: Plan stuck in "Pending Approval"
**Solution**: Check approval workflow and approver availability

### Compliance Check Issues

**Problem**: Compliance check fails
**Solution**: Verify asset configuration and baseline rules

**Problem**: Low compliance score
**Solution**: Review failed controls and update asset configuration

## Related Documentation

- [SecOps Agent API Reference](../api/secops-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/26-secops-agent.md)
