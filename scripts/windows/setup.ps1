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

function Test-PythonInvocation {
    param([string[]]$Command)
    $exe = $Command[0]
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        return $false
    }
    $args = @()
    if ($Command.Length -gt 1) {
        $args = $Command[1..($Command.Length - 1)]
    }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $exe @args -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Find-Python {
    $candidates = @(
        ,@("py", "-3")
        ,@("python")
        ,@("python3")
    )
    foreach ($cmd in $candidates) {
        if (Test-PythonInvocation -Command $cmd) {
            return $cmd
        }
    }
    Write-Host "Python 3.10+ not found on PATH." -ForegroundColor Yellow
    Write-Host "Install: https://www.python.org/downloads/ (mark 'Add python.exe to PATH')"
    Write-Host "Or: winget install Python.Python.3.12"
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
