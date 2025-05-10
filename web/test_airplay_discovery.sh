#!/bin/bash
# Test script for AirPlay device discovery and listing

# Store the root directory path
ROOT_DIR="$(pwd)"

# Set up colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== AirPlay Device Discovery Test ===${NC}"
echo "This test will discover AirPlay devices on the network and list them."
echo "Make sure the dashboard is running before executing this test."
echo ""

# Check if we're in the right directory
if [ ! -d "web/backend" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed. Please install curl to run this test.${NC}"
    exit 1
fi

# Check if jq is installed (optional but helpful)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. Output will not be formatted.${NC}"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# Define API base URL
API_BASE="http://localhost:8000/api"

# Function to format JSON output
format_json() {
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

echo -e "${YELLOW}Step 1: Discovering AirPlay devices using dns-sd${NC}"
echo "This will search for AirPlay devices on the network using Bonjour/mDNS."
echo ""

DISCOVER_RESPONSE=$(curl -s "${API_BASE}/renderer/airplay/discover")
format_json "$DISCOVER_RESPONSE"

echo ""
echo -e "${YELLOW}Step 2: Listing AirPlay devices from System Preferences${NC}"
echo "This will list AirPlay devices available in System Preferences."
echo ""

LIST_RESPONSE=$(curl -s "${API_BASE}/renderer/airplay/list")
format_json "$LIST_RESPONSE"

echo ""
echo -e "${YELLOW}Step 3: Getting all AirPlay devices (combined)${NC}"
echo "This will get all AirPlay devices using both discovery methods."
echo ""

ALL_RESPONSE=$(curl -s "${API_BASE}/renderer/airplay/devices")
format_json "$ALL_RESPONSE"

echo ""
echo -e "${GREEN}Test completed!${NC}"
echo "The AirPlay discovery and listing functionality has been tested."
