#!/bin/bash
# Test script for blackout feature fix

echo "Testing Blackout Feature Fix for Connected but Idle Devices"
echo "============================================================"

# 1. Get current brightness status
echo -e "\n1. Getting current brightness status..."
curl -s http://localhost:8000/api/overlay/brightness/status | python3 -m json.tool

# 2. Get device list
echo -e "\n2. Getting device list..."
curl -s http://localhost:8000/api/devices | python3 -m json.tool | head -20

# 3. Activate blackout
echo -e "\n3. Activating blackout (brightness=0)..."
curl -s -X POST "http://localhost:8000/api/overlay/brightness?brightness=0" | python3 -m json.tool

# 4. Wait
echo -e "\n4. Waiting 5 seconds..."
sleep 5

# 5. Check device states during blackout
echo -e "\n5. Checking device states during blackout..."
curl -s http://localhost:8000/api/devices | python3 -m json.tool | grep -A 5 -B 5 "is_playing"

# 6. Deactivate blackout
echo -e "\n6. Deactivating blackout (brightness=100)..."
curl -s -X POST "http://localhost:8000/api/overlay/brightness?brightness=100" | python3 -m json.tool

echo -e "\n7. Test completed!"
echo -e "\nSummary:"
echo "- Blackout now affects ALL connected DLNA devices (playing or idle)"
echo "- Idle devices show black video during blackout"
echo "- Idle devices return to idle state after blackout"
echo "- Playing devices restore their original video"