#!/usr/bin/env python3
"""Test infrastructure manager for the Nano-DLNA project."""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}\n")

def run_validation():
    """Run the test infrastructure validation."""
    print_header("NANO-DLNA TEST INFRASTRUCTURE")
    
    validation_script = Path(project_root) / "tests" / "validate_infrastructure.py"
    if validation_script.exists():
        print("Running infrastructure validation...\n")
        result = subprocess.run([sys.executable, str(validation_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode == 0
    else:
        print("⚠️  Validation script not found!")
        return False

def run_quick_tests():
    """Run a quick subset of tests to verify setup."""
    print_header("QUICK TEST VERIFICATION")
    
    test_commands = [
        ("Unit Tests", ["pytest", "-v", "-k", "test_dlna_device", "--tb=short"]),
        ("Integration Tests", ["pytest", "-v", "-k", "test_api_contracts", "--tb=short"]),
        ("Factory Tests", ["pytest", "-v", "tests/test_infrastructure.py", "--tb=short"])
    ]
    
    for test_name, command in test_commands:
        print(f"\nRunning {test_name}...")
        result = subprocess.run(command, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
            print(f"   Output: {result.stdout[-200:] if result.stdout else 'No output'}")
            print(f"   Error: {result.stderr[-200:] if result.stderr else 'No error'}")

def show_test_commands():
    """Show available test commands."""
    print_header("AVAILABLE TEST COMMANDS")
    
    commands = [
        ("Run all tests", "./run_tests.sh"),
        ("Run unit tests only", "./run_tests.sh --unit"),
        ("Run integration tests", "./run_tests.sh --integration"),
        ("Run with coverage", "./run_tests.sh --coverage"),
        ("Run performance tests", "pytest -m performance tests/performance/"),
        ("Run specific test file", "pytest tests/unit/test_dlna_device.py -v"),
        ("Run tests in parallel", "pytest -n auto"),
        ("Run with debugging", "pytest -vvs --pdb"),
        ("Generate coverage report", "pytest --cov=web --cov-report=html"),
        ("Run load tests", "locust -f tests/performance/test_load.py")
    ]
    
    for desc, cmd in commands:
        print(f"{desc:.<40} {cmd}")

def main():
    """Run the test infrastructure."""
    print("\n🚀 Nano-DLNA Test Infrastructure Manager\n")
    
    # Run validation
    validation_passed = run_validation()
    
    if validation_passed:
        # Show available commands
        show_test_commands()
        
        # Optionally run quick tests
        response = input("\nRun quick test verification? (y/N): ").strip().lower()
        if response == 'y':
            run_quick_tests()
    else:
        print("\n❌ Please fix validation issues before running tests.")
        sys.exit(1)
    
    print("\n✨ Test infrastructure is ready for use!")
    print("\nFor full documentation, see: tests/TEST_INFRASTRUCTURE.md")

if __name__ == "__main__":
    main()