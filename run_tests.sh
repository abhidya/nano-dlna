#!/bin/bash

# Store the root directory path
ROOT_DIR="$(pwd)"

echo "Running nano-dlna tests..."

# Create test directory if it doesn't exist (harmless if it already does)
mkdir -p tests

# Export test environment variables
export PYTEST_CURRENT_TEST=true
export DATABASE_URL="sqlite:///:memory:"

# Default pytest arguments for coverage and reporting
PYTEST_ARGS="--cov=web/backend --cov=nanodlna --cov-report=xml --cov-report=html"
# Default pytest execution options (parallel execution)
PYTEST_EXEC_OPTS="-n auto"
# Target for pytest (all tests by default)
PYTEST_TARGET=""
# Default test type (all)
TEST_TYPE="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --unit)
      TEST_TYPE="unit"
      PYTEST_ARGS="$PYTEST_ARGS -m unit"
      shift
      ;;
    --integration)
      TEST_TYPE="integration"
      PYTEST_ARGS="$PYTEST_ARGS -m integration"
      shift
      ;;
    --e2e)
      TEST_TYPE="e2e"
      PYTEST_ARGS="$PYTEST_ARGS -m e2e"
      shift
      ;;
    --no-parallel)
      PYTEST_EXEC_OPTS=""
      shift
      ;;
    --backend)
      PYTEST_TARGET="web/backend/tests_backend"
      shift
      ;;
    --core)
      PYTEST_TARGET="tests"
      shift
      ;;
    *)
      # Assume it's a specific test path
      TEST_PATH_ARG="$1"
      echo "Running specific test(s)/path: $TEST_PATH_ARG"
      # When running specific tests, disable parallel execution for clearer output/debugging
      PYTEST_EXEC_OPTS=""
      PYTEST_TARGET="$TEST_PATH_ARG"
      shift
      ;;
  esac
done

if [ "$TEST_TYPE" != "all" ]; then
  echo "Running $TEST_TYPE tests only."
fi

# Construct the full pytest command
# Using web/backend/venv/bin/python to ensure correct environment for backend tests
COMMAND="\"$ROOT_DIR/web/backend/venv/bin/python\" -m pytest $PYTEST_EXEC_OPTS $PYTEST_ARGS $PYTEST_TARGET"

echo "Executing: $COMMAND"
# Using eval to correctly handle quotes and arguments in COMMAND
eval $COMMAND

EXIT_CODE=$?

echo "Tests completed with exit code: $EXIT_CODE"

# Clean up any temporary test files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

exit $EXIT_CODE
