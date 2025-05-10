#!/bin/bash
# Test script for AirPlay API endpoints

# Store the root directory path
ROOT_DIR="$(pwd)"

# Set up colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== AirPlay API Test ===${NC}"
echo "This test will call the AirPlay API endpoints to verify they are working correctly."
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

# Function to test an API endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -e "${YELLOW}Testing: ${description}${NC}"
    echo "Endpoint: ${API_BASE}${endpoint}"
    echo ""
    
    local response=$(curl -s "${API_BASE}${endpoint}")
    format_json "$response"
    
    echo ""
    echo -e "${GREEN}Test completed!${NC}"
    echo "----------------------------------------"
    echo ""
}

# Test AirPlay discovery endpoints
test_endpoint "/renderer/airplay/discover" "Discover AirPlay devices on the network"
test_endpoint "/renderer/airplay/list" "List AirPlay devices from System Preferences"
test_endpoint "/renderer/airplay/devices" "Get all AirPlay devices (combined)"

echo -e "${GREEN}All tests completed!${NC}"
