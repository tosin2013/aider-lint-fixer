#!/usr/bin/env python3
"""
Native Lint Script Detection System

Detects and uses project-native lint commands (npm run lint, poetry run lint, etc.)
to ensure our tool matches the project's own linting behavior exactly.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class NativeLintCommand:
    """Represents a native lint command for a project."""

    command: List[str]
    linter_type: str  # eslint, flake8, pylint, etc.
    package_manager: str  # npm, poetry, pip, etc.
    script_name: str  # lint, lint:check, etc.
    working_directory: str
    supports_json_output: bool = True
    json_format_args: List[str] = None


class NativeLintDetector:
    """Detects native lint scripts in projects across different languages."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def detect_all_native_lint_commands(self) -> Dict[str, NativeLintCommand]:
        """Detect all native lint commands in the project."""
        commands = {}

        # JavaScript/TypeScript projects
        js_commands = self._detect_npm_lint_scripts()
        commands.update(js_commands)

        # Python projects
        python_commands = self._detect_python_lint_scripts()
        commands.update(python_commands)

        # Add more language detectors here

        return commands

    def _detect_npm_lint_scripts(self) -> Dict[str, NativeLintCommand]:
        """Detect npm/yarn lint scripts."""
        commands = {}

        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return commands

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            scripts = data.get("scripts", {})

            # Look for lint-related scripts
            lint_scripts = {
                name: script
                for name, script in scripts.items()
                if "lint" in name.lower()
                and not name.endswith(":fix")
                and not name.endswith(":all")
            }

            for script_name, script_command in lint_scripts.items():
                # Determine linter type from script content
                linter_type = self._identify_linter_from_script(script_command)

                # Special handling for scripts that call make
                if not linter_type and "make lint" in script_command:
                    linter_type = (
                        "eslint"  # Assume make lint is for ESLint in JS projects
                    )

                if linter_type:
                    # Build the npm command
                    base_command = ["npm", "run", script_name]

                    # Add JSON format support (only for direct ESLint, not make-based)
                    json_args = []
                    supports_json = False

                    if linter_type == "eslint" and "make" not in script_command:
                        json_args = ["--", "--format=json"]
                        supports_json = True

                    commands[linter_type] = NativeLintCommand(
                        command=base_command,
                        linter_type=linter_type,
                        package_manager="npm",
                        script_name=script_name,
                        working_directory=str(self.project_root),
                        supports_json_output=supports_json,
                        json_format_args=json_args,
                    )

        except Exception as e:
            logger.debug(f"Failed to parse package.json: {e}")

        return commands

    def _detect_python_lint_scripts(self) -> Dict[str, NativeLintCommand]:
        """Detect Python lint scripts (poetry, pip, tox, etc.)."""
        commands = {}

        # Check for Poetry
        pyproject_toml = self.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            poetry_commands = self._detect_poetry_lint_scripts()
            commands.update(poetry_commands)

        # Check for tox
        tox_ini = self.project_root / "tox.ini"
        if tox_ini.exists():
            tox_commands = self._detect_tox_lint_scripts()
            commands.update(tox_commands)

        # Check for Makefile
        makefile = self.project_root / "Makefile"
        if makefile.exists():
            make_commands = self._detect_makefile_lint_scripts()
            commands.update(make_commands)

        return commands

    def _detect_poetry_lint_scripts(self) -> Dict[str, NativeLintCommand]:
        """Detect Poetry lint scripts."""
        commands = {}

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                logger.debug("TOML parsing not available")
                return commands

        pyproject_toml = self.project_root / "pyproject.toml"
        try:
            with open(pyproject_toml, "rb") as f:
                data = tomllib.load(f)

            # Check for poetry scripts
            scripts = data.get("tool", {}).get("poetry", {}).get("scripts", {})

            for script_name, script_command in scripts.items():
                if "lint" in script_name.lower():
                    linter_type = self._identify_linter_from_script(script_command)
                    if linter_type:
                        commands[linter_type] = NativeLintCommand(
                            command=["poetry", "run", script_name],
                            linter_type=linter_type,
                            package_manager="poetry",
                            script_name=script_name,
                            working_directory=str(self.project_root),
                            supports_json_output=linter_type in ["flake8", "pylint"],
                        )

        except Exception as e:
            logger.debug(f"Failed to parse pyproject.toml: {e}")

        return commands

    def _detect_tox_lint_scripts(self) -> Dict[str, NativeLintCommand]:
        """Detect tox lint environments."""
        commands = {}

        tox_ini = self.project_root / "tox.ini"
        try:
            import configparser

            config = configparser.ConfigParser()
            config.read(tox_ini)

            # Look for lint environments
            for section_name in config.sections():
                if "lint" in section_name.lower() and section_name.startswith(
                    "testenv:"
                ):
                    env_name = section_name.replace("testenv:", "")
                    commands_str = config.get(section_name, "commands", fallback="")

                    linter_type = self._identify_linter_from_script(commands_str)
                    if linter_type:
                        commands[linter_type] = NativeLintCommand(
                            command=["tox", "-e", env_name],
                            linter_type=linter_type,
                            package_manager="tox",
                            script_name=env_name,
                            working_directory=str(self.project_root),
                            supports_json_output=False,  # tox usually doesn't support JSON directly
                        )

        except Exception as e:
            logger.debug(f"Failed to parse tox.ini: {e}")

        return commands

    def _detect_makefile_lint_scripts(self) -> Dict[str, NativeLintCommand]:
        """Detect Makefile lint targets."""
        commands = {}

        makefile = self.project_root / "Makefile"
        try:
            with open(makefile, "r") as f:
                content = f.read()

            # Simple parsing for lint targets
            lines = content.split("\n")
            for line in lines:
                if line.startswith("lint") and ":" in line:
                    target_name = line.split(":")[0].strip()

                    # Look for the command in subsequent lines
                    # This is a simplified parser - real Makefiles are more complex
                    commands[f"make_{target_name}"] = NativeLintCommand(
                        command=["make", target_name],
                        linter_type="mixed",  # Makefiles often run multiple linters
                        package_manager="make",
                        script_name=target_name,
                        working_directory=str(self.project_root),
                        supports_json_output=False,
                    )

        except Exception as e:
            logger.debug(f"Failed to parse Makefile: {e}")

        return commands

    def _identify_linter_from_script(self, script_command: str) -> Optional[str]:
        """Identify the linter type from a script command."""
        script_lower = script_command.lower()

        # JavaScript/TypeScript linters
        if "eslint" in script_lower:
            return "eslint"
        elif "jshint" in script_lower:
            return "jshint"
        elif "tslint" in script_lower:
            return "tslint"

        # Python linters
        elif "flake8" in script_lower:
            return "flake8"
        elif "pylint" in script_lower:
            return "pylint"
        elif "black" in script_lower:
            return "black"
        elif "isort" in script_lower:
            return "isort"
        elif "mypy" in script_lower:
            return "mypy"

        # Ansible linters
        elif "ansible-lint" in script_lower:
            return "ansible-lint"

        return None

    def get_baseline_command(self, linter_type: str) -> Optional[NativeLintCommand]:
        """Get the native baseline command for a specific linter."""
        commands = self.detect_all_native_lint_commands()
        return commands.get(linter_type)

    def test_native_command(self, command: NativeLintCommand) -> Tuple[bool, str]:
        """Test if a native command works and returns the expected output."""
        try:
            # Build test command
            test_command = command.command.copy()
            if command.supports_json_output and command.json_format_args:
                test_command.extend(command.json_format_args)

            # Add a quick test (just version or help)
            if command.linter_type == "eslint":
                test_command = command.command[:2] + [
                    "--version"
                ]  # npm run lint --version

            result = subprocess.run(
                test_command,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=command.working_directory,
            )

            if result.returncode == 0:
                return True, f"Command works: {' '.join(test_command)}"
            else:
                return (
                    False,
                    f"Command failed with code {result.returncode}: {result.stderr}",
                )

        except Exception as e:
            return False, f"Command test failed: {e}"


def compare_native_vs_tool_results(project_root: str, linter_type: str) -> Dict:
    """Compare native lint results vs our tool's results."""
    detector = NativeLintDetector(project_root)
    native_command = detector.get_baseline_command(linter_type)

    if not native_command:
        return {"error": f"No native {linter_type} command found"}

    # This would integrate with our existing lint runner
    # to compare results and identify discrepancies
    return {
        "native_command": native_command,
        "comparison": "Would compare error counts and types here",
    }
