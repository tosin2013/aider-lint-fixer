"""
Prettier specific implementation.

Tested with Prettier v3.6.2
"""

import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class PrettierLinter(BaseLinter):
    """Prettier implementation for code formatting checks."""

    SUPPORTED_VERSIONS = ["3.6.2", "3.6", "3.", "2."]

    @property
    def name(self) -> str:
        return "prettier"

    @property
    def supported_extensions(self) -> List[str]:
        return [
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".json",
            ".css",
            ".scss",
            ".html",
            ".md",
            ".yaml",
            ".yml",
        ]

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if Prettier is installed."""
        try:
            # Try npx first, then global prettier
            result = self.run_command(["npx", "prettier", "--version"], timeout=10)
            if result.returncode == 0:
                return True

            # Fallback to global prettier
            result = self.run_command(["prettier", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get Prettier version."""
        try:
            # Try npx first
            result = self.run_command(["npx", "prettier", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "3.6.2"
                version = result.stdout.strip()
                if re.match(r"^\d+\.\d+\.\d+", version):
                    return version

            # Fallback to global prettier
            result = self.run_command(["prettier", "--version"], timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                if re.match(r"^\d+\.\d+\.\d+", version):
                    return version
        except Exception:
            pass
        return None

    def build_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
        """Build Prettier command."""
        # Use npx if available, otherwise global prettier
        command = ["npx", "prettier"] if self._has_npx() else ["prettier"]

        # Add check mode (don't write files)
        command.append("--check")

        # Add configuration options
        if "config" in kwargs:
            command.extend(["--config", kwargs["config"]])

        # Add ignore path
        if "ignore_path" in kwargs:
            command.extend(["--ignore-path", kwargs["ignore_path"]])

        # Add formatting options
        if "tab_width" in kwargs:
            command.extend(["--tab-width", str(kwargs["tab_width"])])

        if "use_tabs" in kwargs:
            command.extend(["--use-tabs", str(kwargs["use_tabs"]).lower()])

        if "single_quote" in kwargs:
            command.extend(["--single-quote", str(kwargs["single_quote"]).lower()])

        if "trailing_comma" in kwargs:
            command.extend(["--trailing-comma", kwargs["trailing_comma"]])

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
        """Parse Prettier output."""
        errors = []
        warnings = []

        # Prettier with --check outputs files that need formatting
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("[") and not line.startswith("Checking"):
                    file_path = line

                    # Convert absolute path to relative
                    project_root_str = str(self.project_root)
                    if file_path.startswith(project_root_str):
                        file_path = file_path[len(project_root_str) :].lstrip("/")

                    lint_error = LintError(
                        file_path=file_path,
                        line=0,  # Prettier doesn't provide line numbers for formatting issues
                        column=0,
                        rule_id="formatting",
                        message="Code style issues found. Run Prettier with --write to fix.",
                        severity=ErrorSeverity.WARNING,  # Formatting issues are warnings
                        linter=self.name,
                    )

                    warnings.append(lint_error)

        # Check stderr for actual errors
        if stderr.strip():
            for line in stderr.strip().split("\n"):
                if line.strip() and not line.startswith("[warn]"):
                    lint_error = LintError(
                        file_path="unknown",
                        line=0,
                        column=0,
                        rule_id="prettier-error",
                        message=line.strip(),
                        severity=ErrorSeverity.ERROR,
                        linter=self.name,
                    )

                    errors.append(lint_error)

        return errors, warnings

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # Prettier returns 0 for no formatting issues, 1 for formatting issues found
        return return_code in [0, 1]

    def run_with_profile(
        self, profile: str, file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run Prettier with different profiles.

        Args:
            profile: 'basic' for minimal formatting, 'strict' for comprehensive formatting
            file_paths: Optional list of files to check
        """
        if profile == "basic":
            # Basic profile: Minimal formatting rules
            kwargs = {"tab_width": 4, "use_tabs": False, "single_quote": False}
        elif profile == "strict":
            # Strict profile: Comprehensive formatting
            kwargs = {
                "tab_width": 2,
                "use_tabs": False,
                "single_quote": True,
                "trailing_comma": "es5",
            }
        else:
            # Default profile: Standard formatting
            kwargs = {"tab_width": 2, "use_tabs": False, "single_quote": True}

        return self.run(file_paths, **kwargs)
