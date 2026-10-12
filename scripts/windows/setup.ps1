#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "../..")
Set-Location $Root

Write-Host "=== Carbon-aware template (Python) - Windows setup ===" -ForegroundColor Cyan
Write-Host "Installs: Python venv, pip packages from requirements.txt."
Write-Host "Before run: set MAIN_SERVER_URL in .env to the URL from your facilitator."
Write-Host ""

& (Join-Path $PSScriptRoot "../ensure-env.ps1")

function Test-PythonCommand {
    param([string[]]$Command)
    $exe = $Command[0]
    $isPath = $exe -match '[\\/]' -or $exe.EndsWith('.exe')
    if ($isPath) {
        if (-not (Test-Path -LiteralPath $exe)) {
            return $false
        }
    } elseif (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
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

function Get-WindowsPythonInstallCandidates {
    $paths = [ordered]@{}
    function Add-Candidate([string]$Path) {
        if (-not $Path) { return }
        try {
            $full = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
            if (-not $paths.Contains($full)) {
                $paths[$full] = $true
            }
        } catch {
        }
    }

    foreach ($pattern in @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe"
        "$env:ProgramFiles\Python*\python.exe"
        "${env:ProgramFiles(x86)}\Python*\python.exe"
    )) {
        foreach ($match in (Get-Item -Path $pattern -ErrorAction SilentlyContinue)) {
            Add-Candidate $match.FullName
        }
    }

    foreach ($hive in @("HKCU:\Software\Python\PythonCore", "HKLM:\Software\Python\PythonCore")) {
        if (-not (Test-Path $hive)) { continue }
        Get-ChildItem $hive -ErrorAction SilentlyContinue | ForEach-Object {
            $install = (Get-ItemProperty -Path "$($_.PSPath)\InstallPath" -ErrorAction SilentlyContinue)."(default)"
            if ($install) {
                Add-Candidate (Join-Path $install "python.exe")
            }
        }
    }

    return @($paths.Keys)
}

function Find-Python {
    $candidates = @(
        ,@("py", "-3")
        ,@("python")
        ,@("python3")
    )
    foreach ($cmd in $candidates) {
        if (Test-PythonCommand -Command $cmd) {
            return $cmd
        }
    }
    foreach ($exe in Get-WindowsPythonInstallCandidates) {
        $cmd = ,@($exe)
        if (Test-PythonCommand -Command $cmd) {
            return $cmd
        }
    }
    return $null
}

function Install-PythonWithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }
    Write-Host "Python not found. Installing Python 3.12 with winget (may take a few minutes)..." -ForegroundColor Yellow
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    } finally {
        $ErrorActionPreference = $prev
    }
    return $LASTEXITCODE -eq 0
}

$py = Find-Python
if (-not $py) {
    if (Install-PythonWithWinget) {
        $py = Find-Python
    }
}

if (-not $py) {
    Write-Host "Python 3.10+ not found." -ForegroundColor Yellow
    Write-Host "Install from https://www.python.org/downloads/ and enable 'Add python.exe to PATH', then open a new terminal."
    Write-Host "Or run: winget install Python.Python.3.12"
    Write-Host "Tip: use scripts\windows\setup.cmd to avoid PowerShell profile errors (Windows PowerShell 5.1)."
    throw "Python 3 is required."
}

Write-Host "Using: $($py -join ' ')"

& @py -m venv .venv
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "Failed to create .venv at $venvPy"
}
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

$firewallCmd = Join-Path $PSScriptRoot "open-lan-firewall.cmd"
& cmd.exe /c "`"$firewallCmd`" 3916"

Write-Host ""
Write-Host "Setup complete. Run: scripts\windows\run.cmd" -ForegroundColor Green
