#!/bin/bash
# Test script for Chrome renderer to AirPlay integration

# Store the root directory path
ROOT_DIR="$(pwd)"

# Set up colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Chrome to AirPlay Integration Test ===${NC}"
echo "This test will attempt to connect to an AirPlay device and display content."
echo "Make sure your Mac has AirPlay devices available in the network."
echo ""

# Check if we're in the right directory
if [ ! -d "web/backend" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory.${NC}"
    exit 1
fi

# Check if the Python virtual environment exists
if [ ! -d "web/backend/venv" ] && [ ! -d "nanodlna_venv" ]; then
    echo -e "${YELLOW}No virtual environment found. Using system Python.${NC}"
    PYTHON="python3"
else
    if [ -d "web/backend/venv" ]; then
        echo -e "${GREEN}Using web/backend/venv virtual environment.${NC}"
        PYTHON="web/backend/venv/bin/python"
    else
        echo -e "${GREEN}Using nanodlna_venv virtual environment.${NC}"
        PYTHON="nanodlna_venv/bin/python"
    fi
fi

echo ""
echo -e "${YELLOW}Starting AirPlay integration test...${NC}"
echo "The test will:"
echo "1. Find an AirPlay projector in your configuration"
echo "2. Render a scene using Chrome"
echo "3. Connect to the AirPlay device and display the content"
echo ""
echo -e "${YELLOW}When the content appears on your AirPlay device, press Enter to stop the test.${NC}"
echo ""

# Run the test script
cd "$ROOT_DIR/web/backend"
$PYTHON tests/test_airplay_integration.py

# Check the result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully!${NC}"
else
    echo -e "${RED}Test failed. Check the error messages above.${NC}"
    echo "Common issues:"
    echo "- No AirPlay devices found in your network"
    echo "- No AirPlay projectors configured in renderer_config.json"
    echo "- AppleScript permissions not granted (check System Preferences > Security & Privacy > Accessibility)"
    echo "- Chrome browser not installed at the expected path"
fi

# Return to the original directory
cd "$ROOT_DIR"
