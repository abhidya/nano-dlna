#!/bin/bash

# Test memory bank initialization
echo "Testing memory bank MCP server..."

# Test 1: Initialize memory bank
echo "Test 1: Initializing memory bank for nano-dlna..."
claude -p "Create a memory bank for the nano-dlna project. Document that the main entry point is web/backend/main.py and streaming logic is in web/backend/core/streaming_service.py" --print

# Test 2: Query the memory
echo -e "\n\nTest 2: Querying memory bank..."
claude -p "What do you remember about this project's structure?" --print

# Test 3: Add more memory
echo -e "\n\nTest 3: Adding more to memory bank..."
claude -p "Remember: This project uses FastAPI for the web backend, implements DLNA/UPnP for media streaming, and has a React frontend in web/frontend/" --print