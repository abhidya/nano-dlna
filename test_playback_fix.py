#!/usr/bin/env python3
"""
Test script to verify the playback restart loop fix
"""
import time
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_playback_fix():
    print("Testing playback restart loop fix...")
    
    # 1. Get devices
    print("\n1. Getting devices...")
    response = requests.get(f"{API_BASE}/devices/")
    devices = response.json()
    print(f"Found {len(devices)} devices")
    
    if not devices:
        print("No devices found. Please ensure devices are connected.")
        return
    
    # Get first device
    device = devices[0]
    device_id = device['id']
    device_name = device['name']
    print(f"Testing with device: {device_name} (ID: {device_id})")
    
    # 2. Get a video to play
    print("\n2. Getting videos...")
    response = requests.get(f"{API_BASE}/videos/")
    videos = response.json()['items']
    if not videos:
        print("No videos found.")
        return
    
    video = videos[0]
    video_id = video['id']
    print(f"Using video: {video['name']} (ID: {video_id})")
    
    # 3. Start playback
    print(f"\n3. Starting playback on device {device_name}...")
    response = requests.post(f"{API_BASE}/devices/{device_id}/play/{video_id}")
    if response.status_code == 200:
        print("✓ Playback started successfully")
    else:
        print(f"✗ Failed to start playback: {response.text}")
        return
    
    # Wait for playback to establish
    time.sleep(5)
    
    # 4. Check device status
    print("\n4. Checking device status...")
    response = requests.get(f"{API_BASE}/devices/{device_id}")
    device_info = response.json()
    print(f"Device is_playing: {device_info.get('is_playing')}")
    print(f"Current video: {device_info.get('current_video')}")
    print(f"User control mode: {device_info.get('user_control_mode', 'Not set')}")
    
    # 5. Stop playback
    print(f"\n5. Stopping playback on device {device_name}...")
    response = requests.post(f"{API_BASE}/devices/{device_id}/stop")
    if response.status_code == 200:
        print("✓ Playback stopped successfully")
    else:
        print(f"✗ Failed to stop playback: {response.text}")
        return
    
    # 6. Check device status after stop
    print("\n6. Checking device status after stop...")
    response = requests.get(f"{API_BASE}/devices/{device_id}")
    device_info = response.json()
    print(f"Device is_playing: {device_info.get('is_playing')}")
    print(f"Current video: {device_info.get('current_video')}")
    print(f"User control mode: {device_info.get('user_control_mode', 'Not set')}")
    print(f"User control reason: {device_info.get('user_control_reason', 'Not set')}")
    
    # 7. Wait and monitor for auto-restart attempts
    print("\n7. Monitoring for auto-restart attempts (30 seconds)...")
    print("If the fix is working, the device should NOT auto-restart.")
    
    restart_detected = False
    for i in range(6):  # Check every 5 seconds for 30 seconds
        time.sleep(5)
        response = requests.get(f"{API_BASE}/devices/{device_id}")
        device_info = response.json()
        is_playing = device_info.get('is_playing', False)
        current_video = device_info.get('current_video')
        
        print(f"   [{i*5}s] is_playing: {is_playing}, current_video: {current_video}")
        
        if is_playing or current_video:
            restart_detected = True
            print("   ✗ Auto-restart detected! The fix may not be working properly.")
            break
    
    if not restart_detected:
        print("\n✓ SUCCESS: No auto-restart detected. The fix is working!")
    else:
        print("\n✗ FAILURE: Auto-restart was detected. Check the implementation.")
    
    # 8. Test discovery toggle scenario
    print("\n8. Testing discovery toggle scenario...")
    
    # Pause discovery
    print("   Pausing discovery...")
    response = requests.post(f"{API_BASE}/devices/discovery/pause")
    print(f"   Discovery pause response: {response.status_code}")
    
    time.sleep(2)
    
    # Resume discovery
    print("   Resuming discovery...")
    response = requests.post(f"{API_BASE}/devices/discovery/resume")
    print(f"   Discovery resume response: {response.status_code}")
    
    # Check if device tries to auto-play
    print("   Checking if device auto-plays after discovery resume...")
    time.sleep(5)
    response = requests.get(f"{API_BASE}/devices/{device_id}")
    device_info = response.json()
    is_playing = device_info.get('is_playing', False)
    
    if not is_playing:
        print("   ✓ Device did not auto-play after discovery resume")
    else:
        print("   ✗ Device auto-played after discovery resume")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_playback_fix()