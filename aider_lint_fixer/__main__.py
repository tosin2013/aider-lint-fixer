#!/usr/bin/env python3
"""
Entry point for running aider_lint_fixer as a module.

This allows the package to be executed with:
    python -m aider_lint_fixer
"""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
