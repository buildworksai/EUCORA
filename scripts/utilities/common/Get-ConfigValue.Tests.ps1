# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Pester tests for Get-ConfigValue.
.DESCRIPTION
Verifies config retrieval, nested keys, environment fallback, caching, defaults, and required errors.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: documentation-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Get-ConfigValue' {
    BeforeAll {
        . "$PSScriptRoot/Get-ConfigValue.ps1"
        $script:ConfigDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config\tests\config'))
        New-Item -ItemType Directory -Path $script:ConfigDir -Force | Out-Null
        $script:TestConfigPath = Join-Path $script:ConfigDir ("settings-$([guid]::NewGuid()).json")
        $script:SampleConfig = @{
            control_plane = @{ api_url = 'https://test-api.corp/v1'; timeout_seconds = 45 }
            retry = @{ max_attempts = 7 }
        } | ConvertTo-Json -Depth 5
        Set-Content -Path $script:TestConfigPath -Value $script:SampleConfig
    }
    BeforeEach {
        Clear-ConfigCache
    }
    AfterAll {
        Remove-Item -Path $script:TestConfigPath -Force
    }
    It 'Reads existing key from JSON' {
        $value = Get-ConfigValue -Key 'control_plane.api_url' -ConfigPath $script:TestConfigPath
        $value | Should -Be 'https://test-api.corp/v1'
    }
    It 'Reads nested key' {
        $value = Get-ConfigValue -Key 'retry.max_attempts' -ConfigPath $script:TestConfigPath
        $value | Should -Be 7
    }
    It 'Falls back to environment variable when key missing' {
        $env:CONTROL_PLANE_ALT_URL = 'https://env-api.corp/v2'
        $value = Get-ConfigValue -Key 'control_plane.alt_url' -ConfigPath $script:TestConfigPath
        $value | Should -Be 'https://env-api.corp/v2'
        Remove-Item Env:CONTROL_PLANE_ALT_URL
    }
    It 'Returns default value when missing' {
        $value = Get-ConfigValue -Key 'missing.key' -ConfigPath $script:TestConfigPath -DefaultValue 42
        $value | Should -Be 42
    }
    It '-Required throws when missing' {
        { Get-ConfigValue -Key 'missing.key' -ConfigPath $script:TestConfigPath -Required } | Should -Throw
    }
    It 'Caches config file load' {
        Mock -CommandName Get-Content -MockWith { return $script:SampleConfig } -Verifiable
        Get-ConfigValue -Key 'control_plane.api_url' -ConfigPath $script:TestConfigPath | Out-Null
        Get-ConfigValue -Key 'control_plane.timeout_seconds' -ConfigPath $script:TestConfigPath | Out-Null
        Assert-MockCalled Get-Content -Times 1
    }
}
