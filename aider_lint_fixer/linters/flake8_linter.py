"""
Flake8 specific implementation.

Tested with flake8 7.3.0
"""

import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class Flake8Linter(BaseLinter):
    """Flake8 implementation for Python code style checking."""

    SUPPORTED_VERSIONS = ["7.3.0", "7.2", "7.1", "7.0", "6."]

    @property
    def name(self) -> str:
        return "flake8"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py"]

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if flake8 is installed."""
        try:
            result = self.run_command(["flake8", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get flake8 version."""
        try:
            result = self.run_command(["flake8", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "7.3.0 (mccabe: 0.7.0, pycodestyle: 2.14.0, pyflakes: 3.4.0)"
                match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def build_command(
        self, file_paths: Optional[List[str]] = None, **kwargs
    ) -> List[str]:
        """Build flake8 command."""
        command = ["flake8"]

        # Add configuration options
        if "config" in kwargs:
            command.extend(["--config", kwargs["config"]])

        # Add max line length if specified
        if "max_line_length" in kwargs:
            command.extend(["--max-line-length", str(kwargs["max_line_length"])])

        # Add ignore rules if specified
        if "ignore" in kwargs:
            command.extend(["--ignore", kwargs["ignore"]])

        # Add file paths
        if file_paths:
            command.extend(file_paths)
        else:
            command.append(".")

        return command

    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse flake8 output.

        Flake8 format: file:line:column: code message
        Example: problematic_code.py:4:1: F401 'os' imported but unused
        """
        errors = []
        warnings = []

        if not stdout.strip():
            return errors, warnings

        # Pattern to match flake8 output
        pattern = r"^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)$"

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                column = int(match.group(3))
                rule_id = match.group(4)
                message = match.group(5)

                # Determine severity based on rule type
                # E = Error, W = Warning, F = Flake (pyflakes), C = Complexity
                if rule_id.startswith(("E", "F")):
                    severity = ErrorSeverity.ERROR
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
            else:
                self.logger.debug(f"Could not parse flake8 line: {line}")

        return errors, warnings

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # flake8 returns 0 for no issues, 1 for issues found
        return return_code in [0, 1]

    def run_with_profile(
        self, profile: str, file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run flake8 with different profiles.

        Args:
            profile: 'basic' for essential checks, 'strict' for comprehensive checks
            file_paths: Optional list of files to check
        """
        if profile == "basic":
            # Basic profile: Focus on errors and important warnings
            kwargs = {
                "ignore": "W293,W291",
                "max_line_length": "100",
            }  # Ignore whitespace warnings
        elif profile == "strict":
            # Strict profile: All checks enabled
            kwargs = {"max_line_length": "79"}  # PEP 8 standard
        else:
            # Default profile
            kwargs = {}

        return self.run(file_paths, **kwargs)
