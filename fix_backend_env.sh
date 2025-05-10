#!/bin/bash

# Exit on error
set -e

# Store the root directory path
ROOT_DIR="$(pwd)"
echo "Working directory: $ROOT_DIR"

# Navigate to the backend directory
cd "$ROOT_DIR/web/backend"
echo "Changed to backend directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check Python version
echo "Python version:"
python --version

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Verify fastapi is installed
echo "Verifying fastapi installation..."
pip list | grep fastapi

echo "Environment setup complete. You can now run the dashboard with:"
echo "cd $ROOT_DIR && ./run_dashboard.sh"
