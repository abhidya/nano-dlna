#!/usr/bin/env python3
"""
Run tests with auto-reload on file changes
Supports running specific test modules or all tests
"""
import subprocess
import sys
import os

def main():
    # Activate virtual environment
    venv_path = os.path.join(os.path.dirname(__file__), "venv", "bin", "activate")
    
    # Build pytest-watch command
    cmd = ["pytest-watch"]
    
    # Add specific arguments if provided
    if len(sys.argv) > 1:
        if sys.argv[1] == "live":
            # Run live API tests
            cmd.extend(["--", "-m", "live", "tests/test_api_live.py"])
        elif sys.argv[1] == "unit":
            # Run unit tests only
            cmd.extend(["--", "-m", "unit"])
        elif sys.argv[1] == "integration":
            # Run integration tests
            cmd.extend(["--", "-m", "integration"])
        elif sys.argv[1] == "all":
            # Run all tests
            cmd.extend(["--", "-v"])
        else:
            # Run specific test file/pattern
            cmd.extend(["--", sys.argv[1]])
    else:
        # Default: run all tests with coverage
        cmd.extend(["--", "--cov", "--cov-report=term-missing"])
    
    print(f"Running: {' '.join(cmd)}")
    print("Press Ctrl+C to stop watching\n")
    
    try:
        # Run pytest-watch
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopped watching tests")
        sys.exit(0)

if __name__ == "__main__":
    main()