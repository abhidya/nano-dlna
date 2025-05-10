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

echo -e "${GREEN}=== Testing Backend API Endpoints ===${NC}"

# Test health endpoint
test_endpoint "GET" "/health" 200 "Health check"

# Test device endpoints
test_endpoint "GET" "/api/devices/" 200 "Get all devices"
test_endpoint "GET" "/api/devices/discover" 200 "Discover devices"

# Test video endpoints
test_endpoint "GET" "/api/videos/" 200 "Get all videos"

# Test renderer endpoints
test_endpoint "GET" "/api/renderer/list" 200 "List all active renderers"
test_endpoint "GET" "/api/renderer/projectors" 200 "List all available projectors"
test_endpoint "GET" "/api/renderer/scenes" 200 "List all available scenes"

# Test depth processing endpoints
test_endpoint "GET" "/api/depth/preview/nonexistent-uuid" 404 "Get preview of nonexistent depth map"

# Test streaming endpoints
test_endpoint "GET" "/api/streaming/" 200 "Get streaming statistics"
test_endpoint "GET" "/api/streaming/sessions" 200 "Get all streaming sessions"
test_endpoint "GET" "/api/streaming/health" 200 "Get streaming health status"

echo -e "${GREEN}=== Testing Frontend Proxy ===${NC}"

# Test proxy endpoints
test_proxy_endpoint "GET" "/api/devices/" 200 "Get all devices through proxy"
test_proxy_endpoint "GET" "/api/devices/discover" 200 "Discover devices through proxy"
test_proxy_endpoint "GET" "/api/videos/" 200 "Get all videos through proxy"
test_proxy_endpoint "GET" "/api/renderer/list" 200 "List all active renderers through proxy"
test_proxy_endpoint "GET" "/api/renderer/projectors" 200 "List all available projectors through proxy"
test_proxy_endpoint "GET" "/api/renderer/scenes" 200 "List all available scenes through proxy"
test_proxy_endpoint "GET" "/api/depth/preview/nonexistent-uuid" 404 "Get preview of nonexistent depth map through proxy"
test_proxy_endpoint "GET" "/api/streaming/" 200 "Get streaming statistics through proxy"
test_proxy_endpoint "GET" "/api/streaming/sessions" 200 "Get all streaming sessions through proxy"
test_proxy_endpoint "GET" "/api/streaming/health" 200 "Get streaming health status through proxy"

echo -e "${GREEN}=== All tests completed ===${NC}"

# Clean up
rm -f response.txt proxy_response.txt

exit 0
