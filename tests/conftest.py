"""
Shared pytest fixtures for aider-lint-fixer tests.

This file provides fixtures that are available to all test modules.
"""

import glob
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Import fixtures from utils.py to make them available globally
from tests.utils import (
    temp_project_dir,
    python_project,
    nodejs_project,
    ansible_project,
    mock_config
)

# Import performance fixtures
from tests.fixtures.performance_fixtures import (
    performance_tracker,
    benchmark_suite
)

# Additional global fixtures can be defined here if needed

@pytest.fixture(scope="session", autouse=True)
def cleanup_coverage_data():
    """Clean up any leftover coverage data files before and after test session."""
    # Clean up before tests
    coverage_files = glob.glob(".coverage*")
    for file in coverage_files:
        try:
            os.remove(file)
        except (OSError, FileNotFoundError):
            pass
    
    yield
    
    # Clean up after tests (but leave .coverage for reports)
    coverage_files = glob.glob(".coverage.*")  # Only parallel data files
    for file in coverage_files:
        try:
            os.remove(file)
        except (OSError, FileNotFoundError):
            pass