#!/usr/bin/env python3
"""
Script to run backend tests with coverage.
"""
import os
import sys
import pytest
import subprocess
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_backend_tests():
    """Run all backend tests with coverage."""
    print("Running backend tests with coverage...")
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Make sure the tests_backend directory exists
    tests_dir = backend_dir / "tests_backend"
    if not tests_dir.exists():
        tests_dir.mkdir(exist_ok=True)
    
    # Run pytest with coverage
    # -v: verbose
    # --cov=.: coverage for all modules in the current directory
    # --cov-report=term: report coverage in the terminal
    # --cov-report=html: create HTML coverage report
    result = pytest.main([
        "-v",
        "--cov=.",
        "--cov-report=term",
        "--cov-report=html",
        str(tests_dir)
    ])
    
    # Save the coverage report to a file
    coverage_report_path = backend_dir.parent.parent / "backend_coverage_report.txt"
    
    try:
        # Run pytest with coverage and save output to a file
        print(f"Saving coverage report to {coverage_report_path}...")
        with open(coverage_report_path, "w") as f:
            subprocess.run([
                "python", "-m", "pytest",
                "-v",
                "--cov=.",
                "--cov-report=term",
                str(tests_dir)
            ], stdout=f, stderr=subprocess.STDOUT, check=False)
    
        print(f"Coverage report saved to {coverage_report_path}")
    except Exception as e:
        print(f"Error saving coverage report: {e}")
    
    return result == 0


if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1) 