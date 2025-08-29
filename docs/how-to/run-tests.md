# Run Tests

This guide covers how to run tests for aider-lint-fixer in various scenarios.

## Quick Start

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest
```

### Run with Coverage

```bash
pytest --cov=aider_lint_fixer --cov-report=html
```

## Test Categories

### Unit Tests

Test individual components:

```bash
pytest tests/unit/
```

### Integration Tests

Test component interactions:

```bash
pytest tests/integration/
```

### End-to-End Tests

Test full workflows:

```bash
pytest tests/e2e/
```

## Test Specific Components

### Linter Tests

```bash
pytest tests/test_lint_runner.py
```

### Configuration Tests

```bash
pytest tests/test_config_manager.py
```

### Error Analysis Tests

```bash
pytest tests/test_error_analyzer.py
```

## Running Tests in Different Environments

### Local Development

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_main.py::test_main_function

# Run with debugging
pytest --pdb
```

### Docker Environment

```bash
# Build test image
docker build -t aider-lint-fixer-test .

# Run tests in container
docker run --rm aider-lint-fixer-test pytest
```

### CI/CD Environment

```bash
# GitHub Actions
pytest --junitxml=test-results.xml --cov=aider_lint_fixer

# Generate coverage report
coverage xml
```

## Test Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Running Specific Test Types

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration
```

## Test Data and Fixtures

### Using Test Data

```bash
# Tests with sample repositories
pytest tests/test_with_sample_repos.py
```

### Temporary Test Environments

```bash
# Create isolated test environment
pytest --tmp-path-retention-count=3
```

## Performance Testing

### Benchmark Tests

```bash
pytest tests/benchmark/ --benchmark-only
```

### Memory Usage Tests

```bash
pytest tests/test_memory_usage.py --memory-profiler
```

## Debugging Test Failures

### Verbose Output

```bash
pytest -vvv --tb=long
```

### Drop into Debugger

```bash
pytest --pdb --pdb-trace
```

### Capture Output

```bash
pytest -s  # Don't capture stdout/stderr
```

## Test Reports

### HTML Coverage Report

```bash
pytest --cov=aider_lint_fixer --cov-report=html
open htmlcov/index.html
```

### XML Reports for CI

```bash
pytest --junitxml=test-results.xml --cov-report=xml
```

## Common Test Scenarios

### Testing Linter Integration

```bash
pytest tests/linters/
```

### Testing Error Handling

```bash
pytest tests/test_error_handling.py
```

### Testing Configuration Loading

```bash
pytest tests/test_config/
```

## Troubleshooting

### Common Issues

1. **Import errors**: Check PYTHONPATH and virtual environment
2. **Missing dependencies**: Run `pip install -r requirements-test.txt`
3. **Permission errors**: Check file permissions for test data
4. **Timeout issues**: Increase timeout for slow tests

### Environment Issues

```bash
# Reset test environment
rm -rf .pytest_cache/
pip install -e . --force-reinstall
```

## Next Steps

- [Monitor Performance](./monitor-performance.md)
- [Setup Development Environment](./setup-development-environment.md)
- [Security Best Practices](./security-best-practices.md)
