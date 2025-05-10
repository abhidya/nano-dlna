#!/bin/bash

# Test script for Chrome renderer with door6.mp4 video
# This script tests the Chrome renderer with the door6.mp4 video via AirPlay

# Set the base URL
BASE_URL="http://localhost:3000/api"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Chrome Renderer with door6.mp4 Video${NC}"
echo "=================================================="

# Test 1: Start the projector with chrome-visible renderer
echo -e "\n${YELLOW}Test 1: Starting projector 'proj-hccast' with chrome-visible renderer${NC}"
START_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/start_projector" \
  -H "Content-Type: application/json" \
  -d '{"projector_id": "proj-hccast"}')

echo "Response: $START_RESPONSE"

# Check if start was successful
START_SUCCESS=$(echo $START_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$START_SUCCESS" ]; then
  echo -e "${RED}Failed to start projector${NC}"
  exit 1
else
  echo -e "${GREEN}Successfully started projector with chrome-visible renderer${NC}"
fi

# Extract projector ID from the response
PROJECTOR_ID=$(echo $START_RESPONSE | grep -o '"projector_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PROJECTOR_ID" ]; then
  echo -e "${RED}Failed to extract projector ID${NC}"
  exit 1
fi

# Wait for the projector to fully start
echo "Waiting 5 seconds for projector to fully start..."
sleep 5

# Test 2: Get the renderer status
echo -e "\n${YELLOW}Test 2: Getting renderer status for projector '$PROJECTOR_ID'${NC}"
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/renderer/status/$PROJECTOR_ID" \
  -H "Content-Type: application/json")

echo "Response: $STATUS_RESPONSE"

# Check if status was successful
STATUS_SUCCESS=$(echo $STATUS_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$STATUS_SUCCESS" ]; then
  echo -e "${RED}Failed to get renderer status${NC}"
else
  echo -e "${GREEN}Successfully got renderer status${NC}"
fi

# Wait for user to observe the Chrome window
echo -e "\n${YELLOW}Chrome window should now be visible with door6.mp4 playing.${NC}"
echo -e "${YELLOW}Press Enter to continue to the next test...${NC}"
read

# Test 3: Pause the renderer
echo -e "\n${YELLOW}Test 3: Pausing renderer for projector '$PROJECTOR_ID'${NC}"
PAUSE_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/pause/$PROJECTOR_ID" \
  -H "Content-Type: application/json")

echo "Response: $PAUSE_RESPONSE"

# Check if pause was successful
PAUSE_SUCCESS=$(echo $PAUSE_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$PAUSE_SUCCESS" ]; then
  echo -e "${RED}Failed to pause renderer${NC}"
else
  echo -e "${GREEN}Successfully paused renderer${NC}"
fi

# Wait for user to observe the paused Chrome window
echo -e "\n${YELLOW}Chrome window should now be paused.${NC}"
echo -e "${YELLOW}Press Enter to continue to the next test...${NC}"
read

# Test 4: Resume the renderer
echo -e "\n${YELLOW}Test 4: Resuming renderer for projector '$PROJECTOR_ID'${NC}"
RESUME_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/resume/$PROJECTOR_ID" \
  -H "Content-Type: application/json")

echo "Response: $RESUME_RESPONSE"

# Check if resume was successful
RESUME_SUCCESS=$(echo $RESUME_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$RESUME_SUCCESS" ]; then
  echo -e "${RED}Failed to resume renderer${NC}"
else
  echo -e "${GREEN}Successfully resumed renderer${NC}"
fi

# Wait for user to observe the resumed Chrome window
echo -e "\n${YELLOW}Chrome window should now be resumed.${NC}"
echo -e "${YELLOW}Press Enter to continue to the next test...${NC}"
read

# Test 5: Stop the renderer
echo -e "\n${YELLOW}Test 5: Stopping renderer for projector '$PROJECTOR_ID'${NC}"
STOP_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/stop" \
  -H "Content-Type: application/json" \
  -d "{\"projector\":\"$PROJECTOR_ID\"}")

echo "Response: $STOP_RESPONSE"

# Check if stop was successful
STOP_SUCCESS=$(echo $STOP_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$STOP_SUCCESS" ]; then
  echo -e "${RED}Failed to stop renderer${NC}"
else
  echo -e "${GREEN}Successfully stopped renderer${NC}"
fi

echo -e "\n${GREEN}All tests completed${NC}"
