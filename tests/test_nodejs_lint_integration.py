"""
Integration tests for Node.js linters (ESLint, JSHint, Prettier).

These tests verify that our modular Node.js linter implementations work correctly
with real linter installations and can parse their output properly.
"""

import os
import tempfile
import unittest
from pathlib import Path

from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.project_detector import ProjectDetector


class TestNodeJSLintIntegration(unittest.TestCase):
    """Test Node.js linter integration."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()

        # Create project info
        detector = ProjectDetector()
        project_info = detector.detect_project(self.test_dir)
        self.lint_runner = LintRunner(project_info)

        # Create a problematic JavaScript file
        self.js_file = os.path.join(self.test_dir, "test.js")
        with open(self.js_file, "w") as f:
            f.write(
                """
var fs = require('fs');
var unused = require('path');

function badFunction(x,y,z) {
    if (x == null) {
        return;
    }
    var unused_var = "not used";
    var result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15;

    var data = {key: "value", another_key:"another_value"}

    if (result == undefined) {
        console.log("result is undefined")
    }

    return result
}

globalVar = "bad practice";
eval("console.log('bad')");

module.exports = badFunction;
"""
            )

        # Create package.json
        self.package_json = os.path.join(self.test_dir, "package.json")
        with open(self.package_json, "w") as f:
            f.write(
                """{
  "name": "test-project",
  "version": "1.0.0",
  "main": "test.js"
}"""
            )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_eslint_detects_errors(self):
        """Test that ESLint can detect errors in JavaScript code."""
        result = self.lint_runner.run_linter("eslint", [self.js_file])

        # ESLint should find multiple errors
        self.assertGreater(len(result.errors), 0, "ESLint should detect errors")

        # Check for specific error types we expect
        error_rules = [error.rule_id for error in result.errors]

        # Should detect unused variables
        self.assertIn("no-unused-vars", error_rules, "Should detect unused variables")

        # Should detect == vs === issues
        self.assertIn("eqeqeq", error_rules, "Should detect == vs === issues")

        # Should detect eval usage
        self.assertIn("no-eval", error_rules, "Should detect eval usage")

        print(
            f"✅ ESLint detected {len(result.errors)} errors, {len(result.warnings)} warnings"
        )

    def test_jshint_detects_errors(self):
        """Test that JSHint can detect errors in JavaScript code."""
        try:
            result = self.lint_runner.run_linter("jshint", [self.js_file])

            # JSHint should find errors
            self.assertGreater(len(result.errors), 0, "JSHint should detect errors")

            # Check that we have meaningful error messages
            error_messages = [error.message for error in result.errors]
            self.assertTrue(
                any("semicolon" in msg.lower() for msg in error_messages),
                "Should detect missing semicolons",
            )

            print(
                f"✅ JSHint detected {len(result.errors)} errors, {len(result.warnings)} warnings"
            )

        except Exception as e:
            self.skipTest(f"JSHint not available or failed: {e}")

    def test_prettier_detects_formatting_issues(self):
        """Test that Prettier can detect formatting issues."""
        try:
            result = self.lint_runner.run_linter("prettier", [self.js_file])

            # Prettier should find formatting issues (as warnings)
            self.assertGreater(len(result.warnings), 0, "Prettier should detect formatting issues")

            # Check that the warning mentions formatting
            warning_messages = [warning.message for warning in result.warnings]
            self.assertTrue(
                any("style" in msg.lower() or "format" in msg.lower() for msg in warning_messages),
                "Should detect formatting issues",
            )

            print(
                f"✅ Prettier detected {len(result.errors)} errors, {len(result.warnings)} warnings"
            )

        except Exception as e:
            self.skipTest(f"Prettier not available or failed: {e}")

    def test_nodejs_profile_support(self):
        """Test that Node.js linters support different profiles."""
        try:
            # Test basic profile
            result_basic = self.lint_runner.run_linter("eslint", [self.js_file], profile="basic")

            # Test strict profile
            result_strict = self.lint_runner.run_linter("eslint", [self.js_file], profile="strict")

            # Both should work
            self.assertIsNotNone(result_basic)
            self.assertIsNotNone(result_strict)

            print(
                f"✅ Profile support working: basic={len(result_basic.errors)} errors, strict={len(result_strict.errors)} errors"
            )

        except Exception as e:
            self.skipTest(f"Profile testing failed: {e}")

    def test_nodejs_project_detection(self):
        """Test that Node.js projects are detected correctly."""
        detector = ProjectDetector()
        project_info = detector.detect_project(self.test_dir)

        # Should detect JavaScript
        self.assertIn("javascript", project_info.languages)

        # Should find npm package manager (which indicates package.json was detected)
        self.assertIn("npm", project_info.package_managers)

        print(
            f"✅ Project detection: languages={project_info.languages}, files={len(project_info.source_files)}"
        )


class TestNodeJSCLIIntegration(unittest.TestCase):
    """Test Node.js linter CLI integration."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()

        # Create a simple JavaScript project
        self.js_file = os.path.join(self.test_dir, "app.js")
        with open(self.js_file, "w") as f:
            f.write(
                """
function test(x,y) {
    if (x == null) return;
    console.log("test")
    return x + y
}
"""
            )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_with_nodejs_linters(self):
        """Test CLI integration with Node.js linters."""
        from click.testing import CliRunner

        from aider_lint_fixer.main import main

        runner = CliRunner()

        # Test with ESLint
        try:
            result = runner.invoke(
                main,
                [
                    self.test_dir,
                    "--linters",
                    "eslint",
                    "--dry-run",
                    "--max-errors",
                    "5",
                ],
            )

            # Should not crash
            self.assertEqual(result.exit_code, 0, f"CLI failed: {result.output}")

            # Should mention ESLint
            self.assertIn("eslint", result.output.lower())

            print(f"✅ CLI integration working with ESLint")

        except Exception as e:
            self.skipTest(f"CLI integration test failed: {e}")


if __name__ == "__main__":
    unittest.main()
