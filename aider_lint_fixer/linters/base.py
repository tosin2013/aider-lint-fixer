"""
Base linter interface and common functionality.
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ..lint_runner import LintError

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
    def build_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
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
        import os
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
                f for f in file_paths if any(f.endswith(ext) for ext in self.supported_extensions)
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
        # Prepare environment for subprocess
        env = os.environ.copy()
        # Ensure ansible-specific environment variables are passed through
        if self.name == "ansible-lint":
            self._setup_ansible_environment(env)
        
        # Run linter
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.project_root),
                env=env,
            )
            execution_time = time.time() - start_time
            # Parse output
            errors, warnings = self.parse_output(result.stdout, result.stderr, result.returncode)
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

    def run_command(self, command: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Helper method to run a command."""
        import os
        env = os.environ.copy()
        # Ensure ansible-specific environment variables are passed through for ansible-lint
        if self.name == "ansible-lint":
            self._setup_ansible_environment(env)
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.project_root),
            env=env,
        )

    def _setup_ansible_environment(self, env: dict) -> None:
        """Set up ansible environment variables for proper temp directory handling."""
        import os
        from pathlib import Path

        # Set ansible temp directories to writable locations
        if "ANSIBLE_LOCAL_TEMP" not in env:
            env["ANSIBLE_LOCAL_TEMP"] = "/tmp/ansible-local"
        if "ANSIBLE_REMOTE_TEMP" not in env:
            env["ANSIBLE_REMOTE_TEMP"] = "/tmp/ansible-local"
        if "ANSIBLE_GALAXY_CACHE_DIR" not in env:
            env["ANSIBLE_GALAXY_CACHE_DIR"] = "/tmp/ansible-galaxy-cache"
        if "ANSIBLE_LOG_PATH" not in env:
            env["ANSIBLE_LOG_PATH"] = "/tmp/ansible.log"
            
        # Ensure temp directories exist
        for temp_dir_var in ["ANSIBLE_LOCAL_TEMP", "ANSIBLE_REMOTE_TEMP", "ANSIBLE_GALAXY_CACHE_DIR"]:
            temp_dir = env.get(temp_dir_var)
            if temp_dir:
                try:
                    Path(temp_dir).mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f"Created ansible temp directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to create ansible temp directory {temp_dir}: {e}")
                    # Fallback to current working directory relative path
                    fallback_dir = str(self.project_root / f".ansible-{temp_dir_var.lower().split('_')[-1]}")
                    env[temp_dir_var] = fallback_dir
                    try:
                        Path(fallback_dir).mkdir(parents=True, exist_ok=True)
                        self.logger.debug(f"Using fallback ansible temp directory: {fallback_dir}")
                    except Exception as e2:
                        self.logger.error(f"Failed to create fallback ansible temp directory {fallback_dir}: {e2}")
        
        self.logger.debug(f"Ansible environment setup: ANSIBLE_LOCAL_TEMP={env.get('ANSIBLE_LOCAL_TEMP')}")
