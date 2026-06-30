' Launch the nano-dlna tray host completely hidden (no console window).
' Usage: wscript.exe nano-dlna-tray.vbs [port]
Dim shell, scriptDir, port, cmd
Set shell = CreateObject("WScript.Shell")
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
port = "8010"
If WScript.Arguments.Count > 0 Then port = WScript.Arguments(0)
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & scriptDir & "nano-dlna-tray.ps1"" -Port " & port
' Second arg 0 = hidden window, third arg False = don't wait.
shell.Run cmd, 0, False
