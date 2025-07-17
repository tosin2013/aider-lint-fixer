"""
Lint Runner Module

This module handles running linters and parsing their output to identify errors.
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .project_detector import ProjectInfo

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for lint errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


@dataclass
class LintError:
    """Represents a single lint error."""
    file_path: str
    line: int
    column: int
    rule_id: str
    message: str
    severity: ErrorSeverity
    linter: str
    context: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class LintResult:
    """Results from running a linter."""
    linter: str
    success: bool
    errors: List[LintError] = field(default_factory=list)
    warnings: List[LintError] = field(default_factory=list)
    raw_output: str = ""
    execution_time: float = 0.0


class LintRunner:
    """Runs linters and parses their output."""
    
    # Linter command configurations
    LINTER_COMMANDS = {
        # Python linters
        'flake8': {
            'command': ['flake8'],
            'check_installed': ['flake8', '--version'],
            'output_format': 'text',
            'file_extensions': ['.py']
        },
        'pylint': {
            'command': ['pylint', '--output-format=json'],
            'check_installed': ['pylint', '--version'],
            'output_format': 'json',
            'file_extensions': ['.py']
        },
        'black': {
            'command': ['black', '--check', '--diff'],
            'check_installed': ['black', '--version'],
            'output_format': 'diff',
            'file_extensions': ['.py']
        },
        'isort': {
            'command': ['isort', '--check-only', '--diff'],
            'check_installed': ['isort', '--version'],
            'output_format': 'diff',
            'file_extensions': ['.py']
        },
        'mypy': {
            'command': ['mypy', '--show-error-codes'],
            'check_installed': ['mypy', '--version'],
            'output_format': 'text',
            'file_extensions': ['.py']
        },
        
        # JavaScript/TypeScript linters
        'eslint': {
            'command': ['npx', 'eslint', '--format=json'],
            'check_installed': ['npx', 'eslint', '--version'],
            'output_format': 'json',
            'file_extensions': ['.js', '.jsx', '.ts', '.tsx']
        },
        'prettier': {
            'command': ['npx', 'prettier', '--check'],
            'check_installed': ['npx', 'prettier', '--version'],
            'output_format': 'text',
            'file_extensions': ['.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.md']
        },
        
        # Go linters
        'golint': {
            'command': ['golint'],
            'check_installed': ['golint'],
            'output_format': 'text',
            'file_extensions': ['.go']
        },
        'gofmt': {
            'command': ['gofmt', '-l'],
            'check_installed': ['gofmt'],
            'output_format': 'text',
            'file_extensions': ['.go']
        },
        'govet': {
            'command': ['go', 'vet'],
            'check_installed': ['go', 'version'],
            'output_format': 'text',
            'file_extensions': ['.go']
        },
        
        # Rust linters
        'rustfmt': {
            'command': ['rustfmt', '--check'],
            'check_installed': ['rustfmt', '--version'],
            'output_format': 'text',
            'file_extensions': ['.rs']
        },
        'clippy': {
            'command': ['cargo', 'clippy', '--message-format=json'],
            'check_installed': ['cargo', '--version'],
            'output_format': 'json',
            'file_extensions': ['.rs']
        },
        
        # Ansible linters
        'ansible-lint': {
            'command': ['ansible-lint', '--format=json'],
            'check_installed': ['ansible-lint', '--version'],
            'output_format': 'json',
            'file_extensions': ['.yml', '.yaml']
        }
    }
    
    def __init__(self, project_info: ProjectInfo):
        """Initialize the lint runner.

        Args:
            project_info: Information about the project
        """
        self.project_info = project_info
        self.available_linters = {}  # Will be populated on-demand
    
    def _detect_available_linters(self, linter_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """Detect which linters are available in the system.

        Args:
            linter_names: Optional list of specific linters to check. If None, checks all.

        Returns:
            Dictionary mapping linter names to availability
        """
        available = {}

        # If specific linters requested, only check those
        linters_to_check = linter_names or list(self.LINTER_COMMANDS.keys())

        for linter_name in linters_to_check:
            if linter_name not in self.LINTER_COMMANDS:
                logger.warning(f"Unknown linter: {linter_name}")
                available[linter_name] = False
                continue

            config = self.LINTER_COMMANDS[linter_name]
            try:
                # Try to run the version command
                result = subprocess.run(
                    config['check_installed'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.project_info.root_path
                )
                available[linter_name] = result.returncode == 0

                if available[linter_name]:
                    logger.debug(f"Linter {linter_name} is available")
                else:
                    logger.debug(f"Linter {linter_name} check failed: {result.stderr}")

            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
                available[linter_name] = False
                logger.debug(f"Linter {linter_name} not available: {e}")

        return available
    
    def run_linter(self, linter_name: str, file_paths: Optional[List[str]] = None) -> LintResult:
        """Run a specific linter on the project or specific files.
        
        Args:
            linter_name: Name of the linter to run
            file_paths: Optional list of specific files to lint
            
        Returns:
            LintResult object containing the results
        """
        if linter_name not in self.LINTER_COMMANDS:
            raise ValueError(f"Unknown linter: {linter_name}")
        
        if not self.available_linters.get(linter_name, False):
            logger.warning(f"Linter {linter_name} is not available")
            return LintResult(linter=linter_name, success=False, raw_output="Linter not available")
        
        config = self.LINTER_COMMANDS[linter_name]
        command = config['command'].copy()
        
        # Add file paths or project root
        if file_paths:
            # Filter files by supported extensions
            supported_extensions = config.get('file_extensions', [])
            if supported_extensions:
                filtered_files = [
                    f for f in file_paths 
                    if any(f.endswith(ext) for ext in supported_extensions)
                ]
                if not filtered_files:
                    logger.info(f"No files with supported extensions for {linter_name}")
                    return LintResult(linter=linter_name, success=True)
                command.extend(filtered_files)
            else:
                command.extend(file_paths)
        else:
            # Add project root or current directory
            if linter_name in ['govet', 'clippy']:
                # These linters work on the entire project
                pass
            else:
                command.append('.')
        
        logger.info(f"Running {linter_name}: {' '.join(command)}")
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.project_info.root_path
            )
            
            execution_time = time.time() - start_time
            
            # Parse the output
            lint_result = self._parse_linter_output(
                linter_name, result.stdout, result.stderr, result.returncode
            )
            lint_result.execution_time = execution_time
            
            logger.info(f"Linter {linter_name} completed in {execution_time:.2f}s with {len(lint_result.errors)} errors")
            
            return lint_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Linter {linter_name} timed out")
            return LintResult(
                linter=linter_name,
                success=False,
                raw_output="Linter execution timed out"
            )
        except Exception as e:
            logger.error(f"Error running linter {linter_name}: {e}")
            return LintResult(
                linter=linter_name,
                success=False,
                raw_output=f"Error: {str(e)}"
            )
    
    def _parse_linter_output(self, linter_name: str, stdout: str, stderr: str, return_code: int) -> LintResult:
        """Parse linter output into structured errors.
        
        Args:
            linter_name: Name of the linter
            stdout: Standard output from the linter
            stderr: Standard error from the linter
            return_code: Exit code from the linter
            
        Returns:
            LintResult object with parsed errors
        """
        config = self.LINTER_COMMANDS[linter_name]
        output_format = config['output_format']
        
        errors = []
        warnings = []
        raw_output = stdout + stderr
        
        # Success is typically return_code == 0, but some linters use different codes
        success = return_code == 0
        
        try:
            if output_format == 'json':
                errors, warnings = self._parse_json_output(linter_name, stdout)
            elif output_format == 'text':
                errors, warnings = self._parse_text_output(linter_name, stdout, stderr)
            elif output_format == 'diff':
                errors, warnings = self._parse_diff_output(linter_name, stdout)
            
        except Exception as e:
            logger.error(f"Error parsing {linter_name} output: {e}")
        
        return LintResult(
            linter=linter_name,
            success=success,
            errors=errors,
            warnings=warnings,
            raw_output=raw_output
        )
    
    def _parse_json_output(self, linter_name: str, output: str) -> Tuple[List[LintError], List[LintError]]:
        """Parse JSON format linter output.
        
        Args:
            linter_name: Name of the linter
            output: JSON output string
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not output.strip():
            return errors, warnings
        
        try:
            if linter_name == 'flake8':
                # Flake8 JSON format
                data = json.loads(output)
                for file_path, file_errors in data.items():
                    for error in file_errors:
                        lint_error = LintError(
                            file_path=file_path,
                            line=error.get('line_number', 0),
                            column=error.get('column_number', 0),
                            rule_id=error.get('code', ''),
                            message=error.get('text', ''),
                            severity=ErrorSeverity.ERROR,
                            linter=linter_name
                        )
                        errors.append(lint_error)
            
            elif linter_name == 'pylint':
                # Pylint JSON format
                data = json.loads(output)
                for item in data:
                    severity = ErrorSeverity.WARNING
                    if item.get('type') == 'error':
                        severity = ErrorSeverity.ERROR
                    elif item.get('type') == 'warning':
                        severity = ErrorSeverity.WARNING
                    elif item.get('type') in ['convention', 'refactor']:
                        severity = ErrorSeverity.STYLE
                    
                    lint_error = LintError(
                        file_path=item.get('path', ''),
                        line=item.get('line', 0),
                        column=item.get('column', 0),
                        rule_id=item.get('symbol', ''),
                        message=item.get('message', ''),
                        severity=severity,
                        linter=linter_name
                    )
                    
                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)
            
            elif linter_name == 'eslint':
                # ESLint JSON format
                data = json.loads(output)
                for file_result in data:
                    file_path = file_result.get('filePath', '')
                    for message in file_result.get('messages', []):
                        severity = ErrorSeverity.ERROR if message.get('severity') == 2 else ErrorSeverity.WARNING
                        
                        lint_error = LintError(
                            file_path=file_path,
                            line=message.get('line', 0),
                            column=message.get('column', 0),
                            rule_id=message.get('ruleId', ''),
                            message=message.get('message', ''),
                            severity=severity,
                            linter=linter_name
                        )
                        
                        if severity == ErrorSeverity.ERROR:
                            errors.append(lint_error)
                        else:
                            warnings.append(lint_error)
            
            elif linter_name == 'ansible-lint':
                # Ansible-lint JSON format
                data = json.loads(output)
                for item in data:
                    if isinstance(item, dict):
                        # Extract error information
                        file_path = item.get('filename', '')
                        line_num = item.get('linenumber', 0)
                        column = item.get('column', 0)
                        rule_id = item.get('rule', {}).get('id', '') if isinstance(item.get('rule'), dict) else str(item.get('rule', ''))
                        message = item.get('message', '')
                        severity_str = item.get('level', 'error').lower()
                        
                        # Map ansible-lint levels to our severity
                        if severity_str in ['error', 'very_high']:
                            severity = ErrorSeverity.ERROR
                        elif severity_str in ['warning', 'high', 'medium']:
                            severity = ErrorSeverity.WARNING
                        else:
                            severity = ErrorSeverity.WARNING
                        
                        lint_error = LintError(
                            file_path=file_path,
                            line=int(line_num) if line_num else 0,
                            column=int(column) if column else 0,
                            rule_id=rule_id,
                            message=message,
                            severity=severity,
                            linter=linter_name
                        )
                        
                        if severity == ErrorSeverity.ERROR:
                            errors.append(lint_error)
                        else:
                            warnings.append(lint_error)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output from {linter_name}: {e}")
        
        return errors, warnings
    
    def _parse_text_output(self, linter_name: str, stdout: str, stderr: str) -> Tuple[List[LintError], List[LintError]]:
        """Parse text format linter output.
        
        Args:
            linter_name: Name of the linter
            stdout: Standard output
            stderr: Standard error
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        output = stdout + stderr
        lines = output.split('\n')
        
        if linter_name == 'mypy':
            # MyPy format: file:line: error: message [error-code]
            pattern = r'^(.+?):(\d+):(?:\s*(\d+):)?\s*(error|warning|note):\s*(.+?)(?:\s*\[(.+?)\])?$'
            
            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, severity_str, message, rule_id = match.groups()
                    
                    severity = ErrorSeverity.ERROR if severity_str == 'error' else ErrorSeverity.WARNING
                    
                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num) if col_num else 0,
                        rule_id=rule_id or '',
                        message=message,
                        severity=severity,
                        linter=linter_name
                    )
                    
                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)
        
        elif linter_name == 'flake8':
            # Flake8 format: file:line:column: code message
            pattern = r'^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s*(.+)$'
            
            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, rule_id, message = match.groups()
                    
                    # Determine severity based on rule code
                    severity = ErrorSeverity.ERROR if rule_id.startswith('E') or rule_id.startswith('F') else ErrorSeverity.WARNING
                    
                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id=rule_id,
                        message=message,
                        severity=severity,
                        linter=linter_name
                    )
                    
                    if severity == ErrorSeverity.ERROR:
                        errors.append(lint_error)
                    else:
                        warnings.append(lint_error)
        
        elif linter_name == 'golint':
            # GoLint format: file:line:column: message
            pattern = r'^(.+?):(\d+):(\d+):\s*(.+)$'
            
            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, message = match.groups()
                    
                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id='',
                        message=message,
                        severity=ErrorSeverity.WARNING,
                        linter=linter_name
                    )
                    warnings.append(lint_error)
        
        elif linter_name == 'govet':
            # Go vet format: file:line:column: message
            pattern = r'^(.+?):(\d+):(\d+):\s*(.+)$'
            
            for line in lines:
                match = re.match(pattern, line.strip())
                if match:
                    file_path, line_num, col_num, message = match.groups()
                    
                    lint_error = LintError(
                        file_path=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule_id='',
                        message=message,
                        severity=ErrorSeverity.ERROR,
                        linter=linter_name
                    )
                    errors.append(lint_error)
        
        elif linter_name == 'prettier':
            # Prettier outputs file names that need formatting
            for line in lines:
                line = line.strip()
                if line and not line.startswith('['):
                    lint_error = LintError(
                        file_path=line,
                        line=0,
                        column=0,
                        rule_id='formatting',
                        message='File needs formatting',
                        severity=ErrorSeverity.STYLE,
                        linter=linter_name
                    )
                    warnings.append(lint_error)
        
        return errors, warnings
    
    def _parse_diff_output(self, linter_name: str, output: str) -> Tuple[List[LintError], List[LintError]]:
        """Parse diff format linter output.
        
        Args:
            linter_name: Name of the linter
            output: Diff output string
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not output.strip():
            return errors, warnings
        
        # Parse diff output to extract file names and changes
        lines = output.split('\n')
        current_file = None
        
        for line in lines:
            if line.startswith('--- ') or line.startswith('+++ '):
                # Extract file name from diff header
                if line.startswith('--- '):
                    current_file = line[4:].strip()
            elif line.startswith('@@'):
                # Extract line number from diff hunk header
                match = re.search(r'@@\s*-(\d+)', line)
                if match and current_file:
                    line_num = int(match.group(1))
                    
                    lint_error = LintError(
                        file_path=current_file,
                        line=line_num,
                        column=0,
                        rule_id='formatting',
                        message=f'{linter_name} formatting required',
                        severity=ErrorSeverity.STYLE,
                        linter=linter_name,
                        context=output  # Include full diff as context
                    )
                    warnings.append(lint_error)
        
        return errors, warnings
    
    def run_all_available_linters(self, enabled_linters: Optional[List[str]] = None) -> Dict[str, LintResult]:
        """Run all available linters on the project.

        Args:
            enabled_linters: Optional list of linters to run (runs all available if None)

        Returns:
            Dictionary mapping linter names to their results
        """
        results = {}

        # Determine which linters to check
        linters_to_check = enabled_linters or list(self.LINTER_COMMANDS.keys())

        # Only check availability for the linters we want to run
        if enabled_linters:
            # Check only the requested linters
            self.available_linters.update(self._detect_available_linters(enabled_linters))
        else:
            # Check all linters if none specified
            self.available_linters = self._detect_available_linters()

        for linter_name in linters_to_check:
            if self.available_linters.get(linter_name, False):
                logger.info(f"Running linter: {linter_name}")
                results[linter_name] = self.run_linter(linter_name)
            else:
                logger.warning(f"Skipping unavailable linter: {linter_name}")

        return results
    
    def get_error_summary(self, results: Dict[str, LintResult]) -> Dict[str, Any]:
        """Get a summary of all lint errors.
        
        Args:
            results: Dictionary of lint results
            
        Returns:
            Summary dictionary with error counts and details
        """
        total_errors = 0
        total_warnings = 0
        errors_by_file = {}
        errors_by_rule = {}
        
        for linter_name, result in results.items():
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            
            for error in result.errors + result.warnings:
                # Group by file
                if error.file_path not in errors_by_file:
                    errors_by_file[error.file_path] = []
                errors_by_file[error.file_path].append(error)
                
                # Group by rule
                rule_key = f"{error.linter}:{error.rule_id}"
                if rule_key not in errors_by_rule:
                    errors_by_rule[rule_key] = []
                errors_by_rule[rule_key].append(error)
        
        return {
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'files_with_errors': len(errors_by_file),
            'unique_rules': len(errors_by_rule),
            'errors_by_file': errors_by_file,
            'errors_by_rule': errors_by_rule,
            'linter_results': {name: len(result.errors) for name, result in results.items()}
        }

