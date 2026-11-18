#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Verify,
    [switch]$Launch
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venv = Join-Path $PSScriptRoot '.venv'
$projectPython = Join-Path $venv 'Scripts\python.exe'

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)

    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program exited with code $LASTEXITCODE."
    }
}

if (-not (Test-Path -LiteralPath $projectPython -PathType Leaf)) {
    $pythonCheck = 'import sys, tkinter, venv; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
    $python = $null
    foreach ($candidate in @('py', 'python', 'python3')) {
        $command = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($command) {
            $flags = @(if ($candidate -eq 'py') { '-3' })
            & $command.Source @flags -B -c $pythonCheck
            if ($LASTEXITCODE -eq 0) {
                $python = $command.Source
                break
            }
        }
    }
    if (-not $python) {
        throw 'Setup requires Windows Python 3.10 or newer with Tkinter and venv. Check the existing Python installation.'
    }

    Write-Host "Creating virtual environment in $venv"
    Invoke-Checked $python ($flags + @('-m', 'venv', $venv))
}

Write-Host 'Installing project dependencies'
Invoke-Checked $projectPython @('-m', 'pip', 'install', '-r', (Join-Path $PSScriptRoot 'requirements-demo.txt'))
Invoke-Checked $projectPython @('-B', '-c', 'import tkinter, yaml, pytest, PIL')

if ($Verify) {
    Push-Location $repo
    try {
        Invoke-Checked $projectPython @('-B', '-m', 'pytest', '-p', 'no:cacheprovider', 'prototype1/tests', '-q')
        foreach ($suite in @('prototype2/tests', 'prototype2/keyboard_cli/tests', 'prototype2/workflow/tests')) {
            Invoke-Checked $projectPython @('-B', '-m', 'unittest', 'discover', '-s', $suite, '-v')
        }

        # Use Git for Windows Bash rather than the Windows Subsystem for Linux shim.
        $gitExecPath = & git --exec-path
        if ($LASTEXITCODE -ne 0) { throw 'Could not find the Git for Windows install.' }
        $gitBash = Join-Path $gitExecPath '..\..\..\bin\bash.exe'
        if (-not (Test-Path -LiteralPath $gitBash -PathType Leaf)) {
            throw 'Git for Windows Bash is needed to verify the shell demos.'
        }
        $gitBash = (Resolve-Path -LiteralPath $gitBash).Path
        $previousPython = $env:PYTHON
        try {
            $env:PYTHON = $projectPython.Replace('\', '/')
            $cases = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'tests\demo') -Filter '*.sh' |
                Sort-Object Name
            if ($cases.Count -ne 10) { throw 'Expected ten Bash demo scripts.' }
            foreach ($case in $cases) {
                $casePath = $case.FullName.Replace('\', '/')
                Invoke-Checked $gitBash @('--login', $casePath)
            }
        }
        finally {
            $env:PYTHON = $previousPython
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host 'Setup complete.'
if ($Launch) {
    Invoke-Checked $projectPython @('-B', (Join-Path $PSScriptRoot 'run.py'))
} else {
    Write-Host 'Launch from an interactive Windows terminal with the following command.'
    Write-Host ('& "{0}" -B "{1}"' -f $projectPython, (Join-Path $PSScriptRoot 'run.py'))
}
