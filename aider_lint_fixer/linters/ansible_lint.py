"""
Ansible-lint specific implementation.

Tested with ansible-lint 25.6.1
"""

import json
import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class AnsibleLintLinter(BaseLinter):
    """Ansible-lint implementation."""

    # Version compatibility matrix
    SUPPORTED_VERSIONS = [
        # Latest versions (Technology Preview)
        "25.6.1",  # Tested latest version
        "25.6",  # Minor version compatibility
        "25.",  # Major version compatibility
        # Enterprise/RHEL 9 compatible versions
        "6.22.2",  # Enterprise standard
        "6.22",  # Minor version compatibility
        "6.2",  # Patch version compatibility
        "6.",  # Major version compatibility
        # RHEL 10 compatible versions (ansible-core 2.18.x)
        "24.12.2",  # RHEL 10 compatible
        "24.12",  # Minor version compatibility
        "24.",  # Major version compatibility
    ]

    # Profile configurations
    PROFILES = {
        "basic": {
            "description": "Basic rules for common issues and style",
            "recommended_for": "development",
        },
        "production": {
            "description": "Comprehensive rules for production-ready code",
            "recommended_for": "production",
        },
    }

    @property
    def name(self) -> str:
        return "ansible-lint"

    @property
    def supported_extensions(self) -> List[str]:
        return [".yml", ".yaml"]

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if ansible-lint is installed."""
        try:
            result = self.run_command(["ansible-lint", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get ansible-lint version."""
        try:
            result = self.run_command(["ansible-lint", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "ansible-lint 25.6.1 using..."
                match = re.search(r"ansible-lint\s+(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    version = match.group(1)
                    # Cache the version for performance
                    self._cached_version = version
                    return version
        except Exception as e:
            self.logger.debug(f"Failed to get ansible-lint version: {e}")
        return getattr(self, "_cached_version", None)

    def build_command(
        self, file_paths: Optional[List[str]] = None, profile: str = "basic", **kwargs
    ) -> List[str]:
        """Build ansible-lint command."""
        # Check for ansible_profile in kwargs (used by modular implementation)
        actual_profile = kwargs.get("ansible_profile", profile)
        self.logger.debug(
            f"Building ansible-lint command with profile: {actual_profile}, kwargs: {kwargs}"
        )
        command = ["ansible-lint", "--format=json", "--strict", f"--profile={actual_profile}"]

        # Add exclude patterns if provided
        exclude_patterns = kwargs.get("exclude", [])
        if isinstance(exclude_patterns, str):
            exclude_patterns = [exclude_patterns]

        for pattern in exclude_patterns:
            command.extend(["--exclude", pattern])

        # Add other ansible-lint specific options
        if "config" in kwargs:
            command.extend(["--config-file", kwargs["config"]])

        if "tags" in kwargs:
            command.extend(["--tags", kwargs["tags"]])

        if "skip_list" in kwargs:
            command.extend(["--skip-list", kwargs["skip_list"]])

        self.logger.debug(f"Built command: {' '.join(command)}")

        # Add file paths or find ansible files in current directory
        if file_paths:
            command.extend(file_paths)
        else:
            # Find ansible files in the project directory
            ansible_files = self._find_ansible_files()
            if ansible_files:
                command.extend(ansible_files)
            else:
                command.append(".")

        return command

    def _find_ansible_files(self) -> List[str]:
        """Find ansible files in the project directory recursively."""
        ansible_files = []

        for ext in self.supported_extensions:
            # Use recursive glob to find files in subdirectories
            for file_path in self.project_root.glob(f"**/*{ext}"):
                if file_path.is_file():
                    # Use relative path from project root
                    relative_path = file_path.relative_to(self.project_root)
                    ansible_files.append(str(relative_path))

        return ansible_files

    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse ansible-lint mixed output (human-readable + JSON)."""
        errors = []
        warnings = []

        if not stdout or stdout.strip() == "[]":
            return errors, warnings

        # Extract JSON from mixed output
        json_data = self._extract_json_from_output(stdout)
        if not json_data:
            # If no JSON found, try to parse human-readable format
            return self._parse_human_readable_output(stdout, stderr)

        try:
            # Parse JSON output
            data = json.loads(json_data)

            for item in data:
                if not isinstance(item, dict) or item.get("type") != "issue":
                    continue

                # Extract location information
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

                # Extract error details
                rule_id = item.get("check_name", "")
                message = item.get("description", "")
                severity_str = item.get("severity", "major").lower()

                # Map severity
                if severity_str in ["critical", "blocker"]:
                    severity = ErrorSeverity.ERROR
                elif severity_str in ["major", "minor"]:
                    severity = ErrorSeverity.ERROR  # Treat as errors for ansible-lint
                else:
                    severity = ErrorSeverity.WARNING

                # Create lint error
                lint_error = LintError(
                    file_path=file_path,
                    line=line_num,
                    column=column,
                    rule_id=rule_id,
                    message=message,
                    severity=severity,
                    linter=self.name,
                    context=item.get("content", {}).get("body"),
                    fix_suggestion=self._generate_fix_suggestion(rule_id, message),
                )

                if severity == ErrorSeverity.ERROR:
                    errors.append(lint_error)
                else:
                    warnings.append(lint_error)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse ansible-lint JSON output: {e}")
            # Fallback: create a generic error
            errors.append(
                LintError(
                    file_path="unknown",
                    line=0,
                    column=0,
                    rule_id="parse-error",
                    message=f"Failed to parse ansible-lint output: {e}",
                    severity=ErrorSeverity.ERROR,
                    linter=self.name,
                )
            )

        return errors, warnings

    def _extract_json_from_output(self, output: str) -> Optional[str]:
        """Extract JSON array from mixed ansible-lint output."""
        lines = output.split("\n")

        for line in lines:
            line = line.strip()
            # Look for lines that start with '[' and contain JSON-like content
            if line.startswith("[") and '"type": "issue"' in line:
                return line

        return None

    def _parse_human_readable_output(
        self, stdout: str, stderr: str
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse human-readable ansible-lint output as fallback."""
        errors = []
        warnings = []

        lines = stdout.split("\n")

        # Look for rule violation summary
        in_summary = False
        for line in lines:
            line = line.strip()

            if "# Rule Violation Summary" in line:
                in_summary = True
                continue

            if in_summary and line and not line.startswith("#"):
                # Parse lines like "  1 command-instead-of-shell profile:basic tags:command-shell,idiom"
                if line.startswith("Failed:") or line.startswith("["):
                    break

                # Extract rule information
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        count = int(parts[0])
                        rule_name = parts[1]

                        # Create a generic error for each violation
                        for i in range(count):
                            error = LintError(
                                file_path="unknown",
                                line=0,
                                column=0,
                                rule_id=rule_name,
                                message=f"Rule violation: {rule_name}",
                                severity=ErrorSeverity.ERROR,
                                linter=self.name,
                                fix_suggestion=self._generate_fix_suggestion(rule_name, ""),
                            )
                            errors.append(error)
                    except (ValueError, IndexError):
                        continue

        return errors, warnings

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Ansible-lint returns 2 when issues are found, which is still a successful run."""
        return return_code in [0, 2]  # 0 = no issues, 2 = issues found

    def _generate_fix_suggestion(self, rule_id: str, message: str) -> Optional[str]:
        """Generate fix suggestions for common ansible-lint rules."""
        fix_suggestions = {
            "name[play]": 'Add a name to your play: - name: "Descriptive play name"',
            "name[missing]": 'Add a name to your task: - name: "Descriptive task name"',
            "name[casing]": "Start task names with uppercase letter",
            "command-instead-of-shell": "Use command module instead of shell when shell features are not needed",
            "no-free-form": "Use structured parameters instead of free-form strings",
            "yaml[indentation]": "Fix YAML indentation (use 2 spaces per level)",
            "yaml[truthy]": "Use true/false instead of yes/no for boolean values",
            "fqcn[action-core]": "Use fully qualified collection names (e.g., ansible.builtin.debug)",
            "no-changed-when": "Add changed_when: false for commands that don't change state",
            "risky-shell-pipe": "Set pipefail option when using shell with pipes",
        }

        return fix_suggestions.get(rule_id)

    def get_profile_info(self) -> dict:
        """Get information about available profiles."""
        return self.PROFILES

    def run_with_profile(
        self, profile: str = "basic", file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run ansible-lint with a specific profile."""
        if profile not in self.PROFILES:
            raise ValueError(
                f"Unsupported profile: {profile}. Supported: {list(self.PROFILES.keys())}"
            )

        result = self.run(file_paths=file_paths, profile=profile)
        result.profile = profile
        return result
