#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

# Function to check device status
check_device_status() {
    local device_id=$1
    echo "Checking device status for device ID: $device_id"
    curl -s "http://localhost:8000/api/devices/$device_id" | jq '.'
}

# Function to update playback progress manually (for testing)
update_playback_progress() {
    local device_id=$1
    local position=$2
    local duration=$3
    local progress=$4
    echo "Manually updating playback progress for device ID: $device_id"
    curl -s -X POST "http://localhost:8000/api/devices/$device_id/update-progress?position=$position&duration=$duration&progress=$progress" | jq '.'
}

# List all devices
echo "Listing all devices:"
curl -s "http://localhost:8000/api/devices" | jq '.devices[] | {id, name, friendly_name, status, is_playing}'

# Prompt user to select a device
echo ""
echo "Enter the ID of the device to test playback progress:"
read device_id

# Check initial device status
echo ""
echo "Initial device status:"
check_device_status $device_id

# Simulate playback progress updates
echo ""
echo "Simulating playback progress updates..."
update_playback_progress $device_id "00:00:10" "00:01:40" 10
sleep 2
check_device_status $device_id

update_playback_progress $device_id "00:00:30" "00:01:40" 30
sleep 2
check_device_status $device_id

update_playback_progress $device_id "00:00:50" "00:01:40" 50
sleep 2
check_device_status $device_id

update_playback_progress $device_id "00:01:10" "00:01:40" 70
sleep 2
check_device_status $device_id

update_playback_progress $device_id "00:01:30" "00:01:40" 90
sleep 2
check_device_status $device_id

echo ""
echo "Playback progress test completed."
