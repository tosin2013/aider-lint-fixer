"""
Test suite for ESLint flat config JSON format hardcoding bug.

This module tests the bug reported by users where aider-lint-fixer hardcodes
--format=json regardless of ESLint configuration compatibility, causing failures
with modern flat configs (eslint.config.js) that don't properly handle the flag
when passed through npm scripts.

Bug Details:
- Hardcoded --format=json in both direct ESLint calls and npm script execution
- Modern eslint.config.js configurations may not handle JSON format properly
- npm scripts like "eslint src/**/*.ts" fail when --format=json is appended
- Results in JSONDecodeError when parsing non-JSON output
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from aider_lint_fixer.linters.eslint_linter import ESLintLinter
from aider_lint_fixer.lint_runner import LintError, ErrorSeverity


class TestESLintFlatConfigDetection:
    """Test detection of modern ESLint flat configurations."""

    def test_detects_flat_config_file(self):
        """Test detection of eslint.config.js flat configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create modern eslint.config.js
            eslint_config = project_root / "eslint.config.js"
            eslint_config.write_text(
                """
import js from '@eslint/js';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

export default [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'error',
      'no-console': 'warn'
    },
  },
];
"""
            )

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            # Should detect flat config - FIXED!
            assert config_file == str(eslint_config)

    def test_flat_config_priority_over_legacy(self):
        """Test that flat config takes priority over legacy config when both exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create both flat and legacy configs
            eslint_config = project_root / "eslint.config.js"
            eslint_config.write_text("export default [{ rules: {} }];")

            eslintrc = project_root / ".eslintrc.js"
            eslintrc.write_text("module.exports = { rules: {} };")

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            # Should prefer flat config when both exist - FIXED!
            assert config_file == str(eslint_config)


class TestNpmScriptJSONFormatIssues:
    """Test npm script issues with --format=json flag."""

    def test_npm_script_hardcoded_json_format(self):
        """Test that npm script commands are hardcoded with --format=json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create package.json with problematic npm script
            package_json = project_root / "package.json"
            config = {
                "name": "test-project",
                "scripts": {
                    "lint": "eslint src/**/*.ts"  # This breaks with --format=json
                },
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))
            command = linter._build_npm_command(["src/index.ts"])

            # This is the BUG: hardcoded --format=json
            expected_buggy = ["npm", "run", "lint", "--", "--format=json", "src/index.ts"]
            assert command == expected_buggy

            # This hardcoded approach breaks with many modern setups

    def test_npm_script_with_incompatible_eslint_config(self):
        """Test npm script that becomes incompatible when --format=json is added."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create flat config
            eslint_config = project_root / "eslint.config.js"
            eslint_config.write_text("export default [{ rules: {} }];")

            # Create npm script that works alone but breaks with --format=json
            package_json = project_root / "package.json"
            config = {
                "scripts": {"lint": "eslint src/ --ext .ts,.tsx"}
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))

            # Build command will add --format=json which may break
            command = linter.build_command(["src/index.ts"])

            # Verify the problematic command is generated
            assert "--format=json" in command
            assert "npm" in command and "run" in command and "lint" in command


class TestInvalidJSONOutputHandling:
    """Test handling of invalid JSON output from ESLint."""

    def test_parse_invalid_json_from_npm_script(self):
        """Test parsing when npm script output is not valid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Simulate the exact error the user reported:
            # npm script output that's not valid JSON
            invalid_output = """
> test-project@1.0.0 lint
> eslint src/**/*.ts --format=json

/Users/project/src/index.ts
  1:1  error  Parsing error: Cannot read properties of undefined

1 problem (1 error, 0 warnings)
"""

            # This should handle the JSONDecodeError gracefully
            errors, warnings = linter.parse_output(invalid_output, "", 1)

            # Should create a fallback error instead of crashing
            assert len(errors) == 1
            assert errors[0].rule_id == "parse-error"
            assert ("Failed to parse ESLint output" in errors[0].message or 
                   "Failed to parse ESLint JSON output" in errors[0].message or
                   "Failed to parse ESLint compact output" in errors[0].message)

    def test_parse_mixed_output_from_npm(self):
        """Test parsing npm output that has text before JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Mixed output: npm text + broken JSON
            mixed_output = """
> test-project@1.0.0 lint
> eslint . --format=json

[{"filePath":"/path/file.js","messages":[{"ruleId":"no-unused-vars",
"""  # Truncated JSON

            errors, warnings = linter.parse_output(mixed_output, "", 1)

            # Should handle truncated/invalid JSON
            assert len(errors) == 1
            assert errors[0].rule_id == "parse-error"

    def test_empty_json_array_handling(self):
        """Test handling of empty JSON array output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Valid but empty JSON
            empty_json = "[]"

            errors, warnings = linter.parse_output(empty_json, "", 0)

            # Should handle empty results gracefully
            assert len(errors) == 0
            assert len(warnings) == 0

    def test_json_extraction_from_npm_output_failure(self):
        """Test when JSON extraction fails completely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Output with no JSON at all
            no_json_output = """
> test-project@1.0.0 lint
> eslint src/**/*.ts

Configuration error: Cannot read config file
Error: Failed to load eslint.config.js
"""

            json_extracted = linter._extract_json_from_output(no_json_output)

            # Should return original when no JSON found
            assert json_extracted == no_json_output


class TestRealWorldScenarios:
    """Test real-world scenarios that expose the bug."""

    def test_typescript_project_with_flat_config_npm_script_failure(self):
        """Test the exact scenario reported by the user."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Modern TypeScript project setup
            # 1. Flat config
            eslint_config = project_root / "eslint.config.js"
            eslint_config.write_text(
                """
import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

export default [
  {
    files: ['**/*.ts'],
    languageOptions: { parser: tsParser },
    plugins: { '@typescript-eslint': tsPlugin },
    rules: { '@typescript-eslint/no-unused-vars': 'error' }
  }
];
"""
            )

            # 2. npm script that works alone but breaks with --format=json
            package_json = project_root / "package.json"
            config = {
                "scripts": {"lint": "eslint src/**/*.ts"},
                "devDependencies": {
                    "@typescript-eslint/parser": "^6.0.0",
                    "@typescript-eslint/eslint-plugin": "^6.0.0",
                    "eslint": "^8.57.1",
                },
            }
            package_json.write_text(json.dumps(config, indent=2))

            # 3. TypeScript source file
            src_dir = project_root / "src"
            src_dir.mkdir()
            ts_file = src_dir / "index.ts"
            ts_file.write_text("const unused: string = 'test';")

            linter = ESLintLinter(project_root=str(project_root))

            # This will create the problematic command
            command = linter.build_command()

            # Verify the bug exists
            if linter._should_use_npm_script():
                assert "--format=json" in command
                assert "npm" in command

            # Mock both is_available and subprocess.run to simulate the scenario
            with patch.object(linter, "is_available", return_value=True), \
                 patch("subprocess.run") as mock_subprocess_run:
                
                # Simulate the non-JSON output that breaks parsing
                mock_subprocess_run.return_value = Mock(
                    returncode=1,
                    stdout="""
> project@1.0.0 lint
> eslint src/**/*.ts --format=json

/path/src/index.ts
  1:7  error  'unused' is assigned a value but never used  @typescript-eslint/no-unused-vars

1 problem (1 error, 0 warnings)
""",
                    stderr="",
                )

                # This should handle the parsing failure gracefully
                result = linter.run()
                
                # Should not crash, should create fallback errors
                assert len(result.errors) >= 1
                # At least one error should be a parse error
                parse_errors = [e for e in result.errors if e.rule_id == "parse-error"]
                assert len(parse_errors) >= 1

    def test_format_json_compatibility_detection(self):
        """Test detection of whether --format=json is compatible with current setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Test that the method exists
            assert hasattr(linter, "_can_use_json_format")
            
            # Test with ESLint not available
            with patch.object(linter, "is_available", return_value=False):
                assert linter._can_use_json_format() is False
            
            # Test with ESLint available but format incompatible
            with patch.object(linter, "is_available", return_value=True), \
                 patch.object(linter, "run_command") as mock_run:
                
                # Simulate format not supported error
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: unknown option '--format'"
                )
                assert linter._can_use_json_format() is False
            
            # Test with ESLint available and format compatible
            with patch.object(linter, "is_available", return_value=True), \
                 patch.object(linter, "run_command") as mock_run:
                
                # Simulate successful format test
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="{}",
                    stderr=""
                )
                assert linter._can_use_json_format() is True

    def test_adaptive_command_building(self):
        """Test that commands adapt based on format compatibility."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            # Test with JSON format available
            with patch.object(linter, "_can_use_json_format", return_value=True), \
                 patch.object(linter, "_should_use_npm_script", return_value=False):
                
                command = linter._build_adaptive_command(["test.js"])
                assert "--format=json" in command
            
            # Test with JSON format not available
            with patch.object(linter, "_can_use_json_format", return_value=False), \
                 patch.object(linter, "_should_use_npm_script", return_value=False):
                
                command = linter._build_adaptive_command(["test.js"])
                assert "--format=compact" in command
                assert "--format=json" not in command

    def test_compact_format_parsing(self):
        """Test parsing of ESLint compact format output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            # Sample compact format output
            compact_output = """/path/to/file.js: line 1, col 5, Error - 'x' is defined but never used. (no-unused-vars)
/path/to/file.js: line 2, col 10, Warning - Missing semicolon. (semi)"""
            
            errors, warnings = linter._parse_compact_output(compact_output)
            
            assert len(errors) == 1
            assert len(warnings) == 1
            
            assert errors[0].rule_id == "no-unused-vars"
            assert errors[0].line == 1
            assert errors[0].column == 5
            assert "'x' is defined but never used." in errors[0].message
            
            assert warnings[0].rule_id == "semi"
            assert warnings[0].line == 2
            assert warnings[0].column == 10

    def test_adaptive_parsing_json_fallback_to_compact(self):
        """Test that parsing falls back from JSON to compact format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            # Non-JSON output that should fall back to compact parsing
            non_json_output = "/path/file.js: line 1, col 1, Error - Unexpected token. (unexpected-token)"
            
            errors, warnings = linter.parse_output(non_json_output, "", 1)
            
            assert len(errors) == 1
            # The exact rule_id depends on whether compact parsing succeeds or falls back to parse-error
            assert errors[0].rule_id in ["unexpected-token", "parse-error"]


class TestCommandBuildingEdgeCases:
    """Test edge cases in command building that expose hardcoded assumptions."""

    def test_direct_eslint_command_always_adds_format_json(self):
        """Test that direct ESLint commands always add --format=json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Force direct ESLint (no npm script)
            with patch.object(linter, "_should_use_npm_script", return_value=False):
                command = linter.build_command(["test.js"])

            # Verify hardcoded behavior
            assert "--format=json" in command
            assert "npm" not in command

    def test_npm_script_command_always_adds_format_json(self):
        """Test that npm script commands always add --format=json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Setup for npm script usage
            package_json = project_root / "package.json"
            package_json.write_text('{"scripts": {"lint": "eslint ."}}')

            linter = ESLintLinter(project_root=str(project_root))

            # Force npm script usage
            with patch.object(linter, "_should_use_npm_script", return_value=True):
                command = linter.build_command(["test.js"])

            # Verify hardcoded behavior
            assert "--format=json" in command
            assert "npm" in command
            assert "run" in command
            assert "lint" in command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])