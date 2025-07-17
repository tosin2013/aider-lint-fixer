"""
Pylint specific implementation.

Tested with pylint 3.3.7
"""

import json
import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class PylintLinter(BaseLinter):
    """Pylint implementation for Python code analysis."""

    SUPPORTED_VERSIONS = ["3.3.7", "3.3", "3.2", "3.1", "3.0", "2."]

    @property
    def name(self) -> str:
        return "pylint"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py"]

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if pylint is installed."""
        try:
            result = self.run_command(["pylint", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get pylint version."""
        try:
            result = self.run_command(["pylint", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "pylint 3.3.7"
                match = re.search(r"pylint\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def build_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
        """Build pylint command."""
        command = ["pylint", "--output-format=json"]

        # Add configuration options
        if "config" in kwargs:
            command.extend(["--rcfile", kwargs["config"]])

        # Add disable rules if specified
        if "disable" in kwargs:
            command.extend(["--disable", kwargs["disable"]])

        # Add enable rules if specified
        if "enable" in kwargs:
            command.extend(["--enable", kwargs["enable"]])

        # Add score option
        if kwargs.get("no_score", True):
            command.append("--score=no")

        # Add file paths
        if file_paths:
            command.extend(file_paths)
        else:
            command.append(".")

        return command

    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse pylint JSON output."""
        errors = []
        warnings = []

        if not stdout.strip():
            return errors, warnings

        try:
            # Parse JSON output
            data = json.loads(stdout)

            for item in data:
                file_path = item.get("path", "")
                line_num = item.get("line", 0)
                column = item.get("column", 0)
                rule_id = item.get("symbol", "")
                message = item.get("message", "")
                msg_type = item.get("type", "convention")

                # Map pylint types to our severity levels
                if msg_type in ["error", "fatal"]:
                    severity = ErrorSeverity.ERROR
                elif msg_type in ["warning"]:
                    severity = ErrorSeverity.WARNING
                elif msg_type in ["convention", "refactor"]:
                    # Treat convention and refactor as warnings for now
                    severity = ErrorSeverity.WARNING
                else:
                    severity = ErrorSeverity.WARNING

                lint_error = LintError(
                    file_path=file_path,
                    line=line_num,
                    column=column,
                    rule_id=rule_id,
                    message=message,
                    severity=severity,
                    linter=self.name,
                )

                if severity == ErrorSeverity.ERROR:
                    errors.append(lint_error)
                else:
                    warnings.append(lint_error)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse pylint JSON output: {e}")
            # Create fallback error
            errors.append(
                LintError(
                    file_path="unknown",
                    line=0,
                    column=0,
                    rule_id="parse-error",
                    message=f"Failed to parse pylint output: {e}",
                    severity=ErrorSeverity.ERROR,
                    linter=self.name,
                )
            )

        return errors, warnings

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # pylint returns various exit codes:
        # 0: no issues, 1-32: various issue types found
        # We consider it successful if it ran (even with issues found)
        return return_code < 64  # Anything above 64 is usually a fatal error

    def run_with_profile(
        self, profile: str, file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run pylint with different profiles.

        Args:
            profile: 'basic' for essential checks, 'strict' for comprehensive checks
            file_paths: Optional list of files to check
        """
        if profile == "basic":
            # Basic profile: Disable some verbose checks
            kwargs = {
                "disable": "missing-docstring,line-too-long,trailing-whitespace,too-few-public-methods",
                "no_score": True,
            }
        elif profile == "strict":
            # Strict profile: Enable all checks
            kwargs = {"no_score": True}
        else:
            # Default profile: Moderate checking
            kwargs = {"disable": "missing-docstring,too-few-public-methods", "no_score": True}

        return self.run(file_paths, **kwargs)
