#!/usr/bin/env python3
"""
Integration tests for Python linter support in aider-lint-fixer.
"""

import os
import shutil

# Add the parent directory to the path
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.project_detector import ProjectDetector, ProjectInfo


class TestPythonLintIntegration(unittest.TestCase):
    """Integration tests for Python linter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create problematic Python code
        self.problematic_content = """import os,sys
import json
import requests
from typing import Dict

def bad_function(x,y,z):
    if x==None:
        return
    unused_var = "not used"
    result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15
    try:
        pass
    except:
        pass
    return result

class badClass:
    def __init__(self,name):
        self.name=name
    def method(self,x,y):
        if self.name==None:
            return False
        return True

def process_data(data):
    if data == None:
        return []
    return [item.upper() for item in data if item is not None]

print("Should be in main guard")
"""

        self.python_file = self.project_root / "problematic_code.py"
        self.python_file.write_text(self.problematic_content)

        # Create project info
        self.project_info = ProjectInfo(
            root_path=str(self.project_root),
            languages={"python"},
            package_managers=set(),
            lint_configs=[],
            source_files=[str(self.python_file)],
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_flake8_detects_errors(self):
        """Test that flake8 can detect errors in problematic Python code."""
        # Test both modular and legacy implementations
        self._test_modular_flake8()
        self._test_legacy_flake8()

    def _test_modular_flake8(self):
        """Test the new modular flake8 implementation."""
        try:
            from aider_lint_fixer.linters.flake8_linter import Flake8Linter
        except ImportError:
            self.skipTest("Modular flake8 implementation not available")

        # Create modular linter
        linter = Flake8Linter(str(self.project_root))

        # Skip test if flake8 is not installed
        if not linter.is_available():
            self.skipTest("flake8 not installed")

        # Test basic profile
        result = linter.run_with_profile("basic", [str(self.python_file)])

        # Should find errors in our problematic code
        self.assertTrue(result.success)  # Should succeed even with errors found
        self.assertGreater(len(result.errors), 0, "Should detect lint errors in problematic code")

        # Verify error structure
        first_error = result.errors[0]
        self.assertIsInstance(first_error.file_path, str)
        self.assertIsInstance(first_error.line, int)
        self.assertIsInstance(first_error.rule_id, str)
        self.assertIsInstance(first_error.message, str)
        self.assertEqual(first_error.linter, "flake8")

        print(f"✅ Modular flake8: {len(result.errors)} errors detected")

    def _test_legacy_flake8(self):
        """Test the legacy flake8 implementation for comparison."""
        lint_runner = LintRunner(self.project_info)

        # Skip test if flake8 is not installed
        available_linters = lint_runner._detect_available_linters(["flake8"])
        if not available_linters.get("flake8", False):
            self.skipTest("flake8 not installed")

        # Force legacy implementation by testing specific file
        result = lint_runner.run_linter("flake8", [str(self.python_file)])

        print(f"✅ Legacy flake8: {len(result.errors)} errors detected")
        print(f"   Raw output preview: {result.raw_output[:100]}")

        # Check that we get reasonable error information
        if len(result.errors) > 0:
            first_error = result.errors[0]
            self.assertTrue(first_error.file_path.endswith("problematic_code.py"))
            self.assertGreater(first_error.line, 0)
            self.assertIsNotNone(first_error.rule_id)
            self.assertIsNotNone(first_error.message)

    def test_pylint_detects_errors(self):
        """Test that pylint can detect errors in problematic Python code."""
        # Test both modular and legacy implementations
        self._test_modular_pylint()
        self._test_legacy_pylint()

    def _test_modular_pylint(self):
        """Test the new modular pylint implementation."""
        try:
            from aider_lint_fixer.linters.pylint_linter import PylintLinter
        except ImportError:
            self.skipTest("Modular pylint implementation not available")

        # Create modular linter
        linter = PylintLinter(str(self.project_root))

        # Skip test if pylint is not installed
        if not linter.is_available():
            self.skipTest("pylint not installed")

        # Test basic profile
        result = linter.run_with_profile("basic", [str(self.python_file)])

        # Should find issues in our problematic code
        self.assertTrue(result.success)  # Should succeed even with issues found
        total_issues = len(result.errors) + len(result.warnings)
        self.assertGreater(total_issues, 0, "Should detect lint issues in problematic code")

        # Verify issue structure
        if result.errors:
            first_issue = result.errors[0]
        else:
            first_issue = result.warnings[0]

        self.assertIsInstance(first_issue.file_path, str)
        self.assertIsInstance(first_issue.line, int)
        self.assertIsInstance(first_issue.rule_id, str)
        self.assertIsInstance(first_issue.message, str)
        self.assertEqual(first_issue.linter, "pylint")

        print(
            f"✅ Modular pylint: {len(result.errors)} errors, {len(result.warnings)} warnings detected"
        )

    def _test_legacy_pylint(self):
        """Test the legacy pylint implementation for comparison."""
        lint_runner = LintRunner(self.project_info)

        # Skip test if pylint is not installed
        available_linters = lint_runner._detect_available_linters(["pylint"])
        if not available_linters.get("pylint", False):
            self.skipTest("pylint not installed")

        # Force legacy implementation by testing specific file
        result = lint_runner.run_linter("pylint", [str(self.python_file)])

        print(
            f"✅ Legacy pylint: {len(result.errors)} errors, {len(result.warnings)} warnings detected"
        )
        print(f"   Raw output preview: {result.raw_output[:100]}")

    def test_python_profile_support(self):
        """Test that Python linters support different profiles."""
        try:
            from aider_lint_fixer.linters.flake8_linter import Flake8Linter
            from aider_lint_fixer.linters.pylint_linter import PylintLinter
        except ImportError:
            self.skipTest("Modular Python linter implementations not available")

        # Test flake8 profiles
        flake8_linter = Flake8Linter(str(self.project_root))
        if flake8_linter.is_available():
            basic_result = flake8_linter.run_with_profile("basic", [str(self.python_file)])
            strict_result = flake8_linter.run_with_profile("strict", [str(self.python_file)])

            # Both should succeed
            self.assertTrue(basic_result.success)
            self.assertTrue(strict_result.success)

            # Strict should find same or more issues than basic
            basic_total = len(basic_result.errors) + len(basic_result.warnings)
            strict_total = len(strict_result.errors) + len(strict_result.warnings)
            self.assertGreaterEqual(strict_total, basic_total)

            print(f"✅ Flake8 basic: {basic_total} issues")
            print(f"✅ Flake8 strict: {strict_total} issues")

        # Test pylint profiles
        pylint_linter = PylintLinter(str(self.project_root))
        if pylint_linter.is_available():
            basic_result = pylint_linter.run_with_profile("basic", [str(self.python_file)])
            strict_result = pylint_linter.run_with_profile("strict", [str(self.python_file)])

            # Both should succeed
            self.assertTrue(basic_result.success)
            self.assertTrue(strict_result.success)

            # Strict should find same or more issues than basic
            basic_total = len(basic_result.errors) + len(basic_result.warnings)
            strict_total = len(strict_result.errors) + len(strict_result.warnings)
            self.assertGreaterEqual(strict_total, basic_total)

            print(f"✅ Pylint basic: {basic_total} issues")
            print(f"✅ Pylint strict: {strict_total} issues")

    def test_python_project_detection(self):
        """Test that Python projects are detected correctly."""
        detector = ProjectDetector()
        project_info = detector.detect_project(str(self.project_root))

        self.assertIn("python", project_info.languages)
        self.assertEqual(len(project_info.source_files), 1)
        self.assertTrue(any(str(f).endswith(".py") for f in project_info.source_files))


class TestPythonLintCLIIntegration(unittest.TestCase):
    """Test CLI integration with Python linters."""

    def test_cli_with_python_linters(self):
        """Test that the CLI works with Python linters."""
        # This is a basic smoke test - full CLI testing would require subprocess
        from aider_lint_fixer.lint_runner import LintRunner
        from aider_lint_fixer.project_detector import ProjectDetector

        # Test that we can create a lint runner and detect Python linters
        detector = ProjectDetector()
        project_info = detector.detect_project("test_python")

        if "python" in project_info.languages:
            lint_runner = LintRunner(project_info)
            available_linters = lint_runner._detect_available_linters(["flake8", "pylint"])

            # At least one Python linter should be available
            python_linters_available = any(available_linters.values())
            self.assertTrue(
                python_linters_available, "At least one Python linter should be available"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
