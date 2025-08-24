#!/usr/bin/env python3
"""
Integration tests for ansible-lint support in aider-lint-fixer.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position
from aider_lint_fixer.lint_runner import LintRunner  # noqa: E402
from aider_lint_fixer.project_detector import ProjectDetector, ProjectInfo  # noqa: E402


class TestAnsibleLintIntegration(unittest.TestCase):
    """Integration tests for ansible-lint functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create a problematic Ansible playbook (based on our test script findings)
        self.playbook_content = """---
- hosts: localhost
  tasks:
  - shell: echo "test"
  - debug: msg="test"
"""

        self.playbook_path = self.project_root / "playbook.yml"
        self.playbook_path.write_text(self.playbook_content)

        # Create project info
        self.project_info = ProjectInfo(
            root_path=str(self.project_root),
            languages={"ansible"},
            package_managers=set(),
            lint_configs=[],
            source_files=[str(self.playbook_path)],
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_ansible_lint_availability(self):
        """Test that ansible-lint is available and can be detected."""
        lint_runner = LintRunner(self.project_info)
        available_linters = lint_runner._detect_available_linters(["ansible-lint"])

        # Skip test if ansible-lint is not installed
        if not available_linters.get("ansible-lint", False):
            self.skipTest("ansible-lint not installed")

        self.assertTrue(available_linters["ansible-lint"])

    def test_ansible_lint_detects_errors(self):
        """Test that ansible-lint can detect errors in problematic playbooks."""
        # Test both modular and legacy implementations
        self._test_modular_implementation()
        self._test_legacy_implementation()

    def _test_modular_implementation(self):
        """Test the new modular ansible-lint implementation."""
        try:
            from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
        except ImportError:
            self.skipTest("Modular ansible-lint implementation not available")

        # Create modular linter
        linter = AnsibleLintLinter(str(self.project_root))

        # Skip test if ansible-lint is not installed
        if not linter.is_available():
            self.skipTest("ansible-lint not installed")

        # Test basic profile
        result = linter.run_with_profile("basic", [str(self.playbook_path)])

        # Should find errors in our problematic playbook
        self.assertTrue(result.success)  # Should succeed even with errors found
        self.assertGreater(
            len(result.errors), 0, "Should detect lint errors in problematic playbook"
        )

        # Verify error structure
        first_error = result.errors[0]
        self.assertIsInstance(first_error.file_path, str)
        self.assertIsInstance(first_error.line, int)
        self.assertIsInstance(first_error.rule_id, str)
        self.assertIsInstance(first_error.message, str)
        self.assertEqual(first_error.linter, "ansible-lint")

        print(f"✅ Modular implementation: {len(result.errors)} errors detected")

    def _test_legacy_implementation(self):
        """Test the legacy ansible-lint implementation for comparison."""
        lint_runner = LintRunner(self.project_info)

        # Skip test if ansible-lint is not installed
        available_linters = lint_runner._detect_available_linters(["ansible-lint"])
        if not available_linters.get("ansible-lint", False):
            self.skipTest("ansible-lint not installed")

        # Force legacy implementation by testing specific file
        result = lint_runner.run_linter("ansible-lint", [str(self.playbook_path)])

        print(f"✅ Legacy implementation: {len(result.errors)} errors detected")
        print(f"   Raw output preview: {result.raw_output[:100]}")

        # Note: Legacy implementation might have different behavior

        # Check that we get reasonable error information
        if len(result.errors) > 0:
            first_error = result.errors[0]
            self.assertEqual(first_error.file_path, "playbook.yml")
            self.assertGreater(first_error.line, 0)
            self.assertIsNotNone(first_error.rule_id)
            self.assertIsNotNone(first_error.message)

    def test_ansible_lint_json_parsing(self):
        """Test that ansible-lint JSON output is parsed correctly."""
        try:
            from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
        except ImportError:
            self.skipTest("Modular ansible-lint implementation not available")

        # Create modular linter
        linter = AnsibleLintLinter(str(self.project_root))

        # Skip test if ansible-lint is not installed
        if not linter.is_available():
            self.skipTest("ansible-lint not installed")

        # Test with real ansible-lint output (saved from our debugging)
        sample_output = (
            """[{"type": "issue", "check_name": "name[play]", "categories": ["idiom"], """
            """"url": "https://ansible.readthedocs.io/projects/lint/rules/name/", """
            """"severity": "major", "description": "All plays should be named.","""
            """"fingerprint": "695eeb9d297c19090389897ca43f1dc7880f825960fa9bfd401749ba9e784999","""
            """"location": {"path": "playbook.yml", "lines": {"begin": 2}}}]"""
        )

        # Test our parsing logic directly
        errors, warnings = linter.parse_output(sample_output, "", 2)

        # Should parse the JSON correctly
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(warnings), 0)

        # Verify error structure
        error = errors[0]
        self.assertIsInstance(error.file_path, str)
        self.assertIsInstance(error.line, int)
        self.assertIsInstance(error.column, int)
        self.assertIsInstance(error.rule_id, str)
        self.assertIsInstance(error.message, str)
        self.assertEqual(error.linter, "ansible-lint")
        self.assertEqual(error.rule_id, "name[play]")
        self.assertEqual(error.line, 2)

    def test_ansible_lint_profile_support(self):
        """Test that ansible-lint supports different profiles."""
        try:
            from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
        except ImportError:
            self.skipTest("Modular ansible-lint implementation not available")

        # Create modular linter
        linter = AnsibleLintLinter(str(self.project_root))

        # Skip test if ansible-lint is not installed
        if not linter.is_available():
            self.skipTest("ansible-lint not installed")

        # Test basic profile
        basic_result = linter.run_with_profile("basic", [str(self.playbook_path)])

        # Test production profile
        production_result = linter.run_with_profile("production", [str(self.playbook_path)])

        # Both should succeed (even with errors found)
        self.assertTrue(basic_result.success)
        self.assertTrue(production_result.success)

        # Production profile should find same or more errors than basic
        self.assertGreaterEqual(len(production_result.errors), len(basic_result.errors))

        print(f"✅ Basic profile: {len(basic_result.errors)} errors")
        print(f"✅ Production profile: {len(production_result.errors)} errors")

    def test_ansible_project_detection(self):
        """Test that Ansible projects are detected correctly."""
        detector = ProjectDetector()
        project_info = detector.detect_project(str(self.project_root))

        self.assertIn("ansible", project_info.languages)
        self.assertEqual(len(project_info.source_files), 1)
        self.assertTrue(any(str(f).endswith(".yml") for f in project_info.source_files))

    def test_ansible_error_categorization(self):
        """Test that ansible-lint errors are categorized correctly."""
        from aider_lint_fixer.error_analyzer import ErrorAnalyzer

        lint_runner = LintRunner(self.project_info)

        # Skip test if ansible-lint is not installed
        available_linters = lint_runner._detect_available_linters(["ansible-lint"])
        if not available_linters.get("ansible-lint", False):
            self.skipTest("ansible-lint not installed")

        # Run ansible-lint
        result = lint_runner.run_linter("ansible-lint")

        if len(result.errors) > 0:
            # Analyze errors - need to pass results in the expected format
            analyzer = ErrorAnalyzer(project_root=self.temp_dir)
            results_dict = {"ansible-lint": result}
            analyzed_errors = analyzer.analyze_errors(results_dict)

            # Should have categorized the errors
            self.assertGreater(len(analyzed_errors), 0)

            # Check that errors have categories
            for file_path, file_analysis in analyzed_errors.items():
                self.assertIsNotNone(file_analysis)
                for error_analysis in file_analysis.error_analyses:
                    self.assertIsNotNone(error_analysis.category)
                    self.assertIsNotNone(error_analysis.fix_strategy)

    @patch("aider_lint_fixer.aider_integration.AiderIntegration._find_aider_executable")
    @patch("subprocess.run")
    def test_ansible_lint_with_aider_integration(self, mock_subprocess, mock_find_aider):
        """Test that ansible-lint errors can be processed by aider integration."""
        # Skip test if ansible-lint is not installed
        lint_runner = LintRunner(self.project_info)
        available_linters = lint_runner._detect_available_linters(["ansible-lint"])
        if not available_linters.get("ansible-lint", False):
            self.skipTest("ansible-lint not installed")

        # Mock aider executable
        mock_find_aider.return_value = "aider"

        # Mock successful aider execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully fixed ansible-lint issues"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Test the integration
        from aider_lint_fixer.aider_integration import AiderIntegration
        from aider_lint_fixer.config_manager import Config

        config = Config()
        config.llm.provider = "deepseek"
        config.llm.model = "deepseek/deepseek-chat"

        # Mock config manager for API key
        mock_config_manager = Mock()
        mock_config_manager.get_api_key_for_provider.return_value = "test-api-key"

        integration = AiderIntegration(config, str(self.project_root), mock_config_manager)

        # Run lint and get errors
        lint_result = lint_runner.run_linter("ansible-lint")

        if len(lint_result.errors) > 0:
            # Test that aider integration can process the errors
            integration._run_aider_fix(
                "playbook.yml", lint_result.errors[:3]
            )  # Test with first 3 errors

            # Should have attempted to fix
            self.assertTrue(mock_subprocess.called)

            # Check that the command was built correctly
            call_args = mock_subprocess.call_args
            command = call_args[0][0]
            self.assertIn("aider", command)
            self.assertIn("--model", command)
            self.assertIn("deepseek/deepseek-chat", command)
            self.assertIn("playbook.yml", command)


class TestAnsibleLintCLIIntegration(unittest.TestCase):
    """Test ansible-lint integration through the CLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create a simple playbook with issues
        playbook_content = """---
- hosts: localhost
  tasks:
  - shell: echo "test"
  - debug: msg="test"
"""
        (self.project_root / "test.yml").write_text(playbook_content)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_cli_with_ansible_lint(self):
        """Test running the CLI with ansible-lint on an Ansible project."""
        # Check if ansible-lint is available
        try:
            subprocess.run(
                ["ansible-lint", "--version"],
                capture_output=True,
                check=True,
                timeout=10,
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            self.skipTest("ansible-lint not available")

        # Test CLI execution (dry run to avoid needing API keys)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            # This would normally require a real API key, so we'll just test argument parsing
            try:
                result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "aider_lint_fixer",
                        str(self.project_root),
                        "--linters",
                        "ansible-lint",
                        "--dry-run",
                        "--no-banner",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Should not crash and should detect the project
                self.assertIn("ansible", result.stdout.lower())

            except subprocess.TimeoutExpired:
                self.skipTest("CLI test timed out")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
