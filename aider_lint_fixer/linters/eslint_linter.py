"""
ESLint specific implementation.

Tested with ESLint v8.57.1
"""

import json
import re
from typing import List, Optional, Tuple

from .base import BaseLinter, LinterResult
from ..lint_runner import LintError, ErrorSeverity


class ESLintLinter(BaseLinter):
    """ESLint implementation for JavaScript/TypeScript code quality checking."""
    
    SUPPORTED_VERSIONS = ["8.57.1", "8.57", "8.5", "8.", "7."]
    
    @property
    def name(self) -> str:
        return "eslint"
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']
    
    @property
    def supported_versions(self) -> List[str]:
        return self.SUPPORTED_VERSIONS
    
    def is_available(self) -> bool:
        """Check if ESLint is installed."""
        try:
            # Try npx first, then global eslint
            result = self.run_command(['npx', 'eslint', '--version'], timeout=10)
            if result.returncode == 0:
                return True
            
            # Fallback to global eslint
            result = self.run_command(['eslint', '--version'], timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_version(self) -> Optional[str]:
        """Get ESLint version."""
        try:
            # Try npx first
            result = self.run_command(['npx', 'eslint', '--version'], timeout=10)
            if result.returncode == 0:
                # Parse version from output like "v8.57.1"
                match = re.search(r'v?(\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
            
            # Fallback to global eslint
            result = self.run_command(['eslint', '--version'], timeout=10)
            if result.returncode == 0:
                match = re.search(r'v?(\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None
    
    def build_command(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[str]:
        """Build ESLint command."""
        # Use npx if available, otherwise global eslint
        command = ['npx', 'eslint'] if self._has_npx() else ['eslint']
        
        # Add JSON format for parsing
        command.extend(['--format=json'])
        
        # Add configuration options
        if 'config' in kwargs:
            command.extend(['--config', kwargs['config']])
        
        # Add ignore patterns
        if 'ignore_pattern' in kwargs:
            command.extend(['--ignore-pattern', kwargs['ignore_pattern']])
        
        # Add rules to disable/enable
        if 'disable_rules' in kwargs:
            for rule in kwargs['disable_rules']:
                command.extend(['--rule', f'{rule}: off'])
        
        # Add file paths
        if file_paths:
            command.extend(file_paths)
        else:
            command.append('.')
        
        return command
    
    def _has_npx(self) -> bool:
        """Check if npx is available."""
        try:
            result = self.run_command(['npx', '--version'], timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def parse_output(self, stdout: str, stderr: str, return_code: int) -> Tuple[List[LintError], List[LintError]]:
        """Parse ESLint JSON output."""
        errors = []
        warnings = []
        
        if not stdout.strip():
            return errors, warnings
        
        try:
            # Parse JSON output
            data = json.loads(stdout)
            
            for file_result in data:
                file_path = file_result.get('filePath', '')
                # Convert absolute path to relative
                project_root_str = str(self.project_root)
                if file_path.startswith(project_root_str):
                    file_path = file_path[len(project_root_str):].lstrip('/')
                
                messages = file_result.get('messages', [])
                
                for message in messages:
                    line_num = message.get('line', 0)
                    column = message.get('column', 0)
                    rule_id = message.get('ruleId', 'unknown')
                    msg_text = message.get('message', '')
                    severity = message.get('severity', 1)
                    
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
                        linter=self.name
                    )
                    
                    if error_severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse ESLint JSON output: {e}")
            # Create fallback error
            errors.append(LintError(
                file_path="unknown",
                line=0,
                column=0,
                rule_id="parse-error",
                message=f"Failed to parse ESLint output: {e}",
                severity=ErrorSeverity.ERROR,
                linter=self.name
            ))
        
        return errors, warnings
    
    def is_success(self, return_code: int, errors: List[LintError], warnings: List[LintError]) -> bool:
        """Determine if the linter run was successful."""
        # ESLint returns 0 for no issues, 1 for issues found, 2 for errors
        return return_code in [0, 1]
    
    def run_with_profile(self, profile: str, file_paths: Optional[List[str]] = None) -> LinterResult:
        """Run ESLint with different profiles.
        
        Args:
            profile: 'basic' for essential checks, 'strict' for comprehensive checks
            file_paths: Optional list of files to check
        """
        if profile == 'basic':
            # Basic profile: Focus on errors and important warnings
            kwargs = {
                'disable_rules': ['no-console', 'no-unused-vars']
            }
        elif profile == 'strict':
            # Strict profile: All checks enabled
            kwargs = {}
        else:
            # Default profile: Moderate checking
            kwargs = {
                'disable_rules': ['no-console']
            }
        
        return self.run(file_paths, **kwargs)
