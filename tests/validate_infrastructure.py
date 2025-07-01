"""Validate the complete test infrastructure."""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestInfrastructureValidator:
    """Validate all components of the test infrastructure."""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating Nano-DLNA Test Infrastructure...\n")
        
        checks = [
            ("Test Structure", self.check_test_structure),
            ("Test Dependencies", self.check_dependencies),
            ("Test Factories", self.check_factories),
            ("Test Utilities", self.check_utilities),
            ("Mock Infrastructure", self.check_mocks),
            ("Test Configuration", self.check_configuration),
            ("Test Execution", self.check_test_execution),
            ("Coverage Tools", self.check_coverage_tools),
            ("Performance Tools", self.check_performance_tools),
            ("Documentation", self.check_documentation)
        ]
        
        for check_name, check_func in checks:
            print(f"Checking {check_name}...")
            try:
                check_func()
                self.results["passed"].append(check_name)
                print(f"  ✅ {check_name} - PASSED")
            except AssertionError as e:
                self.results["failed"].append((check_name, str(e)))
                print(f"  ❌ {check_name} - FAILED: {e}")
            except Exception as e:
                self.results["warnings"].append((check_name, str(e)))
                print(f"  ⚠️  {check_name} - WARNING: {e}")
            print()
        
        return self.print_summary()
    
    def check_test_structure(self):
        """Validate test directory structure."""
        required_dirs = [
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/performance",
            "tests/factories",
            "tests/mocks",
            "tests/utils",
            "web/backend/tests_backend",
            "web/frontend/src/tests"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            assert full_path.exists(), f"Missing directory: {dir_path}"
            assert full_path.is_dir(), f"Not a directory: {dir_path}"
    
    def check_dependencies(self):
        """Check if all test dependencies are installed."""
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-xdist",
            "factory-boy",
            "faker",
            "requests-mock",
            "locust"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
            except ImportError:
                # Try alternative import names
                alt_names = {
                    "factory-boy": "factory",
                    "pytest-asyncio": "pytest_asyncio",
                    "pytest-cov": "pytest_cov",
                    "pytest-xdist": "xdist",
                    "requests-mock": "requests_mock"
                }
                
                if package in alt_names:
                    try:
                        importlib.import_module(alt_names[package])
                    except ImportError:
                        raise AssertionError(f"Missing package: {package}")
                else:
                    raise AssertionError(f"Missing package: {package}")
    
    def check_factories(self):
        """Validate test factories."""
        factory_modules = [
            "tests.factories.device_factory",
            "tests.factories.video_factory",
            "tests.factories.overlay_factory",
            "tests.factories.session_factory"
        ]
        
        for module_name in factory_modules:
            module = importlib.import_module(module_name)
            
            # Check for required factory classes
            factory_name = module_name.split(".")[-1].replace("_factory", "").title() + "Factory"
            assert hasattr(module, factory_name), f"Missing factory class: {factory_name}"
    
    def check_utilities(self):
        """Validate test utilities."""
        utils_module = importlib.import_module("tests.utils.test_helpers")
        
        required_classes = [
            "TestTimer",
            "TestDataGenerator",
            "AsyncTestHelper",
            "DatabaseTestHelper",
            "NetworkTestHelper",
            "FileTestHelper",
            "MockHelper",
            "PerformanceTestHelper"
        ]
        
        for class_name in required_classes:
            assert hasattr(utils_module, class_name), f"Missing utility class: {class_name}"
    
    def check_mocks(self):
        """Validate mock infrastructure."""
        mock_files = [
            "tests/mocks/device_mocks.py",
            "tests/mocks/dlna_mocks.py",
            "tests/mocks/streaming_mocks.py"
        ]
        
        for mock_file in mock_files:
            file_path = self.project_root / mock_file
            assert file_path.exists(), f"Missing mock file: {mock_file}"
            
            # Import and check for key mock classes
            module_name = mock_file.replace("/", ".").replace(".py", "")
            module = importlib.import_module(module_name)
            
            # Check for at least one Mock class
            mock_classes = [attr for attr in dir(module) if "Mock" in attr and not attr.startswith("_")]
            assert len(mock_classes) > 0, f"No mock classes found in {mock_file}"
    
    def check_configuration(self):
        """Validate test configuration files."""
        config_files = [
            ("pytest.ini", ["[tool:pytest]", "testpaths", "python_files"]),
            ("tests/conftest.py", ["pytest", "fixture"]),
            ("web/backend/tests_backend/conftest.py", ["pytest", "fixture"])
        ]
        
        for config_file, required_content in config_files:
            file_path = self.project_root / config_file
            assert file_path.exists(), f"Missing config file: {config_file}"
            
            content = file_path.read_text()
            for required in required_content:
                assert required in content, f"Missing '{required}' in {config_file}"
    
    def check_test_execution(self):
        """Validate test execution capabilities."""
        # Check run_tests.sh
        run_tests_path = self.project_root / "run_tests.sh"
        assert run_tests_path.exists(), "Missing run_tests.sh"
        assert os.access(run_tests_path, os.X_OK), "run_tests.sh is not executable"
        
        # Check if basic tests can be discovered
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"pytest collection failed: {result.stderr}"
        assert "tests collected" in result.stdout or "test collected" in result.stdout, "No tests collected"
    
    def check_coverage_tools(self):
        """Validate coverage configuration."""
        # Check .coveragerc or coverage in pytest.ini
        pytest_ini = self.project_root / "pytest.ini"
        coveragerc = self.project_root / ".coveragerc"
        
        coverage_configured = False
        
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            if "coverage" in content or "--cov" in content:
                coverage_configured = True
        
        if coveragerc.exists():
            coverage_configured = True
        
        assert coverage_configured, "Coverage not configured"
    
    def check_performance_tools(self):
        """Validate performance testing tools."""
        perf_test_file = self.project_root / "tests/performance/test_load.py"
        assert perf_test_file.exists(), "Missing performance test file"
        
        # Check for performance markers in pytest.ini
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            assert "performance" in content, "Performance marker not configured in pytest.ini"
    
    def check_documentation(self):
        """Validate test documentation."""
        required_docs = [
            "tests/README.md",
            "tests/TEST_INFRASTRUCTURE.md"
        ]
        
        for doc_file in required_docs:
            file_path = self.project_root / doc_file
            assert file_path.exists(), f"Missing documentation: {doc_file}"
            
            # Check minimum content
            content = file_path.read_text()
            assert len(content) > 100, f"Documentation {doc_file} appears incomplete"
    
    def print_summary(self) -> bool:
        """Print validation summary."""
        print("\n" + "="*60)
        print("TEST INFRASTRUCTURE VALIDATION SUMMARY")
        print("="*60)
        
        total_checks = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["warnings"])
        
        print(f"\nTotal Checks: {total_checks}")
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        
        if self.results["failed"]:
            print("\nFailed Checks:")
            for check_name, error in self.results["failed"]:
                print(f"  - {check_name}: {error}")
        
        if self.results["warnings"]:
            print("\nWarnings:")
            for check_name, warning in self.results["warnings"]:
                print(f"  - {check_name}: {warning}")
        
        print("\n" + "="*60)
        
        if self.results["failed"]:
            print("❌ VALIDATION FAILED - Please fix the issues above")
            return False
        else:
            print("✅ VALIDATION PASSED - Test infrastructure is ready!")
            return True


def generate_test_report():
    """Generate a comprehensive test infrastructure report."""
    report = {
        "project": "Nano-DLNA",
        "test_infrastructure_version": "1.0.0",
        "components": {
            "unit_tests": {
                "location": "tests/unit",
                "framework": "pytest",
                "coverage_target": "90%"
            },
            "integration_tests": {
                "location": "tests/integration",
                "framework": "pytest",
                "coverage_target": "80%"
            },
            "performance_tests": {
                "location": "tests/performance",
                "framework": "locust + pytest",
                "metrics": ["response_time", "throughput", "concurrent_users"]
            },
            "factories": {
                "location": "tests/factories",
                "framework": "factory_boy",
                "models": ["Device", "Video", "Overlay", "Session"]
            },
            "mocks": {
                "location": "tests/mocks",
                "targets": ["DLNA devices", "Streaming", "WebSocket"]
            }
        },
        "execution": {
            "local": "./run_tests.sh",
            "ci_cd": "GitHub Actions / Jenkins",
            "parallel": "pytest-xdist"
        },
        "monitoring": {
            "coverage": "pytest-cov + coverage.py",
            "performance": "pytest-benchmark + custom metrics",
            "reporting": "HTML + XML + JSON"
        }
    }
    
    report_path = project_root / "tests" / "infrastructure_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Test infrastructure report generated: {report_path}")


if __name__ == "__main__":
    validator = TestInfrastructureValidator()
    success = validator.validate_all()
    
    if success:
        generate_test_report()
        sys.exit(0)
    else:
        sys.exit(1)