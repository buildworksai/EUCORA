# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Format data as Table, JSON, or CSV for dapctl commands.
.DESCRIPTION
    Accepts arbitrary objects and emits them in the requested format. Table uses Format-Table,
    JSON uses ConvertTo-Json, CSV uses ConvertTo-Csv without type information.
.PARAMETER Data
    Object to format.
.PARAMETER Format
    Desired output format: Table, JSON, or CSV.
.EXAMPLE
    Format-Output -Data $response -Format 'JSON'
.NOTES
Version: 1.0
Author: Platform Engineering
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Format-Output {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Data,

        [Parameter(Mandatory = $false)]
        [ValidateSet('Table','JSON','CSV')]
        [string]$Format = 'Table'
    )

    switch ($Format) {
        'Table' { $Data | Format-Table -AutoSize }
        'JSON' { $Data | ConvertTo-Json -Depth 10 }
        'CSV' { $Data | ConvertTo-Csv -NoTypeInformation }
    }
}
