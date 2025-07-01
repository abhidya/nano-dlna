# nano-dlna Test Architecture

## Overview

The nano-dlna testing infrastructure is designed to provide comprehensive test coverage while maintaining fast execution and good developer experience.

## Directory Structure

```
tests/                          # Core functionality and integration tests
├── mocks/                      # Centralized mock modules
│   ├── __init__.py
│   ├── device_mocks.py        # Mock device classes
│   ├── dlna_mocks.py          # Mock DLNA functions
│   └── streaming_mocks.py     # Mock streaming services
├── conftest.py                # Pytest configuration and fixtures
├── test_utils.py              # Shared test utilities
├── requirements.txt           # Test dependencies
└── test_*.py                  # Test modules

web/backend/tests_backend/      # Backend API unit tests
├── conftest.py                # Backend-specific fixtures
└── test_*.py                  # Backend test modules
```

## Running Tests

### All Tests
```bash
./run_tests.sh
```

### Specific Test Suites
```bash
# Run only backend tests
./run_tests.sh --backend

# Run only core tests
./run_tests.sh --core

# Run specific test file
./run_tests.sh tests/test_dlna_device.py

# Run without parallel execution (for debugging)
./run_tests.sh --no-parallel
```

### Test Categories
```bash
# Run only unit tests
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Run only end-to-end tests
./run_tests.sh --e2e
```

## Writing Tests

### Using Mocks

Import mocks from the centralized location:

```python
from tests.mocks import MockDevice, MockDLNADevice, mock_discover_devices
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

```python
def test_with_mock_discovery(mock_dlna_discovery):
    devices = mock_dlna_discovery()
    assert len(devices) == 2

def test_with_temp_dir(temp_test_dir):
    # temp_test_dir is automatically cleaned up
    test_file = os.path.join(temp_test_dir, "test.mp4")
```

### Test Markers

Mark tests with appropriate categories:

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration
def test_database_operation(test_db):
    pass

@pytest.mark.network
def test_dlna_discovery():
    pass
```

## Common Issues and Solutions

### SQLAlchemy "Multiple classes found" Error

This is handled automatically by the conftest.py files which clear metadata before tests run.

### Network Tests Failing

Use the provided mocks to avoid actual network calls:

```python
from tests.mocks.dlna_mocks import mock_discover_devices

@patch('nanodlna.dlna._discover_upnp_devices', mock_discover_devices)
def test_discovery():
    # Test without actual network calls
    pass
```

### Twisted Reactor Issues

The `cleanup_twisted` fixture automatically cleans up Twisted servers after tests.

## Best Practices

1. **Use mocks for external dependencies** - Network, file system, databases
2. **Keep tests isolated** - Each test should be independent
3. **Use appropriate markers** - Help with test organization and CI/CD
4. **Clean up resources** - Use fixtures and context managers
5. **Test both success and failure cases** - Ensure robust error handling

## CI/CD Integration

The test suite is designed for CI/CD compatibility:

- Tests can run in parallel (`pytest-xdist`)
- All tests use in-memory databases
- No network access required (mocks provided)
- Clear exit codes and reporting