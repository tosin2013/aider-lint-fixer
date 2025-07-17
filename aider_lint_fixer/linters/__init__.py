"""
Linter modules for aider-lint-fixer.

This package contains linter-specific implementations that handle
the unique behavior, configuration, and output parsing for each
supported linter.
"""

from .base import BaseLinter, LinterResult
from .ansible_lint import AnsibleLintLinter

__all__ = [
    'BaseLinter',
    'LinterResult', 
    'AnsibleLintLinter'
]
