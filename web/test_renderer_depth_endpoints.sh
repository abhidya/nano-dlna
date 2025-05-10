#!/bin/bash

# Exit on error
set -e

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    echo -e "${YELLOW}Testing ${method} ${endpoint} - ${description}${NC}"
    
    # Build the curl command
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o response.txt -w "%{http_code}" -X ${method} http://localhost:8000${endpoint})
    else
        if [ -z "$data" ]; then
            response=$(curl -s -o response.txt -w "%{http_code}" -X ${method} http://localhost:8000${endpoint})
        else
            response=$(curl -s -o response.txt -w "%{http_code}" -X ${method} -H "Content-Type: application/json" -d "${data}" http://localhost:8000${endpoint})
        fi
    fi
    
    # Check if the status code matches the expected status
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status code ${response} matches expected ${expected_status}${NC}"
        echo -e "${GREEN}✓ Response:${NC}"
        cat response.txt | jq . 2>/dev/null || cat response.txt
        echo ""
    else
        echo -e "${RED}✗ Status code ${response} does not match expected ${expected_status}${NC}"
        echo -e "${RED}✗ Response:${NC}"
        cat response.txt
        echo ""
    fi
}

# Function to test the proxy
test_proxy_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    echo -e "${YELLOW}Testing PROXY ${method} ${endpoint} - ${description}${NC}"
    
    # Build the curl command
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o proxy_response.txt -w "%{http_code}" -X ${method} http://localhost:3000${endpoint})
    else
        if [ -z "$data" ]; then
            response=$(curl -s -o proxy_response.txt -w "%{http_code}" -X ${method} http://localhost:3000${endpoint})
        else
            response=$(curl -s -o proxy_response.txt -w "%{http_code}" -X ${method} -H "Content-Type: application/json" -d "${data}" http://localhost:3000${endpoint})
        fi
    fi
    
    # Check if the status code matches the expected status
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Status code ${response} matches expected ${expected_status}${NC}"
        echo -e "${GREEN}✓ Response:${NC}"
        cat proxy_response.txt | jq . 2>/dev/null || cat proxy_response.txt
        echo ""
    else
        echo -e "${RED}✗ Status code ${response} does not match expected ${expected_status}${NC}"
        echo -e "${RED}✗ Response:${NC}"
        cat proxy_response.txt
        echo ""
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. JSON responses will not be formatted.${NC}"
fi

# Check if the backend is running
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo -e "${RED}Error: Backend is not running. Please start the backend first.${NC}"
    exit 1
fi

# Check if the frontend is running
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo -e "${RED}Error: Frontend is not running. Please start the frontend first.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Testing Renderer API Endpoints ===${NC}"

# Test renderer endpoints
test_endpoint "GET" "/api/renderer/list" 200 "List all active renderers"
test_endpoint "GET" "/api/renderer/projectors" 200 "List all available projectors"
test_endpoint "GET" "/api/renderer/scenes" 200 "List all available scenes"

# Test renderer status endpoint with a projector ID
# Note: Replace 'proj-1' with an actual projector ID from your system
test_endpoint "GET" "/api/renderer/status/proj-hccast" 200 "Get renderer status for a projector"

# Test starting a renderer
# Note: Replace 'test-scene' and 'proj-1' with actual scene and projector IDs from your system
test_endpoint "POST" "/api/renderer/start" 200 "Start a renderer" '{"scene": "overlay-frontdoor", "projector": "proj-hccast", "options": {}}'

# Test stopping a renderer
# Note: Replace 'proj-1' with an actual projector ID from your system
test_endpoint "POST" "/api/renderer/stop" 200 "Stop a renderer" '{"projector": "proj-hccast"}'

# Test starting a projector with its default scene
# Note: Replace 'proj-1' with an actual projector ID from your system
test_endpoint "POST" "/api/renderer/start_projector?projector_id=proj-hccast" 200 "Start a projector with its default scene"

echo -e "${GREEN}=== Testing Depth Processing API Endpoints ===${NC}"

# Test depth processing endpoints
# Note: The depth map upload endpoint requires a file upload, which is not easily testable with curl
# We'll test the other endpoints that don't require a file upload

# Test getting a preview of a non-existent depth map (should return 404)
test_endpoint "GET" "/api/depth/preview/nonexistent-uuid" 404 "Get preview of nonexistent depth map"

# Test segmenting a non-existent depth map (should return 404)
test_endpoint "POST" "/api/depth/segment/nonexistent-uuid" 404 "Segment nonexistent depth map" '{"method": "kmeans", "n_clusters": 5}'

# Test getting a segmentation preview of a non-existent depth map (should return 404)
test_endpoint "GET" "/api/depth/segmentation_preview/nonexistent-uuid" 404 "Get segmentation preview of nonexistent depth map"

# Test getting a mask for a non-existent depth map (should return 404)
test_endpoint "GET" "/api/depth/mask/nonexistent-uuid/1" 404 "Get mask for nonexistent depth map"

# Test deleting a non-existent depth map (should return 404)
test_endpoint "DELETE" "/api/depth/nonexistent-uuid" 404 "Delete nonexistent depth map"

echo -e "${GREEN}=== Testing Renderer API Endpoints through Proxy ===${NC}"

# Test renderer endpoints through proxy
test_proxy_endpoint "GET" "/api/renderer/list" 200 "List all active renderers through proxy"
test_proxy_endpoint "GET" "/api/renderer/projectors" 200 "List all available projectors through proxy"
test_proxy_endpoint "GET" "/api/renderer/scenes" 200 "List all available scenes through proxy"

# Test renderer status endpoint with a projector ID through proxy
# Note: Replace 'proj-1' with an actual projector ID from your system
test_proxy_endpoint "GET" "/api/renderer/status/proj-hccast" 200 "Get renderer status for a projector through proxy"

echo -e "${GREEN}=== Testing Depth Processing API Endpoints through Proxy ===${NC}"

# Test depth processing endpoints through proxy
# Note: The depth map upload endpoint requires a file upload, which is not easily testable with curl
# We'll test the other endpoints that don't require a file upload

# Test getting a preview of a non-existent depth map through proxy (should return 404)
test_proxy_endpoint "GET" "/api/depth/preview/nonexistent-uuid" 404 "Get preview of nonexistent depth map through proxy"

# Test segmenting a non-existent depth map through proxy (should return 404)
test_proxy_endpoint "POST" "/api/depth/segment/nonexistent-uuid" 404 "Segment nonexistent depth map through proxy" '{"method": "kmeans", "n_clusters": 5}'

# Test getting a segmentation preview of a non-existent depth map through proxy (should return 404)
test_proxy_endpoint "GET" "/api/depth/segmentation_preview/nonexistent-uuid" 404 "Get segmentation preview of nonexistent depth map through proxy"

# Test getting a mask for a non-existent depth map through proxy (should return 404)
test_proxy_endpoint "GET" "/api/depth/mask/nonexistent-uuid/1" 404 "Get mask for nonexistent depth map through proxy"

# Test deleting a non-existent depth map through proxy (should return 404)
test_proxy_endpoint "DELETE" "/api/depth/nonexistent-uuid" 404 "Delete nonexistent depth map through proxy"

echo -e "${GREEN}=== All tests completed ===${NC}"

# Clean up
rm -f response.txt proxy_response.txt

exit 0
