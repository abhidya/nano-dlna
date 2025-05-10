#!/usr/bin/env python3

import os
import json
import sys

def check_config_file(file_path):
    """
    Check if a configuration file exists and is valid JSON
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        bool: True if the file exists and is valid JSON, False otherwise
    """
    print(f"Checking configuration file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"  ERROR: File does not exist: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        # Check if the file has the expected structure
        if "devices" in config:
            devices = config["devices"]
            print(f"  Found {len(devices)} devices in the configuration file")
            for i, device in enumerate(devices):
                print(f"    Device {i+1}: {device.get('device_name', 'Unknown')} ({device.get('type', 'Unknown')})")
        else:
            # Try to interpret the file as a list of devices
            devices = config
            if isinstance(devices, list):
                print(f"  Found {len(devices)} devices in the configuration file")
                for i, device in enumerate(devices):
                    print(f"    Device {i+1}: {device.get('device_name', 'Unknown')} ({device.get('type', 'Unknown')})")
            else:
                print(f"  ERROR: Invalid configuration file format: {file_path}")
                return False
        
        return True
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON in file {file_path}: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: Error reading file {file_path}: {e}")
        return False

def main():
    # Check configuration files in the project root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_files = [
        os.path.join(root_dir, "my_device_config.json"),
        os.path.join(root_dir, "tramscreem+device_config.json"),
    ]
    
    # Also check in the current working directory
    cwd_config_files = [
        os.path.join(os.getcwd(), "my_device_config.json"),
        os.path.join(os.getcwd(), "tramscreem+device_config.json"),
    ]
    
    config_files.extend(cwd_config_files)
    
    # Remove duplicates
    config_files = list(set(config_files))
    
    found = False
    for config_file in config_files:
        if os.path.exists(config_file):
            found = True
            valid = check_config_file(config_file)
            if not valid:
                print(f"Configuration file {config_file} exists but is not valid")
    
    if not found:
        print("No configuration files found. Please make sure the files exist in the correct location.")
        print("Expected locations:")
        for config_file in config_files:
            print(f"  - {config_file}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
