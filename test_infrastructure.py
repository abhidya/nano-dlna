#!/usr/bin/env python3
"""
Quick test script to verify the test infrastructure is working correctly
"""
import subprocess
import sys
import os

def run_test(test_command, description):
    """Run a test command and report results"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {test_command}")
    print(f"{'='*60}")
    
    result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ {description} - PASSED")
        # Show summary of test results
        if "passed" in result.stdout:
            for line in result.stdout.split('\n'):
                if " passed" in line and ("warning" in line or "failed" in line):
                    print(f"  {line.strip()}")
    else:
        print(f"✗ {description} - FAILED")
        # Show error summary
        if result.stderr:
            print("\nError output:")
            print(result.stderr[:500])  # First 500 chars of error
    
    return result.returncode == 0

def main():
    """Run a series of tests to verify infrastructure"""
    print("Testing nano-dlna test infrastructure...")
    
    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Define tests to run
    tests = [
        ("./run_tests.sh tests/test_nanodlna_core.py", "Core nanodlna functionality"),
        ("./run_tests.sh tests/test_dlna_device.py", "DLNA device tests with mocks"),
        ("./run_tests.sh --backend test_app", "Backend API tests"),
        ("./run_tests.sh --no-parallel tests/test_import_errors.py::TestImportErrors::test_nanodlna_imports", "Import test (single test)"),
    ]
    
    passed = 0
    failed = 0
    
    for test_cmd, description in tests:
        if run_test(test_cmd, description):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Infrastructure Summary:")
    print(f"  Tests Run: {len(tests)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}")
    
    if failed == 0:
        print("\n✓ All infrastructure tests passed! The test setup is working correctly.")
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()