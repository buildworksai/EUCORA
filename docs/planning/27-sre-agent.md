# E18: SRE Agent (Self-Healing & Remediation)

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P1-Critical
**Sprint**: 17-18 (Weeks 33-36)
**Dependencies**: E3 (RBAC), E7 (pgvector), E8 (AI Workflows), E9 (PowerShell)
**ALM L2 Category**: Non-Functional Requirements (NFRs)

---

## Overview

The SRE Agent assists with typical RunOps tasks such as monitoring SLOs, executing routine maintenance tasks such as preparing and testing backups. It includes self-healing capabilities for proactive remediation and integrates with monitoring platforms for health checks.

### Key Benefits

- Automates documentation-heavy, repetitive RunOps tasks
- Ensures alignment with enterprise standards
- Self-healing scripts for automatic recovery
- Proactive remediation before user impact
- SLO monitoring and enforcement

### Data Sources

- ServiceNow
- SOPs (Standard Operating Procedures)
- SLAs/SLOs
- Monitoring platforms (Prometheus, Datadog, Azure Monitor)
- Health check endpoints

---

## Requirements

### 1. Self-Healing Automation

**Capabilities**:
- Automatic service restart on failure
- Disk space cleanup
- Certificate renewal
- Cache clearing
- Connection pool reset
- Process termination and restart

**Trigger Types**:
- Threshold-based (CPU, memory, disk)
- Pattern-based (error log detection)
- Schedule-based (preventive maintenance)
- Alert-based (from monitoring platforms)

### 2. Proactive Remediation

**Detection**:
- Trend analysis (degradation detection)
- Anomaly detection (unusual patterns)
- Predictive alerts (before failure)
- Health check failures

**Actions**:
- Preventive restart
- Resource scaling recommendations
- Preemptive cleanup
- Configuration adjustment

### 3. SLO Monitoring

**Metrics**:
- Availability (uptime %)
- Latency (p50, p95, p99)
- Error rate
- Throughput
- Resource utilization

**Capabilities**:
- SLO definition from natural language
- Error budget tracking
- Burn rate alerts
- SLO compliance reporting

### 4. Health Monitoring Integration

**Platforms**:
- Prometheus/Grafana
- Datadog
- Azure Monitor
- New Relic
- Custom health endpoints

**Integration**:
- Pull metrics
- Push alerts
- Execute runbooks
- Update dashboards

### 5. Runbook Automation

**Capabilities**:
- Runbook library management
- Automated runbook execution
- Step-by-step guidance
- Evidence collection
- Audit trail

---

## Data Model

### Django Models

```python
# apps/sre_agent/models.py

class MonitoringPlatform(TimeStampedModel):
    """Configured monitoring platform."""
    name = models.CharField(max_length=255)
    platform_type = models.CharField(max_length=50)  # prometheus, datadog, azure_monitor, newrelic
    connection_config = models.JSONField()
    is_active = models.BooleanField(default=True)

class HealthEndpoint(TimeStampedModel):
    """Application health check endpoint."""
    name = models.CharField(max_length=255)
    application = models.ForeignKey('application_portfolio.Application', null=True, on_delete=models.SET_NULL)
    url = models.URLField()
    method = models.CharField(max_length=10, default='GET')
    expected_status = models.IntegerField(default=200)
    timeout_seconds = models.IntegerField(default=30)
    check_interval_minutes = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

class HealthCheckResult(TimeStampedModel):
    """Health check result."""
    endpoint = models.ForeignKey(HealthEndpoint, on_delete=models.CASCADE)
    check_time = models.DateTimeField()
    status = models.CharField(max_length=20)  # healthy, degraded, unhealthy
    response_time_ms = models.IntegerField(null=True)
    status_code = models.IntegerField(null=True)
    error_message = models.TextField(null=True)

class SLODefinition(TimeStampedModel):
    """Service Level Objective definition."""
    name = models.CharField(max_length=255)
    service_name = models.CharField(max_length=255)
    slo_type = models.CharField(max_length=50)  # availability, latency, error_rate, throughput
    target_value = models.FloatField()
    target_unit = models.CharField(max_length=20)  # percent, ms, per_second
    measurement_window = models.CharField(max_length=20)  # hourly, daily, weekly, monthly
    error_budget_policy = models.JSONField(null=True)
    is_active = models.BooleanField(default=True)

class SLOMetric(TimeStampedModel):
    """SLO measurement."""
    slo = models.ForeignKey(SLODefinition, on_delete=models.CASCADE)
    measurement_time = models.DateTimeField()
    actual_value = models.FloatField()
    target_met = models.BooleanField()
    error_budget_remaining = models.FloatField(null=True)
    burn_rate = models.FloatField(null=True)

class SelfHealingRule(TimeStampedModel):
    """Self-healing automation rule."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    trigger_type = models.CharField(max_length=50)  # threshold, pattern, schedule, alert
    trigger_config = models.JSONField()
    target_type = models.CharField(max_length=50)  # service, process, disk, connection
    target_config = models.JSONField()
    remediation_script = models.TextField()
    script_type = models.CharField(max_length=20)  # powershell, bash, python
    risk_level = models.CharField(max_length=10)  # R1, R2, R3
    requires_approval = models.BooleanField(default=False)
    max_executions_per_hour = models.IntegerField(default=3)
    cooldown_minutes = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)

class SelfHealingExecution(TimeStampedModel, CorrelationIdModel):
    """Self-healing execution record."""
    rule = models.ForeignKey(SelfHealingRule, on_delete=models.CASCADE)
    trigger_event = models.JSONField()
    status = models.CharField(max_length=20)  # pending, approved, executing, completed, failed
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    output = models.TextField(null=True)
    error_message = models.TextField(null=True)
    metrics_before = models.JSONField(null=True)
    metrics_after = models.JSONField(null=True)

class Runbook(TimeStampedModel):
    """Operational runbook."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    steps = models.JSONField()
    automation_level = models.CharField(max_length=20)  # manual, semi_auto, full_auto
    risk_level = models.CharField(max_length=10)
    estimated_duration_minutes = models.IntegerField()
    is_active = models.BooleanField(default=True)

class RunbookExecution(TimeStampedModel, CorrelationIdModel):
    """Runbook execution record."""
    runbook = models.ForeignKey(Runbook, on_delete=models.CASCADE)
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    trigger_reason = models.TextField()
    status = models.CharField(max_length=20)
    current_step = models.IntegerField(default=0)
    step_results = models.JSONField(default=list)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    evidence = models.JSONField(default=list)
```

---

## Self-Healing Scripts (Enhanced Connectors)

### PowerShell Self-Healing Library

```powershell
# scripts/self-healing/Invoke-ServiceRestart.ps1
function Invoke-ServiceRestart {
    param(
        [Parameter(Mandatory)]
        [string]$ServiceName,
        [int]$MaxRetries = 3,
        [int]$WaitSeconds = 30
    )

    # Correlation ID for audit
    $CorrelationId = [guid]::NewGuid()
    Write-StructuredLog -Level "INFO" -Message "Starting service restart" -CorrelationId $CorrelationId

    # Pre-check
    $ServiceBefore = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Restart-Service -Name $ServiceName -Force
            Start-Sleep -Seconds $WaitSeconds

            $ServiceAfter = Get-Service -Name $ServiceName
            if ($ServiceAfter.Status -eq 'Running') {
                Write-StructuredLog -Level "INFO" -Message "Service restarted successfully" -CorrelationId $CorrelationId
                return @{
                    Success = $true
                    Attempts = $i
                    CorrelationId = $CorrelationId
                }
            }
        } catch {
            Write-StructuredLog -Level "WARN" -Message "Retry $i failed: $_" -CorrelationId $CorrelationId
        }
    }

    return @{ Success = $false; Attempts = $MaxRetries; CorrelationId = $CorrelationId }
}

# scripts/self-healing/Clear-DiskSpace.ps1
function Clear-DiskSpace {
    param(
        [string]$DriveLetter = "C",
        [int]$TargetFreePercent = 15
    )

    $CorrelationId = [guid]::NewGuid()
    $Actions = @()

    # Clear temp files
    Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    $Actions += "Cleared user temp"

    # Clear Windows temp
    Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    $Actions += "Cleared Windows temp"

    # Clear old logs
    Get-ChildItem -Path "C:\Logs" -Recurse -File |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force
    $Actions += "Cleared old logs"

    # Verify
    $Drive = Get-PSDrive -Name $DriveLetter
    $FreePercent = ($Drive.Free / ($Drive.Free + $Drive.Used)) * 100

    return @{
        Success = $FreePercent -ge $TargetFreePercent
        FreePercent = [math]::Round($FreePercent, 2)
        Actions = $Actions
        CorrelationId = $CorrelationId
    }
}

# scripts/self-healing/Reset-ConnectionPool.ps1
function Reset-ConnectionPool {
    param(
        [Parameter(Mandatory)]
        [string]$AppPoolName
    )

    $CorrelationId = [guid]::NewGuid()

    Import-Module WebAdministration
    Restart-WebAppPool -Name $AppPoolName

    Start-Sleep -Seconds 10
    $Pool = Get-WebAppPoolState -Name $AppPoolName

    return @{
        Success = $Pool.Value -eq 'Started'
        CorrelationId = $CorrelationId
    }
}
```

---

## Agent Workflow Definition

```json
{
  "name": "sre_self_healing_workflow",
  "agent_type": "sre",
  "risk_level": "R2",
  "is_continuous": true,
  "poll_interval_minutes": 5,
  "steps": [
    {
      "name": "collect_metrics",
      "description": "Collect metrics from monitoring platforms",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "check_health_endpoints",
      "description": "Check all configured health endpoints",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "evaluate_slos",
      "description": "Evaluate SLO compliance and error budget",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "detect_anomalies",
      "description": "Detect anomalies and degradation patterns",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "trigger_self_healing",
      "description": "Trigger self-healing rules if conditions met",
      "risk_level": "R2",
      "requires_approval": "conditional",
      "approval_condition": "rule.requires_approval == true"
    },
    {
      "name": "execute_remediation",
      "description": "Execute remediation scripts",
      "risk_level": "R2",
      "requires_approval": "conditional"
    },
    {
      "name": "verify_recovery",
      "description": "Verify system recovery after remediation",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "update_metrics",
      "description": "Update metrics and SLO status",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "operations_policy",
    "change_management_policy"
  ]
}
```

---

## API Endpoints

```
# Monitoring Platforms
GET/POST /api/sre/monitoring-platforms/
POST /api/sre/monitoring-platforms/{id}/test/

# Health Endpoints
GET/POST /api/sre/health-endpoints/
POST /api/sre/health-endpoints/{id}/check/
GET /api/sre/health-endpoints/{id}/history/

# SLOs
GET/POST /api/sre/slos/
GET /api/sre/slos/{id}/metrics/
GET /api/sre/slos/{id}/error-budget/

# Self-Healing Rules
GET/POST /api/sre/self-healing-rules/
GET/PUT/DELETE /api/sre/self-healing-rules/{id}/
POST /api/sre/self-healing-rules/{id}/test/
POST /api/sre/self-healing-rules/{id}/execute/

# Executions
GET /api/sre/executions/
GET /api/sre/executions/{id}/
POST /api/sre/executions/{id}/approve/

# Runbooks
GET/POST /api/sre/runbooks/
POST /api/sre/runbooks/{id}/execute/
GET /api/sre/runbook-executions/

# Dashboard
GET /api/sre/dashboard/overview/
GET /api/sre/dashboard/slo-status/
GET /api/sre/dashboard/healing-activity/
```

---

## Frontend Components

### 1. SRE Dashboard

```
AI Agents > SRE
├── System Health
│   ├── Overall health score
│   ├── Endpoint status grid
│   ├── Recent issues
│   └── Active remediations
├── SLO Status
│   ├── SLO cards with compliance %
│   ├── Error budget remaining
│   ├── Burn rate alerts
│   └── Trend charts
├── Self-Healing Activity
│   ├── Recent executions
│   ├── Success/failure rate
│   ├── Pending approvals
│   └── Rule effectiveness
├── Runbook Library
│   ├── Available runbooks
│   ├── Recent executions
│   └── Execute runbook
└── Monitoring Integration
    ├── Connected platforms
    ├── Metric queries
    └── Alert rules
```

### 2. Self-Healing Rule Editor

```
Self-Healing Rule: Restart on High CPU
├── Trigger Configuration
│   ├── Type: Threshold
│   ├── Metric: CPU utilization
│   ├── Operator: Greater than
│   ├── Threshold: 90%
│   └── Duration: 5 minutes
├── Target Configuration
│   ├── Type: Service
│   ├── Service name pattern
│   └── Scope (devices/groups)
├── Remediation Script
│   ├── Script type: PowerShell
│   ├── Script content (editor)
│   └── Test script
├── Safety Controls
│   ├── Risk level: R2
│   ├── Requires approval: No
│   ├── Max executions/hour: 3
│   └── Cooldown: 15 min
└── Save / Test / Enable
```

---

## Acceptance Criteria

- [ ] Monitoring platform integration (at least 2)
- [ ] Health endpoint monitoring
- [ ] SLO definition and tracking
- [ ] Self-healing rule engine
- [ ] PowerShell self-healing scripts
- [ ] Approval workflow for R2/R3
- [ ] Runbook library and execution
- [ ] Evidence collection
- [ ] Dashboard with health status
- [ ] ≥90% test coverage
