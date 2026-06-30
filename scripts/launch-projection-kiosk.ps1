<#
.SYNOPSIS
    Open the nano-dlna projection page full-screen (kiosk) on the projector display.

.DESCRIPTION
    The overlay projection window is normally opened from the dashboard with
    window.open(), so it does not survive a reboot. This script reopens it at
    logon: it waits for the backend to answer, finds the projector display
    (the non-primary monitor by default), and launches Chrome/Edge in kiosk
    mode positioned on that display.

    Pair it with the backend autostart task (install-nano-dlna-task.ps1) and
    Windows auto-login so a power cycle returns straight to the projection.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\launch-projection-kiosk.ps1 -Port 8010

.EXAMPLE
    # Project a specific page on monitor index 1
    powershell -ExecutionPolicy Bypass -File .\scripts\launch-projection-kiosk.ps1 -Port 8010 -DisplayIndex 1 -Path "/backend-static/overlay_window.html"
#>
[CmdletBinding()]
param(
    [int]$Port = 8010,
    [string]$Path = "/backend-static/overlay_window.html",
    # Which monitor to project on. -1 = first non-primary display (the projector).
    [int]$DisplayIndex = -1,
    [int]$WaitSeconds = 120,
    [string]$BrowserPath = ""
)

$ErrorActionPreference = "Stop"

$BaseUrl = "http://localhost:$Port"
$Url = "$BaseUrl$Path"

function Find-Browser {
    param([string]$Override)
    if ($Override -and (Test-Path $Override)) { return $Override }
    $candidates = @(
        $env:CHROME_PATH,
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    throw "No Chrome or Edge install found. Pass -BrowserPath explicitly."
}

function Get-ProjectorScreen {
    param([int]$Index)
    Add-Type -AssemblyName System.Windows.Forms
    $screens = [System.Windows.Forms.Screen]::AllScreens
    if ($Index -ge 0) {
        if ($Index -ge $screens.Count) {
            throw "DisplayIndex $Index out of range; only $($screens.Count) display(s) detected."
        }
        return $screens[$Index]
    }
    # Default: first non-primary display, i.e. the projector. Fall back to primary.
    $projector = $screens | Where-Object { -not $_.Primary } | Select-Object -First 1
    if ($null -eq $projector) { $projector = [System.Windows.Forms.Screen]::PrimaryScreen }
    return $projector
}

# 1. Wait for the backend to be reachable (it may still be starting at logon).
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        Invoke-WebRequest -Uri "$BaseUrl/app" -UseBasicParsing -TimeoutSec 3 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $ready) {
    Write-Warning "Backend at $BaseUrl did not respond within $WaitSeconds s; launching anyway."
}

# 2. Locate the projector display and launch the browser in kiosk mode there.
$browser = Find-Browser -Override $BrowserPath
$screen = Get-ProjectorScreen -Index $DisplayIndex
$bounds = $screen.Bounds

$profileDir = Join-Path $env:TEMP "nano_dlna_kiosk_profile"

$browserArgs = @(
    "--new-window",
    "--no-first-run",
    "--disable-infobars",
    "--kiosk",
    "--window-position=$($bounds.X),$($bounds.Y)",
    "--window-size=$($bounds.Width),$($bounds.Height)",
    "--user-data-dir=`"$profileDir`"",
    $Url
)

Write-Output "Launching projection kiosk on display '$($screen.DeviceName)' at $($bounds.X),$($bounds.Y): $Url"
Start-Process -FilePath $browser -ArgumentList $browserArgs
