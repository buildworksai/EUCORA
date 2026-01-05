# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Format-Output' {
    BeforeAll {
        $path = Join-Path $PSScriptRoot 'Format-Output.ps1'
        . (Resolve-Path $path).Path
    }
    It 'emits JSON content' {
        $data = @{ status = 'ok'; value = 1 }
        $json = Format-Output -Data $data -Format 'JSON'
        $json | Should -Match '"status":\s*"ok"'
    }
    It 'emits CSV headers' {
        $data = @(@{ status = 'ok' }, @{ status = 'fail' })
        $csv = Format-Output -Data $data -Format 'CSV'
        ($csv -split "`n")[0] | Should -Match 'status'
    }
}
