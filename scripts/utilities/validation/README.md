# Validation Utility Functions

Functions to validate evidence packs, scopes, CAB approvals, and promotion gates.

## Functions
| Function | Purpose | Related Docs |
|---|---|---|
| `Test-EvidencePackCompleteness` | Validate evidence pack fields and schema | .agents/rules/10-evidence-pack-rules.md |
| `Test-ScopeValidity` | Ensure scope subset constraints | .agents/rules/09-rbac-enforcement-rules.md |
| `Test-CABApproval` | Verify CAB approval status and expiry | .agents/rules/05-cab-approval-rules.md |
| `Test-PromotionGates` | Enforce ring promotion thresholds | .agents/rules/06-ring-rollout-rules.md |

## Testing
```powershell
Invoke-Pester -Path .\Test-EvidencePackCompleteness.Tests.ps1
Invoke-Pester -Path .\Test-ScopeValidity.Tests.ps1
Invoke-Pester -Path .\Test-CABApproval.Tests.ps1
Invoke-Pester -Path .\Test-PromotionGates.Tests.ps1
```

## Usage Example
```powershell
$packResult = Test-EvidencePackCompleteness -EvidencePack $evidencePack
if (-not $packResult.IsValid) { throw $packResult.Errors }
$scopeResult = Test-ScopeValidity -TargetScope $target -PublisherScope $publisher -AppScope $app -CABApprovalId $cabId
if (-not $scopeResult.IsValid) { throw $scopeResult.Errors }
$approval = Test-CABApproval -ApprovalId $cabId -EventStoreConnectionString $path
$gateResult = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent
```
