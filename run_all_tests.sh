#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

echo "Running all nano-dlna tests with improved coverage..."

# Create test directory if it doesn't exist (harmless if it already does)
mkdir -p tests

# Default pytest arguments for coverage and reporting
PYTEST_ARGS="--cov=web/backend --cov=nanodlna --cov-report=xml --cov-report=html --cov-report=term"

# Run the tests
echo "Running backend tests..."
"$ROOT_DIR/web/backend/venv/bin/python" -m pytest tests/ web/backend/tests_backend/ $PYTEST_ARGS

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed successfully!"
    echo "Coverage report generated in htmlcov/ directory"
    echo "Open htmlcov/index.html in your browser to view the report"
else
    echo "Some tests failed. Please check the output above for details."
fi

exit $EXIT_CODE
