"""
Project Detection Module

This module handles automatic detection of project types, programming languages,
package managers, and lint configurations.
"""

import configparser
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Information about a detected project."""

    root_path: Path
    languages: Set[str] = field(default_factory=set)
    package_managers: Set[str] = field(default_factory=set)
    lint_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    source_files: List[Path] = field(default_factory=list)
    config_files: List[Path] = field(default_factory=list)


class ProjectDetector:
    """Detects project structure, languages, and lint configurations."""

    # File patterns for different languages
    LANGUAGE_PATTERNS = {
        "python": {
            "extensions": [".py", ".pyx", ".pyi"],
            "files": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "directories": ["__pycache__"],
        },
        "javascript": {
            "extensions": [".js", ".jsx", ".mjs"],
            "files": ["package.json", "package-lock.json", "yarn.lock"],
            "directories": ["node_modules"],
        },
        "typescript": {
            "extensions": [".ts", ".tsx", ".d.ts"],
            "files": ["tsconfig.json", "tslint.json"],
            "directories": [],
        },
        "go": {
            "extensions": [".go"],
            "files": ["go.mod", "go.sum", "Gopkg.toml"],
            "directories": ["vendor"],
        },
        "rust": {
            "extensions": [".rs"],
            "files": ["Cargo.toml", "Cargo.lock"],
            "directories": ["target"],
        },
        "java": {
            "extensions": [".java"],
            "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "directories": ["target", "build"],
        },
        "c": {
            "extensions": [".c", ".h"],
            "files": ["Makefile", "CMakeLists.txt"],
            "directories": [],
        },
        "cpp": {
            "extensions": [".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh"],
            "files": ["Makefile", "CMakeLists.txt"],
            "directories": [],
        },
        "ansible": {
            "extensions": [".yml", ".yaml"],
            "files": ["ansible.cfg", "hosts", "inventory", "site.yml", "playbook.yml"],
            "directories": ["group_vars", "host_vars", "roles", "playbooks"],
        },
    }

    # Package manager detection
    PACKAGE_MANAGERS = {
        "npm": ["package.json", "package-lock.json"],
        "yarn": ["yarn.lock"],
        "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
        "pipenv": ["Pipfile", "Pipfile.lock"],
        "poetry": ["pyproject.toml"],
        "go_modules": ["go.mod"],
        "cargo": ["Cargo.toml"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle", "build.gradle.kts"],
    }

    # Lint configuration files
    LINT_CONFIGS = {
        # Python linters
        "flake8": [".flake8", "setup.cfg", "tox.ini", "pyproject.toml"],
        "pylint": [".pylintrc", "pylint.cfg", "pyproject.toml"],
        "black": ["pyproject.toml", ".black"],
        "isort": [".isort.cfg", "setup.cfg", "pyproject.toml"],
        "mypy": ["mypy.ini", ".mypy.ini", "setup.cfg", "pyproject.toml"],
        # JavaScript/TypeScript linters
        "eslint": [
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
            ".eslintrc.yml",
            "package.json",
        ],
        "prettier": [
            ".prettierrc",
            ".prettierrc.js",
            ".prettierrc.json",
            ".prettierrc.yml",
            "package.json",
        ],
        "tslint": ["tslint.json"],
        # Go linters
        "golint": [],  # No config file, uses defaults
        "gofmt": [],  # No config file, uses defaults
        "govet": [],  # No config file, uses defaults
        "golangci-lint": [".golangci.yml", ".golangci.yaml"],
        # Rust linters
        "rustfmt": ["rustfmt.toml", ".rustfmt.toml"],
        "clippy": ["clippy.toml", ".clippy.toml"],
        # Java linters
        "checkstyle": ["checkstyle.xml"],
        "spotbugs": ["spotbugs.xml"],
        "pmd": ["pmd.xml"],
        # Ansible linters
        "ansible-lint": [
            ".ansible-lint",
            ".ansible-lint.yml",
            ".ansible-lint.yaml",
            "ansible-lint.yml",
            "ansible-lint.yaml",
        ],
    }

    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        """Initialize the project detector.

        Args:
            exclude_patterns: List of patterns to exclude from scanning
        """
        self.exclude_patterns = exclude_patterns or [
            "*.min.js",
            "*.min.css",
            "node_modules/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            "build/",
            "dist/",
            "target/",
        ]

    def detect_project(self, project_path: str) -> ProjectInfo:
        """Detect project information for the given path.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectInfo object containing detected information
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {project_path}")

        logger.info(f"Detecting project information for: {project_path}")

        project_info = ProjectInfo(root_path=project_path)

        # Scan the project directory
        self._scan_directory(project_path, project_info)

        # Detect languages based on file extensions and special files
        self._detect_languages(project_info)

        # Detect package managers
        self._detect_package_managers(project_info)

        # Detect lint configurations
        self._detect_lint_configs(project_info)

        logger.info(f"Detected languages: {project_info.languages}")
        logger.info(f"Detected package managers: {project_info.package_managers}")
        logger.info(f"Detected lint configs: {list(project_info.lint_configs.keys())}")

        return project_info

    def _scan_directory(
        self, directory: Path, project_info: ProjectInfo, max_depth: int = 10
    ) -> None:
        """Recursively scan directory for files and configurations.

        Args:
            directory: Directory to scan
            project_info: ProjectInfo object to update
            max_depth: Maximum recursion depth
        """
        if max_depth <= 0:
            return

        try:
            for item in directory.iterdir():
                # Skip excluded patterns
                if self._should_exclude(item):
                    continue

                if item.is_file():
                    project_info.source_files.append(item)

                    # Check if it's a configuration file
                    if self._is_config_file(item):
                        project_info.config_files.append(item)

                elif item.is_dir() and not item.name.startswith("."):
                    # Recursively scan subdirectories
                    self._scan_directory(item, project_info, max_depth - 1)

        except PermissionError:
            logger.warning(f"Permission denied accessing: {directory}")

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from scanning.

        Args:
            path: Path to check

        Returns:
            True if the path should be excluded
        """
        path_str = str(path)

        for pattern in self.exclude_patterns:
            if pattern.endswith("/"):
                # Directory pattern
                if pattern[:-1] in path.parts:
                    return True
            elif "*" in pattern:
                # Wildcard pattern
                import fnmatch

                if fnmatch.fnmatch(path.name, pattern):
                    return True
            else:
                # Exact match
                if pattern in path_str:
                    return True

        return False

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if a file is a configuration file.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a configuration file
        """
        config_extensions = {".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".xml"}
        config_names = {
            "Makefile",
            "Dockerfile",
            ".gitignore",
            ".dockerignore",
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "requirements.txt",
            "package.json",
            "tsconfig.json",
            "webpack.config.js",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
        }

        return (
            file_path.suffix in config_extensions
            or file_path.name in config_names
            or file_path.name.startswith(".")
        )

    def _detect_languages(self, project_info: ProjectInfo) -> None:
        """Detect programming languages used in the project.

        Args:
            project_info: ProjectInfo object to update
        """
        file_counts = {}

        for file_path in project_info.source_files:
            extension = file_path.suffix.lower()

            # Count files by extension
            file_counts[extension] = file_counts.get(extension, 0) + 1

            # Check against language patterns
            for language, patterns in self.LANGUAGE_PATTERNS.items():
                if extension in patterns["extensions"]:
                    project_info.languages.add(language)
                elif file_path.name in patterns["files"]:
                    project_info.languages.add(language)

        # Log file distribution
        logger.debug(f"File extension distribution: {file_counts}")

    def _detect_package_managers(self, project_info: ProjectInfo) -> None:
        """Detect package managers used in the project.

        Args:
            project_info: ProjectInfo object to update
        """
        for file_path in project_info.source_files:
            for pm_name, pm_files in self.PACKAGE_MANAGERS.items():
                if file_path.name in pm_files:
                    project_info.package_managers.add(pm_name)

    def _detect_lint_configs(self, project_info: ProjectInfo) -> None:
        """Detect lint configurations in the project.

        Args:
            project_info: ProjectInfo object to update
        """
        for linter_name, config_files in self.LINT_CONFIGS.items():
            for file_path in project_info.config_files:
                if file_path.name in config_files:
                    # Parse the configuration
                    config_data = self._parse_config_file(file_path, linter_name)
                    if config_data:
                        project_info.lint_configs[linter_name] = {
                            "config_file": str(file_path),
                            "config_data": config_data,
                        }
                        break

    def _parse_config_file(self, file_path: Path, linter_name: str) -> Optional[Dict[str, Any]]:
        """Parse a configuration file.

        Args:
            file_path: Path to the configuration file
            linter_name: Name of the linter

        Returns:
            Parsed configuration data or None if parsing fails
        """
        try:
            if file_path.suffix in [".json"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Extract linter-specific config from package.json
                    if file_path.name == "package.json":
                        if linter_name == "eslint" and "eslintConfig" in data:
                            return data["eslintConfig"]
                        elif linter_name == "prettier" and "prettier" in data:
                            return data["prettier"]

                    return data

            elif file_path.suffix in [".yml", ".yaml"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)

            elif file_path.suffix in [".toml"]:
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        logger.warning(f"TOML parsing not available for {file_path}")
                        return None

                with open(file_path, "rb") as f:
                    data = tomllib.load(f)

                    # Extract linter-specific config from pyproject.toml
                    if file_path.name == "pyproject.toml":
                        if linter_name == "black" and "tool" in data and "black" in data["tool"]:
                            return data["tool"]["black"]
                        elif linter_name == "isort" and "tool" in data and "isort" in data["tool"]:
                            return data["tool"]["isort"]
                        elif linter_name == "mypy" and "tool" in data and "mypy" in data["tool"]:
                            return data["tool"]["mypy"]

                    return data

            elif file_path.suffix in [".ini", ".cfg"] or file_path.name in [
                "setup.cfg",
                ".flake8",
            ]:
                config = configparser.ConfigParser()
                config.read(file_path)

                # Convert to dictionary
                result = {}
                for section in config.sections():
                    result[section] = dict(config[section])

                return result

            else:
                # Try to read as plain text for simple configs
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return {"content": content}

        except Exception as e:
            logger.warning(f"Failed to parse config file {file_path}: {e}")

        return None

    def get_available_linters(self, project_info: ProjectInfo) -> List[str]:
        """Get list of linters that could be applicable to this project.

        Args:
            project_info: ProjectInfo object

        Returns:
            List of applicable linter names
        """
        applicable_linters = []

        # Map languages to their common linters
        language_linters = {
            "python": ["flake8", "pylint", "black", "isort", "mypy"],
            "javascript": ["eslint", "prettier"],
            "typescript": ["eslint", "prettier", "tslint"],
            "go": ["golint", "gofmt", "govet", "golangci-lint"],
            "rust": ["rustfmt", "clippy"],
            "java": ["checkstyle", "spotbugs", "pmd"],
        }

        for language in project_info.languages:
            if language in language_linters:
                applicable_linters.extend(language_linters[language])

        # Remove duplicates and return
        return list(set(applicable_linters))
