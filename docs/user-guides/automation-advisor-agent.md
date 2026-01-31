# Automation Advisor Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Automation Advisor Agent helps IT operations teams identify automation opportunities by analyzing task patterns, calculating ROI, and tracking automation candidates through implementation. It helps prioritize automation efforts based on potential savings.

## Key Features

- **Task Pattern Detection**: Identifies repetitive, manual, and error-prone tasks
- **Automation Candidate Scoring**: Scores automation opportunities by ROI and effort
- **ROI Analysis**: Calculates potential time and cost savings
- **Automation Tracking**: Tracks automation candidates from identification to implementation
- **Automation Reports**: Generates reports on automation opportunities and savings

## Getting Started

### Accessing the Agent

1. Navigate to **Automation Advisor** from the main dashboard
2. You'll see the Advisor Dashboard with automation candidates, ROI analysis, and implementation tracking

### Prerequisites

- Automation Advisor Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Viewing Task Patterns

**Step 1**: Navigate to **Patterns** tab
**Step 2**: View detected patterns:
- Pattern name and description
- Task type (Repetitive, Manual, Error-Prone)
- Frequency (how often task is performed)
- Average duration

**Step 3**: Filter by task type
**Step 4**: Click on pattern to view details:
- Task examples
- Automation suggestions
- Related candidates

### 2. Reviewing Automation Candidates

**Step 1**: Go to **Candidates** tab
**Step 2**: View candidate list:
- Candidate name
- Description
- Automation score (0-100)
- ROI score (0-100)
- Estimated savings (hours)
- Implementation effort (Low, Medium, High)
- Status (Identified, Under Review, Approved, Implemented, Rejected)

**Step 3**: Filter by:
- Status
- Minimum ROI score
- Implementation effort
- Automation score

**Step 4**: Sort by ROI score or automation score
**Step 5**: Click on candidate to view details

### 3. Analyzing Automation ROI

**Step 1**: Go to candidate details
**Step 2**: Review ROI analysis:
- **Current State**:
  - Frequency of task
  - Average duration
  - Time spent per period
  - Cost per period
- **Automated State**:
  - Estimated automation time
  - Time saved per period
  - Cost savings per period
- **ROI Calculation**:
  - Implementation cost
  - Maintenance cost
  - Payback period
  - Total savings over time

**Step 3**: Adjust ROI parameters if needed:
- Hourly rate
- Implementation cost
- Maintenance cost

**Step 4**: Review ROI breakdown

### 4. Managing Automation Candidates

**Step 1**: Go to **Candidates** tab
**Step 2**: Select candidate
**Step 3**: Update candidate status:
- **Under Review**: Move to review phase
- **Approved**: Approve for implementation
- **Implemented**: Mark as completed
- **Rejected**: Reject with reason

**Step 4**: Add notes and implementation details
**Step 5**: Track implementation progress

### 5. Running Automation Analysis

**Step 1**: Navigate to **Analyses** tab
**Step 2**: Click **Run Analysis**
**Step 3**: Configure analysis:
- Date range
- Task sources to analyze
- Analysis scope

**Step 4**: Start analysis
**Step 5**: Review analysis results:
- Candidates identified
- Total potential savings
- Top opportunities
- Implementation recommendations

### 6. Configuring ROI Settings

**Step 1**: Go to **ROI Config** tab
**Step 2**: Configure ROI parameters:
- **Hourly Rate**: Average hourly cost for manual tasks
- **Implementation Cost Factor**: Multiplier for implementation cost estimation
- **Maintenance Cost Factor**: Multiplier for maintenance cost estimation

**Step 3**: Save configuration
**Step 4**: ROI calculations use these settings

### 7. Viewing Automation Reports

**Step 1**: Navigate to **Reports** → **Summary**
**Step 2**: Review summary statistics:
- Total candidates identified
- Implemented automations
- Total savings (hours)
- Top opportunity ROI

**Step 3**: View detailed reports:
- **Candidate Report**: List of all candidates with details
- **ROI Report**: ROI analysis by candidate
- **Implementation Report**: Implementation status and progress
- **Savings Report**: Actual vs projected savings

## Configuration Options

### Pattern Detection

- **Detection Rules**: Configure rules for pattern detection
- **Frequency Thresholds**: Minimum frequency to consider for automation
- **Duration Thresholds**: Minimum duration to consider for automation

### Scoring Configuration

- **Automation Score Weights**: Configure weights for automation scoring factors
- **ROI Score Weights**: Configure weights for ROI scoring factors
- **Scoring Thresholds**: Set minimum scores for candidate identification

## Best Practices

1. **Regular Analysis**: Run automation analysis regularly to identify new opportunities
2. **Prioritize High ROI**: Focus on candidates with high ROI scores
3. **Start Small**: Begin with low-effort, high-ROI automations
4. **Track Implementation**: Track automation implementation and actual savings
5. **Review Patterns**: Regularly review task patterns to identify trends
6. **Update ROI Config**: Keep ROI configuration updated with current rates

## Troubleshooting

### Pattern Detection Issues

**Problem**: No patterns detected
**Solution**: Verify task data sources and detection rules

**Problem**: Too many patterns detected
**Solution**: Adjust frequency and duration thresholds

### ROI Calculation Issues

**Problem**: ROI seems incorrect
**Solution**: Review ROI configuration and candidate details

**Problem**: Savings not tracking
**Solution**: Verify implementation tracking and measurement

### Candidate Management Issues

**Problem**: Candidate status not updating
**Solution**: Check permissions and workflow configuration

**Problem**: Duplicate candidates
**Solution**: Review candidate deduplication rules

## Related Documentation

- [Automation Advisor API Reference](../api/automation-advisor-api.yaml)
- [Admin Configuration Guide](../admin-guides/workflow-management.md)
- [Planning Document](../planning/22-automation-advisor-agent.md)
