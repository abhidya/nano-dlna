[CmdletBinding()]
param(
    [int]$Port = 8010,
    [string]$HostAddress = "0.0.0.0",
    [string]$PythonPath = "",
    [switch]$InstallDeps,
    [switch]$BuildFrontend,
    [switch]$PrepareOnly
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "web\backend"
$Frontend = Join-Path $Root "web\frontend"
$Logs = Join-Path $Root "logs"
$LogFile = Join-Path $Logs "nano-dlna-service.log"

New-Item -ItemType Directory -Force -Path $Logs | Out-Null

if (-not $PythonPath) {
    $RepoPython = Join-Path $Root ".venv\python.exe"
    if (Test-Path $RepoPython) {
        $PythonPath = $RepoPython
    } else {
        $PythonPath = "python"
    }
}

$env:PYTHONPATH = "$Root;$Backend"
$env:PYTHONUNBUFFERED = "1"
$env:NANO_DLNA_SERVER_BASE_URL = "http://localhost:$Port"

function Write-ServiceLog {
    param([string]$Message)
    $Line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $Line
}

Write-ServiceLog "starting prep: root=$Root port=$Port"

if ($InstallDeps) {
    Write-ServiceLog "installing backend dependencies"
    & $PythonPath -m pip install -r (Join-Path $Backend "requirements.txt") *>> $LogFile
}

$FrontendBuild = Join-Path $Frontend "build\index.html"
if ($BuildFrontend -or -not (Test-Path $FrontendBuild)) {
    Write-ServiceLog "building frontend"
    Push-Location $Frontend
    try {
        if (-not (Test-Path "node_modules")) {
            npm install *>> $LogFile
        }
        npm run build *>> $LogFile
    } finally {
        Pop-Location
    }
}

if ($PrepareOnly) {
    Write-ServiceLog "prep complete"
    exit 0
}

Write-ServiceLog "starting backend on $HostAddress`:$Port"
Push-Location $Backend
try {
    $RunPy = Join-Path $Backend "run.py"
    $Command = "`"$PythonPath`" `"$RunPy`" --host `"$HostAddress`" --port $Port >> `"$LogFile`" 2>&1"
    & cmd.exe /c $Command
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
