# Phase 5: Operations & Infrastructure - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 3 weeks
**Dependencies**: Phase 1 (Foundation), Phase 2 (Control Plane)

---

## Task Overview

Implement operational and infrastructure scripts for incident response, rollback execution, ring management, drift detection, telemetry, HA/DR, secrets rotation, key management, RBAC setup, and SIEM integration. These scripts ensure the platform is production-ready, resilient, and auditable.

**Success Criteria**:
- Incident response playbooks automated (P0/P1/P2/P3 classification)
- Rollback execution within ≤4h SLA
- Ring promotion automated with gate validation
- Drift detection identifies unauthorized changes
- Telemetry collection for control plane health
- HA/DR failover tested and documented
- Secrets rotation automated (90-day cycle)
- RBAC groups configured with PIM/JIT for Publishers
- SIEM integration with Azure Sentinel operational

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Thin Control Plane**: Infrastructure scripts orchestrate only, never replace execution planes
- ✅ **Separation of Duties**: RBAC enforced, no single user has Packaging + Publishing + Approval
- ✅ **Deterministic Operations**: All operations repeatable and auditable
- ✅ **Evidence-First**: All operational actions logged with correlation IDs
- ✅ **Offline-First**: Scripts support air-gapped environments (SCCM DPs, APT mirrors)

### Quality Standards
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings
- ✅ **Pester Tests**: ≥90% coverage per script
- ✅ **Idempotency**: All operations safe to retry
- ✅ **SLA Adherence**: Rollback ≤4h, incident response per severity
- ✅ **Error Handling**: Structured errors with actionable messages

### Security Requirements
- ✅ **PIM/JIT**: Publishers use Privileged Identity Management with just-in-time activation
- ✅ **Break-Glass**: Dual control for emergency access (two approvers required)
- ✅ **Audit Trail**: Every infrastructure operation logged to SIEM
- ✅ **Immutable Logs**: Event Store and SIEM logs cannot be modified (WORM policy)

---

## Scope: Incident Response (scripts/operations/incident-response/)

### 1. Invoke-IncidentResponse.ps1

```powershell
<#
.SYNOPSIS
    Execute incident response playbook.
.DESCRIPTION
    Classifies incident severity (P0/P1/P2/P3), executes appropriate playbook.
.PARAMETER IncidentDescription
    Description of the incident.
.PARAMETER AffectedRing
    Ring affected by the incident.
.PARAMETER CorrelationId
    Correlation ID of the deployment causing the incident.
.EXAMPLE
    Invoke-IncidentResponse -IncidentDescription "App crashes on startup" -AffectedRing "Canary" -CorrelationId "deploy-123"
#>
function Invoke-IncidentResponse {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$IncidentDescription,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
        [string]$AffectedRing,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Classify severity
    $severity = Get-IncidentSeverity -Description $IncidentDescription -Ring $AffectedRing

    Write-StructuredLog -Level "Critical" -Message "Incident detected: $severity" -CorrelationId $CorrelationId -Metadata @{
        Severity = $severity
        Ring = $AffectedRing
        Description = $IncidentDescription
    }

    # 2. Execute playbook based on severity
    switch ($severity) {
        "P0" {
            # Critical: Global outage or security breach
            # SLA: Immediate response, ≤4h rollback
            Invoke-P0Playbook -CorrelationId $CorrelationId -Ring $AffectedRing
        }
        "P1" {
            # High: Ring outage or major functionality broken
            # SLA: ≤1h response, ≤4h rollback
            Invoke-P1Playbook -CorrelationId $CorrelationId -Ring $AffectedRing
        }
        "P2" {
            # Medium: Partial functionality broken
            # SLA: ≤4h response, ≤24h fix
            Invoke-P2Playbook -CorrelationId $CorrelationId -Ring $AffectedRing
        }
        "P3" {
            # Low: Minor issues, cosmetic bugs
            # SLA: ≤24h response, fix in next deployment
            Invoke-P3Playbook -CorrelationId $CorrelationId -Ring $AffectedRing
        }
    }

    # 3. Notify stakeholders
    Send-IncidentNotification -Severity $severity -Description $IncidentDescription -Ring $AffectedRing
}
```

**Helper Functions**:
- `Get-IncidentSeverity`: Classify incident based on keywords and ring
- `Invoke-P0Playbook`: Immediate rollback, all-hands bridge, CAB emergency session
- `Invoke-P1Playbook`: Rollback affected ring, notify leadership
- `Invoke-P2Playbook`: Create bug ticket, schedule fix for next sprint
- `Invoke-P3Playbook`: Log issue, defer to next release
- `Send-IncidentNotification`: Email/Teams/PagerDuty notification

**Pester Tests Required**:
- P0 incident triggers immediate rollback
- P1 incident notifies leadership
- Severity classification accurate
- All playbooks logged to SIEM

---

## Scope: Rollback Execution (scripts/operations/rollback/)

### 1. Invoke-RollbackExecution.ps1

```powershell
<#
.SYNOPSIS
    Execute rollback for deployment.
.DESCRIPTION
    Rolls back deployment across all execution planes, validates success.
.PARAMETER CorrelationId
    Correlation ID of deployment to rollback.
.PARAMETER TargetRing
    Ring to rollback (default: all rings).
.EXAMPLE
    Invoke-RollbackExecution -CorrelationId "deploy-123" -TargetRing "Canary"
#>
function Invoke-RollbackExecution {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,

        [Parameter(Mandatory = $false)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
        [string]$TargetRing
    )

    $rollbackCid = Get-CorrelationId -Prefix "rollback"

    Write-StructuredLog -Level "Warning" -Message "Starting rollback execution" -CorrelationId $rollbackCid -Metadata @{
        OriginalDeploymentCid = $CorrelationId
        TargetRing = $TargetRing
    }

    # 1. Retrieve original deployment intent
    $intent = Get-DeploymentIntent -CorrelationId $CorrelationId
    if (-not $intent) {
        throw "Deployment intent not found for correlation ID: $CorrelationId"
    }

    # 2. Determine execution planes used
    $connectors = Get-DeploymentConnectors -DeploymentIntent $intent

    # 3. Execute rollback per connector
    $rollbackResults = @()
    foreach ($connector in $connectors) {
        try {
            $result = & "scripts/connectors/$connector/Remove-$($connector)Application.ps1" `
                -ApplicationId $intent.ApplicationId -CorrelationId $rollbackCid
            $rollbackResults += @{ Connector = $connector; Status = "Success"; Result = $result }
        } catch {
            $rollbackResults += @{ Connector = $connector; Status = "Failed"; Error = $_.Exception.Message }
        }
    }

    # 4. Validate rollback success
    $failedRollbacks = $rollbackResults | Where-Object { $_.Status -eq "Failed" }
    if ($failedRollbacks.Count -gt 0) {
        Write-StructuredLog -Level "Error" -Message "Rollback failed for some connectors" -CorrelationId $rollbackCid -Metadata @{
            FailedConnectors = ($failedRollbacks | ForEach-Object { $_.Connector })
        }
        throw "Rollback incomplete: $($failedRollbacks.Count) connectors failed"
    }

    # 5. Update deployment intent status
    Update-DeploymentIntentStatus -CorrelationId $CorrelationId -Status "RolledBack"

    Write-StructuredLog -Level "Info" -Message "Rollback completed successfully" -CorrelationId $rollbackCid
    return @{ Status = "Success"; RollbackCorrelationId = $rollbackCid; Results = $rollbackResults }
}
```

**Helper Functions**:
- `Get-DeploymentIntent`: Retrieve original deployment intent from control plane
- `Get-DeploymentConnectors`: Determine which connectors were used
- `Update-DeploymentIntentStatus`: Mark intent as RolledBack

**Pester Tests Required**:
- Rollback succeeds for single connector
- Rollback succeeds for multiple connectors
- Partial rollback failure throws error
- Rollback correlation ID has "rollback" prefix
- SLA: Rollback completes within 4 hours (mock test)

---

## Scope: Ring Management (scripts/operations/ring-management/)

### 1. Invoke-RingPromotion.ps1

```powershell
<#
.SYNOPSIS
    Promote deployment to next ring.
.DESCRIPTION
    Validates promotion gates, advances deployment to next ring if criteria met.
.PARAMETER CorrelationId
    Correlation ID of deployment.
.PARAMETER CurrentRing
    Current ring.
.EXAMPLE
    Invoke-RingPromotion -CorrelationId "deploy-123" -CurrentRing "Canary"
#>
function Invoke-RingPromotion {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department")]
        [string]$CurrentRing
    )

    # 1. Get deployment status for current ring
    $status = Get-DeploymentStatus -CorrelationId $CorrelationId

    # 2. Validate promotion gates
    $gatePassed = Test-PromotionGates -Ring $CurrentRing -SuccessRate $status.SuccessRate

    if (-not $gatePassed) {
        Write-StructuredLog -Level "Warning" -Message "Promotion gate not met" -CorrelationId $CorrelationId -Metadata @{
            CurrentRing = $CurrentRing
            SuccessRate = $status.SuccessRate
        }
        return @{ Status = "GateNotMet"; CurrentRing = $CurrentRing; SuccessRate = $status.SuccessRate }
    }

    # 3. Determine next ring
    $nextRing = Get-NextRing -CurrentRing $CurrentRing

    # 4. Submit deployment intent for next ring
    $nextIntent = $status.DeploymentIntent
    $nextIntent.Ring = $nextRing
    $nextIntent.CorrelationId = Get-CorrelationId -Prefix "promote"

    $result = Invoke-Deploy -DeploymentIntent $nextIntent

    Write-StructuredLog -Level "Info" -Message "Deployment promoted to next ring" -CorrelationId $CorrelationId -Metadata @{
        CurrentRing = $CurrentRing
        NextRing = $nextRing
        NewCorrelationId = $nextIntent.CorrelationId
    }

    return @{ Status = "Promoted"; NextRing = $nextRing; NewCorrelationId = $nextIntent.CorrelationId }
}
```

**Helper Functions**:
- `Get-NextRing`: Map current ring to next (Lab→Canary→Pilot→Department→Global)

**Pester Tests Required**:
- Promotion succeeds when gate met
- Promotion blocked when gate not met
- Correct next ring determined
- New correlation ID generated with "promote" prefix

---

## Scope: Drift Detection (scripts/operations/drift-detection/)

### 1. Invoke-DriftDetection.ps1

```powershell
<#
.SYNOPSIS
    Detect configuration drift from desired state.
.DESCRIPTION
    Compares deployed applications against approved deployment intents, identifies unauthorized changes.
.PARAMETER Ring
    Ring to check for drift.
.EXAMPLE
    Invoke-DriftDetection -Ring "Canary"
#>
function Invoke-DriftDetection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
        [string]$Ring
    )

    $driftCid = Get-CorrelationId -Prefix "drift"

    Write-StructuredLog -Level "Info" -Message "Starting drift detection" -CorrelationId $driftCid -Metadata @{ Ring = $Ring }

    # 1. Get approved deployment intents for ring
    $approvedIntents = Get-ApprovedDeploymentIntents -Ring $Ring

    # 2. Get actual deployed applications from execution planes
    $actualApps = Get-DeployedApplications -Ring $Ring

    # 3. Compare: Detect unauthorized apps, missing apps, version drift
    $driftResults = @{
        UnauthorizedApps = @()
        MissingApps = @()
        VersionDrift = @()
    }

    foreach ($actualApp in $actualApps) {
        $matchingIntent = $approvedIntents | Where-Object { $_.AppName -eq $actualApp.Name }
        if (-not $matchingIntent) {
            $driftResults.UnauthorizedApps += $actualApp
        } elseif ($matchingIntent.Version -ne $actualApp.Version) {
            $driftResults.VersionDrift += @{ App = $actualApp; ExpectedVersion = $matchingIntent.Version; ActualVersion = $actualApp.Version }
        }
    }

    foreach ($intent in $approvedIntents) {
        $matchingApp = $actualApps | Where-Object { $_.Name -eq $intent.AppName }
        if (-not $matchingApp) {
            $driftResults.MissingApps += $intent
        }
    }

    # 4. Log drift to SIEM
    if ($driftResults.UnauthorizedApps.Count -gt 0 -or $driftResults.MissingApps.Count -gt 0 -or $driftResults.VersionDrift.Count -gt 0) {
        Write-StructuredLog -Level "Warning" -Message "Configuration drift detected" -CorrelationId $driftCid -Metadata $driftResults
        Send-SIEMEvent -Event @{
            EventType = "DriftDetected"
            CorrelationId = $driftCid
            Ring = $Ring
            DriftResults = $driftResults
        }
    } else {
        Write-StructuredLog -Level "Info" -Message "No drift detected" -CorrelationId $driftCid
    }

    return $driftResults
}
```

**Helper Functions**:
- `Get-ApprovedDeploymentIntents`: Query control plane for approved intents
- `Get-DeployedApplications`: Query execution planes for actual apps

**Pester Tests Required**:
- Unauthorized app detected
- Missing app detected
- Version drift detected
- No drift returns empty results

---

## Scope: Telemetry (scripts/operations/telemetry/)

### 1. Collect-Telemetry.ps1

```powershell
<#
.SYNOPSIS
    Collect control plane health telemetry.
.DESCRIPTION
    Gathers metrics: API latency, event store size, evidence pack count, connector health.
.EXAMPLE
    Collect-Telemetry
#>
function Collect-Telemetry {
    [CmdletBinding()]
    param()

    $telemetryCid = Get-CorrelationId -Prefix "telemetry"

    # 1. Control Plane API health
    $apiHealth = Test-ControlPlaneHealth

    # 2. Event Store metrics
    $eventStoreMetrics = Get-EventStoreMetrics

    # 3. Evidence Store metrics
    $evidenceStoreMetrics = Get-EvidenceStoreMetrics

    # 4. Connector health
    $connectorHealth = @{}
    foreach ($connector in @("Intune", "Jamf", "SCCM", "Landscape", "Ansible")) {
        $connectorHealth[$connector] = Test-ConnectorHealth -Connector $connector
    }

    # 5. Aggregate telemetry
    $telemetry = @{
        Timestamp = (Get-Date -Format "o")
        CorrelationId = $telemetryCid
        ControlPlaneHealth = $apiHealth
        EventStoreMetrics = $eventStoreMetrics
        EvidenceStoreMetrics = $evidenceStoreMetrics
        ConnectorHealth = $connectorHealth
    }

    # 6. Send to SIEM and Application Insights
    Send-SIEMEvent -Event $telemetry
    Send-ApplicationInsights -Telemetry $telemetry

    Write-StructuredLog -Level "Info" -Message "Telemetry collected" -CorrelationId $telemetryCid
    return $telemetry
}
```

**Helper Functions**:
- `Test-ControlPlaneHealth`: GET /health endpoint, measure latency
- `Get-EventStoreMetrics`: Count events, average events/day
- `Get-EvidenceStoreMetrics`: Count evidence packs, total size
- `Test-ConnectorHealth`: Call Test-Connection for each connector
- `Send-ApplicationInsights`: POST telemetry to Azure Application Insights

**Pester Tests Required**:
- Telemetry collected successfully
- All connectors checked
- SIEM event sent

---

## Scope: HA/DR (scripts/infrastructure/ha-dr/)

### 1. Invoke-HADRFailover.ps1

```powershell
<#
.SYNOPSIS
    Execute HA/DR failover to secondary region.
.DESCRIPTION
    Fails over control plane to secondary Azure region, validates RTO ≤8h.
.PARAMETER Reason
    Failover reason.
.EXAMPLE
    Invoke-HADRFailover -Reason "Primary region outage"
#>
function Invoke-HADRFailover {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Reason
    )

    $failoverCid = Get-CorrelationId -Prefix "failover"

    Write-StructuredLog -Level "Critical" -Message "HA/DR failover initiated" -CorrelationId $failoverCid -Metadata @{ Reason = $Reason }

    # 1. Promote secondary database to primary
    $database = Get-AzSqlDatabase -ResourceGroupName "ControlPlane-RG" -ServerName "controlplane-secondary-sql"
    Set-AzSqlDatabaseFailoverGroup -ResourceGroupName "ControlPlane-RG" -ServerName "controlplane-secondary-sql" -FailoverGroupName "controlplane-fg" -AllowDataLoss

    # 2. Update DNS to point to secondary API Gateway
    # (Azure Traffic Manager handles this automatically)

    # 3. Validate secondary region health
    $healthCheck = Test-ControlPlaneHealth -Region "Secondary"
    if ($healthCheck.Status -ne "Healthy") {
        throw "Secondary region health check failed: $($healthCheck.Error)"
    }

    Write-StructuredLog -Level "Info" -Message "HA/DR failover completed" -CorrelationId $failoverCid
    Send-SIEMEvent -Event @{ EventType = "FailoverCompleted"; CorrelationId = $failoverCid; Reason = $Reason }

    return @{ Status = "Success"; NewRegion = "Secondary"; HealthCheck = $healthCheck }
}
```

**Pester Tests Required**:
- Failover promotes secondary database (mock)
- Health check validates secondary region
- SIEM event logged

---

## Scope: Secrets Rotation (scripts/infrastructure/secrets-management/)

### 1. Invoke-SecretsRotation.ps1

```powershell
<#
.SYNOPSIS
    Rotate secrets and service principal credentials.
.DESCRIPTION
    Rotates secrets per 90-day policy, updates Key Vault, validates connector health.
.EXAMPLE
    Invoke-SecretsRotation
#>
function Invoke-SecretsRotation {
    [CmdletBinding()]
    param()

    $rotationCid = Get-CorrelationId -Prefix "rotation"

    Write-StructuredLog -Level "Info" -Message "Starting secrets rotation" -CorrelationId $rotationCid

    # 1. Rotate service principal client secrets
    $servicePrincipals = @("Intune-SP", "Jamf-SP", "SCCM-SP", "Landscape-SP", "Ansible-SP")
    foreach ($sp in $servicePrincipals) {
        $spObject = Get-AzADServicePrincipal -DisplayName $sp
        $newSecret = New-AzADServicePrincipalCredential -ObjectId $spObject.Id -EndDate (Get-Date).AddDays(90)

        # Update Key Vault
        Set-AzKeyVaultSecret -VaultName "ControlPlaneVault" -Name "$sp-Secret" -SecretValue (ConvertTo-SecureString $newSecret.SecretText -AsPlainText -Force)

        Write-StructuredLog -Level "Info" -Message "Service principal secret rotated" -CorrelationId $rotationCid -Metadata @{ ServicePrincipal = $sp }
    }

    # 2. Rotate signing certificates (if expiring within 30 days)
    $certs = Get-AzKeyVaultCertificate -VaultName "ControlPlaneVault"
    foreach ($cert in $certs) {
        $daysUntilExpiry = ($cert.Expires - (Get-Date)).Days
        if ($daysUntilExpiry -le 30) {
            # Renew certificate
            Update-AzKeyVaultCertificate -VaultName "ControlPlaneVault" -Name $cert.Name
            Write-StructuredLog -Level "Warning" -Message "Certificate renewed" -CorrelationId $rotationCid -Metadata @{ Certificate = $cert.Name; DaysUntilExpiry = $daysUntilExpiry }
        }
    }

    # 3. Validate connector health post-rotation
    foreach ($connector in @("Intune", "Jamf", "SCCM", "Landscape", "Ansible")) {
        $health = Test-ConnectorHealth -Connector $connector
        if ($health.Status -ne "Healthy") {
            throw "Connector health check failed after rotation: $connector"
        }
    }

    Write-StructuredLog -Level "Info" -Message "Secrets rotation completed" -CorrelationId $rotationCid
    Send-SIEMEvent -Event @{ EventType = "SecretsRotated"; CorrelationId = $rotationCid }
}
```

**Pester Tests Required**:
- Service principal secrets rotated (mock)
- Certificates renewed if expiring soon
- Connector health validated post-rotation

---

## Scope: RBAC Setup (scripts/infrastructure/rbac/)

### 1. Initialize-RBACGroups.ps1

```powershell
<#
.SYNOPSIS
    Create Entra ID groups for RBAC model.
.DESCRIPTION
    Creates 7 RBAC groups, configures PIM/JIT for Publishers.
.EXAMPLE
    Initialize-RBACGroups
#>
function Initialize-RBACGroups {
    [CmdletBinding()]
    param()

    $rbacCid = Get-CorrelationId -Prefix "rbac-setup"

    Write-StructuredLog -Level "Info" -Message "Initializing RBAC groups" -CorrelationId $rbacCid

    # Define RBAC groups per docs/infrastructure/rbac-configuration.md
    $groups = @(
        @{ Name = "Platform-Admins"; Description = "Full control plane access" },
        @{ Name = "Packaging-Engineers"; Description = "Package creation and evidence generation" },
        @{ Name = "Publishers"; Description = "Publish to execution planes (PIM/JIT)" },
        @{ Name = "CAB-Approvers"; Description = "Approve high-risk deployments" },
        @{ Name = "Endpoint-Ops"; Description = "Read-only monitoring" },
        @{ Name = "Auditors"; Description = "Audit trail access" },
        @{ Name = "Break-Glass"; Description = "Emergency access (dual control)" }
    )

    foreach ($group in $groups) {
        $existingGroup = Get-AzADGroup -DisplayName $group.Name
        if ($existingGroup) {
            Write-Host "Group already exists: $($group.Name)"
            continue
        }

        $newGroup = New-AzADGroup -DisplayName $group.Name -MailNickname ($group.Name -replace '-', '') -Description $group.Description -SecurityEnabled
        Write-StructuredLog -Level "Info" -Message "RBAC group created" -CorrelationId $rbacCid -Metadata @{ GroupName = $group.Name; GroupId = $newGroup.Id }
    }

    # Configure PIM for Publishers group
    $publishersGroup = Get-AzADGroup -DisplayName "Publishers"
    # NOTE: PIM configuration requires Azure AD Premium P2 and Graph API calls
    # Assign eligible role with 4-hour activation, MFA required

    Write-StructuredLog -Level "Info" -Message "RBAC groups initialized" -CorrelationId $rbacCid
}
```

**Pester Tests Required**:
- All 7 groups created
- Duplicate run skips existing groups
- Publishers group configured for PIM (mock)

---

## Quality Checklist

### Per Script
- [ ] PSScriptAnalyzer ZERO errors/warnings
- [ ] Pester tests ≥90% coverage
- [ ] All operations idempotent
- [ ] All operations logged with correlation IDs
- [ ] SLAs documented and validated

### Integration Tests
- [ ] Incident response playbooks execute correctly
- [ ] Rollback completes within ≤4h (mock test)
- [ ] Ring promotion validates gates
- [ ] Drift detection identifies unauthorized changes
- [ ] HA/DR failover succeeds (test environment)
- [ ] Secrets rotation validated with connector health

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Rollback SLA exceeds 4 hours
2. HA/DR failover fails health check
3. Secrets rotation breaks connector authentication
4. RBAC groups grant unauthorized privileges
5. Break-glass activation without dual control

**Escalate to human if**:
- Primary region outage requires HA/DR failover
- Multiple P0 incidents in short timeframe
- Drift detection shows widespread unauthorized changes

---

## Delivery Checklist

- [ ] All 5 operations categories implemented (incident-response, rollback, ring-management, drift-detection, telemetry)
- [ ] All 4 infrastructure categories implemented (ha-dr, secrets-management, key-management, rbac)
- [ ] PSScriptAnalyzer: 0 errors, 0 warnings
- [ ] Pester tests: ≥90% coverage
- [ ] Runbooks documented (docs/runbooks/)
- [ ] SLAs validated

---

## Related Documentation

- [docs/runbooks/incident-response.md](../../runbooks/incident-response.md)
- [docs/runbooks/rollback-execution.md](../../runbooks/rollback-execution.md)
- [docs/architecture/ring-model.md](../../architecture/ring-model.md)
- [docs/infrastructure/ha-dr-requirements.md](../../infrastructure/ha-dr-requirements.md)
- [docs/infrastructure/secrets-management.md](../../infrastructure/secrets-management.md)
- [docs/infrastructure/rbac-configuration.md](../../infrastructure/rbac-configuration.md)
- [docs/infrastructure/siem-integration.md](../../infrastructure/siem-integration.md)
- [.agents/rules/06-ring-rollout-rules.md](../../.agents/rules/06-ring-rollout-rules.md)
- [.agents/rules/07-rollback-rules.md](../../.agents/rules/07-rollback-rules.md)

---

**End of Phase 5 Prompt**
