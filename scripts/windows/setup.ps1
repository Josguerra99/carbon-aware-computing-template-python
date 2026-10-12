#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $Root

Write-Host "=== Carbon-aware template (Python) - Windows setup ===" -ForegroundColor Cyan
Write-Host "Installs: Python venv, pip packages from requirements.txt."
Write-Host "Before run: set MAIN_SERVER_URL in .env to the URL from your facilitator."
Write-Host "You need: Python 3.11+ (python.org or winget)."
Write-Host ""

& (Join-Path $PSScriptRoot "../ensure-env.ps1")

function Find-Python {
    $candidates = @("py -3", "python", "python3")
    foreach ($name in $candidates) {
        $parts = $name -split " "
        if ($parts.Count -eq 2) {
            & py -3 -c "import sys; print(sys.version)" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
        } else {
            if (Get-Command $name -ErrorAction SilentlyContinue) {
                & $name -c "import sys; print(sys.version)" 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return @($name) }
            }
        }
    }
    Write-Host "Python not found. Install from https://www.python.org/downloads/ or: winget install Python.Python.3.12" -ForegroundColor Yellow
    throw "Python 3 is required."
}

$py = Find-Python
Write-Host "Using: $($py -join ' ')"

& @py -m venv .venv
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete. Run: powershell -ExecutionPolicy Bypass -File scripts/windows/run.ps1" -ForegroundColor Green
