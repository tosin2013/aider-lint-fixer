# Writing and Running Tests for Aider-Lint-Fixer

Learn how to write effective tests for aider-lint-fixer using pytest and the project's testing framework.

## Test Structure

Tests should follow the AAA pattern:
- **Arrange**: Set up test data and conditions
- **Act**: Execute the code being tested
- **Assert**: Verify the results

## Setting Up Your Test Environment

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Verify pytest installation
pytest --version
```

## Writing Your First Test

Create a test file with the `test_*.py` pattern:

```python
# tests/test_example.py
import pytest
from aider_lint_fixer.linters.base import BaseLinter

class TestBaseLinter:
    """Test cases for the BaseLinter class."""
    
    def test_linter_initialization(self):
        """Test that linter initializes correctly."""
        # Arrange
        config = {"enabled": True, "severity": "error"}
        
        # Act
        linter = BaseLinter(config)
        
        # Assert
        assert linter.config == config
        assert linter.enabled is True
    
    def test_linter_validation(self):
        """Test linter validation functionality."""
        # Arrange
        linter = BaseLinter({"enabled": True})
        test_code = "print('hello world')"
        
        # Act
        result = linter.validate_code(test_code)
        
        # Assert
        assert isinstance(result, dict)
        assert "issues" in result
```

## Running Tests

### Execute All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
pytest tests/test_linters.py
pytest tests/test_aider_integration.py
```

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Tests in Watch Mode
```bash
pytest-watch
# or
ptw
```

## Test Coverage

### Generate Coverage Report
```bash
pytest --cov=aider_lint_fixer
```

### Generate HTML Coverage Report
```bash
pytest --cov=aider_lint_fixer --cov-report=html
open htmlcov/index.html
```

### Coverage with Missing Lines
```bash
pytest --cov=aider_lint_fixer --cov-report=term-missing
```

## Testing Different Components

### Testing Linters

```python
# tests/test_linters/test_python_linters.py
import pytest
from aider_lint_fixer.linters.flake8_linter import Flake8Linter

class TestFlake8Linter:
    
    @pytest.fixture
    def linter(self):
        """Create a Flake8Linter instance for testing."""
        config = {
            "max_line_length": 88,
            "ignore": ["E203", "W503"]
        }
        return Flake8Linter(config)
    
    def test_detects_style_issues(self, linter):
        """Test that flake8 detects style violations."""
        # Arrange
        bad_code = "x=1+2"  # Missing spaces
        
        # Act
        result = linter.run(bad_code)
        
        # Assert
        assert len(result.issues) > 0
        assert any("E225" in issue.code for issue in result.issues)
    
    def test_fixes_style_issues(self, linter):
        """Test that flake8 can fix style violations."""
        # Arrange
        bad_code = "x=1+2"
        
        # Act
        fixed_code = linter.fix(bad_code)
        
        # Assert
        assert fixed_code == "x = 1 + 2"
```

### Testing AI Integration

```python
# tests/test_aider_integration.py
import pytest
from unittest.mock import Mock, patch
from aider_lint_fixer.aider_integration import AiderIntegration

class TestAiderIntegration:
    
    @pytest.fixture
    def aider_integration(self):
        """Create AiderIntegration instance for testing."""
        return AiderIntegration(api_key="test-key")
    
    @patch('aider_lint_fixer.aider_integration.aider_chat')
    def test_ai_fix_success(self, mock_aider, aider_integration):
        """Test successful AI-powered code fix."""
        # Arrange
        mock_aider.return_value.fix_code.return_value = "fixed code"
        problematic_code = "def bad_function():\n    pass"
        
        # Act
        result = aider_integration.fix_code(problematic_code)
        
        # Assert
        assert result.success is True
        assert result.fixed_code == "fixed code"
        mock_aider.return_value.fix_code.assert_called_once()
```

### Testing Configuration

```python
# tests/test_config_manager.py
import pytest
import tempfile
import yaml
from pathlib import Path
from aider_lint_fixer.config_manager import ConfigManager

class TestConfigManager:
    
    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        # Arrange
        config_data = {
            "profile": "development",
            "linters": {"python": ["flake8", "pylint"]}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        # Act
        config_manager = ConfigManager(config_path)
        
        # Assert
        assert config_manager.profile == "development"
        assert "flake8" in config_manager.get_linters("python")
        
        # Cleanup
        Path(config_path).unlink()
```

## Test Fixtures and Utilities

### Common Test Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
""")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()

@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "profile": "test",
        "linters": {
            "python": ["flake8"],
            "javascript": ["eslint"]
        },
        "ai_integration": {
            "enabled": False
        }
    }
```

## Integration Tests

```python
# tests/test_integration.py
import pytest
import subprocess
from pathlib import Path

class TestCLIIntegration:
    """Integration tests for the CLI interface."""
    
    def test_cli_help_command(self):
        """Test that CLI help command works."""
        # Act
        result = subprocess.run(
            ["python", "-m", "aider_lint_fixer", "--help"],
            capture_output=True,
            text=True
        )
        
        # Assert
        assert result.returncode == 0
        assert "aider-lint-fixer" in result.stdout
    
    def test_cli_version_command(self):
        """Test that CLI version command works."""
        # Act
        result = subprocess.run(
            ["python", "-m", "aider_lint_fixer", "--version"],
            capture_output=True,
            text=True
        )
        
        # Assert
        assert result.returncode == 0
        assert "aider-lint-fixer" in result.stdout
```

## Performance Tests

```python
# tests/test_performance.py
import pytest
import time
from aider_lint_fixer.lint_runner import LintRunner

class TestPerformance:
    """Performance tests for aider-lint-fixer."""
    
    @pytest.mark.performance
    def test_large_file_processing_time(self):
        """Test processing time for large files."""
        # Arrange
        large_code = "print('hello')\n" * 1000
        runner = LintRunner()
        
        # Act
        start_time = time.time()
        result = runner.run_linters(large_code, language="python")
        end_time = time.time()
        
        # Assert
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete in under 5 seconds
        assert result is not None
```

## Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"

# Run tests matching a pattern
pytest -k "test_linter"
```

## Continuous Integration Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=aider_lint_fixer --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## Best Practices

1. **Test behavior, not implementation**: Focus on what the code does, not how it does it
2. **Use descriptive test names**: Test names should explain the scenario being tested
3. **Keep tests independent**: Each test should be able to run in isolation
4. **Use fixtures for common setup**: Reduce code duplication with pytest fixtures
5. **Mock external dependencies**: Use `unittest.mock` for API calls and file operations
6. **Test edge cases**: Include tests for error conditions and boundary values
7. **Maintain good coverage**: Aim for 80%+ test coverage on critical code paths

## Debugging Tests

```bash
# Run tests with debugging output
pytest -s -v

# Drop into debugger on failure
pytest --pdb

# Run a specific test with debugging
pytest tests/test_linters.py::TestFlake8Linter::test_detects_style_issues -s -v
```
