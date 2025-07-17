"""
Aider Lint Fixer - Automated lint error detection and fixing using aider.chat

This package provides automated lint error detection and fixing capabilities
using aider.chat with support for multiple LLM providers.
"""

__version__ = "1.1.0"
__author__ = "Aider Lint Fixer Team"
__email__ = "support@aider-lint-fixer.com"

from .main import main
from .project_detector import ProjectDetector
from .lint_runner import LintRunner
from .aider_integration import AiderIntegration
from .error_analyzer import ErrorAnalyzer
from .config_manager import ConfigManager

__all__ = [
    "main",
    "ProjectDetector", 
    "LintRunner",
    "AiderIntegration",
    "ErrorAnalyzer",
    "ConfigManager",
]

