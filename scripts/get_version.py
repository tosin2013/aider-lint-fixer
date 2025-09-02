#!/usr/bin/env python3
"""
Get current version from aider_lint_fixer/__init__.py
"""
import sys
from pathlib import Path

# Add the parent directory to Python path to import aider_lint_fixer
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from aider_lint_fixer import __version__
    print(__version__)
except ImportError as e:
    print(f"Error importing version: {e}", file=sys.stderr)
    sys.exit(1)