#!/usr/bin/env python3
"""
Test utilities library for aider-lint-fixer test suite.

This module provides reusable utilities, mock generators, and helper functions
to improve test development efficiency and maintainability.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, Mock

import pytest
import yaml


class TestDataBuilder:
    """Factory for creating test data and scenarios."""
    
    @staticmethod
    def create_lint_error(
        file_path: str = "test_file.py",
        line: int = 1,
        column: int = 1,
        rule_id: str = "E001",
        message: str = "Test error message",
        severity: str = "ERROR",
        linter: str = "test-linter"
    ) -> Dict[str, Any]:
        """Create a standardized lint error structure."""
        return {
            "file_path": file_path,
            "line": line,
            "column": column,
            "rule_id": rule_id,
            "message": message,
            "severity": severity,
            "linter": linter
        }
    
    @staticmethod
    def create_project_structure(
        base_dir: Path,
        files: Dict[str, str],
        configs: Optional[Dict[str, str]] = None
    ) -> Dict[str, Path]:
        """Create a temporary project structure for testing."""
        created_files = {}
        
        # Create source files
        for file_path, content in files.items():
            full_path = base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            created_files[file_path] = full_path
        
        # Create config files
        if configs:
            for config_path, content in configs.items():
                full_path = base_dir / config_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                created_files[config_path] = full_path
        
        return created_files


class MockGenerator:
    """Generator for common mock objects used in tests."""
    
    @staticmethod
    def create_config_mock(
        llm_provider: str = "deepseek",
        llm_model: str = "deepseek/deepseek-chat",
        api_key: Optional[str] = "test-api-key"
    ) -> Mock:
        """Create a mock Config object with standard settings."""
        mock_config = MagicMock()
        mock_config.llm = MagicMock()
        mock_config.llm.provider = llm_provider
        mock_config.llm.model = llm_model
        mock_config.llm.api_key = api_key
        return mock_config
    
    @staticmethod
    def create_lint_result_mock(
        errors: Optional[List[Dict[str, Any]]] = None,
        raw_output: str = "",
        success: bool = True
    ) -> Mock:
        """Create a mock LintResult object."""
        mock_result = MagicMock()
        mock_result.errors = errors or []
        mock_result.raw_output = raw_output
        mock_result.success = success
        return mock_result
    
    @staticmethod
    def create_subprocess_mock(
        returncode: int = 0,
        stdout: str = "",
        stderr: str = ""
    ) -> Mock:
        """Create a mock subprocess result."""
        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        return mock_result


class FileSystemFixtures:
    """Utilities for creating and managing test file systems."""
    
    @staticmethod
    def create_python_project(base_dir: Path) -> Dict[str, Path]:
        """Create a sample Python project structure."""
        files = {
            "main.py": """#!/usr/bin/env python3
import sys

def main():
    print("Hello World")
    return 0

if __name__ == "__main__":
    sys.exit(main())
""",
            "module.py": """def calculate(x, y):
    result = x + y
    return result

class Calculator:
    def add(self, a, b):
        return a + b
""",
            "requirements.txt": """pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
""",
            "setup.py": """from setuptools import setup, find_packages

setup(
    name="test-project",
    version="0.1.0",
    packages=find_packages(),
)
"""
        }
        
        configs = {
            ".flake8": """[flake8]
max-line-length = 88
extend-ignore = E203, W503
""",
            "pyproject.toml": """[tool.black]
line-length = 88

[tool.isort]
profile = "black"
"""
        }
        
        return TestDataBuilder.create_project_structure(base_dir, files, configs)
    
    @staticmethod
    def create_nodejs_project(base_dir: Path) -> Dict[str, Path]:
        """Create a sample Node.js project structure."""
        files = {
            "index.js": """const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
""",
            "utils.js": """function add(a, b) {
    return a + b;
}

function multiply(x, y) {
    return x * y;
}

module.exports = { add, multiply };
""",
            "package.json": """{
  "name": "test-project",
  "version": "1.0.0",
  "description": "Test Node.js project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "jest": "^28.0.0"
  }
}
"""
        }
        
        configs = {
            ".eslintrc.json": """{
  "env": {
    "node": true,
    "es2021": true
  },
  "extends": ["eslint:recommended"],
  "rules": {
    "no-console": "warn",
    "semi": ["error", "always"]
  }
}
""",
            ".prettierrc": """{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2
}
"""
        }
        
        return TestDataBuilder.create_project_structure(base_dir, files, configs)
    
    @staticmethod
    def create_ansible_project(base_dir: Path) -> Dict[str, Path]:
        """Create a sample Ansible project structure."""
        files = {
            "playbook.yml": """---
- name: Test playbook
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Print message
      debug:
        msg: "Hello from Ansible"
    
    - name: Create directory
      file:
        path: /tmp/test
        state: directory
""",
            "inventory.ini": """[local]
localhost ansible_connection=local
""",
            "requirements.yml": """---
collections:
  - community.general
  - ansible.posix
"""
        }
        
        configs = {
            ".ansible-lint": """---
exclude_paths:
  - .cache/
  - .github/
  - molecule/
  - .pytest_cache/

use_default_rules: true
""",
            "ansible.cfg": """[defaults]
inventory = inventory.ini
host_key_checking = False
"""
        }
        
        return TestDataBuilder.create_project_structure(base_dir, files, configs)


class PerformanceHelper:
    """Utilities for performance testing and benchmarking."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    @staticmethod
    def assert_performance_threshold(
        func,
        threshold_seconds: float,
        *args,
        **kwargs
    ) -> Any:
        """Assert that function execution time is below threshold."""
        result, execution_time = PerformanceHelper.measure_execution_time(
            func, *args, **kwargs
        )
        assert execution_time < threshold_seconds, (
            f"Function execution took {execution_time:.3f}s, "
            f"exceeding threshold of {threshold_seconds}s"
        )
        return result


class AssertionHelpers:
    """Custom assertion helpers for common test scenarios."""
    
    @staticmethod
    def assert_lint_error_structure(error: Dict[str, Any]) -> None:
        """Assert that an error dict has the expected lint error structure."""
        required_keys = {"file_path", "line", "rule_id", "message", "linter"}
        assert all(key in error for key in required_keys), (
            f"Missing required keys in lint error: {required_keys - error.keys()}"
        )
        
        assert isinstance(error["line"], int), "Line number must be an integer"
        assert error["line"] > 0, "Line number must be positive"
        assert isinstance(error["file_path"], str), "File path must be a string"
        assert len(error["message"]) > 0, "Error message cannot be empty"
    
    @staticmethod
    def assert_file_exists_and_readable(file_path: Union[str, Path]) -> None:
        """Assert that a file exists and is readable."""
        path = Path(file_path)
        assert path.exists(), f"File does not exist: {path}"
        assert path.is_file(), f"Path is not a file: {path}"
        assert os.access(path, os.R_OK), f"File is not readable: {path}"
    
    @staticmethod
    def assert_config_structure(config: Dict[str, Any]) -> None:
        """Assert that a config dict has expected structure."""
        assert isinstance(config, dict), "Config must be a dictionary"
        # Add more specific config validation as needed


class NetworkMocks:
    """Mock utilities for network-related testing."""
    
    @staticmethod
    def create_http_response_mock(
        status_code: int = 200,
        text: str = "",
        json_data: Optional[Dict[str, Any]] = None
    ) -> Mock:
        """Create a mock HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = text
        mock_response.json.return_value = json_data or {}
        mock_response.raise_for_status.return_value = None
        
        if status_code >= 400:
            mock_response.raise_for_status.side_effect = Exception(
                f"HTTP {status_code} Error"
            )
        
        return mock_response


# Pytest fixtures that can be imported in test files
@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def python_project(temp_project_dir):
    """Create a sample Python project in a temporary directory."""
    return FileSystemFixtures.create_python_project(temp_project_dir)


@pytest.fixture
def nodejs_project(temp_project_dir):
    """Create a sample Node.js project in a temporary directory."""
    return FileSystemFixtures.create_nodejs_project(temp_project_dir)


@pytest.fixture
def ansible_project(temp_project_dir):
    """Create a sample Ansible project in a temporary directory."""
    return FileSystemFixtures.create_ansible_project(temp_project_dir)


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MockGenerator.create_config_mock()