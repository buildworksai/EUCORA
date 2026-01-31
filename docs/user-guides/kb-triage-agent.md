# KB & Triage Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The KB & Triage Agent helps desktop support teams resolve tickets faster by providing AI-powered ticket triage, semantic knowledge base search, and incident pattern detection. It integrates with ServiceNow KB, Confluence, SharePoint, and other knowledge sources.

## Key Features

- **Knowledge Base Integration**: Syncs articles from ServiceNow KB, Confluence, SharePoint
- **Semantic Search**: AI-powered search across knowledge articles
- **AI-Powered Triage**: Automatically categorizes and prioritizes tickets
- **Incident Pattern Detection**: Identifies recurring issues and suggests resolutions
- **Resolution Guidance**: Provides step-by-step resolution steps based on similar incidents

## Getting Started

### Accessing the Agent

1. Navigate to **KB & Triage** from the main dashboard
2. You'll see the Triage Dashboard with pending tickets and knowledge base statistics

### Prerequisites

- Knowledge source access (ServiceNow KB, Confluence, or SharePoint)
- KB & Triage Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Configuring Knowledge Sources

**Step 1**: Navigate to **Knowledge Sources** tab
**Step 2**: Click **Add Source**
**Step 3**: Select source type:
- ServiceNow KB
- Confluence
- SharePoint
- Vendor Documentation
- Custom

**Step 4**: Enter connection details:
- Source URL
- Authentication credentials
- Test connection

**Step 5**: Configure sync schedule (default: every 6 hours)
**Step 6**: Save and activate source

### 2. Syncing Knowledge Articles

**Automatic Sync**: Sources sync automatically based on configured schedule

**Manual Sync**:
1. Go to **Knowledge Sources** tab
2. Select source
3. Click **Sync** button
4. Monitor sync progress
5. Review synced article count

### 3. Searching Knowledge Base

**Semantic Search**:
1. Go to **Articles** tab
2. Click **Search**
3. Enter natural language query (e.g., "How to reset password")
4. Review search results ranked by relevance
5. Click on article to view full content

**Filtered Search**:
1. Use filters:
   - Source
   - Category
   - Tags
2. Combine with text search for precise results

### 4. Creating Triage Request

**Step 1**: Navigate to **Triage** tab
**Step 2**: Click **New Request**
**Step 3**: Enter ticket details:
- ServiceNow ticket number (optional)
- Caller name and email
- Affected service
- Short description
- Detailed description

**Step 4**: Submit request
**Step 5**: AI automatically:
- Categorizes ticket
- Assigns priority
- Searches knowledge base
- Suggests resolution steps

### 5. Reviewing AI Triage Results

**Step 1**: Go to **Triage** tab
**Step 2**: Select triaged request
**Step 3**: Review AI suggestions:
- **Category**: Suggested ticket category
- **Priority**: Suggested priority level
- **Resolution**: Suggested resolution steps
- **Escalation**: Whether escalation is recommended

**Step 4**: Review matched articles:
- Relevant knowledge articles
- Similar past incidents
- Resolution patterns

**Step 5**: Accept or modify suggestions
**Step 6**: Apply suggestions to ticket

### 6. Performing Manual Triage

**Step 1**: Select pending request
**Step 2**: Click **Triage** button
**Step 3**: Review ticket details
**Step 4**: Use semantic search to find relevant articles
**Step 5**: Manually set:
- Category
- Priority
- Resolution steps
- Escalation status

**Step 6**: Save triage results

### 7. Viewing Incident Patterns

**Step 1**: Navigate to **Patterns** tab
**Step 2**: Review detected patterns:
- Pattern name and description
- Matching keywords
- Frequency of occurrence
- Last seen date
- Suggested resolution

**Step 3**: Use patterns to:
- Identify recurring issues
- Improve knowledge articles
- Update triage rules

### 8. Providing Feedback

**Step 1**: After resolving ticket, go to **Triage** tab
**Step 2**: Select resolved request
**Step 3**: Click **Provide Feedback**
**Step 4**: Rate triage suggestions:
- Category accuracy
- Priority accuracy
- Resolution helpfulness

**Step 5**: Add comments
**Step 6**: Submit feedback (helps improve AI accuracy)

## Configuration Options

### Knowledge Source Configuration

- **Sync Schedule**: Configure automatic sync frequency
- **Article Filtering**: Filter articles by category or tags
- **Content Indexing**: Configure what content to index

### Triage Configuration

- **AI Confidence Thresholds**: Minimum confidence for auto-applying suggestions
- **Auto-Triage Rules**: Enable automatic triage for certain ticket types
- **Escalation Rules**: Configure when to escalate tickets

## Best Practices

1. **Keep Knowledge Base Updated**: Regularly sync knowledge sources
2. **Provide Feedback**: Rate triage suggestions to improve AI accuracy
3. **Use Semantic Search**: Use natural language queries for better results
4. **Review Patterns**: Regularly review incident patterns to identify trends
5. **Document Resolutions**: Add new resolutions to knowledge base
6. **Train on Examples**: Provide feedback on triage results

## Troubleshooting

### Knowledge Source Issues

**Problem**: Sync fails with authentication error
**Solution**: Verify source credentials and permissions

**Problem**: No articles synced
**Solution**: Check source configuration and article filters

### Search Issues

**Problem**: Search returns no results
**Solution**: Try broader search terms or check article indexing

**Problem**: Search results not relevant
**Solution**: Refine search query or use filters

### Triage Issues

**Problem**: AI suggestions inaccurate
**Solution**: Provide feedback and review triage configuration

**Problem**: Triage request stuck
**Solution**: Check agent status and retry triage operation

## Related Documentation

- [KB & Triage Agent API Reference](../api/kb-triage-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/30-kb-triage-agent.md)
