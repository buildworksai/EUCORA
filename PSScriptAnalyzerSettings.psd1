@{
    # Exclude specific rules that have false positives
    ExcludeRules = @(
        # False positive: .PARAMETER in comment-based help is flagged as alias
        'PSAvoidUsingCmdletAliases'
    )
    
    # Include default rules except the ones we exclude
    IncludeDefaultRules = $true
    
    # Severity levels to check
    Severity = @('Error', 'Warning')
    
    # Custom rule configurations
    Rules = @{
        PSAvoidUsingCmdletAliases = @{
            # Allow certain patterns in comment-based help
            Exclude = @('*.ps1')
        }
    }
}

