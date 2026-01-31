# Planning Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Planning Agent helps application managers create AI-powered deployment plans from natural language requests. It generates ring assignments, performs blast radius analysis, optimizes schedules, and creates rollback plans.

## Key Features

- **Natural Language Planning**: Generate deployment plans from text descriptions
- **Ring Assignment**: Automatically assign devices to deployment rings
- **Blast Radius Analysis**: Analyze impact of deployments
- **Schedule Optimization**: Optimize deployment windows and avoid change freezes
- **Rollback Planning**: Generate rollback plans for each deployment

## Getting Started

### Accessing the Agent

1. Navigate to **Planning** from the main dashboard
2. You'll see the Planning Dashboard with active plans, ring assignments, and deployment windows

### Prerequisites

- Application portfolio access
- Planning Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Generating Deployment Plan from Natural Language

**Step 1**: Navigate to **Plans** tab
**Step 2**: Click **Generate Plan**
**Step 3**: Enter natural language request:
  Example: "Deploy Office 365 v2.4 to IT department first, then Finance. Start with 10 devices in Ring 1."

**Step 4**: Review generated plan:
- Application and version
- Target scope
- Ring assignments
- Risk assessment
- AI reasoning

**Step 5**: Modify plan if needed:
- Adjust ring assignments
- Change target scope
- Update schedule

**Step 6**: Submit for approval

### 2. Creating Deployment Plan Manually

**Step 1**: Go to **Plans** tab
**Step 2**: Click **Create Plan**
**Step 3**: Enter plan details:
- Name and description
- Application and version
- Target scope (departments, regions, groups)

**Step 4**: Define ring assignments:
- Ring 1 (Canary): Small test group
- Ring 2 (Pilot): Expanded test group
- Ring 3 (Department): Department-wide
- Ring 4 (Global): Organization-wide

**Step 5**: Set success thresholds for each ring
**Step 6**: Save plan

### 3. Assigning Devices to Rings

**Step 1**: Go to plan details
**Step 2**: Navigate to **Rings** tab
**Step 3**: Select ring
**Step 4**: Click **Add Devices**
**Step 5**: Choose device selection method:
- **Automatic**: AI selects devices based on criteria
- **Manual**: Select specific devices
- **Criteria-based**: Define selection criteria

**Step 6**: Review device list:
- Device name and ID
- User principal
- Selection reason
- Criticality level

**Step 7**: Save assignments

### 4. Performing Blast Radius Analysis

**Step 1**: Go to plan details
**Step 2**: Navigate to **Blast Radius** tab
**Step 3**: Click **Analyze**
**Step 4**: Review analysis results:
- Affected devices count
- Affected users count
- Affected departments
- Risk level (Low, Medium, High, Critical)
- Analysis details

**Step 5**: Use analysis to:
- Adjust ring assignments
- Modify target scope
- Update risk assessment

### 5. Configuring Deployment Windows

**Step 1**: Navigate to **Windows** tab
**Step 2**: Click **Create Window**
**Step 3**: Configure window:
- Name and description
- Days of week (e.g., Monday-Friday)
- Start and end time
- Timezone

**Step 4**: Save window
**Step 5**: Windows are automatically considered during schedule optimization

### 6. Managing Change Freeze Periods

**Step 1**: Go to **Freezes** tab
**Step 2**: Click **Create Freeze Period**
**Step 3**: Enter freeze details:
- Name and description
- Start and end dates
- Reason for freeze

**Step 4**: Save freeze period
**Step 5**: Deployments automatically avoid freeze periods

### 7. Creating Rollback Plans

**Step 1**: Go to plan details
**Step 2**: Navigate to **Rollback** tab
**Step 3**: Click **Generate Rollback Plan**
**Step 4**: Review generated plan:
- Rollback strategy (Version Rollback, Uninstall, Configuration Revert)
- Rollback steps
- Estimated duration
- Risk assessment

**Step 5**: Modify rollback plan if needed
**Step 6**: Save rollback plan

### 8. Approving and Executing Plans

**Step 1**: Go to plan details
**Step 2**: Review plan completeness:
- Ring assignments
- Blast radius analysis
- Rollback plan
- Risk assessment

**Step 3**: Click **Approve** (if you have approval permissions)
**Step 4**: After approval, click **Execute**
**Step 5**: Monitor execution progress:
- Ring deployment status
- Success rates
- Device compliance

## Configuration Options

### Plan Generation Settings

- **AI Model**: Choose AI model for plan generation
- **Risk Thresholds**: Configure risk score thresholds
- **Default Ring Sizes**: Set default device counts per ring

### Schedule Optimization

- **Optimization Rules**: Configure schedule optimization preferences
- **Window Preferences**: Prioritize deployment windows
- **Freeze Handling**: Configure freeze period handling

## Best Practices

1. **Start Small**: Begin with Ring 1 (Canary) before expanding
2. **Analyze Blast Radius**: Always perform blast radius analysis before execution
3. **Plan Rollback**: Create rollback plan before deployment
4. **Respect Freezes**: Avoid scheduling during change freeze periods
5. **Monitor Progress**: Track ring success rates before promoting
6. **Document Decisions**: Document plan decisions and reasoning

## Troubleshooting

### Plan Generation Issues

**Problem**: Natural language parsing fails
**Solution**: Use more specific language or create plan manually

**Problem**: Generated plan doesn't match requirements
**Solution**: Refine natural language request or manually adjust plan

### Ring Assignment Issues

**Problem**: No devices assigned to ring
**Solution**: Check device selection criteria and available devices

**Problem**: Too many devices in ring
**Solution**: Adjust ring size or selection criteria

### Schedule Issues

**Problem**: Schedule conflicts with freeze periods
**Solution**: Adjust deployment dates or request freeze exception

**Problem**: No available deployment windows
**Solution**: Create additional deployment windows or adjust schedule

## Related Documentation

- [Planning Agent API Reference](../api/planning-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/workflow-management.md)
- [Planning Document](../planning/29-planning-agent.md)
