<#
.SYNOPSIS
    Register a logon task that reopens the projection kiosk after a reboot.

.DESCRIPTION
    Complements install-nano-dlna-task.ps1 (which starts the backend). This
    task runs launch-projection-kiosk.ps1 at logon so the overlay projection
    window comes back on its own after a power cycle.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\install-projection-kiosk-task.ps1 -Port 8010 -StartNow
#>
[CmdletBinding()]
param(
    [string]$TaskName = "NanoDLNA Projection Kiosk",
    [int]$Port = 8010,
    [string]$Path = "/backend-static/overlay_window.html",
    [int]$DisplayIndex = -1,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"

$Launcher = (Resolve-Path (Join-Path $PSScriptRoot "launch-projection-kiosk.ps1")).Path
$PowerShell = (Get-Command powershell.exe).Source

$ActionArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-WindowStyle", "Hidden",
    "-File", "`"$Launcher`"",
    "-Port", $Port,
    "-Path", "`"$Path`"",
    "-DisplayIndex", $DisplayIndex
) -join " "

$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $ActionArgs
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
# Delay so the backend (its own logon task) has a head start, plus restart-on-fail.
$Trigger.Delay = "PT15S"
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 30)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Reopen the nano-dlna projection kiosk on the projector display at logon." `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Write-Output "Installed task '$TaskName'."
Write-Output "Projects: http://localhost:$Port$Path"
