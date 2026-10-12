<#
.SYNOPSIS
    Cross-platform local development entry point for asciidoctrine.

.DESCRIPTION
    AGENTS.md documents the development workflow in terms of POSIX shell
    (venv/bin/python3, ./run-tck.sh), which leaves Windows contributors without
    an equivalent happy path. This script provides one, resolving the venv
    interpreter correctly on both PowerShell (Windows) and POSIX shells.

    Each task mirrors a tier documented in AGENTS.md.

.PARAMETER Task
    verify   - Tier 2: core tests + ruff + mypy (the pre-commit check)
    test     - Tier 1: core tests only, quiet
    doctest  - Tier 3: real-world doctest corpus (RUN_DOCTESTS=1)
    tck      - Tier 3: upstream Node.js TCK conformance
    lint     - ruff format --check + ruff check + mypy
    setup    - create the venv and install .[test]
    all      - verify + doctest

.EXAMPLE
    .\bin\dev.ps1 setup
    .\bin\dev.ps1 verify
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('verify', 'test', 'doctest', 'tck', 'lint', 'setup', 'all')]
    [string]$Task = 'verify'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Always operate from the repository root regardless of the caller's cwd.
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    # Resolve the venv interpreter for the current platform.
    $IsWindowsEnv = $null -ne $env:OS -and $env:OS -match 'Windows'
    $Candidates = if ($IsWindowsEnv) {
        @('venv\Scripts\python.exe', 'venv\bin\python3')
    } else {
        @('venv/bin/python3', 'venv\Scripts\python.exe')
    }

    $Python = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $Python) {
        if ($Task -ne 'setup') {
            throw "No virtual environment found. Run '.\bin\dev.ps1 setup' first."
        }
    }

    function Invoke-Tool {
        param([string[]]$Arguments, [hashtable]$Environment = @{})
        $prev = @{}
        foreach ($k in $Environment.Keys) {
            $prev[$k] = [Environment]::GetEnvironmentVariable($k)
            Set-Item -Path "Env:$k" -Value $Environment[$k]
        }
        try {
            & $Python @Arguments
            if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Python $($Arguments -join ' ')" }
        } finally {
            foreach ($k in $Environment.Keys) {
                Set-Item -Path "Env:$k" -Value $prev[$k]
            }
        }
    }

    switch ($Task) {
        'setup' {
            if (-not $Python) {
                Write-Host 'Creating virtual environment...' -ForegroundColor Cyan
                python -m venv venv
                $Python = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
            }
            Write-Host 'Installing .[test] (editable)...' -ForegroundColor Cyan
            & $Python -m pip install --disable-pip-version-check --upgrade pip
            & $Python -m pip install --disable-pip-version-check -e '.[test]'
        }
        'test' {
            Invoke-Tool @('-m', 'pytest', '-k', 'not functional', '-q', '--tb=short')
        }
        'lint' {
            Invoke-Tool @('-m', 'ruff', 'format', '--check', '.')
            Invoke-Tool @('-m', 'ruff', 'check', '.')
            Invoke-Tool @('-m', 'mypy', 'src/asciidoctrine')
        }
        'doctest' {
            Invoke-Tool @('-m', 'pytest', 'tests/test_doctest_parsing.py', '-q', '--tb=short') -Environment @{ RUN_DOCTESTS = '1' }
        }
        'tck' {
            # The upstream TCK runner is a bash script; prefer bash when present.
            $bash = Get-Command bash -ErrorAction SilentlyContinue
            if ($bash) {
                & bash ./run-tck.sh
                if ($LASTEXITCODE -ne 0) { throw "TCK failed ($LASTEXITCODE)" }
            } else {
                throw "TCK requires bash (Git for Windows). Run: npm ci && ./run-tck.sh from Git Bash."
            }
        }
        'verify' {
            Invoke-Tool @('-m', 'pytest', '-k', 'not functional', '-q', '--tb=short')
            Invoke-Tool @('-m', 'ruff', 'format', '--check', '.')
            Invoke-Tool @('-m', 'ruff', 'check', '.')
            Invoke-Tool @('-m', 'mypy', 'src/asciidoctrine')
        }
        'all' {
            Invoke-Tool @('-m', 'pytest', '-k', 'not functional', '-q', '--tb=short')
            Invoke-Tool @('-m', 'ruff', 'format', '--check', '.')
            Invoke-Tool @('-m', 'ruff', 'check', '.')
            Invoke-Tool @('-m', 'mypy', 'src/asciidoctrine')
            Invoke-Tool @('-m', 'pytest', 'tests/test_doctest_parsing.py', '-q', '--tb=short') -Environment @{ RUN_DOCTESTS = '1' }
        }
    }

    Write-Host "Task '$Task' completed successfully." -ForegroundColor Green
}
finally {
    Pop-Location
}
