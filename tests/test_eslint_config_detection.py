"""
Test suite for enhanced ESLint configuration detection and project-specific integration.

This module tests the improved ESLint integration that properly respects:
1. Project-specific ESLint configurations (.eslintrc.js, .eslintrc.json, etc.)
2. TypeScript parser setup (@typescript-eslint/parser)
3. npm script integration (npm run lint)
4. Project dependencies (local vs global ESLint)
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.linters.eslint_linter import ESLintLinter


class TestESLintConfigDetection:
    """Test ESLint configuration detection and project-specific setup."""

    def test_detects_eslintrc_js(self):
        """Test detection of .eslintrc.js configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create .eslintrc.js
            eslintrc = project_root / ".eslintrc.js"
            eslintrc.write_text(
                """
module.exports = {
    "extends": ["eslint:recommended"],
    "parserOptions": {
        "ecmaVersion": 2021
    },
    "rules": {
        "no-unused-vars": "error"
    }
};
"""
            )

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            assert config_file == str(eslintrc)

    def test_detects_eslintrc_json(self):
        """Test detection of .eslintrc.json configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create .eslintrc.json
            eslintrc = project_root / ".eslintrc.json"
            config = {
                "extends": ["eslint:recommended"],
                "rules": {"no-unused-vars": "error"},
            }
            eslintrc.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            assert config_file == str(eslintrc)

    def test_detects_package_json_eslint_config(self):
        """Test detection of ESLint config in package.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create package.json with eslintConfig
            package_json = project_root / "package.json"
            config = {
                "name": "test-project",
                "eslintConfig": {
                    "extends": ["eslint:recommended"],
                    "rules": {"no-unused-vars": "error"},
                },
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            assert config_file == str(package_json)

    def test_config_priority_order(self):
        """Test that configuration files are detected in correct priority order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create multiple config files
            eslintrc_js = project_root / ".eslintrc.js"
            eslintrc_json = project_root / ".eslintrc.json"
            package_json = project_root / "package.json"

            eslintrc_js.write_text("module.exports = {};")
            eslintrc_json.write_text('{"extends": ["eslint:recommended"]}')
            package_json.write_text('{"eslintConfig": {"rules": {}}}')

            linter = ESLintLinter(project_root=str(project_root))
            config_file = linter._detect_eslint_config()

            # .eslintrc.js should have highest priority
            assert config_file == str(eslintrc_js)


class TestTypeScriptSupport:
    """Test TypeScript support detection."""

    def test_detects_tsconfig_json(self):
        """Test detection of TypeScript via tsconfig.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create tsconfig.json
            tsconfig = project_root / "tsconfig.json"
            tsconfig.write_text('{"compilerOptions": {"target": "es2020"}}')

            linter = ESLintLinter(project_root=str(project_root))
            has_ts = linter._has_typescript_support()

            assert has_ts is True

    def test_detects_typescript_dependencies(self):
        """Test detection of TypeScript via package.json dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create package.json with TypeScript dependencies
            package_json = project_root / "package.json"
            config = {
                "name": "test-project",
                "devDependencies": {
                    "typescript": "^4.9.0",
                    "@typescript-eslint/parser": "^5.0.0",
                    "@typescript-eslint/eslint-plugin": "^5.0.0",
                },
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))
            has_ts = linter._has_typescript_support()

            assert has_ts is True

    def test_detects_typescript_files(self):
        """Test detection of TypeScript via .ts/.tsx files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create TypeScript files
            ts_file = project_root / "src" / "index.ts"
            ts_file.parent.mkdir(parents=True)
            ts_file.write_text("const x: number = 42;")

            linter = ESLintLinter(project_root=str(project_root))
            has_ts = linter._has_typescript_support()

            assert has_ts is True

    def test_supported_extensions_with_typescript(self):
        """Test that TypeScript extensions are included when TypeScript is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create tsconfig.json to enable TypeScript
            tsconfig = project_root / "tsconfig.json"
            tsconfig.write_text('{"compilerOptions": {}}')

            linter = ESLintLinter(project_root=str(project_root))
            extensions = linter.supported_extensions

            assert ".ts" in extensions
            assert ".tsx" in extensions
            assert ".js" in extensions
            assert ".jsx" in extensions


class TestNpmScriptIntegration:
    """Test npm script integration."""

    def test_detects_npm_lint_script(self):
        """Test detection of npm run lint script."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create package.json with lint script
            package_json = project_root / "package.json"
            config = {
                "name": "test-project",
                "scripts": {"lint": "eslint src/", "lint:fix": "eslint src/ --fix"},
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))
            should_use_npm = linter._should_use_npm_script()

            assert should_use_npm is True

    def test_builds_npm_command(self):
        """Test building npm run lint command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            linter = ESLintLinter(project_root=str(project_root))
            command = linter._build_npm_command(["src/index.js"])

            expected = ["npm", "run", "lint", "--", "--format=json", "src/index.js"]
            assert command == expected

    def test_npm_script_takes_priority(self):
        """Test that npm script is used when available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create package.json with lint script
            package_json = project_root / "package.json"
            config = {"scripts": {"lint": "eslint ."}}
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))

            with patch.object(linter, "_build_npm_command") as mock_npm:
                mock_npm.return_value = ["npm", "run", "lint", "--", "--format=json"]

                command = linter.build_command()

                mock_npm.assert_called_once()
                assert command[0] == "npm"


class TestJSONOutputParsing:
    """Test JSON output parsing from various sources."""

    def test_extracts_json_from_npm_output(self):
        """Test extraction of JSON from npm script output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Simulate npm output with extra text
            npm_output = """
> test-project@1.0.0 lint
> eslint . --format=json

[{"filePath":"/path/to/file.js","messages":[{"ruleId":"no-unused-vars","severity":2,"message":"'x' is defined but never used.","line":1,"column":7}]}]
"""

            json_output = linter._extract_json_from_output(npm_output)

            # Should extract just the JSON part
            assert json_output.startswith("[")
            assert '"no-unused-vars"' in json_output

    def test_handles_clean_json_output(self):
        """Test handling of clean JSON output (direct ESLint)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Clean JSON output
            clean_output = '[{"filePath":"/path/to/file.js","messages":[]}]'

            json_output = linter._extract_json_from_output(clean_output)

            # Should return the same output
            assert json_output == clean_output


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_typescript_project_with_eslint_config(self):
        """Test a TypeScript project with proper ESLint configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create TypeScript project structure
            tsconfig = project_root / "tsconfig.json"
            tsconfig.write_text('{"compilerOptions": {"target": "es2020"}}')

            eslintrc = project_root / ".eslintrc.js"
            eslintrc.write_text(
                """
module.exports = {
    parser: '@typescript-eslint/parser',
    plugins: ['@typescript-eslint'],
    extends: [
        'eslint:recommended',
        '@typescript-eslint/recommended'
    ],
    rules: {
        '@typescript-eslint/no-unused-vars': 'error'
    }
};
"""
            )

            package_json = project_root / "package.json"
            config = {
                "scripts": {"lint": "eslint src/ --ext .ts,.tsx"},
                "devDependencies": {
                    "@typescript-eslint/parser": "^5.0.0",
                    "@typescript-eslint/eslint-plugin": "^5.0.0",
                },
            }
            package_json.write_text(json.dumps(config, indent=2))

            linter = ESLintLinter(project_root=str(project_root))

            # Should detect TypeScript support
            assert linter._has_typescript_support() is True

            # Should detect ESLint config
            assert linter._detect_eslint_config() == str(eslintrc)

            # Should prefer npm script
            assert linter._should_use_npm_script() is True

            # Should include TypeScript extensions
            extensions = linter.supported_extensions
            assert ".ts" in extensions
            assert ".tsx" in extensions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
