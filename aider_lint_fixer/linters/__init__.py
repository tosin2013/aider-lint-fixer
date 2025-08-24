"""
Linter modules for aider-lint-fixer.
This package contains linter-specific implementations that handle
the unique behavior, configuration, and output parsing for each
supported linter.
"""

from .base import BaseLinter, LinterResult

# Import available linters
try:
    from .ansible_lint import AnsibleLintLinter

    ANSIBLE_LINT_AVAILABLE = True
except ImportError:
    ANSIBLE_LINT_AVAILABLE = False
try:
    from .flake8_linter import Flake8Linter

    FLAKE8_AVAILABLE = True
except ImportError:
    FLAKE8_AVAILABLE = False
try:
    from .pylint_linter import PylintLinter

    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False
try:
    from .eslint_linter import ESLintLinter

    ESLINT_AVAILABLE = True
except ImportError:
    ESLINT_AVAILABLE = False
try:
    from .jshint_linter import JSHintLinter

    JSHINT_AVAILABLE = True
except ImportError:
    JSHINT_AVAILABLE = False
try:
    from .prettier_linter import PrettierLinter

    PRETTIER_AVAILABLE = True
except ImportError:
    PRETTIER_AVAILABLE = False
__all__ = ["BaseLinter", "LinterResult"]
# Add available linters to __all__
if ANSIBLE_LINT_AVAILABLE:
    __all__.append("AnsibleLintLinter")
if FLAKE8_AVAILABLE:
    __all__.append("Flake8Linter")
if PYLINT_AVAILABLE:
    __all__.append("PylintLinter")
if ESLINT_AVAILABLE:
    __all__.append("ESLintLinter")
if JSHINT_AVAILABLE:
    __all__.append("JSHintLinter")
if PRETTIER_AVAILABLE:
    __all__.append("PrettierLinter")
