# Troubleshooting Agents Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides troubleshooting procedures for common AI agent issues in EUCORA. It covers diagnosis, resolution, and prevention strategies.

## Prerequisites

- Platform Admin or Endpoint Operations role
- Access to EUCORA admin interface
- Understanding of agent architecture

---

## Common Issues

### Agent Not Responding

#### Symptoms
- Health check fails
- Tasks not executing
- API requests timeout

#### Diagnosis Steps

1. **Check Agent Service Status**
   - Navigate to **Monitoring** → **Agent Health**
   - Verify agent service is running
   - Check service logs

2. **Verify Network Connectivity**
   - Test agent endpoint connectivity
   - Verify database connectivity
   - Check external API connectivity

3. **Review Agent Logs**
   - Navigate to **Monitoring** → **Logs**
   - Filter by agent and error level
   - Look for connection errors, timeouts, or exceptions

#### Resolution Steps

1. **Restart Agent Service**
   ```bash
   # Restart agent service
   systemctl restart eucora-agent-{agent-name}
   ```

2. **Verify Configuration**
   - Check agent configuration
   - Verify credentials
   - Review connection settings

3. **Check Resource Usage**
   - Monitor CPU and memory usage
   - Check disk space
   - Review database connections

---

### Workflow Execution Failures

#### Symptoms
- Workflow doesn't trigger
- Workflow fails mid-execution
- Steps not executing in order

#### Diagnosis Steps

1. **Review Workflow Configuration**
   - Navigate to workflow details
   - Verify workflow is activated
   - Check trigger conditions

2. **Check Workflow Execution Logs**
   - Navigate to **Workflows** → **Executions**
   - Review failed execution logs
   - Identify failing step

3. **Verify Agent Permissions**
   - Check agent permissions for workflow steps
   - Verify scope restrictions
   - Review approval requirements

#### Resolution Steps

1. **Fix Workflow Configuration**
   - Correct trigger conditions
   - Fix step configuration
   - Update approval gates

2. **Resolve Permission Issues**
   - Grant required permissions
   - Adjust scope restrictions
   - Configure approvers

3. **Retry Workflow**
   - Manually trigger workflow
   - Monitor execution
   - Verify completion

---

### External Integration Failures

#### Symptoms
- Integration sync fails
- Connection test fails
- Data not syncing

#### Diagnosis Steps

1. **Test Connection**
   - Navigate to integration configuration
   - Click **Test Connection**
   - Review test results

2. **Check Integration Logs**
   - Navigate to **Monitoring** → **Integration Health**
   - Review integration logs
   - Check sync history

3. **Verify Credentials**
   - Check API credentials
   - Verify token expiration
   - Review OAuth configuration

#### Resolution Steps

1. **Update Credentials**
   - Refresh API tokens
   - Update passwords
   - Reconfigure OAuth

2. **Check External System Status**
   - Verify external system is operational
   - Check API availability
   - Review rate limits

3. **Retry Sync**
   - Manually trigger sync
   - Monitor sync progress
   - Verify data sync

---

### AI Provider Errors

#### Symptoms
- AI operations fail
- API errors from AI provider
- Timeout errors

#### Diagnosis Steps

1. **Check AI Provider Status**
   - Navigate to **Settings** → **AI Providers**
   - Test provider connection
   - Review provider status

2. **Review API Errors**
   - Check API error messages
   - Verify rate limits
   - Review quota usage

3. **Check Configuration**
   - Verify API credentials
   - Check model availability
   - Review API endpoint

#### Resolution Steps

1. **Update API Credentials**
   - Refresh API keys
   - Update endpoint URLs
   - Verify model names

2. **Handle Rate Limits**
   - Implement retry logic
   - Reduce request frequency
   - Upgrade API tier if needed

3. **Switch Provider**
   - Configure backup provider
   - Update workflow configuration
   - Test with new provider

---

### Data Quality Issues

#### Symptoms
- Incorrect data synced
- Missing data
- Data inconsistencies

#### Diagnosis Steps

1. **Review Sync Logs**
   - Check sync execution logs
   - Review data transformation logs
   - Identify data issues

2. **Compare Source Data**
   - Compare source system data
   - Verify data mappings
   - Check transformation rules

3. **Review Validation Rules**
   - Check validation rule failures
   - Review data quality scores
   - Identify validation issues

#### Resolution Steps

1. **Fix Data Mappings**
   - Update field mappings
   - Correct transformation rules
   - Verify data formats

2. **Update Validation Rules**
   - Adjust validation rules
   - Fix false positives
   - Update data quality thresholds

3. **Resync Data**
   - Trigger full sync
   - Monitor sync progress
   - Verify data quality

---

## Diagnostic Tools

### Health Check Command

```bash
# Check agent health
curl https://api.control-plane.corp/api/{agent}/health/

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "external_apis": "ok"
  }
}
```

### Log Query Examples

```bash
# Query agent logs
curl "https://api.control-plane.corp/api/monitoring/logs?agent={agent}&level=error&since=1h"

# Query workflow execution logs
curl "https://api.control-plane.corp/api/workflows/executions?status=failed&since=24h"
```

### Performance Metrics Query

```bash
# Query agent performance metrics
curl "https://api.control-plane.corp/api/monitoring/metrics?agent={agent}&metric=task_execution_time&since=1h"
```

---

## Prevention Strategies

### Regular Monitoring

1. **Set Up Health Checks**
   - Configure automatic health checks
   - Set up health alerts
   - Monitor health trends

2. **Monitor Performance**
   - Track performance metrics
   - Set performance alerts
   - Review performance trends

3. **Review Logs Regularly**
   - Check logs daily
   - Identify error patterns
   - Address issues proactively

### Configuration Management

1. **Version Control**
   - Use version control for configurations
   - Review configuration changes
   - Test changes before deployment

2. **Documentation**
   - Document configuration changes
   - Maintain runbooks
   - Update troubleshooting guides

3. **Testing**
   - Test configurations in non-production
   - Validate changes before deployment
   - Monitor after deployment

---

## Escalation Procedures

### Level 1: Self-Service Resolution

- Check documentation
- Review logs
- Test connections
- Restart services

### Level 2: Platform Admin Support

- Review complex configurations
- Investigate integration issues
- Resolve permission problems
- Debug workflow issues

### Level 3: Engineering Support

- Investigate code-level issues
- Resolve data corruption
- Fix system bugs
- Performance optimization

---

## Related Documentation

- [Agent Configuration Guide](agent-configuration.md)
- [Monitoring Agents Guide](monitoring-agents.md)
- [Integration Setup Guide](integration-setup.md)
- [Workflow Management Guide](workflow-management.md)
