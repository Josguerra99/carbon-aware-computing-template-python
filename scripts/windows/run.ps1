#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $Root

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

Write-Host ""
Write-Host "=== Red del taller (Windows) ===" -ForegroundColor Cyan
Write-Host "1) Wi-Fi en perfil PRIVADA."
Write-Host "2) Si Windows pregunta por Python: RED PRIVADA y PERMITIR (no bloquear en privada)." -ForegroundColor Yellow
Write-Host ""

$lanMarker = Join-Path $Root ".local\lan-defender-ok"
if (-not (Test-Path $lanMarker)) {
    New-Item -ItemType Directory -Path (Split-Path $lanMarker) -Force | Out-Null
    & (Join-Path $PSScriptRoot "prompt-lan-firewall.ps1") `
        -Exe $venvPy `
        -ProcessArguments @("-m", "uvicorn", "src.server.index:app", "--host", "0.0.0.0", "--port", "$port") `
        -WorkingDirectory $Root -Port ([int]$port)
    Set-Content -Path $lanMarker -Value (Get-Date -Format "o") -Encoding utf8
}

& (Join-Path $PSScriptRoot "ensure-lan-access.ps1") -ProgramPath $venvPy -ServerPort ([int]$port)

Write-Host "Starting forecast server (uvicorn) on port $port..."
& $venvPy -m uvicorn src.server.index:app --host 0.0.0.0 --port $port
