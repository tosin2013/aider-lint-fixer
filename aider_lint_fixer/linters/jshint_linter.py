"""
JSHint specific implementation.

Tested with JSHint v2.13.6
"""

import json
import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class JSHintLinter(BaseLinter):
    """JSHint implementation for JavaScript code quality checking."""

    SUPPORTED_VERSIONS = ["2.13.6", "2.13", "2.1", "2."]

    @property
    def name(self) -> str:
        return "jshint"

    @property
    def supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if JSHint is installed."""
        try:
            # Try npx first, then global jshint
            result = self.run_command(["npx", "jshint", "--version"], timeout=10)
            if result.returncode == 0:
                return True

            # Fallback to global jshint
            result = self.run_command(["jshint", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get JSHint version."""
        try:
            # Try npx first
            result = self.run_command(["npx", "jshint", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "jshint v2.13.6"
                match = re.search(r"jshint v?(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)

            # Fallback to global jshint
            result = self.run_command(["jshint", "--version"], timeout=10)
            if result.returncode == 0:
                match = re.search(r"jshint v?(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def build_command(
        self, file_paths: Optional[List[str]] = None, **kwargs
    ) -> List[str]:
        """Build JSHint command."""
        # Use npx if available, otherwise global jshint
        command = ["npx", "jshint"] if self._has_npx() else ["jshint"]

        # Add JSON reporter for parsing
        command.extend(["--reporter=json"])

        # Add configuration options
        if "config" in kwargs:
            command.extend(["--config", kwargs["config"]])

        # Add JSHint options
        if "esversion" in kwargs:
            command.extend(["--esversion", str(kwargs["esversion"])])

        # Add strict mode
        if kwargs.get("strict", False):
            command.append("--strict")

        # Add file paths
        if file_paths:
            command.extend(file_paths)
        else:
            command.append(".")

        return command

    def _has_npx(self) -> bool:
        """Check if npx is available."""
        try:
            result = self.run_command(["npx", "--version"], timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse JSHint JSON output."""
        errors = []
        warnings = []

        if not stdout.strip():
            return errors, warnings

        try:
            # Parse JSON output
            data = json.loads(stdout)

            for message in data:
                file_path = message.get("file", "")
                # Convert absolute path to relative
                project_root_str = str(self.project_root)
                if file_path.startswith(project_root_str):
                    file_path = file_path[len(project_root_str) :].lstrip("/")

                line_num = message.get("line", 0)
                character = message.get("character", 0)
                reason = message.get("reason", "")
                code = message.get("code", "unknown")

                # JSHint doesn't have explicit severity levels
                # We'll treat all as errors for consistency
                lint_error = LintError(
                    file_path=file_path,
                    line=line_num,
                    column=character,
                    rule_id=code,
                    message=reason,
                    severity=ErrorSeverity.ERROR,
                    linter=self.name,
                )

                errors.append(lint_error)

        except json.JSONDecodeError:
            # Fallback to text parsing if JSON fails
            self.logger.warning("JSHint JSON parsing failed, attempting text parsing")
            errors.extend(self._parse_text_output(stdout))

        return errors, warnings

    def _parse_text_output(self, output: str) -> List[LintError]:
        """Parse JSHint text output as fallback."""
        errors = []

        for line in output.split("\n"):
            if not line.strip():
                continue

            # Parse format: "file.js: line X, col Y, message"
            match = re.match(r"^(.+?):\s*line\s+(\d+),\s*col\s+(\d+),\s*(.+)$", line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                column = int(match.group(3))
                message = match.group(4)

                # Convert absolute path to relative
                project_root_str = str(self.project_root)
                if file_path.startswith(project_root_str):
                    file_path = file_path[len(project_root_str) :].lstrip("/")

                lint_error = LintError(
                    file_path=file_path,
                    line=line_num,
                    column=column,
                    rule_id="jshint-error",
                    message=message,
                    severity=ErrorSeverity.ERROR,
                    linter=self.name,
                )

                errors.append(lint_error)

        return errors

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # JSHint returns 0 for no issues, 2 for issues found
        return return_code in [0, 2]

    def run_with_profile(
        self, profile: str, file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run JSHint with different profiles.

        Args:
            profile: 'basic' for essential checks, 'strict' for comprehensive checks
            file_paths: Optional list of files to check
        """
        if profile == "basic":
            # Basic profile: ES6 support, less strict
            kwargs = {"esversion": 6, "strict": False}
        elif profile == "strict":
            # Strict profile: Latest ES version, strict mode
            kwargs = {"esversion": 8, "strict": True}
        else:
            # Default profile: Moderate checking
            kwargs = {"esversion": 6}

        return self.run(file_paths, **kwargs)
