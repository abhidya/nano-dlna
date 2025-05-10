#!/bin/bash
# End-to-End Test Script for Renderer and Depth Processing API Endpoints
# This script tests the renderer and depth processing API endpoints to ensure they work correctly.

# Set up variables
API_BASE_URL="http://localhost:8000"
PROXY_BASE_URL="http://localhost:3000/api"
TEMP_DIR="/tmp/nano-dlna-test"
TEST_DEPTH_MAP="$TEMP_DIR/test_depth_map.png"
TEST_DEPTH_ID=""
TEST_PROJECTOR_ID=""
TEST_SCENE_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create temp directory if it doesn't exist
mkdir -p $TEMP_DIR

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        echo -e "${YELLOW}Response: $3${NC}"
    fi
}

# Function to test an API endpoint
test_endpoint() {
    local url=$1
    local method=$2
    local expected_status=$3
    local description=$4
    local data=$5
    local content_type=${6:-"application/json"}
    
    echo -e "${YELLOW}Testing: $description${NC}"
    
    # Build curl command
    local curl_cmd="curl -s -X $method"
    
    # Add headers
    curl_cmd="$curl_cmd -H 'Accept: application/json'"
    
    # Add data if provided
    if [ -n "$data" ]; then
        if [ "$content_type" == "application/json" ]; then
            curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
        elif [ "$content_type" == "multipart/form-data" ]; then
            # For file uploads, data should be in the format: "file=@/path/to/file"
            curl_cmd="$curl_cmd -F '$data'"
        fi
    fi
    
    # Add URL
    curl_cmd="$curl_cmd $url"
    
    # Execute curl command
    local response=$(eval $curl_cmd)
    local status=$?
    
    # Check if curl command succeeded
    if [ $status -ne 0 ]; then
        print_result 1 "$description" "Curl command failed with status $status"
        return 1
    fi
    
    # Check if response contains expected status code
    if [[ "$response" == *"$expected_status"* ]] || [[ "$response" == *"\"success\":true"* ]]; then
        print_result 0 "$description" ""
        echo "$response"
        return 0
    else
        print_result 1 "$description" "$response"
        return 1
    fi
}

# Function to create a test depth map
create_test_depth_map() {
    print_header "Creating Test Depth Map"
    
    # Create a simple gradient image as a test depth map
    # This requires ImageMagick to be installed
    if command -v convert &> /dev/null; then
        convert -size 100x100 gradient: $TEST_DEPTH_MAP
        if [ -f $TEST_DEPTH_MAP ]; then
            echo -e "${GREEN}✓ Created test depth map at $TEST_DEPTH_MAP${NC}"
        else
            echo -e "${RED}✗ Failed to create test depth map${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ ImageMagick not installed. Cannot create test depth map.${NC}"
        echo -e "${YELLOW}Creating a dummy file instead.${NC}"
        # Create a dummy file
        dd if=/dev/urandom of=$TEST_DEPTH_MAP bs=1024 count=10
        if [ -f $TEST_DEPTH_MAP ]; then
            echo -e "${GREEN}✓ Created dummy test depth map at $TEST_DEPTH_MAP${NC}"
        else
            echo -e "${RED}✗ Failed to create dummy test depth map${NC}"
            exit 1
        fi
    fi
}

# Function to clean up test files
cleanup() {
    print_header "Cleaning Up"
    
    # Delete test depth map
    if [ -f $TEST_DEPTH_MAP ]; then
        rm $TEST_DEPTH_MAP
        echo -e "${GREEN}✓ Deleted test depth map${NC}"
    fi
    
    # Delete test depth ID if it exists
    if [ -n "$TEST_DEPTH_ID" ]; then
        test_endpoint "$API_BASE_URL/depth/$TEST_DEPTH_ID" "DELETE" "200" "Delete test depth map"
    fi
    
    # Stop renderer if it's running
    if [ -n "$TEST_PROJECTOR_ID" ]; then
        test_endpoint "$API_BASE_URL/renderer/stop" "POST" "200" "Stop renderer" "{\"projector\": \"$TEST_PROJECTOR_ID\"}"
    fi
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Set up trap to clean up on exit
trap cleanup EXIT

# Main test function
run_tests() {
    print_header "Starting Renderer and Depth Processing API Tests"
    
    # Test if backend is running
    test_endpoint "$API_BASE_URL/health" "GET" "200" "Backend health check"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Backend is not running. Exiting.${NC}"
        exit 1
    fi
    
    # Test if frontend is running
    test_endpoint "$PROXY_BASE_URL/health" "GET" "200" "Frontend proxy health check"
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Frontend proxy is not running. Continuing with direct API tests.${NC}"
    fi
    
    # Test Renderer API Endpoints
    print_header "Testing Renderer API Endpoints"
    
    # Get projectors
    local projectors_response=$(curl -s -X GET "$API_BASE_URL/renderer/projectors")
    echo "$projectors_response" | grep -q "\"success\":true"
    if [ $? -eq 0 ]; then
        print_result 0 "Get projectors" ""
        # Extract first projector ID
        TEST_PROJECTOR_ID=$(echo "$projectors_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN}Found projector ID: $TEST_PROJECTOR_ID${NC}"
    else
        print_result 1 "Get projectors" "$projectors_response"
    fi
    
    # Get scenes
    local scenes_response=$(curl -s -X GET "$API_BASE_URL/renderer/scenes")
    echo "$scenes_response" | grep -q "\"success\":true"
    if [ $? -eq 0 ]; then
        print_result 0 "Get scenes" ""
        # Extract first scene ID
        TEST_SCENE_ID=$(echo "$scenes_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN}Found scene ID: $TEST_SCENE_ID${NC}"
    else
        print_result 1 "Get scenes" "$scenes_response"
    fi
    
    # If we have a projector ID and scene ID, test starting a renderer
    if [ -n "$TEST_PROJECTOR_ID" ] && [ -n "$TEST_SCENE_ID" ]; then
        test_endpoint "$API_BASE_URL/renderer/start" "POST" "200" "Start renderer" "{\"projector\": \"$TEST_PROJECTOR_ID\", \"scene\": \"$TEST_SCENE_ID\"}"
        
        # Test getting renderer status
        test_endpoint "$API_BASE_URL/renderer/status/$TEST_PROJECTOR_ID" "GET" "200" "Get renderer status"
        
        # Test listing active renderers
        test_endpoint "$API_BASE_URL/renderer/list" "GET" "200" "List active renderers"
        
        # Test stopping renderer
        test_endpoint "$API_BASE_URL/renderer/stop" "POST" "200" "Stop renderer" "{\"projector\": \"$TEST_PROJECTOR_ID\"}"
    else
        echo -e "${YELLOW}Skipping renderer start/stop tests due to missing projector or scene ID${NC}"
    fi
    
    # Test Depth Processing API Endpoints
    print_header "Testing Depth Processing API Endpoints"
    
    # Create test depth map
    create_test_depth_map
    
    # Upload depth map
    local upload_response=$(curl -s -X POST -F "file=@$TEST_DEPTH_MAP" -F "normalize=true" "$API_BASE_URL/depth/upload")
    echo "$upload_response" | grep -q "\"success\":true"
    if [ $? -eq 0 ]; then
        print_result 0 "Upload depth map" ""
        # Extract depth ID
        TEST_DEPTH_ID=$(echo "$upload_response" | grep -o '"depth_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}Uploaded depth map with ID: $TEST_DEPTH_ID${NC}"
    else
        print_result 1 "Upload depth map" "$upload_response"
    fi
    
    # If we have a depth ID, test other depth processing endpoints
    if [ -n "$TEST_DEPTH_ID" ]; then
        # Test preview depth map
        test_endpoint "$API_BASE_URL/depth/preview/$TEST_DEPTH_ID" "GET" "200" "Preview depth map"
        
        # Test segment depth map using KMeans
        test_endpoint "$API_BASE_URL/depth/segment/$TEST_DEPTH_ID" "POST" "200" "Segment depth map (KMeans)" "{\"method\": \"kmeans\", \"n_clusters\": 5}"
        
        # Test preview segmentation
        test_endpoint "$API_BASE_URL/depth/segmentation_preview/$TEST_DEPTH_ID" "GET" "200" "Preview segmentation"
        
        # Test get mask for segment 1
        test_endpoint "$API_BASE_URL/depth/mask/$TEST_DEPTH_ID/1" "GET" "200" "Get mask for segment 1"
        
        # Test segment depth map using threshold
        test_endpoint "$API_BASE_URL/depth/segment/$TEST_DEPTH_ID" "POST" "200" "Segment depth map (threshold)" "{\"method\": \"threshold\", \"thresholds\": [0.25, 0.5, 0.75]}"
        
        # Test segment depth map using bands
        test_endpoint "$API_BASE_URL/depth/segment/$TEST_DEPTH_ID" "POST" "200" "Segment depth map (bands)" "{\"method\": \"bands\", \"n_bands\": 5}"
        
        # Test export masks
        test_endpoint "$API_BASE_URL/depth/export_masks/$TEST_DEPTH_ID" "POST" "200" "Export masks" "{\"segments\": [1, 2, 3]}"
        
        # Test delete depth map
        test_endpoint "$API_BASE_URL/depth/delete/$TEST_DEPTH_ID" "DELETE" "200" "Delete depth map"
    else
        echo -e "${YELLOW}Skipping depth processing tests due to missing depth ID${NC}"
    fi
    
    # Test Renderer and Depth Integration
    print_header "Testing Renderer and Depth Integration"
    
    # This is a placeholder for testing the integration between renderer and depth processing
    # In a real test, we would create a projection mapping configuration and then use it with a renderer
    echo -e "${YELLOW}Renderer and Depth Integration tests not implemented yet${NC}"
    
    print_header "Tests Completed"
}

# Run the tests
run_tests
