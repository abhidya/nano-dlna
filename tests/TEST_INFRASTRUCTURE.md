# Nano-DLNA Test Infrastructure

## Overview

This document describes the comprehensive test infrastructure for the Nano-DLNA project, covering all testing aspects from unit tests to E2E tests, performance testing, and security validation.

## Test Architecture

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for component interactions
├── e2e/                    # End-to-end tests for complete workflows
├── performance/            # Performance and load tests
├── security/               # Security vulnerability tests
├── contracts/              # API contract tests
├── fixtures/               # Shared test fixtures and data
├── factories/              # Test data factories
├── utils/                  # Test utilities and helpers
└── reports/               # Test execution reports

web/
├── backend/tests_backend/  # Backend-specific tests
└── frontend/src/tests/     # Frontend component tests
```

## Test Categories

### 1. Unit Tests
- **Purpose**: Test individual functions and classes in isolation
- **Markers**: `@pytest.mark.unit`
- **Coverage Target**: 90%
- **Key Areas**:
  - Core DLNA operations
  - Device management logic
  - Streaming service functions
  - Data models and schemas

### 2. Integration Tests
- **Purpose**: Test component interactions and data flow
- **Markers**: `@pytest.mark.integration`
- **Coverage Target**: 80%
- **Key Areas**:
  - Database operations
  - API endpoint functionality
  - Service layer interactions
  - WebSocket communications

### 3. End-to-End Tests
- **Purpose**: Test complete user workflows
- **Markers**: `@pytest.mark.e2e`
- **Framework**: Playwright/Cypress
- **Key Scenarios**:
  - Device discovery and connection
  - Video playback workflow
  - Multi-device synchronization
  - Overlay configuration

### 4. Performance Tests
- **Purpose**: Validate system performance under load
- **Framework**: Locust/pytest-benchmark
- **Key Metrics**:
  - API response times
  - Streaming throughput
  - Concurrent device handling
  - Memory usage patterns

### 5. Security Tests
- **Purpose**: Identify security vulnerabilities
- **Tools**: bandit, safety, OWASP ZAP
- **Key Areas**:
  - Input validation
  - Authentication/authorization
  - SQL injection prevention
  - XSS protection

## Test Execution Strategy

### Local Development
```bash
# Run all tests
./run_tests.sh

# Run specific test categories
./run_tests.sh --unit
./run_tests.sh --integration
./run_tests.sh --e2e

# Run with coverage
./run_tests.sh --coverage

# Run in watch mode
pytest-watch -n auto
```

### CI/CD Pipeline
```yaml
test-pipeline:
  - lint-and-format
  - unit-tests
  - integration-tests
  - security-scan
  - performance-tests
  - e2e-tests
  - coverage-report
```

## Test Data Management

### Test Fixtures
- Database fixtures with known state
- Mock device configurations
- Sample video files for streaming
- WebSocket connection mocks

### Data Factories
```python
# Example factory usage
device = DeviceFactory.create(
    type="dlna",
    status="connected",
    capabilities=["play", "pause", "seek"]
)
```

### Test Database
- Isolated test database per test run
- Automatic cleanup after tests
- Seeded with representative data
- Transaction rollback for isolation

## Mocking Strategy

### Core Mocks
- `MockDLNADevice`: Simulates DLNA device behavior
- `MockStreamingService`: Simulates video streaming
- `MockWebSocket`: Simulates real-time communications
- `MockDiscoveryService`: Simulates device discovery

### External Service Mocks
- Network requests (requests-mock)
- File system operations
- System time and delays
- External API calls

## Coverage Requirements

### Minimum Coverage Thresholds
- Overall: 85%
- Core modules: 90%
- API endpoints: 95%
- Critical paths: 100%

### Coverage Reporting
- HTML reports in `htmlcov/`
- XML reports for CI integration
- Coverage badges in README
- Historical coverage tracking

## Performance Benchmarks

### Response Time Targets
- API endpoints: < 200ms (p95)
- Device discovery: < 5s
- Video start: < 3s
- WebSocket latency: < 50ms

### Load Testing Scenarios
- 10 concurrent devices
- 100 API requests/second
- 1GB video streaming
- 24-hour stability test

## Security Testing

### Automated Scans
- Dependency vulnerability scanning
- Static code analysis
- Dynamic security testing
- Container image scanning

### Manual Testing
- Penetration testing checklist
- Authentication bypass attempts
- Data validation testing
- Session management review

## Test Monitoring

### Metrics Collection
- Test execution time
- Flaky test detection
- Coverage trends
- Performance regression

### Reporting
- Daily test summary emails
- Slack notifications for failures
- Dashboard with test metrics
- Historical trend analysis

## Best Practices

### Test Writing Guidelines
1. Follow AAA pattern (Arrange, Act, Assert)
2. One assertion per test when possible
3. Descriptive test names
4. Isolated and independent tests
5. Use fixtures for common setup

### Test Maintenance
1. Regular test review and cleanup
2. Update tests with code changes
3. Fix flaky tests immediately
4. Maintain test documentation
5. Review test performance

### Test Review Checklist
- [ ] Tests cover all code paths
- [ ] Edge cases are tested
- [ ] Error conditions are verified
- [ ] Tests are maintainable
- [ ] Performance impact is acceptable

## Troubleshooting

### Common Issues
1. **Flaky Tests**: Use retry mechanisms and proper waits
2. **Slow Tests**: Parallelize and optimize fixtures
3. **Database Issues**: Ensure proper cleanup
4. **Network Tests**: Use appropriate mocks
5. **Coverage Gaps**: Add targeted tests

### Debug Commands
```bash
# Run with debugging
pytest -vvs tests/unit/test_device.py::test_specific

# Run with pdb on failure
pytest --pdb

# Show test execution order
pytest --collect-only

# Profile test execution
pytest --profile
```

## Future Enhancements

### Planned Improvements
1. Visual regression testing
2. Accessibility testing automation
3. Chaos engineering tests
4. API fuzzing
5. Mobile app testing
6. Cross-browser compatibility
7. Internationalization testing
8. Performance profiling integration

### Research Areas
1. AI-powered test generation
2. Self-healing tests
3. Predictive test selection
4. Test impact analysis
5. Automated test maintenance