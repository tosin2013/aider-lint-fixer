"""
Base linter interface and common functionality.
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..lint_runner import ErrorSeverity, LintError

logger = logging.getLogger(__name__)


@dataclass
class LinterResult:
    """Result from running a linter."""

    linter: str
    success: bool
    errors: List[LintError]
    warnings: List[LintError]
    raw_output: str
    version: Optional[str] = None
    profile: Optional[str] = None
    execution_time: Optional[float] = None


class BaseLinter(ABC):
    """Base class for all linter implementations."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Linter name."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """File extensions this linter supports."""
        pass

    @property
    @abstractmethod
    def supported_versions(self) -> List[str]:
        """Linter versions this implementation supports."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the linter is installed and available."""
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Get the installed linter version."""
        pass

    @abstractmethod
    def build_command(
        self, file_paths: Optional[List[str]] = None, **kwargs
    ) -> List[str]:
        """Build the command to run the linter."""
        pass

    @abstractmethod
    def parse_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Tuple[List[LintError], List[LintError]]:
        """Parse linter output into errors and warnings."""
        pass

    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> LinterResult:
        """Run the linter and return results."""
        import time

        if not self.is_available():
            return LinterResult(
                linter=self.name,
                success=False,
                errors=[],
                warnings=[],
                raw_output=f"{self.name} is not available",
            )
        # Filter files by supported extensions
        if file_paths:
            filtered_files = [
                f
                for f in file_paths
                if any(f.endswith(ext) for ext in self.supported_extensions)
            ]
            if not filtered_files:
                return LinterResult(
                    linter=self.name,
                    success=True,
                    errors=[],
                    warnings=[],
                    raw_output="No supported files found",
                )
            file_paths = filtered_files
        # Build command
        command = self.build_command(file_paths, **kwargs)
        # Run linter
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.project_root),
            )
            execution_time = time.time() - start_time
            # Parse output
            errors, warnings = self.parse_output(
                result.stdout, result.stderr, result.returncode
            )
            # Determine success
            success = self.is_success(result.returncode, errors, warnings)
            return LinterResult(
                linter=self.name,
                success=success,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout + result.stderr,
                version=self.get_version(),
                execution_time=execution_time,
            )
        except subprocess.TimeoutExpired:
            return LinterResult(
                linter=self.name,
                success=False,
                errors=[],
                warnings=[],
                raw_output=f"{self.name} timed out after 5 minutes",
            )
        except Exception as e:
            self.logger.error(f"Error running {self.name}: {e}")
            return LinterResult(
                linter=self.name,
                success=False,
                errors=[],
                warnings=[],
                raw_output=f"Error running {self.name}: {e}",
            )

    def is_success(
        self, return_code: int, errors: List[LintError], warnings: List[LintError]
    ) -> bool:
        """Determine if the linter run was successful."""
        # Default: success if return code is 0
        return return_code == 0

    def check_version_compatibility(self) -> bool:
        """Check if the installed version is supported."""
        version = self.get_version()
        if not version:
            return False
        # Simple version check - can be overridden for more complex logic
        return any(version.startswith(v) for v in self.supported_versions)

    def run_command(
        self, command: List[str], timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Helper method to run a command."""
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.project_root),
        )
