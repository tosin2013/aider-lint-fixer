"""
ESLint specific implementation.

Tested with ESLint v8.57.1
"""

import json
import re
from typing import List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError
from .base import BaseLinter, LinterResult


class ESLintLinter(BaseLinter):
    """ESLint implementation for JavaScript/TypeScript code quality checking."""

    SUPPORTED_VERSIONS = ["8.57.1", "8.57", "8.5", "8.", "7."]

    @property
    def name(self) -> str:
        return "eslint"

    @property
    def supported_extensions(self) -> List[str]:
        # Dynamically detect supported extensions based on project setup
        base_extensions = [".js", ".jsx", ".mjs", ".cjs"]

        # Add TypeScript extensions if TypeScript is detected
        if self._has_typescript_support():
            base_extensions.extend([".ts", ".tsx"])

        return base_extensions

    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS

    def is_available(self) -> bool:
        """Check if ESLint is installed."""
        try:
            # Try npx first, then global eslint
            result = self.run_command(["npx", "eslint", "--version"], timeout=10)
            if result.returncode == 0:
                return True

            # Fallback to global eslint
            result = self.run_command(["eslint", "--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Get ESLint version."""
        try:
            # Try npx first
            result = self.run_command(["npx", "eslint", "--version"], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "v8.57.1"
                match = re.search(r"v?(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)

            # Fallback to global eslint
            result = self.run_command(["eslint", "--version"], timeout=10)
            if result.returncode == 0:
                match = re.search(r"v?(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def build_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
        """Build ESLint command with project-specific configuration detection."""
        # Try to use npm script first if available
        if self._should_use_npm_script():
            return self._build_npm_command(file_paths, **kwargs)

        # Use npx if available, otherwise global eslint
        command = ["npx", "eslint"] if self._has_npx() else ["eslint"]

        # Add JSON format for parsing
        command.extend(["--format=json"])

        # Auto-detect and use project configuration
        config_file = self._detect_eslint_config()
        if config_file and "config" not in kwargs:
            command.extend(["--config", str(config_file)])
        elif "config" in kwargs:
            command.extend(["--config", kwargs["config"]])

        # Add ignore patterns
        if "ignore_pattern" in kwargs:
            command.extend(["--ignore-pattern", kwargs["ignore_pattern"]])

        # Add rules to disable/enable
        if "disable_rules" in kwargs:
            for rule in kwargs["disable_rules"]:
                command.extend(["--rule", f"{rule}: of"])

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

    def _should_use_npm_script(self) -> bool:
        """Check if we should use npm run lint instead of direct ESLint."""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return False

        try:
            import json

            with open(package_json, "r") as f:
                data = json.load(f)

            scripts = data.get("scripts", {})
            # Check if there's a lint script that uses ESLint
            lint_script = scripts.get("lint", "")
            return "eslint" in lint_script.lower()
        except Exception:
            return False

    def _build_npm_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
        """Build npm run lint command."""
        command = ["npm", "run", "lint", "--", "--format=json"]

        # Add file paths if specified
        if file_paths:
            command.extend(file_paths)

        return command

    def _detect_eslint_config(self) -> Optional[str]:
        """Auto-detect ESLint configuration file."""
        config_files = [
            "eslint.config.js",     # Modern flat config (ESLint v9+)
            "eslint.config.mjs",    # ES modules flat config
            "eslint.config.cjs",    # CommonJS flat config
            ".eslintrc.js",         # Legacy configs
            ".eslintrc.cjs",
            ".eslintrc.yaml",
            ".eslintrc.yml",
            ".eslintrc.json",
            ".eslintrc",
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                return str(config_path)

        # Check package.json for eslintConfig
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json

                with open(package_json, "r") as f:
                    data = json.load(f)
                if "eslintConfig" in data:
                    return str(package_json)
            except Exception:
                pass

        return None

    def _has_typescript_support(self) -> bool:
        """Check if the project has TypeScript support configured."""
        # Check for tsconfig.json
        if (self.project_root / "tsconfig.json").exists():
            return True

        # Check for TypeScript dependencies in package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json

                with open(package_json, "r") as f:
                    data = json.load(f)

                # Check dependencies and devDependencies
                all_deps = {}
                all_deps.update(data.get("dependencies", {}))
                all_deps.update(data.get("devDependencies", {}))

                # Look for TypeScript-related packages
                ts_packages = [
                    "typescript",
                    "@typescript-eslint/parser",
                    "@typescript-eslint/eslint-plugin",
                    "ts-node",
                    "ts-loader",
                ]

                return any(pkg in all_deps for pkg in ts_packages)
            except Exception:
                pass

        # Check for .ts or .tsx files in the project
        for ext in [".ts", ".tsx"]:
            if any(self.project_root.rglob(f"*{ext}")):
                return True

        return False

    def _extract_json_from_output(self, output: str) -> str:
        """Extract JSON from npm script output which may contain extra text."""
        lines = output.strip().split("\n")

        # Look for JSON array start
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("["):
                json_start = i
                break

        if json_start == -1:
            return output  # No JSON array found, return original

        # Extract from JSON start to end
        json_lines = lines[json_start:]
        return "\n".join(json_lines)

    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse ESLint JSON output."""
        errors = []
        warnings = []

        if not stdout.strip():
            return errors, warnings

        try:
            # Handle npm script output which might have extra text
            json_output = self._extract_json_from_output(stdout)
            if not json_output:
                return errors, warnings

            # Parse JSON output
            data = json.loads(json_output)

            for file_result in data:
                file_path = file_result.get("filePath", "")
                # Convert absolute path to relative
                project_root_str = str(self.project_root)
                if file_path.startswith(project_root_str):
                    file_path = file_path[len(project_root_str) :].lstrip("/")

                messages = file_result.get("messages", [])

                for message in messages:
                    line_num = message.get("line", 0)
                    column = message.get("column", 0)
                    rule_id = message.get("ruleId", "unknown")
                    msg_text = message.get("message", "")
                    severity = message.get("severity", 1)

                    # Map ESLint severity to our severity levels
                    # ESLint: 1 = warning, 2 = error
                    if severity == 2:
                        error_severity = ErrorSeverity.ERROR
                    else:
                        error_severity = ErrorSeverity.WARNING

                    lint_error = LintError(
                        file_path=file_path,
                        line=line_num,
                        column=column,
                        rule_id=rule_id,
                        message=msg_text,
                        severity=error_severity,
                        linter=self.name,
                    )

                    if error_severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse ESLint JSON output: {e}")
            # Create fallback error
            errors.append(
                LintError(
                    file_path="unknown",
                    line=0,
                    column=0,
                    rule_id="parse-error",
                    message=f"Failed to parse ESLint output: {e}",
                    severity=ErrorSeverity.ERROR,
                    linter=self.name,
                )
            )

        return errors, warnings

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # ESLint returns 0 for no issues, 1 for issues found, 2 for errors
        return return_code in [0, 1]

    def run_with_profile(
        self, profile: str, file_paths: Optional[List[str]] = None
    ) -> LinterResult:
        """Run ESLint with different profiles.

        Args:
            profile: 'basic' for essential checks, 'strict' for comprehensive checks
            file_paths: Optional list of files to check
        """
        if profile == "basic":
            # Basic profile: Focus on errors and important warnings
            kwargs = {"disable_rules": ["no-console", "no-unused-vars"]}
        elif profile == "strict":
            # Strict profile: All checks enabled
            kwargs = {}
        else:
            # Default profile: Moderate checking
            kwargs = {"disable_rules": ["no-console"]}

        return self.run(file_paths, **kwargs)
