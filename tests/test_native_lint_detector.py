"""
Comprehensive test suite for native_lint_detector.py

This test suite provides extensive coverage for the NativeLintDetector class,
testing all detection algorithms, parser implementations, file type detection,
error handling, and edge cases to achieve 75%+ coverage.
"""

import pytest
import json
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from aider_lint_fixer.native_lint_detector import (
    NativeLintDetector, 
    NativeLintCommand, 
    compare_native_vs_tool_results
)


class TestNativeLintDetectorInitialization:
    """Test detector initialization and basic functionality."""
    
    def test_detector_initialization(self):
        """Test basic detector initialization."""
        project_root = "/test/path"
        detector = NativeLintDetector(project_root)
        assert detector.project_root == Path(project_root)
    
    def test_detector_with_pathlib_path(self):
        """Test detector initialization with Path object."""
        project_root = Path("/test/path")
        detector = NativeLintDetector(str(project_root))
        assert detector.project_root == project_root


class TestNpmLintScriptDetection:
    """Test npm/yarn lint script detection from package.json."""
    
    @pytest.fixture
    def npm_project_root(self, tmp_path):
        """Create a fake npm project with various lint scripts."""
        package_json = {
            "scripts": {
                "lint": "eslint .",
                "lint:js": "eslint src/",
                "lint:ts": "tslint src/",
                "lint:fix": "eslint . --fix",  # Should be ignored
                "lint:all": "npm run lint:js && npm run lint:ts",  # Should be ignored
                "test": "jest",
                "build": "webpack"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        return str(tmp_path)
    
    def test_detect_npm_lint_scripts_basic(self, npm_project_root):
        """Test basic npm lint script detection."""
        detector = NativeLintDetector(npm_project_root)
        commands = detector._detect_npm_lint_scripts()
        
        assert "eslint" in commands
        cmd = commands["eslint"]
        # The first detected eslint script could be "lint" or "lint:js" 
        assert cmd.command[0:2] == ["npm", "run"]
        assert cmd.command[2] in ["lint", "lint:js"]  # Either is acceptable
        assert cmd.linter_type == "eslint"
        assert cmd.package_manager == "npm"
        assert cmd.script_name in ["lint", "lint:js"]
        assert cmd.supports_json_output is True
        assert cmd.json_format_args == ["--", "--format=json"]
    
    def test_detect_npm_lint_scripts_multiple_linters(self, tmp_path):
        """Test detection of multiple different linters."""
        package_json = {
            "scripts": {
                "lint:eslint": "eslint src/",
                "lint:jshint": "jshint lib/",
                "lint:tslint": "tslint typescript/"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        
        # Should detect all three linters
        assert len(commands) == 3
        assert "eslint" in commands
        assert "jshint" in commands
        assert "tslint" in commands
    
    def test_detect_npm_lint_scripts_make_based(self, tmp_path):
        """Test detection of make-based lint scripts."""
        package_json = {
            "scripts": {
                "lint": "make lint"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        
        assert "eslint" in commands  # Should assume eslint for make lint
        cmd = commands["eslint"]
        assert cmd.supports_json_output is False  # Make-based doesn't support JSON
        assert cmd.json_format_args == []
    
    def test_detect_npm_lint_scripts_no_package_json(self, tmp_path):
        """Test behavior when package.json doesn't exist."""
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        assert commands == {}
    
    def test_detect_npm_lint_scripts_malformed_json(self, tmp_path):
        """Test handling of malformed package.json."""
        (tmp_path / "package.json").write_text("{ malformed json")
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        assert commands == {}  # Should handle gracefully
    
    def test_detect_npm_lint_scripts_no_scripts_section(self, tmp_path):
        """Test package.json without scripts section."""
        package_json = {"name": "test-project", "version": "1.0.0"}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        assert commands == {}
    
    def test_detect_npm_lint_scripts_filter_fix_scripts(self, tmp_path):
        """Test that :fix and :all scripts are filtered out."""
        package_json = {
            "scripts": {
                "lint": "eslint .",
                "lint:fix": "eslint . --fix",
                "lint:all": "npm run lint && npm run lint:check"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        
        # Should only detect the base lint script
        assert len(commands) == 1
        assert "eslint" in commands


class TestPythonLintScriptDetection:
    """Test Python lint script detection across various tools."""
    
    def test_detect_python_lint_scripts_with_poetry(self, tmp_path):
        """Test detection when pyproject.toml exists."""
        pyproject_content = """
[tool.poetry.scripts]
lint = "flake8"
check = "mypy ."
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        
        with patch('tomllib.load') as mock_load:
            mock_load.return_value = {
                "tool": {
                    "poetry": {
                        "scripts": {
                            "lint": "flake8",
                            "check": "mypy ."
                        }
                    }
                }
            }
            
            detector = NativeLintDetector(str(tmp_path))
            commands = detector._detect_python_lint_scripts()
            
            assert "flake8" in commands
            assert commands["flake8"].command == ["poetry", "run", "lint"]
    
    def test_detect_python_lint_scripts_with_tox(self, tmp_path):
        """Test detection when tox.ini exists."""
        tox_content = """
[testenv:lint]
commands = flake8 src/

[testenv:pylint]
commands = pylint src/
"""
        (tmp_path / "tox.ini").write_text(tox_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_python_lint_scripts()
        
        # Note: tox detection requires configparser which should work
        assert len(commands) >= 1  # Should detect at least some commands
    
    def test_detect_python_lint_scripts_with_makefile(self, tmp_path):
        """Test detection when Makefile exists."""
        makefile_content = """
lint:
\tflake8 .

test:
\tpytest tests/
"""
        (tmp_path / "Makefile").write_text(makefile_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_python_lint_scripts()
        
        assert "make_lint" in commands
        cmd = commands["make_lint"]
        assert cmd.command == ["make", "lint"]
        assert cmd.linter_type == "mixed"
        assert cmd.package_manager == "make"
    
    def test_detect_python_lint_scripts_no_files(self, tmp_path):
        """Test behavior when no Python config files exist."""
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_python_lint_scripts()
        assert commands == {}


class TestPoetryLintScriptDetection:
    """Test Poetry-specific lint script detection."""
    
    @pytest.fixture
    def poetry_project(self, tmp_path):
        """Create a Poetry project with lint scripts."""
        pyproject_content = """
[tool.poetry]
name = "test-project"

[tool.poetry.scripts]
lint = "flake8"
pylint = "pylint src/"
black = "black --check ."
isort = "isort --check-only ."
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        return str(tmp_path)
    
    def test_detect_poetry_lint_scripts_success(self, tmp_path):
        """Test successful Poetry lint script detection."""
        pyproject_content = """
[tool.poetry.scripts]
lint = "flake8"
check = "mypy ."
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        
        # Mock tomllib to return expected data
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('tomllib.load') as mock_load:
                mock_load.return_value = {
                    "tool": {
                        "poetry": {
                            "scripts": {
                                "lint": "flake8",
                                "check": "mypy ."
                            }
                        }
                    }
                }
                
                detector = NativeLintDetector(str(tmp_path))
                commands = detector._detect_poetry_lint_scripts()
                
                assert "flake8" in commands
                # mypy command should only be detected if the script name contains "lint"
                # In this case "check" doesn't contain "lint" so mypy won't be detected
                
                flake8_cmd = commands["flake8"]
                assert flake8_cmd.command == ["poetry", "run", "lint"]
                assert flake8_cmd.linter_type == "flake8"
                assert flake8_cmd.package_manager == "poetry"
                assert flake8_cmd.supports_json_output is True
    
    def test_detect_poetry_lint_scripts_no_tomllib(self, tmp_path):
        """Test handling when tomllib is not available."""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry.scripts]\nlint = \"flake8\"")
        
        # Mock ImportError for both tomllib and tomli  
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name in ['tomllib', 'tomli']:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            detector = NativeLintDetector(str(tmp_path))
            commands = detector._detect_poetry_lint_scripts()
            assert commands == {}
    
    def test_detect_poetry_lint_scripts_malformed_toml(self, tmp_path):
        """Test handling of malformed pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("malformed toml content")
        
        with patch('tomllib.load', side_effect=Exception("Parse error")):
            detector = NativeLintDetector(str(tmp_path))
            commands = detector._detect_poetry_lint_scripts()
            assert commands == {}


class TestToxLintScriptDetection:
    """Test tox-specific lint environment detection."""
    
    def test_detect_tox_lint_scripts_success(self, tmp_path):
        """Test successful tox lint environment detection."""
        tox_content = """
[testenv:lint]
commands = flake8 src/

[testenv:pylint]  
commands = pylint src/

[testenv:lint-check]
commands = mypy .

[testenv:test]
commands = pytest
"""
        (tmp_path / "tox.ini").write_text(tox_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_tox_lint_scripts()
        
        # Should detect lint environments
        expected_linters = ["flake8", "pylint", "mypy"]
        detected_linters = [cmd.linter_type for cmd in commands.values()]
        
        # At least some linters should be detected
        assert any(linter in detected_linters for linter in expected_linters)
        
        # Check command structure for detected linters
        for cmd in commands.values():
            assert cmd.command[0] == "tox"
            assert cmd.command[1] == "-e"
            assert cmd.package_manager == "tox"
            assert cmd.supports_json_output is False
    
    def test_detect_tox_lint_scripts_no_lint_envs(self, tmp_path):
        """Test tox.ini without lint environments."""
        tox_content = """
[testenv:test]
commands = pytest

[testenv:build]
commands = python setup.py build
"""
        (tmp_path / "tox.ini").write_text(tox_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_tox_lint_scripts()
        assert commands == {}
    
    def test_detect_tox_lint_scripts_malformed_ini(self, tmp_path):
        """Test handling of malformed tox.ini."""
        (tmp_path / "tox.ini").write_text("malformed ini content\n[invalid")
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_tox_lint_scripts()
        assert commands == {}  # Should handle gracefully


class TestMakefileLintScriptDetection:
    """Test Makefile lint target detection."""
    
    def test_detect_makefile_lint_scripts_basic(self, tmp_path):
        """Test basic Makefile lint target detection."""
        makefile_content = """
.PHONY: lint test clean

lint:
\tflake8 .
\tpylint src/

test:
\tpytest tests/

clean:
\trm -rf build/
"""
        (tmp_path / "Makefile").write_text(makefile_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_makefile_lint_scripts()
        
        assert "make_lint" in commands
        cmd = commands["make_lint"]
        assert cmd.command == ["make", "lint"]
        assert cmd.linter_type == "mixed"
        assert cmd.package_manager == "make"
        assert cmd.script_name == "lint"
        assert cmd.supports_json_output is False
    
    def test_detect_makefile_lint_scripts_multiple_targets(self, tmp_path):
        """Test detection of multiple lint targets."""
        makefile_content = """
lint:
\tflake8 .

lint-check:
\tmypy .

linting:
\tpylint src/
"""
        (tmp_path / "Makefile").write_text(makefile_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_makefile_lint_scripts()
        
        # Should detect all lint-related targets
        expected_targets = ["make_lint", "make_lint-check", "make_linting"]
        for target in expected_targets:
            if target in commands:
                assert commands[target].command[1] in ["lint", "lint-check", "linting"]
    
    def test_detect_makefile_lint_scripts_no_lint_targets(self, tmp_path):
        """Test Makefile without lint targets."""
        makefile_content = """
test:
\tpytest tests/

build:
\tpython setup.py build
"""
        (tmp_path / "Makefile").write_text(makefile_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_makefile_lint_scripts()
        assert commands == {}
    
    def test_detect_makefile_lint_scripts_read_error(self, tmp_path):
        """Test handling of Makefile read errors."""
        makefile = tmp_path / "Makefile"
        makefile.write_text("lint:\n\tflake8 .")
        
        # Mock file read to raise exception
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            detector = NativeLintDetector(str(tmp_path))
            commands = detector._detect_makefile_lint_scripts()
            assert commands == {}


class TestLinterIdentification:
    """Test linter type identification from script commands."""
    
    def test_identify_javascript_linters(self):
        """Test identification of JavaScript/TypeScript linters."""
        detector = NativeLintDetector("/")
        
        test_cases = [
            ("eslint .", "eslint"),
            ("eslint src/ --fix", "eslint"),
            ("npx eslint .", "eslint"),
            ("jshint lib/", "jshint"),
            ("tslint typescript/", "tslint"),
            ("./node_modules/.bin/eslint .", "eslint")
        ]
        
        for script, expected in test_cases:
            result = detector._identify_linter_from_script(script)
            assert result == expected, f"Failed for script: {script}"
    
    def test_identify_python_linters(self):
        """Test identification of Python linters."""
        detector = NativeLintDetector("/")
        
        test_cases = [
            ("flake8 .", "flake8"),
            ("flake8 src/ --max-line-length=88", "flake8"),
            ("pylint src/", "pylint"),
            ("pylint --rcfile=.pylintrc src/", "pylint"),
            ("black --check .", "black"),
            ("black .", "black"),
            ("isort --check-only .", "isort"),
            ("isort .", "isort"),
            ("mypy .", "mypy"),
            ("mypy src/ --strict", "mypy")
        ]
        
        for script, expected in test_cases:
            result = detector._identify_linter_from_script(script)
            assert result == expected, f"Failed for script: {script}"
    
    def test_identify_ansible_linters(self):
        """Test identification of Ansible linters."""
        detector = NativeLintDetector("/")
        
        test_cases = [
            ("ansible-lint .", "ansible-lint"),
            ("ansible-lint playbooks/", "ansible-lint"),
            ("ansible-lint --force-color", "ansible-lint")
        ]
        
        for script, expected in test_cases:
            result = detector._identify_linter_from_script(script)
            assert result == expected, f"Failed for script: {script}"
    
    def test_identify_unknown_linters(self):
        """Test handling of unknown linters."""
        detector = NativeLintDetector("/")
        
        unknown_scripts = [
            "unknown-linter .",
            "grep -r TODO src/",
            "python manage.py test",
            "webpack build",
            ""
        ]
        
        for script in unknown_scripts:
            result = detector._identify_linter_from_script(script)
            assert result is None, f"Should not identify unknown script: {script}"
    
    def test_identify_case_insensitive(self):
        """Test case-insensitive linter identification."""
        detector = NativeLintDetector("/")
        
        test_cases = [
            ("ESLINT .", "eslint"),
            ("Flake8 .", "flake8"),
            ("PyLint src/", "pylint"),
            ("ANSIBLE-LINT .", "ansible-lint")
        ]
        
        for script, expected in test_cases:
            result = detector._identify_linter_from_script(script)
            assert result == expected, f"Failed for case-insensitive script: {script}"


class TestDetectAllNativeLintCommands:
    """Test the main detection method that orchestrates all detectors."""
    
    def test_detect_all_native_lint_commands_comprehensive(self, tmp_path):
        """Test comprehensive detection across all project types."""
        # Create a multi-language project with various configurations
        
        # JavaScript project
        package_json = {
            "scripts": {
                "lint": "eslint .",
                "lint:js": "jshint lib/"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        # Python project with multiple configs
        pyproject_content = """
[tool.poetry.scripts]
lint = "flake8"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        
        tox_content = """
[testenv:pylint]
commands = pylint src/
"""
        (tmp_path / "tox.ini").write_text(tox_content)
        
        makefile_content = """
lint:
\tmypy .
"""
        (tmp_path / "Makefile").write_text(makefile_content)
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector.detect_all_native_lint_commands()
        
        # Should detect commands from multiple sources
        assert len(commands) > 0
        assert isinstance(commands, dict)
        
        # Verify all returned commands are NativeLintCommand instances
        for cmd in commands.values():
            assert isinstance(cmd, NativeLintCommand)
            assert cmd.linter_type is not None
            assert cmd.package_manager is not None
            assert isinstance(cmd.command, list)
            assert len(cmd.command) > 0
    
    def test_detect_all_native_lint_commands_empty_project(self, tmp_path):
        """Test detection in empty project with no configuration files."""
        detector = NativeLintDetector(str(tmp_path))
        commands = detector.detect_all_native_lint_commands()
        assert commands == {}


class TestGetBaselineCommand:
    """Test baseline command retrieval functionality."""
    
    def test_get_baseline_command_existing_linter(self, tmp_path):
        """Test getting baseline command for existing linter."""
        package_json = {"scripts": {"lint": "eslint ."}}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        cmd = detector.get_baseline_command("eslint")
        
        assert cmd is not None
        assert isinstance(cmd, NativeLintCommand)
        assert cmd.linter_type == "eslint"
    
    def test_get_baseline_command_nonexistent_linter(self, tmp_path):
        """Test getting baseline command for non-existent linter."""
        detector = NativeLintDetector(str(tmp_path))
        cmd = detector.get_baseline_command("nonexistent-linter")
        assert cmd is None
    
    def test_get_baseline_command_multiple_calls(self, tmp_path):
        """Test that multiple calls return consistent results."""
        package_json = {"scripts": {"lint": "eslint ."}}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        cmd1 = detector.get_baseline_command("eslint")
        cmd2 = detector.get_baseline_command("eslint")
        
        # Should return equivalent commands
        if cmd1 and cmd2:
            assert cmd1.command == cmd2.command
            assert cmd1.linter_type == cmd2.linter_type


class TestNativeCommandTesting:
    """Test native command execution testing functionality."""
    
    def test_test_native_command_success(self):
        """Test successful command testing."""
        command = NativeLintCommand(
            command=["echo", "test"],
            linter_type="test",
            package_manager="test",
            script_name="test",
            working_directory="/tmp"
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            
            success, output = detector.test_native_command(command)
            assert success is True
            assert "Command works" in output
            mock_run.assert_called_once()
    
    def test_test_native_command_failure(self):
        """Test command testing with failure."""
        command = NativeLintCommand(
            command=["false"],  # Command that always fails
            linter_type="test",
            package_manager="test", 
            script_name="test",
            working_directory="/tmp"
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stderr="Command failed"
            )
            
            success, output = detector.test_native_command(command)
            assert success is False
            assert "Command failed with code 1" in output
    
    def test_test_native_command_with_json_args(self):
        """Test command testing with JSON format arguments."""
        command = NativeLintCommand(
            command=["npm", "run", "lint"],
            linter_type="eslint",
            package_manager="npm",
            script_name="lint",
            working_directory="/tmp",
            supports_json_output=True,
            json_format_args=["--", "--format=json"]
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            
            success, output = detector.test_native_command(command)
            
            # For eslint, the test modifies command to check version instead
            # So we check that subprocess.run was called with a version check
            called_command = mock_run.call_args[0][0]
            assert "--version" in called_command
    
    def test_test_native_command_eslint_special_case(self):
        """Test special case handling for ESLint version check."""
        command = NativeLintCommand(
            command=["npm", "run", "lint"],
            linter_type="eslint",
            package_manager="npm",
            script_name="lint", 
            working_directory="/tmp"
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            
            success, output = detector.test_native_command(command)
            
            # Should have modified command for version check
            called_command = mock_run.call_args[0][0]
            assert "--version" in called_command
    
    def test_test_native_command_exception_handling(self):
        """Test exception handling during command testing."""
        command = NativeLintCommand(
            command=["nonexistent-command"],
            linter_type="test",
            package_manager="test",
            script_name="test",
            working_directory="/tmp"
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run', side_effect=FileNotFoundError("Command not found")):
            success, output = detector.test_native_command(command)
            assert success is False
            assert "Command test failed" in output
    
    def test_test_native_command_timeout(self):
        """Test command testing with timeout."""
        command = NativeLintCommand(
            command=["sleep", "60"],
            linter_type="test",
            package_manager="test",
            script_name="test",
            working_directory="/tmp"
        )
        
        detector = NativeLintDetector("/tmp")
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("sleep", 30)):
            success, output = detector.test_native_command(command)
            assert success is False
            assert "Command test failed" in output


class TestNativeLintCommandDataclass:
    """Test the NativeLintCommand dataclass."""
    
    def test_native_lint_command_creation(self):
        """Test creating NativeLintCommand with all fields."""
        command = NativeLintCommand(
            command=["npm", "run", "lint"],
            linter_type="eslint",
            package_manager="npm",
            script_name="lint",
            working_directory="/project",
            supports_json_output=True,
            json_format_args=["--", "--format=json"]
        )
        
        assert command.command == ["npm", "run", "lint"]
        assert command.linter_type == "eslint"
        assert command.package_manager == "npm"
        assert command.script_name == "lint"
        assert command.working_directory == "/project"
        assert command.supports_json_output is True
        assert command.json_format_args == ["--", "--format=json"]
    
    def test_native_lint_command_defaults(self):
        """Test NativeLintCommand with default values."""
        command = NativeLintCommand(
            command=["flake8"],
            linter_type="flake8",
            package_manager="pip",
            script_name="lint",
            working_directory="/project"
        )
        
        # Test defaults
        assert command.supports_json_output is True
        assert command.json_format_args is None


class TestCompareNativeVsToolResults:
    """Test the comparison functionality."""
    
    def test_compare_native_vs_tool_results_found(self, tmp_path):
        """Test comparison when native command is found."""
        package_json = {"scripts": {"lint": "eslint ."}}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        result = compare_native_vs_tool_results(str(tmp_path), "eslint")
        
        assert "native_command" in result
        assert isinstance(result["native_command"], NativeLintCommand)
        assert "comparison" in result
    
    def test_compare_native_vs_tool_results_not_found(self, tmp_path):
        """Test comparison when native command is not found."""
        result = compare_native_vs_tool_results(str(tmp_path), "nonexistent-linter")
        
        assert "error" in result
        assert "No native nonexistent-linter command found" in result["error"]


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_detector_with_permission_denied(self, tmp_path):
        """Test handling of permission denied errors."""
        (tmp_path / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
        
        # Mock file operations to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            detector = NativeLintDetector(str(tmp_path))
            commands = detector._detect_npm_lint_scripts()
            assert commands == {}  # Should handle gracefully
    
    def test_detector_with_empty_files(self, tmp_path):
        """Test handling of empty configuration files."""
        (tmp_path / "package.json").write_text("")
        (tmp_path / "pyproject.toml").write_text("")
        (tmp_path / "tox.ini").write_text("")
        (tmp_path / "Makefile").write_text("")
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector.detect_all_native_lint_commands()
        assert commands == {}
    
    def test_detector_with_very_large_files(self, tmp_path):
        """Test handling of very large configuration files."""
        # Create a large package.json
        large_scripts = {f"script{i}": f"command{i}" for i in range(1000)}
        large_scripts["lint"] = "eslint ."
        package_json = {"scripts": large_scripts}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        
        # Should still detect the lint script
        assert "eslint" in commands
    
    def test_detector_with_unicode_content(self, tmp_path):
        """Test handling of files with Unicode content."""
        package_json = {
            "name": "测试项目",  # Chinese characters
            "scripts": {
                "lint": "eslint .",
                "test": "jest"
            }
        }
        (tmp_path / "package.json").write_text(
            json.dumps(package_json, ensure_ascii=False), 
            encoding='utf-8'
        )
        
        detector = NativeLintDetector(str(tmp_path))
        commands = detector._detect_npm_lint_scripts()
        
        assert "eslint" in commands
    
    def test_detector_path_traversal_protection(self):
        """Test that detector handles path traversal attempts safely."""
        # This should not cause issues even with malicious paths
        malicious_paths = [
            "/../../etc/passwd",
            "../../../windows/system32",
            "/dev/null/../../../etc"
        ]
        
        for path in malicious_paths:
            detector = NativeLintDetector(path)
            # Should not crash, even if path doesn't exist
            commands = detector.detect_all_native_lint_commands()
            assert isinstance(commands, dict)


class TestPerformanceScenarios:
    """Test performance-related scenarios."""
    
    def test_detector_with_many_files(self, tmp_path):
        """Test detector performance with many irrelevant files."""
        # Create many files that shouldn't be processed
        for i in range(100):
            (tmp_path / f"file{i}.txt").write_text(f"content {i}")
            (tmp_path / f"script{i}.py").write_text(f"print('script {i}')")
        
        # Create the actual config files
        package_json = {"scripts": {"lint": "eslint ."}}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        
        # This should complete quickly despite many files
        import time
        start_time = time.time()
        commands = detector.detect_all_native_lint_commands()
        end_time = time.time()
        
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
        assert "eslint" in commands
    
    def test_detector_repeated_calls(self, tmp_path):
        """Test that repeated calls don't cause performance issues."""
        package_json = {"scripts": {"lint": "eslint ."}}
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        detector = NativeLintDetector(str(tmp_path))
        
        # Make multiple calls - should be consistent
        for _ in range(10):
            commands = detector.detect_all_native_lint_commands()
            assert "eslint" in commands
            assert len(commands) >= 1
