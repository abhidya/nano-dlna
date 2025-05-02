#!/usr/bin/env python3
"""
Script to test device discovery and configuration for nano-dlna.
This will discover DLNA devices on the network and print their information.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import nanodlna
import nanodlna
from nanodlna import discover_devices, send_video


def discover_and_print_devices():
    """Discover DLNA devices and print their information"""
    print("Discovering DLNA devices...")
    devices = discover_devices()
    
    if not devices:
        print("No DLNA devices found on the network.")
        return None
    
    print(f"Found {len(devices)} DLNA devices:")
    for i, device in enumerate(devices, 1):
        print(f"\nDevice {i}:")
        print(json.dumps(device, indent=4))
    
    return devices


def check_config_file(config_path):
    """Check if a configuration file exists and print its contents"""
    config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return False
    
    print(f"\nReading configuration from {config_path}:")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(json.dumps(config, indent=4))
        
        # Check for video files
        videos_to_check = []
        for device in config:
            if "video_file" in device:
                video_path = device["video_file"]
                videos_to_check.append(video_path)
        
        # Check if video files exist
        print("\nChecking video files:")
        for video_path in videos_to_check:
            if os.path.exists(video_path):
                print(f"✓ Found video: {video_path}")
            else:
                print(f"✗ Missing video: {video_path}")
        
        return True
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {config_path}")
        return False
    except Exception as e:
        print(f"Error reading config file: {e}")
        return False


def test_device_connection(device_info):
    """Test connection to a device by sending a simple command"""
    print(f"\nTesting connection to {device_info['friendly_name']}...")
    from nanodlna.dlna import Device
    
    try:
        device = Device(device_info)
        # Get transport info to test connection
        transport_info = device._send_dlna_command("GetTransportInfo")
        
        if transport_info is not None:
            print(f"Successfully connected to {device_info['friendly_name']}")
            print(f"Current state: {transport_info}")
            return True
        else:
            print(f"Failed to get transport info from {device_info['friendly_name']}")
            return False
    except Exception as e:
        print(f"Error connecting to {device_info['friendly_name']}: {e}")
        return False


def main():
    """Main function for the script"""
    parser = argparse.ArgumentParser(description="Test device discovery and configuration for nano-dlna")
    parser.add_argument("-c", "--config", type=str, help="Path to device configuration file", 
                        default="my_device_config.json")
    parser.add_argument("-t", "--test-connection", action="store_true", 
                        help="Test connection to each discovered device")
    args = parser.parse_args()
    
    # Discover devices
    devices = discover_and_print_devices()
    
    # Check configuration
    if args.config:
        check_config_file(args.config)
    
    # Test connection if requested
    if args.test_connection and devices:
        print("\nTesting connection to discovered devices...")
        for device in devices:
            test_device_connection(device)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 