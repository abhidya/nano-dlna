"""
AirPlay device discovery and listing functionality.
"""

import subprocess
import re
import logging
from typing import List, Dict, Optional


class AirPlayDiscovery:
    """Class for discovering and listing AirPlay devices on the network."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the AirPlay discovery.
        
        Args:
            logger: Optional logger for discovery logging
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def discover_devices(self) -> List[Dict]:
        """Discover AirPlay devices on the network.
        
        Returns:
            List of dictionaries containing device information:
                - name: Device name
                - id: Device ID (same as name for AirPlay)
                - type: Device type (always 'airplay')
                - status: Device status ('available')
        """
        try:
            # Use the 'dns-sd' command to discover AirPlay devices
            # This command lists Bonjour services on the network
            cmd = [
                "dns-sd", 
                "-B",  # Browse
                "_airplay._tcp",  # AirPlay service type
                "local"  # Local domain
            ]
            
            self.logger.info("Discovering AirPlay devices...")
            
            # Run the command with a timeout
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Wait for 3 seconds to collect results
            import time
            time.sleep(3)
            
            # Terminate the process
            process.terminate()
            
            # Get the output
            stdout, stderr = process.communicate()
            output = stdout.decode('utf-8')
            
            # Parse the output to extract device names
            devices = []
            
            # Regular expression to match AirPlay device entries
            # Example line: "Browsing for _airplay._tcp.local
            # Timestamp     A/R Flags if Domain               Service Type         Instance Name
            # 10:21:15.724  Add     3  4 local.              _airplay._tcp.       Living Room Apple TV"
            pattern = r'\s+Add\s+\d+\s+\d+\s+local\.\s+_airplay\._tcp\.\s+(.+)$'
            
            for line in output.splitlines():
                match = re.search(pattern, line)
                if match:
                    device_name = match.group(1).strip()
                    devices.append({
                        'name': device_name,
                        'id': device_name,  # Use name as ID
                        'type': 'airplay',
                        'status': 'available'
                    })
            
            self.logger.info(f"Discovered {len(devices)} AirPlay devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Error discovering AirPlay devices: {str(e)}")
            return []
    
    def list_devices_from_system_prefs(self) -> List[Dict]:
        """List AirPlay devices available in System Preferences.
        
        This method uses AppleScript to get the list of AirPlay devices
        from the System Preferences AirPlay menu.
        
        Returns:
            List of dictionaries containing device information:
                - name: Device name
                - id: Device ID (same as name for AirPlay)
                - type: Device type (always 'airplay')
                - status: Device status ('available')
        """
        try:
            # AppleScript to get AirPlay devices from System Preferences
            script = """
            tell application "System Preferences"
                reveal pane "com.apple.preference.displays"
                delay 1
                tell application "System Events"
                    tell process "System Preferences"
                        # Click AirPlay dropdown 
                        click pop up button 1 of tab group 1 of window 1
                        delay 0.5
                        
                        # Get all menu items except "This Mac"
                        set deviceList to {}
                        repeat with menuItem in menu items of menu 1 of pop up button 1 of tab group 1 of window 1
                            set deviceName to name of menuItem
                            if deviceName is not "This Mac" then
                                copy deviceName to end of deviceList
                            end if
                        end repeat
                        
                        # Click "This Mac" to close the menu
                        click menu item "This Mac" of menu 1 of pop up button 1 of tab group 1 of window 1
                        
                        # Return the device list
                        return deviceList
                    end tell
                end tell
            end tell
            """
            
            self.logger.info("Listing AirPlay devices from System Preferences...")
            
            # Run the AppleScript
            process = subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Get the output
            stdout, stderr = process.communicate()
            output = stdout.decode('utf-8')
            
            # Parse the output to extract device names
            devices = []
            
            # Split by commas and remove any quotes
            device_names = [name.strip().strip('"') for name in output.split(',')]
            
            for device_name in device_names:
                if device_name:  # Skip empty names
                    devices.append({
                        'name': device_name,
                        'id': device_name,  # Use name as ID
                        'type': 'airplay',
                        'status': 'available'
                    })
            
            self.logger.info(f"Found {len(devices)} AirPlay devices in System Preferences")
            return devices
            
        except Exception as e:
            self.logger.error(f"Error listing AirPlay devices from System Preferences: {str(e)}")
            return []
    
    def get_devices(self) -> List[Dict]:
        """Get AirPlay devices using both discovery methods.
        
        This method combines the results from both discovery methods
        and removes duplicates.
        
        Returns:
            List of dictionaries containing device information
        """
        # Get devices from both methods
        discovered_devices = self.discover_devices()
        system_prefs_devices = self.list_devices_from_system_prefs()
        
        # Combine the results and remove duplicates
        all_devices = {}
        
        for device in discovered_devices + system_prefs_devices:
            device_id = device['id']
            if device_id not in all_devices:
                all_devices[device_id] = device
        
        return list(all_devices.values())
