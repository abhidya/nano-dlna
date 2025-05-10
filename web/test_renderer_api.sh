#!/bin/bash

# Test script for renderer API endpoints

echo "Testing renderer API endpoints..."

# Test listing projectors
echo -e "\n=== Testing /api/renderer/projectors ==="
curl -s http://localhost:8000/api/renderer/projectors | jq .

# Test listing scenes
echo -e "\n=== Testing /api/renderer/scenes ==="
curl -s http://localhost:8000/api/renderer/scenes | jq .

# Test listing active renderers
echo -e "\n=== Testing /api/renderer/list ==="
curl -s http://localhost:8000/api/renderer/list | jq .

echo -e "\nTests completed."
