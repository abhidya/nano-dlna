#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

# Function to check device status
check_device_status() {
    local device_id=$1
    echo "Checking device status for device ID: $device_id"
    curl -s "http://localhost:8000/api/devices/$device_id" | jq '.'
}

# Function to play a video on a device
play_video() {
    local device_id=$1
    local video_id=$2
    local loop=$3
    echo "Playing video $video_id on device $device_id (loop=$loop)"
    curl -s -X POST "http://localhost:8000/api/devices/$device_id/play" \
        -H "Content-Type: application/json" \
        -d "{\"video_id\": $video_id, \"loop\": $loop}" | jq '.'
}

# Function to monitor playback progress
monitor_progress() {
    local device_id=$1
    local duration=$2
    local interval=$3
    
    echo "Monitoring playback progress for device $device_id for $duration seconds (updating every $interval seconds)"
    echo "Press Ctrl+C to stop monitoring"
    
    # Create a progress bar function
    progress_bar() {
        local progress=$1
        local width=50
        local num_chars=$(($progress * $width / 100))
        local bar=$(printf "%${num_chars}s" | tr ' ' '#')
        local space=$(printf "%$(($width - $num_chars))s")
        printf "[%s%s] %d%%\r" "$bar" "$space" "$progress"
    }
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    
    while [ $(date +%s) -lt $end_time ]; do
        # Get device status
        local response=$(curl -s "http://localhost:8000/api/devices/$device_id")
        
        # Extract playback information
        local position=$(echo $response | jq -r '.playback_position')
        local total_duration=$(echo $response | jq -r '.playback_duration')
        local progress=$(echo $response | jq -r '.playback_progress')
        local is_playing=$(echo $response | jq -r '.is_playing')
        
        # Clear line and print progress
        printf "\033[K"  # Clear line
        
        if [ "$is_playing" = "true" ] && [ "$progress" != "null" ]; then
            echo "Position: $position / $total_duration ($progress%)"
            progress_bar $progress
        else
            echo "Device is not playing or progress information is not available"
        fi
        
        sleep $interval
    done
    
    echo -e "\nMonitoring completed"
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

# List all videos
echo ""
echo "Listing all videos:"
curl -s "http://localhost:8000/api/videos" | jq '.videos[] | {id, name, path}'

# Prompt user to select a video
echo ""
echo "Enter the ID of the video to play:"
read video_id

# Play the video
echo ""
play_video $device_id $video_id true

# Wait for playback to start
echo ""
echo "Waiting for playback to start..."
sleep 3

# Check device status after playing
echo ""
echo "Device status after playing video:"
check_device_status $device_id

# Monitor playback progress
echo ""
echo "Starting playback progress monitoring..."
monitor_progress $device_id 60 1  # Monitor for 60 seconds, update every 1 second

# Final device status
echo ""
echo "Final device status:"
check_device_status $device_id

echo ""
echo "Playback progress test completed."
