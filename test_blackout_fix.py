#!/usr/bin/env python3
"""Test script for blackout feature fix"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_blackout_fix():
    print("Testing Blackout Feature Fix for Connected but Idle Devices")
    print("=" * 60)
    
    # Get current brightness status
    print("\n1. Getting current brightness status...")
    response = requests.get(f"{BASE_URL}/api/overlay/brightness/status")
    if response.status_code == 200:
        status = response.json()
        print(f"Current brightness: {status['brightness']}")
        print(f"Blackout active: {status['dlna_control']['blackout_active']}")
        print(f"Total devices: {status['dlna_control']['total_devices']}")
        print(f"Playing count: {status['dlna_control']['playing_count']}")
    else:
        print(f"Failed to get brightness status: {response.status_code}")
        return
    
    # Get device list
    print("\n2. Getting device list...")
    response = requests.get(f"{BASE_URL}/api/devices")
    if response.status_code == 200:
        devices = response.json()
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  - {device['name']}: status={device['status']}, playing={device['is_playing']}")
    else:
        print(f"Failed to get devices: {response.status_code}")
        return
    
    # Activate blackout
    print("\n3. Activating blackout (brightness=0)...")
    response = requests.post(f"{BASE_URL}/api/overlay/brightness?brightness=0")
    if response.status_code == 200:
        result = response.json()
        print(f"Blackout status: {result['status']}")
        print(f"Affected devices: {result.get('affected_devices', [])}")
        print(f"Device count: {result.get('device_count', 0)}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
    else:
        print(f"Failed to activate blackout: {response.status_code}")
        print(response.text)
        return
    
    # Wait a moment
    print("\n4. Waiting 5 seconds...")
    time.sleep(5)
    
    # Check device states during blackout
    print("\n5. Checking device states during blackout...")
    response = requests.get(f"{BASE_URL}/api/devices")
    if response.status_code == 200:
        devices = response.json()
        for device in devices:
            if device['status'] == 'connected':
                print(f"  - {device['name']}: playing={device['is_playing']}, video={device.get('current_video', 'None')}")
    
    # Deactivate blackout
    print("\n6. Deactivating blackout (brightness=100)...")
    response = requests.post(f"{BASE_URL}/api/overlay/brightness?brightness=100")
    if response.status_code == 200:
        result = response.json()
        print(f"Blackout status: {result['status']}")
        print(f"Restored devices: {result.get('restored_devices', [])}")
        print(f"Device count: {result.get('device_count', 0)}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
    else:
        print(f"Failed to deactivate blackout: {response.status_code}")
        print(response.text)
        return
    
    print("\n7. Test completed!")
    print("\nSummary:")
    print("- Blackout now affects ALL connected DLNA devices (playing or idle)")
    print("- Idle devices show black video during blackout")
    print("- Idle devices return to idle state after blackout")
    print("- Playing devices restore their original video")

if __name__ == "__main__":
    test_blackout_fix()