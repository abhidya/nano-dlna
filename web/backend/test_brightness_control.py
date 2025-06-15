#!/usr/bin/env python3
"""
Test script for brightness control with DLNA devices
"""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/overlay"

def test_brightness_control():
    """Test the brightness control functionality"""
    
    print("=== Brightness Control Test ===\n")
    
    # 1. Get current brightness status
    print("1. Getting current brightness status...")
    response = requests.get(f"{BASE_URL}/brightness/status")
    if response.status_code == 200:
        status = response.json()
        print(f"Current brightness: {status['brightness']}")
        print(f"Blackout active: {status['dlna_control']['blackout_active']}")
        print(f"Playing devices: {status['dlna_control']['playing_count']}")
        print(f"Black video available: {status['dlna_control']['black_video_available']}")
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    # 2. Set brightness to 0 (activate blackout)
    print("2. Setting brightness to 0 (activating blackout)...")
    response = requests.post(f"{BASE_URL}/brightness?brightness=0")
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Affected devices: {result.get('affected_devices', [])}")
        print(f"Device count: {result.get('device_count', 0)}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    # 3. Wait a bit
    print("3. Waiting 5 seconds...")
    time.sleep(5)
    
    # 4. Check status during blackout
    print("4. Checking status during blackout...")
    response = requests.get(f"{BASE_URL}/brightness/status")
    if response.status_code == 200:
        status = response.json()
        print(f"Blackout active: {status['dlna_control']['blackout_active']}")
        print(f"Backed up devices: {status['dlna_control']['backed_up_devices']}")
        
        # Show which devices are playing black video
        playing_devices = status['dlna_control']['playing_devices']
        for device in playing_devices:
            if device['is_black_video']:
                print(f"  - {device['name']} is playing black video")
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    # 5. Restore brightness (deactivate blackout)
    print("5. Setting brightness to 100 (deactivating blackout)...")
    response = requests.post(f"{BASE_URL}/brightness?brightness=100")
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Restored devices: {result.get('restored_devices', [])}")
        print(f"Device count: {result.get('device_count', 0)}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    # 6. Final status check
    print("6. Final status check...")
    response = requests.get(f"{BASE_URL}/brightness/status")
    if response.status_code == 200:
        status = response.json()
        print(f"Brightness: {status['brightness']}")
        print(f"Blackout active: {status['dlna_control']['blackout_active']}")
        print(f"Playing devices: {status['dlna_control']['playing_count']}")
        
        # Show restored devices
        playing_devices = status['dlna_control']['playing_devices']
        for device in playing_devices:
            print(f"  - {device['name']} is playing {device['current_video']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    try:
        test_brightness_control()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the backend is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)