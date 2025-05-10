#!/usr/bin/env python3
"""
Script to run all tests for the nano-dlna project.
This will run unit tests for all components: core nanodlna, backend, and frontend.
"""

import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def discover_and_run_tests():
    """Discover and run all tests in the tests directory"""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Discover tests in the tests directory
    test_dir = Path(__file__).parent / "tests"
    test_suite = loader.discover(str(test_dir), pattern="test_*.py")
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(test_suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    print(f"Running tests for nano-dlna in {os.path.dirname(os.path.abspath(__file__))}")
    
    # Run tests and set exit code
    success = discover_and_run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 