#!/bin/bash

# Simple curl command to test the Chrome renderer with door6.mp4 video
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

# Start the projector with chrome-visible renderer
echo -e "\n${YELLOW}Starting projector 'proj-hccast' with chrome-visible renderer${NC}"
curl -s -X POST "$BASE_URL/renderer/start_projector" \
  -H "Content-Type: application/json" \
  -d '{"projector_id": "proj-hccast"}'

echo -e "\n\n${GREEN}Chrome window should now be visible with door6.mp4 playing.${NC}"
echo -e "${YELLOW}Press Enter to pause the renderer...${NC}"
read

# Pause the renderer
echo -e "\n${YELLOW}Pausing renderer for projector 'proj-hccast'${NC}"
curl -s -X POST "$BASE_URL/renderer/pause/proj-hccast" \
  -H "Content-Type: application/json"

echo -e "\n\n${GREEN}Chrome window should now be paused.${NC}"
echo -e "${YELLOW}Press Enter to resume the renderer...${NC}"
read

# Resume the renderer
echo -e "\n${YELLOW}Resuming renderer for projector 'proj-hccast'${NC}"
curl -s -X POST "$BASE_URL/renderer/resume/proj-hccast" \
  -H "Content-Type: application/json"

echo -e "\n\n${GREEN}Chrome window should now be resumed.${NC}"
echo -e "${YELLOW}Press Enter to stop the renderer...${NC}"
read

# Stop the renderer
echo -e "\n${YELLOW}Stopping renderer for projector 'proj-hccast'${NC}"
curl -s -X POST "$BASE_URL/renderer/stop" \
  -H "Content-Type: application/json" \
  -d '{"projector": "proj-hccast"}'

echo -e "\n\n${GREEN}All tests completed${NC}"
