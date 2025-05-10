on run argv
    set command to item 1 of argv
    
    if command is "start" then
        set deviceName to item 2 of argv
        startMirroring(deviceName)
    else if command is "stop" then
        stopMirroring()
    else
        error "Unknown command: " & command
    end if
end run

on startMirroring(deviceName)
    tell application "System Preferences"
        reveal pane "com.apple.preference.displays"
        delay 1
        tell application "System Events"
            tell process "System Preferences"
                # Click AirPlay dropdown 
                click pop up button 1 of tab group 1 of window 1
                delay 0.5
                
                # Find and click the device with matching name
                repeat with menuItem in menu items of menu 1 of pop up button 1 of tab group 1 of window 1
                    if name of menuItem contains deviceName then
                        click menuItem
                        delay 0.5
                        # Success
                        return 0
                    end if
                end repeat
                
                # Device not found
                error "AirPlay device not found: " & deviceName
            end tell
        end tell
    end tell
end startMirroring

on stopMirroring()
    tell application "System Preferences"
        reveal pane "com.apple.preference.displays"
        delay 1
        tell application "System Events"
            tell process "System Preferences"
                # Click AirPlay dropdown 
                click pop up button 1 of tab group 1 of window 1
                delay 0.5
                
                # Click "This Mac" to stop mirroring
                click menu item "This Mac" of menu 1 of pop up button 1 of tab group 1 of window 1
                delay 0.5
                # Success
                return 0
            end tell
        end tell
    end tell
end stopMirroring 