# Testing Framework Documentation

## Overview
Comprehensive testing setup with auto-reload, API testing, and fixture support.

## Quick Start

### Run Tests with Auto-Reload
```bash
# Watch all tests
./run_tests_watch.py

# Watch specific test types
./run_tests_watch.py unit
./run_tests_watch.py integration
./run_tests_watch.py live

# Watch specific file
./run_tests_watch.py tests/test_device_manager.py
```

### Run Tests Without Watch
```bash
# All tests
source nanodlna_venv/bin/activate
pytest

# Specific markers
pytest -m unit
pytest -m integration
pytest -m live

# With coverage
pytest --cov --cov-report=html
```

## Test Structure

```
tests/
├── test_api_live.py          # Live API tests with retry logic
├── test_comprehensive.py     # Comprehensive unit tests
├── conftest.py              # Shared fixtures
├── integration/             # Integration tests
├── performance/            # Performance tests
└── mocks/                  # Mock objects
```

## Key Features

### 1. Auto-Reload Testing
- Uses `pytest-watch` for automatic test re-runs
- Configurable in `pytest-watch.ini`
- Ignores common non-test files

### 2. Live API Testing
- `APITestClient` with automatic retry
- Handles service restarts gracefully
- Async test support with proper fixtures

### 3. Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.live` - Live API tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.asyncio` - Async tests

### 4. Fixtures

#### API Testing
```python
@pytest.fixture
async def api_client():
    async with APITestClient() as client:
        yield client

@pytest.fixture
async def clean_devices(api_client):
    # Ensures clean device state
```

#### Mock Objects
```python
@pytest.fixture
def mock_device():
    # Returns mock DLNA device

@pytest.fixture
def mock_config():
    # Returns mock configuration
```

## Configuration

### pyproject.toml
- Test paths and discovery patterns
- Coverage configuration
- Timeout settings
- Async mode configuration

### pytest.ini (existing)
- Basic pytest configuration
- Test markers
- Timeout values

## Writing Tests

### API Tests
```python
@pytest.mark.asyncio
@pytest.mark.live
async def test_api_endpoint(api_client):
    response = await api_client.get("/api/endpoint")
    assert response.status_code == 200
```

### Unit Tests
```python
@pytest.mark.unit
def test_function():
    result = function_under_test()
    assert result == expected
```

### Integration Tests
```python
@pytest.mark.integration
async def test_full_flow(device_manager, streaming_service):
    # Test complete workflow
```

## Troubleshooting

### Service Not Available
- API tests automatically retry connections
- Default retry: 5 attempts with 1s delay
- Configurable in `APITestClient`

### Async Test Issues
- Ensure `@pytest.mark.asyncio` decorator
- Use `async def` for test functions
- Fixtures support async with `async def`

### Coverage Reports
- HTML report: `htmlcov/index.html`
- Terminal report with `--cov-report=term-missing`

## CI/CD Integration

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    source nanodlna_venv/bin/activate
    pytest --cov --cov-report=xml
```