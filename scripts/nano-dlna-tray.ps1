<#
.SYNOPSIS
    System-tray host for the nano-dlna backend (no console window).

.DESCRIPTION
    Starts the FastAPI backend as a hidden child process and shows a tray icon
    whose menu links to the dashboard and the logs. Replaces the visible
    PowerShell/cmd console that the plain service runner leaves on screen.

    Launch it hidden via nano-dlna-tray.vbs so nothing appears in the taskbar.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File .\scripts\nano-dlna-tray.ps1 -Port 8010
#>
[CmdletBinding()]
param(
    [int]$Port = 8010,
    [string]$HostAddress = "0.0.0.0",
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $Root "web\backend"
$LogsDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$OutLog = Join-Path $LogsDir "nano-dlna-service.out.log"
$ErrLog = Join-Path $LogsDir "nano-dlna-service.err.log"
$BackendLog = Join-Path $BackendDir "dashboard_run.log"
$DashboardUrl = "http://localhost:$Port/app"

if (-not $PythonPath) {
    $venvPython = Join-Path $Root ".venv\python.exe"
    if (Test-Path $venvPython) { $PythonPath = $venvPython } else { $PythonPath = "python" }
}

$env:PYTHONPATH = "$Root;$BackendDir"
$env:PYTHONUNBUFFERED = "1"
$env:NANO_DLNA_SERVER_BASE_URL = "http://localhost:$Port"

$script:BackendProc = $null

function Start-Backend {
    if ($script:BackendProc -and -not $script:BackendProc.HasExited) { return }
    $runPy = Join-Path $BackendDir "run.py"
    $procArgs = @("`"$runPy`"", "--host", $HostAddress, "--port", "$Port")
    $script:BackendProc = Start-Process -FilePath $PythonPath -ArgumentList $procArgs `
        -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog
}

function Stop-Backend {
    if ($script:BackendProc -and -not $script:BackendProc.HasExited) {
        # Kill the whole tree so uvicorn/child workers go down too.
        try { & taskkill.exe /PID $script:BackendProc.Id /T /F | Out-Null } catch {}
    }
    $script:BackendProc = $null
}

function Open-BestLog {
    if (Test-Path $BackendLog) { Start-Process notepad.exe $BackendLog }
    elseif (Test-Path $ErrLog) { Start-Process notepad.exe $ErrLog }
    else { Start-Process explorer.exe $LogsDir }
}

# --- Tray icon + menu -------------------------------------------------------
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Application
$notify.Text = "nano-dlna projector"
$notify.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip

$itemDash = $menu.Items.Add("Open Dashboard")
$itemDash.add_Click({ Start-Process $DashboardUrl })

$itemLog = $menu.Items.Add("Open Service Log")
$itemLog.add_Click({ Open-BestLog })

$itemLogs = $menu.Items.Add("Open Logs Folder")
$itemLogs.add_Click({ Start-Process explorer.exe $LogsDir })

[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))

$itemRestart = $menu.Items.Add("Restart Backend")
$itemRestart.add_Click({ Stop-Backend; Start-Sleep -Milliseconds 600; Start-Backend })

$itemQuit = $menu.Items.Add("Quit")
$itemQuit.add_Click({
    Stop-Backend
    $notify.Visible = $false
    $notify.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$notify.ContextMenuStrip = $menu
$notify.add_MouseDoubleClick({ Start-Process $DashboardUrl })

Start-Backend
$notify.ShowBalloonTip(
    3000,
    "nano-dlna",
    "Projection service running. Right-click the tray icon for the dashboard and logs.",
    [System.Windows.Forms.ToolTipIcon]::Info
)

# Make sure the backend is stopped if the message loop ever exits.
try {
    [System.Windows.Forms.Application]::Run((New-Object System.Windows.Forms.ApplicationContext))
} finally {
    Stop-Backend
    if ($notify) { $notify.Dispose() }
}
