#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $Root

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw ".venv not found. Run scripts\windows\setup.cmd first."
}

$port = if ($env:PORT) { [int]$env:PORT } else { 3916 }

& (Join-Path $PSScriptRoot "ensure-lan-access.ps1") -ProgramPath $venvPy -ServerPort $port -Force
