#!/usr/bin/env python3
"""
Tests for supported_versions module.

Tests version compatibility checks, linter information retrieval,
and platform compatibility features.
"""

import platform
import unittest
from unittest.mock import patch

from aider_lint_fixer.supported_versions import (
    ALL_LINTERS,
    ANSIBLE_LINTERS,
    NODEJS_LINTERS,
    PROFILES,
    PYTHON_LINTERS,
    LinterVersion,
    generate_version_table,
    get_installation_commands,
    get_linter_info,
    get_linters_by_language,
    get_platform_compatibility_info,
    get_supported_linters,
    is_version_supported,
)


class TestLinterVersion(unittest.TestCase):
    """Test LinterVersion NamedTuple."""

    def test_linter_version_creation(self):
        """Test creating LinterVersion objects."""
        version = LinterVersion(
            name="test-linter",
            tested_version="1.0.0",
            supported_versions=["1.0.0", "1.0", "1."],
            profile_support=True,
            file_extensions=[".py"],
            installation_command="pip install test-linter",
        )

        self.assertEqual(version.name, "test-linter")
        self.assertEqual(version.tested_version, "1.0.0")
        self.assertEqual(version.supported_versions, ["1.0.0", "1.0", "1."])
        self.assertTrue(version.profile_support)
        self.assertEqual(version.file_extensions, [".py"])
        self.assertEqual(version.installation_command, "pip install test-linter")

    def test_linter_version_immutability(self):
        """Test that LinterVersion is immutable."""
        version = LinterVersion(
            name="test-linter",
            tested_version="1.0.0",
            supported_versions=["1.0.0"],
            profile_support=True,
            file_extensions=[".py"],
            installation_command="pip install test-linter",
        )

        with self.assertRaises(AttributeError):
            version.name = "changed-name"


class TestLinterDefinitions(unittest.TestCase):
    """Test predefined linter definitions."""

    def test_ansible_linters_defined(self):
        """Test that Ansible linters are properly defined."""
        self.assertIn("ansible-lint", ANSIBLE_LINTERS)
        
        ansible_lint = ANSIBLE_LINTERS["ansible-lint"]
        self.assertEqual(ansible_lint.name, "ansible-lint")
        self.assertTrue(ansible_lint.tested_version)
        self.assertTrue(ansible_lint.supported_versions)
        self.assertTrue(ansible_lint.profile_support)
        self.assertIn(".yml", ansible_lint.file_extensions)
        self.assertIn(".yaml", ansible_lint.file_extensions)
        self.assertIn("pip install", ansible_lint.installation_command)

    def test_python_linters_defined(self):
        """Test that Python linters are properly defined."""
        expected_python_linters = ["flake8", "pylint"]
        
        for linter_name in expected_python_linters:
            self.assertIn(linter_name, PYTHON_LINTERS)
            
            linter = PYTHON_LINTERS[linter_name]
            self.assertTrue(linter.name)
            self.assertTrue(linter.tested_version)
            self.assertTrue(linter.supported_versions)
            self.assertTrue(linter.profile_support)
            self.assertIn(".py", linter.file_extensions)
            self.assertIn("pip install", linter.installation_command)

    def test_nodejs_linters_defined(self):
        """Test that Node.js linters are properly defined."""
        expected_nodejs_linters = ["eslint", "jshint", "prettier"]
        
        for linter_name in expected_nodejs_linters:
            self.assertIn(linter_name, NODEJS_LINTERS)
            
            linter = NODEJS_LINTERS[linter_name]
            self.assertTrue(linter.name)
            self.assertTrue(linter.tested_version)
            self.assertTrue(linter.supported_versions)
            self.assertTrue(linter.profile_support)
            self.assertTrue(linter.file_extensions)
            self.assertIn("npm install", linter.installation_command)

    def test_all_linters_combination(self):
        """Test that ALL_LINTERS contains all linter types."""
        expected_count = len(ANSIBLE_LINTERS) + len(PYTHON_LINTERS) + len(NODEJS_LINTERS)
        self.assertEqual(len(ALL_LINTERS), expected_count)
        
        # Verify all linters are present
        for linter_name in ANSIBLE_LINTERS:
            self.assertIn(linter_name, ALL_LINTERS)
        for linter_name in PYTHON_LINTERS:
            self.assertIn(linter_name, ALL_LINTERS)
        for linter_name in NODEJS_LINTERS:
            self.assertIn(linter_name, ALL_LINTERS)

    def test_profiles_defined(self):
        """Test that profiles are properly defined."""
        expected_profiles = ["basic", "default", "strict", "production"]
        
        for profile_name in expected_profiles:
            self.assertIn(profile_name, PROFILES)
            
            profile = PROFILES[profile_name]
            self.assertIn("description", profile)
            self.assertIn("recommended_for", profile)
            self.assertIn("characteristics", profile)
            self.assertTrue(profile["description"])
            self.assertTrue(profile["recommended_for"])
            self.assertTrue(profile["characteristics"])


class TestGetLinterInfo(unittest.TestCase):
    """Test get_linter_info function."""

    def test_get_valid_linter_info(self):
        """Test getting info for valid linters."""
        # Test Ansible linter
        ansible_info = get_linter_info("ansible-lint")
        self.assertEqual(ansible_info.name, "ansible-lint")
        self.assertTrue(ansible_info.tested_version)
        
        # Test Python linter
        flake8_info = get_linter_info("flake8")
        self.assertEqual(flake8_info.name, "flake8")
        self.assertTrue(flake8_info.tested_version)
        
        # Test Node.js linter
        eslint_info = get_linter_info("eslint")
        self.assertEqual(eslint_info.name, "ESLint")
        self.assertTrue(eslint_info.tested_version)

    def test_get_invalid_linter_info(self):
        """Test getting info for invalid linters."""
        with self.assertRaises(KeyError) as context:
            get_linter_info("nonexistent-linter")
        
        self.assertIn("not supported", str(context.exception))
        self.assertIn("Supported linters:", str(context.exception))

    def test_get_linter_info_case_sensitive(self):
        """Test that linter names are case-sensitive."""
        with self.assertRaises(KeyError):
            get_linter_info("FLAKE8")  # Should be "flake8"
        
        with self.assertRaises(KeyError):
            get_linter_info("ESLint")  # Should be "eslint"


class TestGetSupportedLinters(unittest.TestCase):
    """Test get_supported_linters function."""

    def test_get_supported_linters_linux(self):
        """Test getting supported linters on Linux."""
        with patch('platform.system', return_value='Linux'):
            supported = get_supported_linters()
            
            # Should include all linters on Linux
            self.assertIn("ansible-lint", supported)
            self.assertIn("flake8", supported)
            self.assertIn("pylint", supported)
            self.assertIn("eslint", supported)
            self.assertIn("jshint", supported)
            self.assertIn("prettier", supported)

    def test_get_supported_linters_windows(self):
        """Test getting supported linters on Windows."""
        with patch('platform.system', return_value='Windows'):
            supported = get_supported_linters()
            
            # Should exclude ansible-lint on Windows
            self.assertNotIn("ansible-lint", supported)
            
            # Should include other linters
            self.assertIn("flake8", supported)
            self.assertIn("pylint", supported)
            self.assertIn("eslint", supported)
            self.assertIn("jshint", supported)
            self.assertIn("prettier", supported)

    def test_get_supported_linters_mac(self):
        """Test getting supported linters on macOS."""
        with patch('platform.system', return_value='Darwin'):
            supported = get_supported_linters()
            
            # Should include all linters on macOS
            self.assertIn("ansible-lint", supported)
            self.assertIn("flake8", supported)
            self.assertIn("pylint", supported)
            self.assertIn("eslint", supported)
            self.assertIn("jshint", supported)
            self.assertIn("prettier", supported)


class TestPlatformCompatibility(unittest.TestCase):
    """Test platform compatibility functions."""

    def test_platform_compatibility_info_linux(self):
        """Test platform compatibility info on Linux."""
        with patch('platform.system', return_value='Linux'):
            compatibility = get_platform_compatibility_info()
            
            # Should be empty for Linux (all linters supported)
            self.assertEqual(len(compatibility), 0)

    def test_platform_compatibility_info_windows(self):
        """Test platform compatibility info on Windows."""
        with patch('platform.system', return_value='Windows'):
            compatibility = get_platform_compatibility_info()
            
            # Should have ansible-lint compatibility note
            self.assertIn("ansible-lint", compatibility)
            self.assertIn("Not available on Windows", compatibility["ansible-lint"])

    def test_platform_compatibility_info_mac(self):
        """Test platform compatibility info on macOS."""
        with patch('platform.system', return_value='Darwin'):
            compatibility = get_platform_compatibility_info()
            
            # Should be empty for macOS (all linters supported)
            self.assertEqual(len(compatibility), 0)


class TestGetLintersByLanguage(unittest.TestCase):
    """Test get_linters_by_language function."""

    def test_get_ansible_linters(self):
        """Test getting Ansible linters."""
        ansible_linters = get_linters_by_language("ansible")
        
        self.assertEqual(ansible_linters, ANSIBLE_LINTERS)
        self.assertIn("ansible-lint", ansible_linters)

    def test_get_python_linters(self):
        """Test getting Python linters."""
        python_linters = get_linters_by_language("python")
        
        self.assertEqual(python_linters, PYTHON_LINTERS)
        self.assertIn("flake8", python_linters)
        self.assertIn("pylint", python_linters)

    def test_get_nodejs_linters(self):
        """Test getting Node.js linters."""
        nodejs_linters = get_linters_by_language("nodejs")
        
        self.assertEqual(nodejs_linters, NODEJS_LINTERS)
        self.assertIn("eslint", nodejs_linters)
        self.assertIn("jshint", nodejs_linters)
        self.assertIn("prettier", nodejs_linters)

    def test_get_javascript_linters_alias(self):
        """Test getting JavaScript linters (alias for nodejs)."""
        javascript_linters = get_linters_by_language("javascript")
        
        self.assertEqual(javascript_linters, NODEJS_LINTERS)

    def test_get_typescript_linters_alias(self):
        """Test getting TypeScript linters (alias for nodejs)."""
        typescript_linters = get_linters_by_language("typescript")
        
        self.assertEqual(typescript_linters, NODEJS_LINTERS)

    def test_get_linters_case_insensitive(self):
        """Test that language matching is case-insensitive."""
        # Test uppercase
        python_linters_upper = get_linters_by_language("PYTHON")
        self.assertEqual(python_linters_upper, PYTHON_LINTERS)
        
        # Test mixed case
        nodejs_linters_mixed = get_linters_by_language("NodeJS")
        self.assertEqual(nodejs_linters_mixed, NODEJS_LINTERS)

    def test_get_unknown_language_linters(self):
        """Test getting linters for unknown language."""
        unknown_linters = get_linters_by_language("unknown")
        
        self.assertEqual(unknown_linters, {})


class TestIsVersionSupported(unittest.TestCase):
    """Test is_version_supported function."""

    def test_exact_version_match(self):
        """Test exact version matching."""
        # Test exact match for flake8
        self.assertTrue(is_version_supported("flake8", "7.3.0"))
        
        # Test exact match for ansible-lint
        self.assertTrue(is_version_supported("ansible-lint", "25.6.1"))

    def test_prefix_version_match(self):
        """Test prefix version matching."""
        # Test prefix matches for flake8 (based on actual supported_versions)
        self.assertTrue(is_version_supported("flake8", "7.2.5"))  # matches "7.2"
        self.assertTrue(is_version_supported("flake8", "7.1.0"))  # matches "7.1"
        self.assertTrue(is_version_supported("flake8", "7.0.0"))  # matches "7.0"
        self.assertTrue(is_version_supported("flake8", "6.5.0"))  # matches "6."
        
        # Test prefix matches for ansible-lint
        self.assertTrue(is_version_supported("ansible-lint", "25.6.2"))  # matches "25.6"
        self.assertTrue(is_version_supported("ansible-lint", "25.7.0"))  # matches "25."

    def test_unsupported_versions(self):
        """Test unsupported version detection."""
        # Test unsupported versions for flake8
        self.assertFalse(is_version_supported("flake8", "5.9.0"))  # Too old
        self.assertFalse(is_version_supported("flake8", "8.0.0"))  # Too new
        
        # Test unsupported versions for ansible-lint
        self.assertFalse(is_version_supported("ansible-lint", "24.0.0"))  # Too old
        self.assertFalse(is_version_supported("ansible-lint", "26.0.0"))  # Too new

    def test_invalid_linter_version_check(self):
        """Test version checking for invalid linters."""
        self.assertFalse(is_version_supported("nonexistent-linter", "1.0.0"))

    def test_empty_version_string(self):
        """Test version checking with empty version string."""
        self.assertFalse(is_version_supported("flake8", ""))

    def test_malformed_version_string(self):
        """Test version checking with malformed version strings."""
        self.assertFalse(is_version_supported("flake8", "not-a-version"))
        self.assertFalse(is_version_supported("flake8", "v7.3.0"))  # prefix not supported


class TestGetInstallationCommands(unittest.TestCase):
    """Test get_installation_commands function."""

    def test_installation_commands_structure(self):
        """Test that installation commands have correct structure."""
        commands = get_installation_commands()
        
        # Check expected languages are present
        self.assertIn("ansible", commands)
        self.assertIn("python", commands)
        self.assertIn("nodejs", commands)
        
        # Check that each language has commands
        self.assertTrue(commands["ansible"])
        self.assertTrue(commands["python"])
        self.assertTrue(commands["nodejs"])

    def test_installation_commands_content(self):
        """Test that installation commands contain expected content."""
        commands = get_installation_commands()
        
        # Check Ansible commands
        ansible_commands = commands["ansible"]
        self.assertTrue(any("ansible-lint" in cmd for cmd in ansible_commands))
        self.assertTrue(any("pip install" in cmd for cmd in ansible_commands))
        
        # Check Python commands
        python_commands = commands["python"]
        self.assertTrue(any("flake8" in cmd for cmd in python_commands))
        self.assertTrue(any("pylint" in cmd for cmd in python_commands))
        self.assertTrue(all("pip install" in cmd for cmd in python_commands))
        
        # Check Node.js commands
        nodejs_commands = commands["nodejs"]
        self.assertTrue(any("eslint" in cmd for cmd in nodejs_commands))
        self.assertTrue(any("jshint" in cmd for cmd in nodejs_commands))
        self.assertTrue(any("prettier" in cmd for cmd in nodejs_commands))
        self.assertTrue(all("npm install" in cmd for cmd in nodejs_commands))


class TestGenerateVersionTable(unittest.TestCase):
    """Test generate_version_table function."""

    def test_version_table_format(self):
        """Test that version table has correct format."""
        table = generate_version_table()
        
        # Check that it's a markdown table
        self.assertIn("| Linter | Tested Version | Supported Versions | Profile Support |", table)
        self.assertIn("|--------|----------------|-------------------|------------------|", table)
        
        # Check that all linters are included
        for linter_name, info in ALL_LINTERS.items():
            self.assertIn(info.name, table)
            self.assertIn(info.tested_version, table)

    def test_version_table_content(self):
        """Test that version table contains expected content."""
        table = generate_version_table()
        
        # Check for specific linters
        self.assertIn("ansible-lint", table)
        self.assertIn("flake8", table)
        self.assertIn("ESLint", table)
        
        # Check for profile support indicators
        self.assertIn("✅", table)  # Should have profile support indicators
        
        # Check for version formatting
        self.assertIn("`", table)  # Should have code formatting for versions


class TestMainExecution(unittest.TestCase):
    """Test main execution functionality."""

    @patch('builtins.print')
    def test_main_execution_output(self, mock_print):
        """Test that main execution produces expected output."""
        # Import and execute the main block
        import runpy
        
        with patch('sys.argv', ['supported_versions.py']):
            try:
                runpy.run_module('aider_lint_fixer.supported_versions', run_name='__main__')
            except SystemExit:
                pass
        
        # Check that print was called with expected content
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        # Should print header
        header_found = any("Aider Lint Fixer - Supported Versions" in str(call) for call in print_calls)
        self.assertTrue(header_found)
        
        # Should print linter categories
        ansible_found = any("Ansible Linters:" in str(call) for call in print_calls)
        python_found = any("Python Linters:" in str(call) for call in print_calls)
        nodejs_found = any("Node.js Linters:" in str(call) for call in print_calls)
        
        self.assertTrue(ansible_found)
        self.assertTrue(python_found)
        self.assertTrue(nodejs_found)
        
        # Should print installation commands
        installation_found = any("Installation Commands:" in str(call) for call in print_calls)
        self.assertTrue(installation_found)


if __name__ == "__main__":
    unittest.main()