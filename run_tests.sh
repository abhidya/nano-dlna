#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

echo "Running nano-dlna tests..."

# Create test directory if it doesn't exist (harmless if it already does)
mkdir -p tests

# Default pytest arguments for coverage and reporting
PYTEST_ARGS="--cov=web/backend --cov=nanodlna --cov-report=xml --cov-report=html"
# Default pytest execution options (parallel execution)
PYTEST_EXEC_OPTS="-n auto"
# Target for pytest (all tests by default)
PYTEST_TARGET=""

# Check if a specific test path is provided as an argument
if [ -n "$1" ]; then
  TEST_PATH_ARG="$1"
  echo "Running specific test(s)/path: $TEST_PATH_ARG"
  # When running specific tests, disable parallel execution for clearer output/debugging
  PYTEST_EXEC_OPTS=""
  PYTEST_TARGET="$TEST_PATH_ARG"
else
  echo "Running all tests."
  # PYTEST_TARGET remains empty, pytest will discover tests in default locations
fi

# Construct the full pytest command
# Using web/backend/venv/bin/python to ensure correct environment for backend tests
COMMAND="\"$ROOT_DIR/web/backend/venv/bin/python\" -m pytest $PYTEST_EXEC_OPTS $PYTEST_ARGS $PYTEST_TARGET"

echo "Executing: $COMMAND"
# Using eval to correctly handle quotes and arguments in COMMAND
eval $COMMAND

EXIT_CODE=$?

echo "Tests completed."
exit $EXIT_CODE
