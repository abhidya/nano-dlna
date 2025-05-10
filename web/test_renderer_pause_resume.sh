#!/bin/bash

# Test script for renderer pause and resume functionality
# This script tests the pause and resume endpoints for the renderer service

# Set the base URL
BASE_URL="http://localhost:3000/api"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Renderer Pause and Resume Functionality${NC}"
echo "=================================================="

# Test 1: Start a projector
echo -e "\n${YELLOW}Test 1: Starting projector 'proj-hccast'${NC}"
START_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/start_projector" \
  -H "Content-Type: application/json" \
  -d '{"projector_id": "proj-hccast"}')

echo "Response: $START_RESPONSE"

# Extract projector ID from the response
PROJECTOR_ID=$(echo $START_RESPONSE | grep -o '"projector_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PROJECTOR_ID" ]; then
  echo -e "${RED}Failed to start projector or extract projector ID${NC}"
  exit 1
fi

echo -e "${GREEN}Successfully started projector: $PROJECTOR_ID${NC}"

# Wait for the projector to fully start
echo "Waiting 3 seconds for projector to fully start..."
sleep 3

# Test 2: Pause the projector
echo -e "\n${YELLOW}Test 2: Pausing projector '$PROJECTOR_ID'${NC}"
PAUSE_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/pause/$PROJECTOR_ID" \
  -H "Content-Type: application/json")

echo "Response: $PAUSE_RESPONSE"

# Check if pause was successful
PAUSE_SUCCESS=$(echo $PAUSE_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$PAUSE_SUCCESS" ]; then
  echo -e "${RED}Failed to pause projector${NC}"
else
  echo -e "${GREEN}Successfully paused projector${NC}"
fi

# Wait a moment
echo "Waiting 2 seconds..."
sleep 2

# Test 3: Resume the projector
echo -e "\n${YELLOW}Test 3: Resuming projector '$PROJECTOR_ID'${NC}"
RESUME_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/resume/$PROJECTOR_ID" \
  -H "Content-Type: application/json")

echo "Response: $RESUME_RESPONSE"

# Check if resume was successful
RESUME_SUCCESS=$(echo $RESUME_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$RESUME_SUCCESS" ]; then
  echo -e "${RED}Failed to resume projector${NC}"
else
  echo -e "${GREEN}Successfully resumed projector${NC}"
fi

# Wait a moment
echo "Waiting 2 seconds..."
sleep 2

# Test 4: Stop the projector
echo -e "\n${YELLOW}Test 4: Stopping projector '$PROJECTOR_ID'${NC}"
STOP_RESPONSE=$(curl -s -X POST "$BASE_URL/renderer/stop" \
  -H "Content-Type: application/json" \
  -d "{\"projector\":\"$PROJECTOR_ID\"}")

echo "Response: $STOP_RESPONSE"

# Check if stop was successful
STOP_SUCCESS=$(echo $STOP_RESPONSE | grep -o '"success":true' || echo "")

if [ -z "$STOP_SUCCESS" ]; then
  echo -e "${RED}Failed to stop projector${NC}"
else
  echo -e "${GREEN}Successfully stopped projector${NC}"
fi

echo -e "\n${GREEN}All tests completed${NC}"
