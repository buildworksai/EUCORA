# Common Utility Functions

Reusable correlation ID, retry, idempotency, and configuration helpers.

## Functions
| Function | Purpose | Related Docs |
|---|---|---|
| `Get-CorrelationId` | Generate deterministic or prefixed correlation IDs | docs/architecture/control-plane-design.md |
| `Test-CorrelationId` | Validate correlation ID formats | .agents/rules/08-connector-rules.md |
| `Invoke-RetryWithBackoff` | Retry transient failures via exponential backoff | .agents/rules/08-connector-rules.md |
| `Test-IdempotencyKey` | Ensure correlation IDs are not reused | docs/architecture/control-plane-design.md |
| `Get-ConfigValue` | Retrieve configuration values with caching | documentation-rules.md |

## Testing
Run the following Pester test suite:

```powershell
Invoke-Pester -Path ./Get-CorrelationId.Tests.ps1 -Output Detailed
Invoke-Pester -Path ./Invoke-RetryWithBackoff.Tests.ps1 -Output Detailed
Invoke-Pester -Path ./Test-IdempotencyKey.Tests.ps1 -Output Detailed
Invoke-Pester -Path ./Get-ConfigValue.Tests.ps1 -Output Detailed
```

## Usage Example
```powershell
$correlationId = Get-CorrelationId -Type deployment -Seed 1234
if (Test-CorrelationId -CorrelationId $correlationId -Type deployment) {
    Write-Host "Correlation ID valid: $correlationId"
}
Invoke-RetryWithBackoff -ScriptBlock { 'ok' } -CorrelationId $correlationId
$exists = Test-IdempotencyKey -CorrelationId $correlationId -EventStoreConnectionString './config/event-store.json'
$value = Get-ConfigValue -Key 'control_plane.api_url' -ConfigPath './config/settings.json'
```
