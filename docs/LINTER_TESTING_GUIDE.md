# Linter Testing Guide

This guide covers comprehensive testing strategies for aider-lint-fixer, including unit tests, integration tests, and validation of linter support across different languages and frameworks.

## Testing Framework Overview

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_error_analyzer.py
│   ├── test_pattern_matcher.py
│   ├── test_aider_integration.py
│   └── test_config_manager.py
├── integration/             # End-to-end integration tests
│   ├── test_python_projects.py
│   ├── test_nodejs_projects.py
│   ├── test_ansible_projects.py
│   └── test_mixed_projects.py
├── fixtures/                # Test data and sample projects
│   ├── python_sample/
│   ├── nodejs_sample/
│   ├── ansible_sample/
│   └── test_files/
└── performance/             # Performance and load testing
    ├── test_large_projects.py
    └── benchmarks/
```

### Test Dependencies

```bash
# Install test dependencies
pip install -e .[dev]

# Core testing tools
pytest                # Test framework
pytest-cov          # Coverage reporting
pytest-mock         # Mocking utilities
pytest-xdist        # Parallel test execution
pytest-benchmark    # Performance testing
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_error_analyzer.py

# Run specific test function
pytest tests/unit/test_error_analyzer.py::test_categorize_error
```

### Coverage Testing

```bash
# Run with coverage
pytest --cov=aider_lint_fixer

# Generate HTML coverage report
pytest --cov=aider_lint_fixer --cov-report=html

# Coverage with minimum threshold
pytest --cov=aider_lint_fixer --cov-fail-under=80
```

### Parallel Testing

```bash
# Run tests in parallel
pytest -n auto

# Specify number of workers
pytest -n 4
```

## Unit Testing

### Error Analyzer Tests

```python
# tests/unit/test_error_analyzer.py
import pytest
from aider_lint_fixer.error_analyzer import ErrorAnalyzer, ErrorCategory
from aider_lint_fixer.lint_runner import LintError, ErrorSeverity

class TestErrorAnalyzer:
    def test_categorize_python_import_error(self):
        analyzer = ErrorAnalyzer()
        error = LintError(
            file_path="test.py",
            line=1,
            column=1,
            rule_id="F401",
            message="'os' imported but unused",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        analysis = analyzer._analyze_error(error, "import os\n")
        assert analysis.category == ErrorCategory.UNUSED
        assert analysis.fixable == True
        assert analysis.complexity.value == "simple"
```

### Pattern Matcher Tests

```python
# tests/unit/test_pattern_matcher.py
import pytest
from aider_lint_fixer.pattern_matcher import SmartErrorClassifier

class TestSmartErrorClassifier:
    def test_javascript_unused_variable(self):
        classifier = SmartErrorClassifier()
        result = classifier.classify_error(
            "'unusedVar' is defined but never used",
            "javascript",
            "eslint"
        )
        
        assert result.fixable == True
        assert result.confidence > 0.8
        assert result.method == "pattern_match"
```

### Configuration Tests

```python
# tests/unit/test_config_manager.py
import pytest
from aider_lint_fixer.config_manager import ConfigManager

class TestConfigManager:
    def test_load_default_config(self):
        config = ConfigManager()
        assert config.get_profile() == "basic"
        assert "flake8" in config.get_enabled_linters()
    
    def test_typescript_project_detection(self):
        config = ConfigManager("./fixtures/typescript_project")
        assert config.is_typescript_project() == True
        assert "eslint" in config.get_enabled_linters()
```

## Integration Testing

### Python Project Testing

```python
# tests/integration/test_python_projects.py
import pytest
import tempfile
import os
from pathlib import Path
from aider_lint_fixer.main import main

class TestPythonIntegration:
    def test_flake8_integration(self):
        """Test complete flake8 error detection and fixing flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file with errors
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
import os
import sys  # unused import

def function_with_long_line():
    return "this is a very long line that exceeds the maximum line length limit and should be fixed"

x=1 # missing spaces
            """)
            
            # Run aider-lint-fixer
            result = main([
                "--dry-run",
                "--linter", "flake8",
                str(tmpdir)
            ])
            
            assert result.total_errors > 0
            assert any("F401" in e.rule_id for e in result.errors)  # unused import
            assert any("E501" in e.rule_id for e in result.errors)  # line too long
```

### Node.js Project Testing

```python
# tests/integration/test_nodejs_projects.py
import pytest
import tempfile
import json
from pathlib import Path
from aider_lint_fixer.main import main

class TestNodeJSIntegration:
    def test_eslint_typescript_integration(self):
        """Test ESLint with TypeScript project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = {
                "name": "test-project",
                "devDependencies": {
                    "eslint": "^8.0.0",
                    "@typescript-eslint/parser": "^6.0.0"
                }
            }
            (Path(tmpdir) / "package.json").write_text(json.dumps(package_json))
            
            # Create TypeScript file with errors
            ts_file = Path(tmpdir) / "src" / "index.ts"
            ts_file.parent.mkdir(exist_ok=True)
            ts_file.write_text("""
let unusedVariable = 'remove me';
const value = 'single quotes should be double'
function noReturnType() {
    return 42
}
            """)
            
            # Create ESLint config
            eslint_config = {
                "parser": "@typescript-eslint/parser",
                "extends": ["@typescript-eslint/recommended"],
                "rules": {
                    "quotes": ["error", "double"],
                    "@typescript-eslint/no-unused-vars": "error"
                }
            }
            (Path(tmpdir) / ".eslintrc.json").write_text(json.dumps(eslint_config))
            
            result = main([
                "--dry-run",
                "--linter", "eslint",
                str(tmpdir)
            ])
            
            assert result.total_errors > 0
            # Should detect unused variable and quote style issues
```

### Ansible Project Testing

```python
# tests/integration/test_ansible_projects.py
import pytest
import tempfile
import yaml
from pathlib import Path
from aider_lint_fixer.main import main

class TestAnsibleIntegration:
    def test_ansible_lint_integration(self):
        """Test ansible-lint integration with YAML playbooks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ansible playbook with errors
            playbook = {
                "name": "Test playbook",
                "hosts": "all",
                "tasks": [
                    {
                        "shell": "echo hello",  # Should use command module
                        "name": "bad shell usage"
                    },
                    {
                        "copy": {
                            "src": "file.txt",
                            "dest": "/tmp/file.txt",
                            "mode": "777"  # Too permissive
                        }
                    }
                ]
            }
            
            playbook_file = Path(tmpdir) / "playbook.yml"
            with open(playbook_file, 'w') as f:
                yaml.dump([playbook], f)
            
            result = main([
                "--dry-run",
                "--linter", "ansible-lint",
                str(tmpdir)
            ])
            
            assert result.total_errors > 0
            # Should detect shell usage and file permissions issues
```

## Performance Testing

### Large Project Simulation

```python
# tests/performance/test_large_projects.py
import pytest
import tempfile
import time
from pathlib import Path
from aider_lint_fixer.main import main

class TestPerformance:
    @pytest.mark.benchmark
    def test_large_python_project_performance(self, benchmark):
        """Test performance on large Python project (100+ files)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 100 Python files with various errors
            for i in range(100):
                file_path = Path(tmpdir) / f"module_{i}.py"
                file_path.write_text(f"""
import os  # unused import
import sys
import json

def function_{i}():
    x=1+2+3+4+5  # spacing issues
    return "very long line that exceeds maximum length and should trigger line length error"

class Class{i}:
    def method(self):
        pass
                """)
            
            # Benchmark the processing
            def run_linter():
                return main([
                    "--dry-run",
                    "--linter", "flake8",
                    str(tmpdir)
                ])
            
            result = benchmark(run_linter)
            
            # Performance assertions
            assert result.total_errors > 200  # Should find many errors
            assert benchmark.stats.median < 30.0  # Should complete in under 30 seconds
```

### Memory Usage Testing

```python
# tests/performance/test_memory_usage.py
import pytest
import psutil
import os
from aider_lint_fixer.main import main

class TestMemoryUsage:
    def test_memory_efficiency_large_project(self):
        """Test memory usage doesn't exceed reasonable limits"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run on large project
        result = main([
            "--dry-run",
            "./tests/fixtures/large_project"
        ])
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should not exceed 500MB for typical projects
        assert memory_increase < 500
```

## Test Fixtures

### Creating Test Projects

```python
# tests/conftest.py - Shared test fixtures
import pytest
import tempfile
import json
from pathlib import Path

@pytest.fixture
def python_project():
    """Create a temporary Python project with common errors"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        
        # Main module
        (project_path / "main.py").write_text("""
import os
import sys  # unused

def long_function_name():
    return "this line is way too long and exceeds the recommended maximum line length for Python code"

x=1+2  # spacing
        """)
        
        # Test file
        (project_path / "test_main.py").write_text("""
import pytest
from main import long_function_name

def test_function():
    assert long_function_name() is not None
        """)
        
        # Setup.py
        (project_path / "setup.py").write_text("""
from setuptools import setup

setup(
    name="test-project",
    version="0.1.0"
)
        """)
        
        yield project_path

@pytest.fixture
def nodejs_project():
    """Create a temporary Node.js project with TypeScript"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        
        # Package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "scripts": {
                "lint": "eslint src/**/*.ts"
            },
            "devDependencies": {
                "eslint": "^8.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0"
            }
        }
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # TypeScript config
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "strict": True
            }
        }
        (project_path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        
        # Source file with errors
        src_dir = project_path / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text("""
let unusedVariable = 'remove me';
const message = 'Hello world';  // should be double quotes
function getValue() {  // missing return type
    return 42;
}
console.log(message)  // missing semicolon
        """)
        
        # ESLint config
        eslintrc = {
            "parser": "@typescript-eslint/parser",
            "plugins": ["@typescript-eslint"],
            "extends": [
                "eslint:recommended",
                "@typescript-eslint/recommended"
            ],
            "rules": {
                "quotes": ["error", "double"],
                "semi": ["error", "always"],
                "@typescript-eslint/no-unused-vars": "error",
                "@typescript-eslint/explicit-function-return-type": "warn"
            }
        }
        (project_path / ".eslintrc.json").write_text(json.dumps(eslintrc, indent=2))
        
        yield project_path
```

## Continuous Integration Testing

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.11, 3.12]
        
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev,learning]
          
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=aider_lint_fixer
        
      - name: Run integration tests
        run: pytest tests/integration/ -v
        
      - name: Run performance tests
        run: pytest tests/performance/ -v --benchmark-only
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Coverage Goals

| Component | Target Coverage | Current |
|-----------|----------------|---------|
| Core modules | 90%+ | 85% |
| Error analysis | 95%+ | 92% |
| Pattern matching | 85%+ | 88% |
| Integration | 80%+ | 76% |
| Overall project | 85%+ | 83% |

## Testing Best Practices

### 1. Test Organization

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test complete workflows
- **Performance tests**: Validate scalability
- **Regression tests**: Prevent bug reintroduction

### 2. Mock Usage

```python
# Example: Mocking external dependencies
@pytest.fixture
def mock_aider_client(mocker):
    mock_client = mocker.Mock()
    mock_client.fix_error.return_value = {"success": True, "fixed": True}
    return mock_client

def test_error_fixing_with_mock(mock_aider_client):
    # Test error fixing logic without actual AI calls
    pass
```

### 3. Test Data Management

- Use fixtures for reusable test data
- Create realistic test projects
- Include edge cases and error conditions
- Version control test data changes

### 4. Debugging Tests

```bash
# Run specific test with debug output
pytest tests/unit/test_error_analyzer.py::test_specific_function -v -s

# Debug with pdb
pytest --pdb tests/unit/test_error_analyzer.py

# Run with logging
pytest tests/ --log-cli-level=DEBUG
```

## Validation Testing

### Linter Compatibility Testing

```python
# Automated testing across different linter versions
@pytest.mark.parametrize("linter_version", [
    "flake8==6.0.0",
    "flake8==7.0.0", 
    "eslint@8.45.0",
    "eslint@9.0.0"
])
def test_linter_compatibility(linter_version):
    # Test compatibility with different linter versions
    pass
```

### Cross-Platform Testing

```python
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_windows_path_handling():
    # Test Windows-specific functionality
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
def test_unix_path_handling():
    # Test Unix-specific functionality
    pass
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Installation Guide](./INSTALLATION_GUIDE.md)
- [Contributor Guide](./CONTRIBUTOR_VERSION_GUIDE.md)
- [Node.js Linters Guide](./NODEJS_LINTERS_GUIDE.md)