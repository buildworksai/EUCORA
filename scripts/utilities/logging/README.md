# Logging Utility Functions

Structured logging and audit exports for the Control Plane.

## Functions
| Function | Purpose | Related Docs |
|---|---|---|
| `Write-StructuredLog` | Emit JSON logs (console + file) | docs/infrastructure/siem-integration.md |
| `Send-SIEMEvent` | Forward logs to Log Analytics via retry | docs/infrastructure/siem-integration.md |
| `Export-AuditTrail` | Export events per correlation ID | docs/architecture/control-plane-design.md |

## Testing
```powershell
Invoke-Pester -Path .\Write-StructuredLog.Tests.ps1
Invoke-Pester -Path .\Send-SIEMEvent.Tests.ps1
Invoke-Pester -Path .\Export-AuditTrail.Tests.ps1
```

## Usage
```powershell
$entry = Write-StructuredLog -Message 'Deployment ready' -Level Info -CorrelationId 'dp-1' -Component 'orchestrator'
Send-SIEMEvent -Event $entry -WorkspaceId $(Get-ConfigValue -Key 'azure.log_analytics_workspace_id') -SharedKey $(Get-ConfigValue -Key 'azure.log_analytics_shared_key')
Export-AuditTrail -CorrelationId 'dp-1' -Format JSON -OutputPath './logs/audit-dp-1.json'
```
