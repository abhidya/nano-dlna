#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

# Run tests using pytest
echo "Running nano-dlna tests..."

# Create test directory if it doesn't exist
mkdir -p tests

# Run the tests using the Python from the virtual environment
"$ROOT_DIR/web/backend/venv/bin/python" -m pytest tests/ -v

echo "Tests completed."
