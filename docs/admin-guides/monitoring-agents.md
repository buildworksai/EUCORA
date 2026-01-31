# Monitoring Agents Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides instructions for monitoring AI agent health, performance, and operational status in EUCORA. It covers health checks, metrics collection, alerting, and troubleshooting.

## Prerequisites

- Platform Admin or Endpoint Operations role
- Access to EUCORA monitoring interface
- Understanding of agent architecture

---

## Agent Health Monitoring

### Health Check Configuration

**Step 1**: Navigate to **Settings** → **Agent Configuration** → **Monitoring**
**Step 2**: Configure health checks:
- **Check Interval**: How often to check agent health (default: 5 minutes)
- **Timeout**: Health check timeout (default: 30 seconds)
- **Retry Count**: Number of retries before marking unhealthy (default: 3)
- **Health Endpoint**: Agent health endpoint URL

**Step 3**: Save configuration

### Viewing Agent Health

**Step 1**: Navigate to **Monitoring** → **Agent Health**
**Step 2**: View agent health dashboard:
- **Overall Status**: Green/Yellow/Red indicator
- **Agent Status**: Individual agent health status
- **Last Check**: Last health check timestamp
- **Uptime**: Agent uptime percentage

**Step 3**: Click on agent to view details:
- Health check history
- Recent errors
- Performance metrics

### Health Check Endpoints

Each agent exposes a health endpoint:

- **Planning Agent**: `/api/planning/health/`
- **SecOps Agent**: `/api/secops/health/`
- **SRE Agent**: `/api/sre/health/`
- **KB Triage Agent**: `/api/kb-triage/health/`
- etc.

Health endpoint returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": "ok",
    "external_apis": "ok",
    "ai_provider": "ok"
  }
}
```

---

## Performance Monitoring

### Agent Performance Metrics

**Step 1**: Navigate to **Monitoring** → **Agent Performance**
**Step 2**: View performance metrics:

#### Task Execution Metrics
- **Tasks Completed**: Number of tasks completed
- **Tasks Failed**: Number of tasks failed
- **Success Rate**: Percentage of successful tasks
- **Average Execution Time**: Average task execution time
- **P95 Execution Time**: 95th percentile execution time

#### API Performance Metrics
- **API Request Count**: Number of API requests
- **API Response Time**: Average API response time
- **API Error Rate**: Percentage of API errors
- **External API Latency**: Latency to external systems

#### Resource Usage Metrics
- **CPU Usage**: CPU utilization percentage
- **Memory Usage**: Memory utilization percentage
- **Database Connections**: Active database connections
- **Queue Depth**: Task queue depth

### Performance Dashboards

**Step 1**: Navigate to **Monitoring** → **Dashboards**
**Step 2**: Select dashboard:
- **Agent Overview**: Overall agent performance
- **Agent Detail**: Detailed metrics for specific agent
- **Workflow Performance**: Workflow execution metrics
- **Integration Health**: External system connectivity

**Step 3**: Customize dashboard:
- Add/remove metrics
- Change time range
- Set refresh interval

---

## Alerting Configuration

### Health Alerts

**Step 1**: Navigate to **Settings** → **Monitoring** → **Alerts**
**Step 2**: Click **Create Alert**
**Step 3**: Configure health alert:
- **Alert Name**: Descriptive name
- **Alert Type**: Select "Agent Health"
- **Condition**: Agent becomes unhealthy
- **Severity**: Critical, High, Medium, Low
- **Notification Channels**: Email, Teams, Slack
- **Recipients**: Alert recipients

**Step 4**: Save alert

### Performance Alerts

**Step 1**: Navigate to **Settings** → **Monitoring** → **Alerts**
**Step 2**: Click **Create Alert**
**Step 3**: Configure performance alert:
- **Alert Name**: Descriptive name
- **Alert Type**: Select "Performance"
- **Metric**: Select metric (e.g., "Task Execution Time")
- **Threshold**: Set threshold value
- **Condition**: Above/Below threshold
- **Duration**: How long threshold must be exceeded

**Step 4**: Configure notifications
**Step 5**: Save alert

### Error Rate Alerts

**Step 1**: Navigate to **Settings** → **Monitoring** → **Alerts**
**Step 2**: Click **Create Alert**
**Step 3**: Configure error rate alert:
- **Alert Name**: Descriptive name
- **Alert Type**: Select "Error Rate"
- **Error Rate Threshold**: Percentage (e.g., 5%)
- **Time Window**: Time window for calculation (e.g., 5 minutes)
- **Minimum Errors**: Minimum errors to trigger alert

**Step 4**: Configure notifications
**Step 5**: Save alert

---

## Log Management

### Viewing Agent Logs

**Step 1**: Navigate to **Monitoring** → **Logs**
**Step 2**: Select agent
**Step 3**: Configure log filters:
- **Log Level**: Debug, Info, Warning, Error
- **Time Range**: Select time range
- **Search**: Search log messages

**Step 4**: View logs:
- Log entries with timestamps
- Log levels
- Log messages
- Correlation IDs

### Log Retention

**Step 1**: Navigate to **Settings** → **Monitoring** → **Log Retention**
**Step 2**: Configure retention:
- **Retention Period**: How long to retain logs (default: 30 days)
- **Archive Policy**: Archive old logs
- **Compression**: Enable log compression

**Step 3**: Save configuration

---

## Integration Health Monitoring

### External System Connectivity

**Step 1**: Navigate to **Monitoring** → **Integration Health**
**Step 2**: View integration status:
- **ServiceNow**: Connection status, last sync, error rate
- **SIEM Platforms**: Connection status, alert sync status
- **Monitoring Platforms**: Connection status, metric collection status
- **Vulnerability Scanners**: Connection status, scan sync status

**Step 3**: Click on integration to view details:
- Connection history
- Sync statistics
- Recent errors

### Connection Testing

**Step 1**: Navigate to integration configuration
**Step 2**: Click **Test Connection**
**Step 3**: Review test results:
- Connection status
- Response time
- Authentication status
- API access verification

---

## Troubleshooting

### Agent Unhealthy

**Problem**: Agent health check fails
**Solution**:
1. Check agent service status
2. Review agent logs for errors
3. Verify database connectivity
4. Check external API connectivity
5. Restart agent service if needed

### High Error Rate

**Problem**: Agent error rate exceeds threshold
**Solution**:
1. Review error logs
2. Identify error patterns
3. Check external system status
4. Verify agent configuration
5. Review recent changes

### Performance Degradation

**Problem**: Agent performance degraded
**Solution**:
1. Check resource usage (CPU, memory)
2. Review task queue depth
3. Check database performance
4. Verify external API latency
5. Scale agent if needed

### Integration Failures

**Problem**: External integration failing
**Solution**:
1. Test connection
2. Verify credentials
3. Check network connectivity
4. Review API rate limits
5. Check external system status

---

## Related Documentation

- [Agent Configuration Guide](agent-configuration.md)
- [Integration Setup Guide](integration-setup.md)
- [Troubleshooting Agents Guide](troubleshooting-agents.md)
