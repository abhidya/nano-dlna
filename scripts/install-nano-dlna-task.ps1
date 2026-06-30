[CmdletBinding()]
param(
    [string]$TaskName = "NanoDLNA Projector",
    [int]$Port = 8010,
    [switch]$InstallDeps,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"

$Runner = (Resolve-Path (Join-Path $PSScriptRoot "run-nano-dlna-service.ps1")).Path
$PowerShell = (Get-Command powershell.exe).Source

$PrepArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $Runner,
    "-Port", $Port,
    "-BuildFrontend",
    "-PrepareOnly"
)
if ($InstallDeps) {
    $PrepArgs += "-InstallDeps"
}

& $PowerShell @PrepArgs
if ($LASTEXITCODE -ne 0) {
    throw "Service prep failed with exit code $LASTEXITCODE"
}

$ActionArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-WindowStyle", "Hidden",
    "-File", "`"$Runner`"",
    "-Port", $Port
) -join " "

$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $ActionArgs
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
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
    -Description "Run Nano-DLNA dashboard and HDMI projector adapter in the interactive user session." `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

Write-Output "Installed task '$TaskName'."
Write-Output "App: http://localhost:$Port/app"
Write-Output "API: http://localhost:$Port/api"
Write-Output "Logs: $(Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')) 'logs\nano-dlna-service.log')"
