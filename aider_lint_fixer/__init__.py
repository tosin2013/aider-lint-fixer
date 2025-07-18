"""
Aider Lint Fixer - Automated lint error detection and fixing using aider.chat

This package provides automated lint error detection and fixing capabilities
using aider.chat with support for multiple LLM providers.
"""

__version__ = "1.8.0"
__author__ = "Aider Lint Fixer Team"
__email__ = "support@aider-lint-fixer.com"

from .aider_integration import AiderIntegration
from .config_manager import ConfigManager
from .error_analyzer import ErrorAnalyzer
from .lint_runner import LintRunner
from .main import main
from .pattern_matcher import SmartErrorClassifier
from .project_detector import ProjectDetector
from .rule_scraper import RuleScraper

__all__ = [
    "main",
    "ProjectDetector",
    "LintRunner",
    "AiderIntegration",
    "ErrorAnalyzer",
    "ConfigManager",
    "SmartErrorClassifier",
    "RuleScraper",
]
