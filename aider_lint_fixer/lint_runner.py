"""
Lint Runner Module

This module handles running linters and parsing their output to identify errors.
"""

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .project_detector import ProjectInfo

# Import modular linters - delay import to avoid circular dependencies
MODULAR_LINTERS_AVAILABLE = False
AnsibleLintLinter = None
Flake8Linter = None
PylintLinter = None
ESLintLinter = None
JSHintLinter = None
PrettierLinter = None


def _import_modular_linters():
    """Import modular linters with individual error handling for platform compatibility."""
    global MODULAR_LINTERS_AVAILABLE, AnsibleLintLinter, Flake8Linter, PylintLinter, ESLintLinter, JSHintLinter, PrettierLinter
    if not MODULAR_LINTERS_AVAILABLE:
        imported_linters = []

        # Import each linter individually to handle platform-specific issues
        try:
            from .linters.ansible_lint import AnsibleLintLinter as _AnsibleLintLinter

            AnsibleLintLinter = _AnsibleLintLinter
            imported_linters.append("ansible-lint")
        except ImportError as e:
            logger.debug(f"Ansible-lint linter not available (platform compatibility): {e}")
            AnsibleLintLinter = None
        except Exception as e:
            logger.debug(f"Unexpected error importing ansible-lint: {e}")
            AnsibleLintLinter = None

        try:
            from .linters.flake8_linter import Flake8Linter as _Flake8Linter

            Flake8Linter = _Flake8Linter
            imported_linters.append("flake8")
        except ImportError as e:
            logger.debug(f"Flake8 linter not available: {e}")
            Flake8Linter = None

        try:
            from .linters.pylint_linter import PylintLinter as _PylintLinter

            PylintLinter = _PylintLinter
            imported_linters.append("pylint")
        except ImportError as e:
            logger.debug(f"Pylint linter not available: {e}")
            PylintLinter = None

        try:
            from .linters.eslint_linter import ESLintLinter as _ESLintLinter

            ESLintLinter = _ESLintLinter
            imported_linters.append("eslint")
        except ImportError as e:
            logger.debug(f"ESLint linter not available: {e}")
            ESLintLinter = None

        try:
            from .linters.jshint_linter import JSHintLinter as _JSHintLinter

            JSHintLinter = _JSHintLinter
            imported_linters.append("jshint")
        except ImportError as e:
            logger.debug(f"JSHint linter not available: {e}")
            JSHintLinter = None

        try:
            from .linters.prettier_linter import PrettierLinter as _PrettierLinter

            PrettierLinter = _PrettierLinter
            imported_linters.append("prettier")
        except ImportError as e:
            logger.debug(f"Prettier linter not available: {e}")
            PrettierLinter = None

        MODULAR_LINTERS_AVAILABLE = True
        if imported_linters:
            logger.debug(f"Successfully imported modular linters: {', '.join(imported_linters)}")
        else:
            logger.debug("No modular linters could be imported")


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for lint errors."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


@dataclass
class LintError:
    """Represents a single lint error."""

    file_path: str
    line: int
    column: int
    rule_id: str
    message: str
    severity: ErrorSeverity
    linter: str
    context: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class LintResult:
    """Results from running a linter."""

    linter: str
    success: bool
    errors: List[LintError] = field(default_factory=list)
    warnings: List[LintError] = field(default_factory=list)
    raw_output: str = ""
    execution_time: float = 0.0


class LintRunner:
    """Runs linters and parses their output."""

    # Linter command configurations
    LINTER_COMMANDS = {
        # Python linters
        "flake8": {
            "command": ["flake8"],
            "check_installed": ["flake8", "--version"],
            "output_format": "text",
            "file_extensions": [".py"],
        },
        "pylint": {
            "command": ["pylint", "--output-format=json"],
            "check_installed": ["pylint", "--version"],
            "output_format": "json",
            "file_extensions": [".py"],
        },
        "black": {
            "command": ["black", "--check", "--diff"],
            "check_installed": ["black", "--version"],
            "output_format": "diff",
            "file_extensions": [".py"],
        },
        "isort": {
            "command": ["isort", "--check-only", "--diff"],
            "check_installed": ["isort", "--version"],
            "output_format": "diff",
            "file_extensions": [".py"],
        },
        "mypy": {
            "command": ["mypy", "--show-error-codes"],
            "check_installed": ["mypy", "--version"],
            "output_format": "text",
            "file_extensions": [".py"],
        },
        # JavaScript/TypeScript linters
        "eslint": {
            "command": ["npx", "eslint", "--format=json"],
            "check_installed": ["npx", "eslint", "--version"],
            "output_format": "json",
            "file_extensions": [".js", ".jsx", ".ts", ".tsx"],
        },
        "jshint": {
            "command": ["npx", "jshint", "--reporter=json"],
            "check_installed": ["npx", "jshint", "--version"],
            "output_format": "json",
            "file_extensions": [".js", ".mjs", ".cjs"],
        },
        "prettier": {
            "command": ["npx", "prettier", "--check"],
            "check_installed": ["npx", "prettier", "--version"],
            "output_format": "text",
            "file_extensions": [".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".md"],
        },
        # Go linters
        "golint": {
            "command": ["golint"],
            "check_installed": ["golint"],
            "output_format": "text",
            "file_extensions": [".go"],
        },
        "gofmt": {
            "command": ["gofmt", "-l"],
            "check_installed": ["gofmt"],
            "output_format": "text",
            "file_extensions": [".go"],
        },
        "govet": {
            "command": ["go", "vet"],
            "check_installed": ["go", "version"],
            "output_format": "text",
            "file_extensions": [".go"],
        },
        # Rust linters
        "rustfmt": {
            "command": ["rustfmt", "--check"],
            "check_installed": ["rustfmt", "--version"],
            "output_format": "text",
            "file_extensions": [".rs"],
        },
        "clippy": {
            "command": ["cargo", "clippy", "--message-format=json"],
            "check_installed": ["cargo", "--version"],
            "output_format": "json",
            "file_extensions": [".rs"],
        },
        # Ansible linters
        "ansible-lint": {
            "command": ["ansible-lint", "--format=json", "--strict", "--profile=basic"],
            "check_installed": ["ansible-lint", "--version"],
            "output_format": "json",
            "file_extensions": [".yml", ".yaml"],
            "profiles": ["basic", "production"],  # Supported profiles
        },
    }

    def __init__(self, project_info: ProjectInfo):
        """Initialize the lint runner.

        Args:
            project_info: Information about the project
        """
        self.project_info = project_info
        self.available_linters = {}  # Will be populated on-demand

    def _detect_available_linters(
        self, linter_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Detect which linters are available in the system.

        Args:
            linter_names: Optional list of specific linters to check. If None, checks all.

        Returns:
            Dictionary mapping linter names to availability
        """
        available = {}

        # If specific linters requested, only check those
        linters_to_check = linter_names or list(self.LINTER_COMMANDS.keys())

        for linter_name in linters_to_check:
            if linter_name not in self.LINTER_COMMANDS:
                logger.warning(f"Unknown linter: {linter_name}")
                available[linter_name] = False
                continue

            config = self.LINTER_COMMANDS[linter_name]
            try:
                # Try to run the version command
                result = subprocess.run(
                    config["check_installed"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.project_info.root_path,
                )
                available[linter_name] = result.returncode == 0

                if available[linter_name]:
                    logger.debug(f"Linter {linter_name} is available")
                else:
                    logger.debug(f"Linter {linter_name} check failed: {result.stderr}")

            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
                available[linter_name] = False
                logger.debug(f"Linter {linter_name} not available: {e}")

        return available

    def run_linter(
        self, linter_name: str, file_paths: Optional[List[str]] = None, **kwargs
    ) -> LintResult:
        """Run a specific linter on the project or specific files.

        Args:
            linter_name: Name of the linter to run
            file_paths: Optional list of specific files to lint

        Returns:
            LintResult object containing the results
        """
        # Try to use modular linter implementation first
        _import_modular_linters()
        if MODULAR_LINTERS_AVAILABLE:
            if linter_name == "ansible-lint":
                return self._run_modular_ansible_lint(file_paths, **kwargs)
            elif linter_name == "flake8":
                return self._run_modular_flake8(file_paths, **kwargs)
            elif linter_name == "pylint":
                return self._run_modular_pylint(file_paths, **kwargs)
            elif linter_name == "eslint":
                return self._run_modular_eslint(file_paths, **kwargs)
            elif linter_name == "jshint":
                return self._run_modular_jshint(file_paths, **kwargs)
            elif linter_name == "prettier":
                return self._run_modular_prettier(file_paths, **kwargs)

        if linter_name not in self.LINTER_COMMANDS:
            raise ValueError(f"Unknown linter: {linter_name}")

        # Check availability if not already checked
        if linter_name not in self.available_linters:
            self.available_linters.update(self._detect_available_linters([linter_name]))

        if not self.available_linters.get(linter_name, False):
            logger.warning(f"Linter {linter_name} is not available")
            return LintResult(linter=linter_name, success=False, raw_output="Linter not available")

        config = self.LINTER_COMMANDS[linter_name]
        command = config["command"].copy()

        # Add file paths or project root
        if file_paths:
            # Filter files by supported extensions
            supported_extensions = config.get("file_extensions", [])
            if supported_extensions:
                filtered_files = [
                    f for f in file_paths if any(f.endswith(ext) for ext in supported_extensions)
                ]
                if not filtered_files:
                    logger.info(f"No files with supported extensions for {linter_name}")
                    return LintResult(linter=linter_name, success=True)
                command.extend(filtered_files)
            else:
                command.extend(file_paths)
        else:
            # Add project root or current directory
            if linter_name in ["govet", "clippy"]:
                # These linters work on the entire project
                pass
            else:
                command.append(".")

        logger.info(f"Running {linter_name}: {' '.join(command)}")

        try:
            import time

            start_time = time.time()

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.project_info.root_path,
            )

            execution_time = time.time() - start_time

            # Parse the output
            lint_result = self._parse_linter_output(
                linter_name, result.stdout, result.stderr, result.returncode
            )
            lint_result.execution_time = execution_time

            logger.info(
                f"Linter {linter_name} completed in {execution_time:.2f}s with {len(lint_result.errors)} errors"
            )

            return lint_result

        except subprocess.TimeoutExpired:
            logger.error(f"Linter {linter_name} timed out")
            return LintResult(
                linter=linter_name, success=False, raw_output="Linter execution timed out"
            )
        except Exception as e:
            logger.error(f"Error running linter {linter_name}: {e}")
            return LintResult(linter=linter_name, success=False, raw_output=f"Error: {str(e)}")

    def _parse_linter_output(
        self, linter_name: str, stdout: str, stderr: str, return_code: int
    ) -> LintResult:
        """Parse linter output into structured errors.

        Args:
            linter_name: Name of the linter
            stdout: Standard output from the linter
            stderr: Standard error from the linter
            return_code: Exit code from the linter

        Returns:
            LintResult object with parsed errors
        """
        config = self.LINTER_COMMANDS[linter_name]
        output_format = config["output_format"]

        errors = []
        warnings = []
        raw_output = stdout + stderr

        # Success is typically return_code == 0, but some linters use different codes
        # For ansible-lint, exit code 2 means violations found, which is still valid output
        if linter_name == "ansible-lint":
            success = return_code in [0, 2]  # 0 = no issues, 2 = issues found
        else:
            success = return_code == 0

        try:
            if output_format == "json":
                errors, warnings = self._parse_json_output(linter_name, stdout)
            elif output_format == "text":
                errors, warnings = self._parse_text_output(linter_name, stdout, stderr)
            elif output_format == "diff":
                errors, warnings = self._parse_diff_output(linter_name, stdout)

        except Exception as e:
            logger.error(f"Error parsing {linter_name} output: {e}")

        return LintResult(
            linter=linter_name,
            success=success,
            errors=errors,
            warnings=warnings,
            raw_output=raw_output,
        )

    def _run_modular_ansible_lint(
        self, file_paths: Optional[List[str]] = None, **kwargs
    ) -> LintResult:
        """Run ansible-lint using the modular implementation."""
        # Check if ansible-lint is available (may be None on Windows)
        if AnsibleLintLinter is None:
            logger.debug(
                "Ansible-lint modular implementation not available, falling back to legacy"
            )
            return self._run_legacy_ansible_lint(file_paths, **kwargs)

        try:
            # Create ansible-lint linter instance
            ansible_linter = AnsibleLintLinter(self.project_info.root_path)

            # Extract profile from kwargs, default to 'basic'
            profile = kwargs.get("profile", "basic")
            logger.debug(f"ansible-lint profile from kwargs: {profile}, all kwargs: {kwargs}")

            # Run the linter with all kwargs
            modular_result = ansible_linter.run(file_paths, **kwargs)

            # Convert modular result to our LintResult format
            return LintResult(
                linter=modular_result.linter,
                success=modular_result.success,
                errors=modular_result.errors,
                warnings=modular_result.warnings,
                raw_output=modular_result.raw_output,
            )

        except Exception as e:
            logger.error(f"Error running modular ansible-lint: {e}")
            # Fallback to legacy implementation
            return self._run_legacy_ansible_lint(file_paths, **kwargs)

    def _run_modular_flake8(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Run flake8 using the modular implementation."""
        if Flake8Linter is None:
            logger.debug("Flake8 modular implementation not available, falling back to legacy")
            return self._run_legacy_flake8(file_paths, **kwargs)

        try:
            logger.info("Using modular flake8 implementation")
            linter = Flake8Linter(self.project_info.root_path)

            if not linter.is_available():
                return LintResult(
                    success=False, errors=[], warnings=[], raw_output="flake8 not available"
                )

            # Check for profile in kwargs
            profile = kwargs.get("profile", "default")
            if hasattr(linter, "run_with_profile"):
                result = linter.run_with_profile(profile, file_paths)
            else:
                result = linter.run(file_paths, **kwargs)

            return result

        except Exception as e:
            logger.error(f"Error running modular flake8: {e}")
            # Fallback to legacy implementation
            return self._run_legacy_flake8(file_paths, **kwargs)

    def _run_modular_pylint(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Run pylint using the modular implementation."""
        if PylintLinter is None:
            logger.debug("Pylint modular implementation not available, falling back to legacy")
            return self._run_legacy_pylint(file_paths, **kwargs)

        try:
            logger.info("Using modular pylint implementation")
            linter = PylintLinter(self.project_info.root_path)

            if not linter.is_available():
                return LintResult(
                    success=False, errors=[], warnings=[], raw_output="pylint not available"
                )

            # Check for profile in kwargs
            profile = kwargs.get("profile", "default")
            if hasattr(linter, "run_with_profile"):
                result = linter.run_with_profile(profile, file_paths)
            else:
                result = linter.run(file_paths, **kwargs)

            return result

        except Exception as e:
            logger.error(f"Error running modular pylint: {e}")
            # Fallback to legacy implementation
            return self._run_legacy_pylint(file_paths, **kwargs)

    def _run_modular_eslint(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Run ESLint using modular implementation."""
        logger.info("Using modular ESLint implementation")

        if ESLintLinter is None:
            logger.warning("ESLintLinter not available, falling back to legacy implementation")
            return self._run_legacy_linter("eslint", file_paths)

        try:
            linter = ESLintLinter(project_root=str(self.project_info.root_path))

            # Handle profile-based execution
            profile = kwargs.get("profile", "default")
            if hasattr(linter, "run_with_profile"):
                result = linter.run_with_profile(profile, file_paths)
            else:
                result = linter.run(file_paths, **kwargs)

            return result
        except Exception as e:
            logger.error(f"Error running modular ESLint: {e}")
            return self._run_legacy_linter("eslint", file_paths)

    def _run_modular_jshint(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Run JSHint using modular implementation."""
        logger.info("Using modular JSHint implementation")

        if JSHintLinter is None:
            logger.warning("JSHintLinter not available, falling back to legacy implementation")
            return self._run_legacy_linter("jshint", file_paths)

        try:
            linter = JSHintLinter(project_root=str(self.project_info.root_path))

            # Handle profile-based execution
            profile = kwargs.get("profile", "default")
            if hasattr(linter, "run_with_profile"):
                result = linter.run_with_profile(profile, file_paths)
            else:
                result = linter.run(file_paths, **kwargs)

            return result
        except Exception as e:
            logger.error(f"Error running modular JSHint: {e}")
            return self._run_legacy_linter("jshint", file_paths)

    def _run_modular_prettier(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Run Prettier using modular implementation."""
        logger.info("Using modular Prettier implementation")

        if PrettierLinter is None:
            logger.warning("PrettierLinter not available, falling back to legacy implementation")
            return self._run_legacy_linter("prettier", file_paths)

        try:
            linter = PrettierLinter(project_root=str(self.project_info.root_path))

            # Handle profile-based execution
            profile = kwargs.get("profile", "default")
            if hasattr(linter, "run_with_profile"):
                result = linter.run_with_profile(profile, file_paths)
            else:
                result = linter.run(file_paths, **kwargs)

            return result
        except Exception as e:
            logger.error(f"Error running modular Prettier: {e}")
            return self._run_legacy_linter("prettier", file_paths)

    def _run_legacy_flake8(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Fallback to legacy flake8 implementation."""
        logger.info("Using legacy flake8 implementation")
        return self._run_legacy_linter("flake8", file_paths)

    def _run_legacy_pylint(self, file_paths: Optional[List[str]] = None, **kwargs) -> LintResult:
        """Fallback to legacy pylint implementation."""
        logger.info("Using legacy pylint implementation")
        return self._run_legacy_linter("pylint", file_paths)

    def _run_legacy_ansible_lint(
        self, file_paths: Optional[List[str]] = None, **kwargs
    ) -> LintResult:
        """Fallback to legacy ansible-lint implementation."""
        logger.info("Using legacy ansible-lint implementation")
        return self._run_legacy_linter("ansible-lint", file_paths)

    def _run_legacy_linter(
        self, linter_name: str, file_paths: Optional[List[str]] = None
    ) -> LintResult:
        """Run linter using the original legacy implementation."""
        linter_name = "ansible-lint"

        if linter_name not in self.LINTER_COMMANDS:
            raise ValueError(f"Unknown linter: {linter_name}")

        # Check availability if not already checked
        if linter_name not in self.available_linters:
            self.available_linters.update(self._detect_available_linters([linter_name]))

        if not self.available_linters.get(linter_name, False):
            logger.warning(f"Linter {linter_name} is not available")
            return LintResult(linter=linter_name, success=False, raw_output="Linter not available")

        # Continue with legacy implementation...
        config = self.LINTER_COMMANDS[linter_name]
        command = config["command"].copy()

        # Add file paths or project root
        if file_paths:
            # Filter files by supported extensions
            supported_extensions = config.get("file_extensions", [])
            if supported_extensions:
                filtered_files = [
                    f for f in file_paths if any(f.endswith(ext) for ext in supported_extensions)
                ]
                if not filtered_files:
                    return LintResult(
                        linter=linter_name,
                        success=True,
                        errors=[],
                        warnings=[],
                        raw_output="No supported files found",
                    )
                command.extend(filtered_files)
        else:
            command.append(".")

        # Run the command
        return self._execute_linter_command(
            linter_name, command, config.get("output_format", "text")
        )

    def _parse_json_output(
        self, linter_name: str, output: str
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse JSON format linter output.

        Args:
            linter_name: Name of the linter
            output: JSON output string

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        if not output.strip():
            return errors, warnings

        try:
            if linter_name == "flake8":
                # Flake8 JSON format
                data = json.loads(output)
                for file_path, file_errors in data.items():
                    for error in file_errors:
                        lint_error = LintError(
                            file_path=file_path,
                            line=error.get("line_number", 0),
                            column=error.get("column_number", 0),
                            rule_id=error.get("code", ""),
                            message=error.get("text", ""),
                            severity=ErrorSeverity.ERROR,
                            linter=linter_name,
                        )
                        errors.append(lint_error)

            elif linter_name == "pylint":
                # Pylint JSON format
                data = json.loads(output)
                for item in data:
                    severity = ErrorSeverity.WARNING
                    if item.get("type") == "error":
                        severity = ErrorSeverity.ERROR
                    elif item.get("type") == "warning":
                        severity = ErrorSeverity.WARNING
                    elif item.get("type") in ["convention", "refactor"]:
                        severity = ErrorSeverity.STYLE

                    lint_error = LintError(
                        file_path=item.get("path", ""),
                        line=item.get("line", 0),
                        column=item.get("column", 0),
                        rule_id=item.get("symbol", ""),
                        message=item.get("message", ""),
                        severity=severity,
                        linter=linter_name,
                    )

                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)

            elif linter_name == "eslint":
                # ESLint JSON format
                data = json.loads(output)
                for file_result in data:
                    file_path = file_result.get("filePath", "")
                    for message in file_result.get("messages", []):
                        severity = (
                            ErrorSeverity.ERROR
                            if message.get("severity") == 2
                            else ErrorSeverity.WARNING
                        )

                        lint_error = LintError(
                            file_path=file_path,
                            line=message.get("line", 0),
                            column=message.get("column", 0),
                            rule_id=message.get("ruleId", ""),
                            message=message.get("message", ""),
                            severity=severity,
                            linter=linter_name,
                        )

                        if severity == ErrorSeverity.ERROR:
                            errors.append(lint_error)
                        else:
                            warnings.append(lint_error)

            elif linter_name == "ansible-lint":
                # Ansible-lint JSON format (new format)
                data = json.loads(output)
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "issue":
                        # Extract error information from new format
                        location = item.get("location", {})
                        file_path = location.get("path", "")

                        # Handle different location formats
                        if "lines" in location:
                            line_num = location["lines"].get("begin", 0)
                            column = 0
                        elif "positions" in location:
                            begin_pos = location["positions"].get("begin", {})
                            line_num = begin_pos.get("line", 0)
                            column = begin_pos.get("column", 0)
                        else:
                            line_num = 0
                            column = 0

                        rule_id = item.get("check_name", "")
                        message = item.get("description", "")
                        severity_str = item.get("severity", "major").lower()

                        # Map ansible-lint severity levels to our severity
                        if severity_str in ["critical", "blocker"]:
                            severity = ErrorSeverity.ERROR
                        elif severity_str in ["major", "minor"]:
                            severity = (
                                ErrorSeverity.ERROR
                            )  # Treat major and minor as errors for ansible-lint
                        else:
                            severity = ErrorSeverity.WARNING

                        lint_error = LintError(
                            file_path=file_path,
                            line=int(line_num) if line_num else 0,
                            column=int(column) if column else 0,
                            rule_id=rule_id,
                            message=message,
                            severity=severity,
                            linter=linter_name,
                        )

                        if severity == ErrorSeverity.ERROR:
                            errors.append(lint_error)
                        else:
                            warnings.append(lint_error)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output from {linter_name}: {e}")

        return errors, warnings

    def _parse_text_output(
        self, linter_name: str, stdout: str, stderr: str
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse text format linter output.

        Args:
            linter_name: Name of the linter
            stdout: Standard output
            stderr: Standard error

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        output = stdout + stderr
        lines = output.split("\n")

        if linter_name == "mypy":
            # MyPy format: file:line: error: message [error-code]
            pattern = (
                r"^(.+?):(\d+):(?:\s*(\d+):)?\s*(error|warning|note):\s*(.+?)(?:\s*\[(.+?)\])?$"
            )

            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, severity_str, message, rule_id = match.groups()

                    severity = (
                        ErrorSeverity.ERROR if severity_str == "error" else ErrorSeverity.WARNING
                    )

                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num) if col_num else 0,
                        rule_id=rule_id or "",
                        message=message,
                        severity=severity,
                        linter=linter_name,
                    )

                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)

        elif linter_name == "flake8":
            # Flake8 format: file:line:column: code message
            pattern = r"^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)$"

            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, rule_id, message = match.groups()

                    # Determine severity based on rule code
                    severity = (
                        ErrorSeverity.ERROR
                        if rule_id.startswith("E") or rule_id.startswith("F")
                        else ErrorSeverity.WARNING
                    )

                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id=rule_id,
                        message=message,
                        severity=severity,
                        linter=linter_name,
                    )

                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)

        elif linter_name == "golint":
            # GoLint format: file:line:column: message
            pattern = r"^(.+?):(\d+):(\d+):\s*(.+)$"

            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, message = match.groups()

                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id="",
                        message=message,
                        severity=ErrorSeverity.WARNING,
                        linter=linter_name,
                    )
                    warnings.append(lint_error)

        elif linter_name == "govet":
            # Go vet format: file:line:column: message
            pattern = r"^(.+?):(\d+):(\d+):\s*(.+)$"

            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, message = match.groups()

                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id="",
                        message=message,
                        severity=ErrorSeverity.ERROR,
                        linter=linter_name,
                    )
                    errors.append(lint_error)

        elif linter_name == "prettier":
            # Prettier outputs file names that need formatting
            for line in lines:
                line = line.strip()
                if line and not line.startswith("["):
                    lint_error = LintError(
                        file_path=line,
                        line=0,
                        column=0,
                        rule_id="formatting",
                        message="File needs formatting",
                        severity=ErrorSeverity.STYLE,
                        linter=linter_name,
                    )
                    warnings.append(lint_error)

        return errors, warnings

    def _parse_diff_output(
        self, linter_name: str, output: str
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse diff format linter output.

        Args:
            linter_name: Name of the linter
            output: Diff output string

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        if not output.strip():
            return errors, warnings

        # Parse diff output to extract file names and changes
        lines = output.split("\n")
        current_file = None

        for line in lines:
            if line.startswith("--- ") or line.startswith("+++ "):
                # Extract file name from diff header
                if line.startswith("--- "):
                    current_file = line[4:].strip()
            elif line.startswith("@@"):
                # Extract line number from diff hunk header
                match = re.search(r"@@\s*-(\d+)", line)
                if match and current_file:
                    line_num = int(match.group(1))

                    lint_error = LintError(
                        file_path=current_file,
                        line=line_num,
                        column=0,
                        rule_id="formatting",
                        message=f"{linter_name} formatting required",
                        severity=ErrorSeverity.STYLE,
                        linter=linter_name,
                        context=output,  # Include full diff as context
                    )
                    warnings.append(lint_error)

        return errors, warnings

    def run_all_available_linters(
        self, enabled_linters: Optional[List[str]] = None, **linter_options
    ) -> Dict[str, LintResult]:
        """Run all available linters on the project.

        Args:
            enabled_linters: Optional list of linters to run (runs all available if None)

        Returns:
            Dictionary mapping linter names to their results
        """
        results = {}

        # Determine which linters to check
        linters_to_check = enabled_linters or list(self.LINTER_COMMANDS.keys())

        # Only check availability for the linters we want to run
        if enabled_linters:
            # Check only the requested linters
            self.available_linters.update(self._detect_available_linters(enabled_linters))
        else:
            # Check all linters if none specified
            self.available_linters = self._detect_available_linters()

        for linter_name in linters_to_check:
            if self.available_linters.get(linter_name, False):
                logger.info(f"Running linter: {linter_name}")

                # Pass linter-specific options
                linter_kwargs = {}
                if linter_name == "ansible-lint":
                    if "ansible_profile" in linter_options:
                        linter_kwargs["profile"] = linter_options["ansible_profile"]
                        logger.debug(
                            f"Setting ansible-lint profile to: {linter_options['ansible_profile']}"
                        )

                    if "exclude" in linter_options:
                        linter_kwargs["exclude"] = linter_options["exclude"]
                        logger.debug(
                            f"Setting ansible-lint exclude patterns: {linter_options['exclude']}"
                        )

                logger.debug(f"Running {linter_name} with kwargs: {linter_kwargs}")
                results[linter_name] = self.run_linter(linter_name, **linter_kwargs)
            else:
                logger.warning(f"Skipping unavailable linter: {linter_name}")

        return results

    def get_error_summary(self, results: Dict[str, LintResult]) -> Dict[str, Any]:
        """Get a summary of all lint errors.

        Args:
            results: Dictionary of lint results

        Returns:
            Summary dictionary with error counts and details
        """
        total_errors = 0
        total_warnings = 0
        errors_by_file = {}
        errors_by_rule = {}

        for linter_name, result in results.items():
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)

            for error in result.errors + result.warnings:
                # Group by file
                if error.file_path not in errors_by_file:
                    errors_by_file[error.file_path] = []
                errors_by_file[error.file_path].append(error)

                # Group by rule
                rule_key = f"{error.linter}:{error.rule_id}"
                if rule_key not in errors_by_rule:
                    errors_by_rule[rule_key] = []
                errors_by_rule[rule_key].append(error)

        return {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "files_with_errors": len(errors_by_file),
            "unique_rules": len(errors_by_rule),
            "errors_by_file": errors_by_file,
            "errors_by_rule": errors_by_rule,
            "linter_results": {name: len(result.errors) for name, result in results.items()},
        }
