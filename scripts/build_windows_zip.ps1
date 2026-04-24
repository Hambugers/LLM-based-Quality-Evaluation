Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PythonVersion = "3.12.10"
$PackageName = "LLM-Evaluation-Demo"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BuildRoot = Join-Path $RepoRoot "artifacts\windows"
$StageRoot = Join-Path $BuildRoot $PackageName
$ZipPath = Join-Path $BuildRoot "$PackageName.zip"
$PythonZipUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Message"
    & $Action
}

function Copy-CleanDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
    Copy-Item -Recurse -Force $Source $Destination
}

function Ensure-FrontendBuild {
    Push-Location (Join-Path $RepoRoot "frontend")
    try {
        if (Get-Command bun -ErrorAction SilentlyContinue) {
            bun install --no-save
            bun run build
            return
        }

        if (Get-Command npm -ErrorAction SilentlyContinue) {
            npm install
            npm run build
            return
        }

        throw "Neither bun nor npm was found. Install one build-time frontend runtime before packaging."
    }
    finally {
        Pop-Location
    }
}

function Install-EmbeddedPython {
    $RuntimeRoot = Join-Path $StageRoot "runtime\python"
    $DownloadDir = Join-Path $BuildRoot "downloads"
    $PythonZip = Join-Path $DownloadDir "python-$PythonVersion-embed-amd64.zip"
    $GetPip = Join-Path $DownloadDir "get-pip.py"

    New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null

    if (-not (Test-Path $PythonZip)) {
        Invoke-WebRequest -Uri $PythonZipUrl -OutFile $PythonZip
    }
    Expand-Archive -Path $PythonZip -DestinationPath $RuntimeRoot -Force

    $PthFile = Get-ChildItem -Path $RuntimeRoot -Filter "python*._pth" | Select-Object -First 1
    if (-not $PthFile) {
        throw "Embedded Python ._pth file was not found."
    }

    $PthLines = Get-Content $PthFile.FullName
    $PthLines = $PthLines | ForEach-Object {
        if ($_ -eq "#import site") { "import site" } else { $_ }
    }
    if ($PthLines -notcontains "Lib\site-packages") {
        $PthLines = @($PthLines[0]) + @("Lib\site-packages") + @($PthLines[1..($PthLines.Count - 1)])
    }
    Set-Content -Path $PthFile.FullName -Value $PthLines -Encoding ASCII

    if (-not (Test-Path $GetPip)) {
        Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPip
    }

    $PythonExe = Join-Path $RuntimeRoot "python.exe"
    & $PythonExe $GetPip --no-warn-script-location
    & $PythonExe -m pip install --upgrade --no-warn-script-location pip
    & $PythonExe -m pip install --no-warn-script-location -r (Join-Path $RepoRoot "requirements.txt")
}

function Write-StartScript {
    $StartScript = @'
@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "%ROOT%logs" mkdir "%ROOT%logs"
if not exist "%ROOT%data\uploads" mkdir "%ROOT%data\uploads"

set "PYTHON_EXE=%ROOT%runtime\python\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Missing runtime Python: %PYTHON_EXE%
  pause
  exit /b 1
)

echo Starting LLM Evaluation Demo...
echo Logs: %ROOT%logs\server.log

powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:LLM_EVAL_PACKAGE_ROOT=$env:ROOT; & (Join-Path $env:ROOT 'runtime\python\python.exe') (Join-Path $env:ROOT 'app\backend\app\package_server.py') 2>&1 | Tee-Object -FilePath (Join-Path $env:ROOT 'logs\server.log') -Append"

echo.
echo Application stopped.
pause
'@

    Set-Content -Path (Join-Path $StageRoot "Start.bat") -Value $StartScript -Encoding ASCII
}

Invoke-Step "Prepare clean staging directory" {
    if (Test-Path $StageRoot) {
        Remove-Item -Recurse -Force $StageRoot
    }
    New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $StageRoot "app\backend") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $StageRoot "data\uploads") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $StageRoot "logs") | Out-Null
}

Invoke-Step "Build frontend static assets" {
    Ensure-FrontendBuild
}

Invoke-Step "Copy application files" {
    Copy-CleanDirectory -Source (Join-Path $RepoRoot "backend\app") -Destination (Join-Path $StageRoot "app\backend\app")
    Copy-CleanDirectory -Source (Join-Path $RepoRoot "frontend\dist") -Destination (Join-Path $StageRoot "app\frontend_dist")
    Copy-CleanDirectory -Source (Join-Path $RepoRoot "images") -Destination (Join-Path $StageRoot "app\images")
    Copy-Item -Force (Join-Path $RepoRoot "model.txt") (Join-Path $StageRoot "app\model.txt")
    Copy-Item -Force (Join-Path $RepoRoot "requirements.txt") (Join-Path $StageRoot "app\backend\requirements.txt")
}

Invoke-Step "Install embedded Python runtime and backend dependencies" {
    Install-EmbeddedPython
}

Invoke-Step "Write Start.bat" {
    Write-StartScript
}

Invoke-Step "Create ZIP package" {
    if (Test-Path $ZipPath) {
        Remove-Item -Force $ZipPath
    }
    Compress-Archive -Path $StageRoot -DestinationPath $ZipPath -Force
}

Write-Host ""
Write-Host "Package created: $ZipPath"
