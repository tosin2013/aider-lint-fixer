"""
Shared pytest fixtures for aider-lint-fixer tests.

This file provides fixtures that are available to all test modules.
"""

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