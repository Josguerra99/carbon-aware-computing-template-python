#Requires -Version 5.1
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $Root

$fixPermissions = $false
foreach ($a in @($RemainingArgs)) {
    if ($a -eq "--fix-permissions" -or $a -eq "-FixPermissions") {
        $fixPermissions = $true
    }
}

& (Join-Path $PSScriptRoot "../ensure-env.ps1")

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host ".venv missing - running setup..."
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "setup.ps1")
}

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $eq = $line.IndexOf("=")
        if ($eq -gt 0) {
            $key = $line.Substring(0, $eq).Trim()
            $val = $line.Substring($eq + 1).Trim()
            Set-Item -Path "Env:$key" -Value $val
        }
    }
}

$port = if ($env:PORT) { $env:PORT } else { "3916" }

if ($fixPermissions) {
    & (Join-Path $PSScriptRoot "ensure-lan-access.ps1") -ProgramPath $venvPy -ServerPort ([int]$port) -Force
}

Write-Host "Starting forecast server (uvicorn --reload) on port $port..."
& $venvPy -m uvicorn src.server.index:app --host 0.0.0.0 --port $port --reload
