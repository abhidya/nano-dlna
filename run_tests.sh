#!/bin/bash

# Run tests using pytest
echo "Running nano-dlna tests..."

# Create test directory if it doesn't exist
mkdir -p tests

# Run the tests with a timeout
python -m pytest tests/ -v --timeout=10

echo "Tests completed." 