#!/usr/bin/env python3
"""
Unit tests for aider integration functionality.
"""

import os

# Add the parent directory to the path so we can import our modules
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from aider_lint_fixer.aider_integration import AiderIntegration
from aider_lint_fixer.config_manager import Config, ConfigManager
from aider_lint_fixer.lint_runner import ErrorSeverity, LintError


class TestAiderIntegration(unittest.TestCase):
    """Test cases for AiderIntegration class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create a mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.llm = Mock()
        self.mock_config.llm.provider = "deepseek"
        self.mock_config.llm.model = "deepseek/deepseek-chat"
        self.mock_config.aider = Mock()
        self.mock_config.aider.auto_commit = False

        # Create a mock config manager with proper return value
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_config_manager.get_api_key_for_provider.return_value = "sk-test123456789"

        # Create test files
        self.test_file = self.project_root / "test_file.py"
        self.test_file.write_text('print("hello world")\n')

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init_with_config_manager(self):
        """Test AiderIntegration initialization with config manager."""
        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        self.assertEqual(integration.config, self.mock_config)
        self.assertEqual(integration.config_manager, self.mock_config_manager)
        self.assertEqual(integration.project_root, self.project_root)

    def test_get_api_key_for_provider_with_config_manager(self):
        """Test API key retrieval with config manager."""
        # Setup mock to return API key
        test_api_key = "sk-test123456789"
        self.mock_config_manager.get_api_key_for_provider.return_value = test_api_key

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        result = integration._get_api_key_for_provider("deepseek")

        self.assertEqual(result, test_api_key)
        # Note: The method gets called during __init__ and again here, so we check it was called
        self.mock_config_manager.get_api_key_for_provider.assert_called_with("deepseek")

    def test_get_api_key_for_provider_fallback_to_env(self):
        """Test API key retrieval fallback to environment variables."""
        # No config manager provided
        integration = AiderIntegration(self.mock_config, str(self.project_root), None)

        test_api_key = "sk-env123456789"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": test_api_key}):
            result = integration._get_api_key_for_provider("deepseek")
            self.assertEqual(result, test_api_key)

    def test_get_api_key_for_provider_not_found(self):
        """Test API key retrieval when key is not found."""
        # Mock config manager returns None
        self.mock_config_manager.get_api_key_for_provider.return_value = None

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Ensure environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            result = integration._get_api_key_for_provider("deepseek")
            self.assertIsNone(result)

    def test_create_aider_config_with_api_key(self):
        """Test .aider.conf.yml creation with API key."""
        test_api_key = "sk-test123456789"
        self.mock_config_manager.get_api_key_for_provider.return_value = test_api_key

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Call the method
        integration._create_aider_config(self.mock_config.llm)

        # Check if config file was created
        config_file = self.project_root / ".aider.conf.yml"
        self.assertTrue(config_file.exists())

        # Check config file contents
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        self.assertEqual(config_data["model"], "deepseek/deepseek-chat")
        self.assertEqual(config_data["api-key"]["deepseek"], test_api_key)
        self.assertEqual(config_data["auto-commits"], False)
        self.assertTrue(config_data["yes"])
        self.assertTrue(config_data["no-pretty"])

    def test_create_aider_config_without_api_key(self):
        """Test .aider.conf.yml creation without API key."""
        self.mock_config_manager.get_api_key_for_provider.return_value = None

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Call the method
        integration._create_aider_config(self.mock_config.llm)

        # Check if config file was created
        config_file = self.project_root / ".aider.conf.yml"
        self.assertTrue(config_file.exists())

        # Check config file contents
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        self.assertEqual(config_data["model"], "deepseek/deepseek-chat")
        self.assertNotIn("api-key", config_data)  # Should not have api-key section

    def test_build_aider_command_basic(self):
        """Test basic aider command building."""
        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Mock the aider executable
        integration.aider_executable = "aider"

        command = integration._build_aider_command("test_file.py", "Fix this file")

        expected_parts = [
            "aider",
            "--model",
            "deepseek/deepseek-chat",
            "--yes",
            "--no-pretty",
            "--no-auto-commits",
            "--message",
            "Fix this file",
            "test_file.py",
        ]

        self.assertEqual(command, expected_parts)

    def test_build_aider_command_with_relative_path(self):
        """Test aider command building with relative path cleanup."""
        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Mock the aider executable
        integration.aider_executable = "aider"

        command = integration._build_aider_command("./test_file.py", "Fix this file")

        # Should remove ./ prefix
        self.assertIn("test_file.py", command)
        self.assertNotIn("./test_file.py", command)

    @patch("aider_lint_fixer.aider_integration.AiderIntegration._find_aider_executable")
    @patch("subprocess.run")
    def test_run_aider_fix_success(self, mock_subprocess, mock_find_aider):
        """Test successful aider fix execution."""
        # Mock aider executable
        mock_find_aider.return_value = "aider"

        # Setup mock subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully fixed the file"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Mock the aider executable
        integration.aider_executable = "aider"

        # Create a test lint error
        lint_error = LintError(
            file_path="test_file.py",
            line=1,
            column=1,
            rule_id="E302",
            message="expected 2 blank lines, found 1",
            severity=ErrorSeverity.ERROR,
            linter="flake8",
        )

        result = integration._run_aider_fix("test_file.py", "test prompt", "test-session-id")

        self.assertTrue(result["success"])
        self.assertIn("Successfully fixed", result["output"])

    @patch("aider_lint_fixer.aider_integration.AiderIntegration._find_aider_executable")
    @patch("subprocess.run")
    def test_run_aider_fix_failure(self, mock_subprocess, mock_find_aider):
        """Test aider fix execution failure."""
        # Mock aider executable
        mock_find_aider.return_value = "aider"

        # Setup mock subprocess result for failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Authentication error"
        mock_subprocess.return_value = mock_result

        integration = AiderIntegration(
            self.mock_config, str(self.project_root), self.mock_config_manager
        )

        # Mock the aider executable
        integration.aider_executable = "aider"

        # Create a test lint error
        lint_error = LintError(
            file_path="test_file.py",
            line=1,
            column=1,
            rule_id="E302",
            message="expected 2 blank lines, found 1",
            severity=ErrorSeverity.ERROR,
            linter="flake8",
        )

        result = integration._run_aider_fix("test_file.py", "test prompt", "test-session-id")

        self.assertFalse(result["success"])
        self.assertIn("Authentication error", result["error"])


class TestConfigManagerIntegration(unittest.TestCase):
    """Test cases for ConfigManager API key functionality."""

    def test_config_manager_api_key_retrieval(self):
        """Test that ConfigManager can retrieve API keys from environment."""
        test_api_key = "sk-test123456789"

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": test_api_key}):
            config_manager = ConfigManager()
            result = config_manager.get_api_key_for_provider("deepseek")
            self.assertEqual(result, test_api_key)

    def test_real_world_integration(self):
        """Test the exact scenario from our application."""
        test_api_key = "sk-test123456789"

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": test_api_key}):
            # Create real ConfigManager and Config like in main.py
            config_manager = ConfigManager()
            project_config = config_manager.load_config("/tmp")  # Use temp path

            # Create AiderIntegration like in main.py
            with patch(
                "aider_lint_fixer.aider_integration.AiderIntegration._find_aider_executable"
            ) as mock_find:
                mock_find.return_value = "aider"

                integration = AiderIntegration(project_config, "/tmp", config_manager)

                # Test API key retrieval
                api_key = integration._get_api_key_for_provider("deepseek")
                self.assertEqual(api_key, test_api_key)

                # Test config file creation
                integration._create_aider_config(project_config.llm)

                # Check if config file was created with API key
                config_file = Path("/tmp/.aider.conf.yml")
                self.assertTrue(config_file.exists())

                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)

                self.assertIn("api-key", config_data)
                self.assertEqual(config_data["api-key"]["deepseek"], test_api_key)

                # Clean up
                config_file.unlink()

    def test_debug_actual_issue(self):
        """Debug the actual issue by checking environment and config loading."""
        # Check if DEEPSEEK_API_KEY is in current environment
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        print(f"DEEPSEEK_API_KEY in environment: {bool(deepseek_key)}")
        if deepseek_key:
            print(f"DEEPSEEK_API_KEY value: {deepseek_key[:10]}...")

        # Test ConfigManager creation and API key retrieval
        config_manager = ConfigManager()
        api_key = config_manager.get_api_key_for_provider("deepseek")
        print(f"ConfigManager.get_api_key_for_provider('deepseek'): {bool(api_key)}")
        if api_key:
            print(f"API key value: {api_key[:10]}...")

        # Test with the actual project path
        project_path = "/Users/tosinakinosho/workspaces/aider-lint-fixer/test/autotrain-repo"
        project_config = config_manager.load_config(project_path)
        print(f"Project config loaded: {bool(project_config)}")
        print(f"LLM provider: {project_config.llm.provider}")

        # Test AiderIntegration creation
        with patch(
            "aider_lint_fixer.aider_integration.AiderIntegration._find_aider_executable"
        ) as mock_find:
            mock_find.return_value = "aider"

            integration = AiderIntegration(project_config, project_path, config_manager)
            test_api_key = integration._get_api_key_for_provider("deepseek")
            print(f"AiderIntegration API key: {bool(test_api_key)}")
            if test_api_key:
                print(f"Integration API key value: {test_api_key[:10]}...")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
