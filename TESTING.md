# Testing Guide for Aider-Lint-Fixer

This comprehensive guide covers testing practices, infrastructure, and maintenance procedures for the aider-lint-fixer project.

## 📋 Table of Contents

- [Testing Infrastructure Overview](#testing-infrastructure-overview)
- [Test Categories and Organization](#test-categories-and-organization)
- [Running Tests](#running-tests)
- [Writing New Tests](#writing-new-tests)
- [Advanced Testing Strategies](#advanced-testing-strategies)
- [Performance Testing](#performance-testing)
- [Coverage Management](#coverage-management)
- [CI/CD Integration](#cicd-integration)
- [Test Utilities and Fixtures](#test-utilities-and-fixtures)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🏗️ Testing Infrastructure Overview

### Test Framework Stack

- **Primary Framework**: pytest 8.4+
- **Coverage Tool**: pytest-cov with coverage.py
- **Mocking**: pytest-mock and unittest.mock
- **Property-Based Testing**: hypothesis
- **Performance Testing**: Custom performance fixtures
- **Parameterization**: pytest.mark.parametrize

### Project Structure

```
tests/
├── utils.py                    # Core test utilities and helpers
├── fixtures/                   # Test data and fixtures
│   ├── sample_lint_data.py    # Sample lint errors and code
│   └── performance_fixtures.py # Performance testing utilities
├── test_*.py                   # Test modules
├── conftest.py                 # Shared pytest fixtures
└── README_NEW_TESTS.md         # Legacy test documentation
```

### Test Categories

| Category | Purpose | Files | Coverage Target |
|----------|---------|-------|-----------------|
| **Unit Tests** | Individual component testing | `test_*.py` | 95%+ |
| **Integration Tests** | Cross-component testing | `test_*_integration.py` | 85%+ |
| **Performance Tests** | Benchmarking and scalability | `test_performance_*.py` | 80%+ |
| **Parameterized Tests** | Data-driven testing | `test_enhanced_*.py` | 90%+ |
| **Property-Based Tests** | Invariant validation | Uses hypothesis | 85%+ |

## 🚀 Running Tests

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_aider_integration.py

# Run specific test function
python -m pytest tests/test_utils.py::TestDataBuilder::test_create_lint_error

# Run tests matching pattern
python -m pytest -k "error_analysis"
```

### Test Categories

```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests  
python -m pytest -m integration

# Run performance tests
python -m pytest tests/test_performance_benchmarks.py

# Skip slow tests
python -m pytest -m "not slow"
```

### Coverage Testing

```bash
# Run tests with coverage
python -m pytest --cov=aider_lint_fixer --cov-report=html

# Coverage with missing lines
python -m pytest --cov=aider_lint_fixer --cov-report=term-missing

# Coverage threshold enforcement
python -m pytest --cov=aider_lint_fixer --cov-fail-under=85
```

### Parallel Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
python -m pytest -n auto

# Run with specific number of workers
python -m pytest -n 4
```

## ✍️ Writing New Tests

### Basic Test Structure

```python
#!/usr/bin/env python3
"""
Test module for [component being tested].
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils import TestDataBuilder, MockGenerator, AssertionHelpers
from aider_lint_fixer.your_module import YourClass


class TestYourClass:
    """Test cases for YourClass functionality."""
    
    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        # Arrange
        test_input = TestDataBuilder.create_lint_error()
        
        # Act
        result = YourClass().process(test_input)
        
        # Assert
        assert result is not None
        AssertionHelpers.assert_lint_error_structure(result)
    
    @pytest.mark.parametrize("input_value,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_parameterized_functionality(self, input_value, expected):
        """Test functionality with different parameters."""
        result = YourClass().transform(input_value)
        assert result == expected
```

### Using Test Utilities

```python
from tests.utils import (
    TestDataBuilder,
    MockGenerator, 
    FileSystemFixtures,
    PerformanceHelper,
    AssertionHelpers
)

# Create test data
error = TestDataBuilder.create_lint_error(
    file_path="test.py",
    line=10,
    rule_id="E501",
    message="Line too long"
)

# Create mock objects
mock_config = MockGenerator.create_config_mock(
    llm_provider="deepseek",
    llm_model="deepseek/deepseek-chat"
)

# Create test projects
python_project = FileSystemFixtures.create_python_project(temp_dir)

# Performance testing
result, time_taken = PerformanceHelper.measure_execution_time(
    your_function, arg1, arg2
)

# Custom assertions
AssertionHelpers.assert_lint_error_structure(error)
AssertionHelpers.assert_file_exists_and_readable("test.py")
```

### Fixtures Usage

```python
def test_with_temp_project(python_project):
    """Test using a temporary Python project."""
    assert "main.py" in python_project
    main_file = python_project["main.py"]
    assert main_file.exists()

def test_with_mock_config(mock_config):
    """Test using a mock configuration."""
    assert mock_config.llm.provider == "deepseek"
```

## 🔬 Advanced Testing Strategies

### Parameterized Testing

Use parameterized tests to test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("linter,expected_rules", [
    ("flake8", ["E501", "E302", "F841"]),
    ("pylint", ["C0103", "W0613"]),
    ("eslint", ["semi", "no-unused-vars"]),
])
def test_linter_rules(linter, expected_rules):
    """Test that sample errors contain expected rules."""
    errors = get_sample_errors_by_linter(linter)
    found_rules = {error["rule_id"] for error in errors}
    
    for rule in expected_rules:
        assert rule in found_rules
```

### Property-Based Testing

Use hypothesis for testing invariants:

```python
from hypothesis import given, strategies as st

@given(
    file_path=st.text(min_size=1, max_size=100),
    line=st.integers(min_value=1, max_value=10000)
)
def test_lint_error_invariants(file_path, line):
    """Test that lint error creation maintains invariants."""
    error = TestDataBuilder.create_lint_error(
        file_path=file_path,
        line=line
    )
    
    # These properties should always hold
    assert error["line"] == line
    assert error["file_path"] == file_path
    assert isinstance(error["line"], int)
    assert error["line"] > 0
```

### Integration Testing

Test component interactions:

```python
def test_full_linting_workflow(temp_project_dir):
    """Test complete linting workflow integration."""
    # Setup
    project = FileSystemFixtures.create_python_project(temp_project_dir)
    
    # Test the full workflow
    detector = ProjectDetector()
    project_info = detector.detect_project(temp_project_dir)
    
    runner = LintRunner(project_info)
    results = runner.run_all_available_linters()
    
    # Assertions
    assert isinstance(results, dict)
    assert len(results) > 0
```

## ⚡ Performance Testing

### Basic Performance Tests

```python
from tests.fixtures.performance_fixtures import (
    performance_test, 
    assert_execution_time_under,
    assert_memory_usage_under
)

@performance_test(max_execution_time=0.1, max_memory_mb=50)
def test_large_error_processing():
    """Test processing large number of errors."""
    errors = [TestDataBuilder.create_lint_error() for _ in range(10000)]
    
    # Process errors
    result = process_errors(errors)
    return result

@assert_execution_time_under(1.0)
def test_file_processing_speed():
    """Test that file processing is fast enough."""
    # Your processing logic here
    pass
```

### Benchmark Testing

```python
def test_performance_benchmark(benchmark_suite):
    """Run performance benchmarks."""
    # Test file processing performance
    benchmark_result = benchmark_suite.benchmark_file_processing(
        process_function, test_file_path, iterations=10
    )
    
    assert benchmark_result["avg_time"] < 0.1
    assert benchmark_result["max_time"] < 0.5
```

### Regression Detection

```python
def test_performance_regression():
    """Test for performance regressions."""
    detector = RegressionDetector()
    
    # Run performance test
    result, metrics = measure_performance()
    
    # Check for regression
    regression_check = detector.check_regression("test_name", metrics)
    
    if regression_check["status"] == "regression":
        pytest.fail(f"Performance regression detected: {regression_check['regressions']}")
```

## 📊 Coverage Management

### Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["aider_lint_fixer"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### Coverage Commands

```bash
# Generate HTML coverage report
python -m pytest --cov=aider_lint_fixer --cov-report=html
open htmlcov/index.html

# Generate XML coverage report (for CI)
python -m pytest --cov=aider_lint_fixer --cov-report=xml

# Check coverage without running tests
coverage report

# See missing lines
coverage report --show-missing
```

### Coverage Quality Gates

```bash
# Fail if coverage below 85%
python -m pytest --cov=aider_lint_fixer --cov-fail-under=85

# Branch coverage
python -m pytest --cov=aider_lint_fixer --cov-branch
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The project uses comprehensive CI/CD workflows in `.github/workflows/`:

- `test-build.yml` - Main testing workflow
- `pr-check.yml` - Pull request validation
- `fast-check.yml` - Quick validation

### Running Tests in CI

```yaml
- name: Run test suite
  run: |
    python -m pytest tests/ \
      --cov=aider_lint_fixer \
      --cov-report=xml \
      --cov-fail-under=85 \
      --maxfail=5 \
      -v

- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Local CI Simulation

```bash
# Run tests like CI
python -m pytest tests/ \
  --cov=aider_lint_fixer \
  --cov-report=term-missing \
  --cov-fail-under=85 \
  --maxfail=5

# Run code quality checks
flake8 aider_lint_fixer tests
black --check aider_lint_fixer tests  
isort --check-only aider_lint_fixer tests
mypy aider_lint_fixer
```

## 🛠️ Test Utilities and Fixtures

### Available Utilities

| Utility | Purpose | Example |
|---------|---------|---------|
| `TestDataBuilder` | Create test data | `create_lint_error()` |
| `MockGenerator` | Generate mocks | `create_config_mock()` |
| `FileSystemFixtures` | Create test projects | `create_python_project()` |
| `PerformanceHelper` | Performance testing | `measure_execution_time()` |
| `AssertionHelpers` | Custom assertions | `assert_lint_error_structure()` |

### Global Fixtures

Available in all test files:

```python
def test_example(temp_project_dir, python_project, mock_config):
    """Test using global fixtures."""
    # temp_project_dir: Path to temporary directory
    # python_project: Dict of created Python project files
    # mock_config: Mock configuration object
    pass
```

### Custom Fixtures

Create custom fixtures in `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    """Create custom test fixture."""
    # Setup
    resource = create_resource()
    yield resource
    # Cleanup
    resource.cleanup()
```

## 🔧 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or in test files
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**2. Missing Dependencies**
```bash
# Install test dependencies
pip install -r requirements-test.txt

# For specific features
pip install hypothesis  # Property-based testing
pip install pytest-xdist  # Parallel execution
```

**3. Slow Tests**
```bash
# Skip slow tests
python -m pytest -m "not slow"

# Run specific fast tests
python -m pytest tests/test_utils.py
```

**4. Coverage Issues**
```bash
# Debug coverage
python -m pytest --cov=aider_lint_fixer --cov-report=term-missing

# Check specific module
python -m pytest --cov=aider_lint_fixer.your_module
```

### Test Environment Issues

**Container/Docker Testing**
```bash
# Run in container
docker run --rm -v $(pwd):/workspace python:3.11 \
  bash -c "cd /workspace && pip install -r requirements-test.txt && python -m pytest"
```

**Network-related Test Failures**
```bash
# Skip network tests
python -m pytest -m "not network"

# Mock network calls
# Use responses library or mock requests
```

## 📚 Best Practices

### Test Writing Guidelines

1. **Test Naming**: Use descriptive names that explain what is being tested
   ```python
   def test_error_analyzer_handles_empty_error_list(self):
   def test_config_manager_loads_valid_yaml_configuration(self):
   ```

2. **Arrange-Act-Assert Pattern**:
   ```python
   def test_example(self):
       # Arrange
       input_data = create_test_data()
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result.is_valid()
   ```

3. **One Concept Per Test**: Each test should verify one specific behavior

4. **Use Fixtures for Setup**: Avoid repetitive setup code

5. **Mock External Dependencies**: Don't let tests depend on external services

### Performance Testing Guidelines

1. **Set Realistic Thresholds**: Base thresholds on actual usage patterns
2. **Test Scalability**: Verify performance with different data sizes
3. **Monitor Trends**: Track performance over time
4. **Isolate Performance Tests**: Don't mix performance with functional tests

### Coverage Guidelines

1. **Aim for 85%+ Overall Coverage**: Target set in project requirements
2. **Focus on Critical Paths**: Ensure high coverage for core functionality
3. **Test Edge Cases**: Cover error conditions and boundary values
4. **Document Excluded Code**: Use `# pragma: no cover` sparingly with justification

### CI/CD Best Practices

1. **Fast Feedback**: Keep basic tests under 2 minutes
2. **Parallel Execution**: Use test parallelization for large suites
3. **Quality Gates**: Fail builds on coverage or test failures
4. **Artifact Collection**: Save test reports and coverage data

## 📈 Continuous Improvement

### Monitoring Test Health

1. **Track Test Execution Time**: Monitor for performance degradation
2. **Monitor Flaky Tests**: Identify and fix unstable tests
3. **Coverage Trends**: Track coverage changes over time
4. **Test Code Quality**: Apply same standards to test code

### Regular Maintenance

1. **Update Dependencies**: Keep testing tools up to date
2. **Review Test Coverage**: Regularly assess coverage gaps
3. **Refactor Test Code**: Improve test maintainability
4. **Documentation Updates**: Keep this guide current

---

## 📞 Getting Help

- **Issues**: Report test issues on GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check existing test files for examples
- **CI Logs**: Review GitHub Actions logs for CI failures

This testing guide provides the foundation for maintaining and improving the test infrastructure for aider-lint-fixer. Follow these practices to ensure reliable, maintainable, and comprehensive test coverage.