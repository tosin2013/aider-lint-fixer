"""
Aider Integration Module

This module integrates with aider.chat to automatically fix lint errors using LLMs.
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .config_manager import Config, LLMConfig
from .error_analyzer import ErrorAnalysis, FileAnalysis, FixComplexity
from .lint_runner import LintError, LintResult

logger = logging.getLogger(__name__)


@dataclass
class FixResult:
    """Result of attempting to fix an error."""
    error_analysis: ErrorAnalysis
    success: bool
    changes_made: bool = False
    fix_description: str = ""
    aider_output: str = ""
    error_message: str = ""


@dataclass
class FixSession:
    """Information about a fixing session."""
    file_path: str
    errors_to_fix: List[ErrorAnalysis]
    results: List[FixResult]
    session_id: str
    total_time: float = 0.0


class AiderIntegration:
    """Integrates with aider.chat for automated lint fixing."""

    # Configuration for scalability
    MAX_ERRORS_PER_BATCH = 10  # Maximum errors to fix in one aider call
    MAX_PROMPT_LENGTH = 8000   # Maximum prompt length to avoid token limits
    AIDER_TIMEOUT = 300        # 5 minutes timeout for aider operations
    BATCH_DELAY = 2            # Seconds to wait between batches

    def __init__(self, config: Config, project_root: str, config_manager=None):
        """Initialize the aider integration.

        Args:
            config: Configuration object
            project_root: Root directory of the project
            config_manager: Optional config manager for API key access
        """
        self.config = config
        self.config_manager = config_manager
        self.project_root = Path(project_root)
        self.aider_executable = self._find_aider_executable()

        # Validate aider installation
        if not self.aider_executable:
            raise RuntimeError("Aider executable not found. Please install aider-chat.")

        # Set up environment variables for LLM
        self._setup_llm_environment()
    
    def _find_aider_executable(self) -> Optional[str]:
        """Find the aider executable.
        
        Returns:
            Path to aider executable or None if not found
        """
        # Try common locations
        possible_paths = [
            'aider',
            'python -m aider',
            str(Path.cwd() / 'venv' / 'bin' / 'aider'),
            str(Path.home() / '.local' / 'bin' / 'aider'),
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    path.split() + ['--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"Found aider at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        return None
    
    def _setup_llm_environment(self) -> None:
        """Set up environment variables for LLM providers."""
        llm_config = self.config.llm

        # Set API keys based on provider
        if llm_config.provider == 'deepseek':
            api_key = self._get_api_key_for_provider('deepseek')
            if api_key:
                os.environ['DEEPSEEK_API_KEY'] = api_key
                # Also set as generic API key for aider
                os.environ['OPENAI_API_KEY'] = api_key
                os.environ['OPENAI_API_BASE'] = 'https://api.deepseek.com'
        
        elif llm_config.provider == 'openrouter':
            api_key = self._get_api_key_for_provider('openrouter')
            if api_key:
                os.environ['OPENROUTER_API_KEY'] = api_key

        elif llm_config.provider == 'ollama':
            api_key = self._get_api_key_for_provider('ollama')
            if api_key:
                os.environ['OLLAMA_API_KEY'] = api_key

            if llm_config.api_base:
                os.environ['OLLAMA_API_BASE'] = llm_config.api_base
            else:
                os.environ['OLLAMA_API_BASE'] = 'http://127.0.0.1:11434'

    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider.

        Args:
            provider: LLM provider name

        Returns:
            API key or None if not found
        """
        if self.config_manager:
            return self.config_manager.get_api_key_for_provider(provider)

        # Fallback to environment variables
        env_vars = {
            'deepseek': 'DEEPSEEK_API_KEY',
            'openrouter': 'OPENROUTER_API_KEY',
            'ollama': 'OLLAMA_API_KEY',
            'openai': 'OPENAI_API_KEY'
        }

        if provider in env_vars:
            return os.getenv(env_vars[provider])

        return None
    
    def fix_errors_in_file(self, file_analysis: FileAnalysis,
                          max_errors: Optional[int] = None,
                          progress_callback: Optional[callable] = None) -> FixSession:
        """Fix errors in a single file.
        
        Args:
            file_analysis: Analysis of the file with errors
            max_errors: Maximum number of errors to fix in one session
            
        Returns:
            FixSession with results
        """
        import time
        import uuid
        
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Starting fix session {session_id} for {file_analysis.file_path}")
        
        # Filter and prioritize errors
        fixable_errors = [
            analysis for analysis in file_analysis.error_analyses 
            if analysis.fixable and analysis.complexity != FixComplexity.MANUAL
        ]
        
        # Sort by priority
        fixable_errors.sort(key=lambda x: (-x.priority, x.complexity.value))
        
        if max_errors:
            fixable_errors = fixable_errors[:max_errors]
        
        session = FixSession(
            file_path=file_analysis.file_path,
            errors_to_fix=fixable_errors,
            results=[],
            session_id=session_id
        )
        
        # Group errors by complexity for batch fixing
        error_groups = self._group_errors_by_complexity(fixable_errors)

        total_groups = len([g for g in error_groups.values() if g])
        processed_groups = 0

        for complexity, errors in error_groups.items():
            if not errors:
                continue

            logger.info(f"Fixing {len(errors)} {complexity.value} errors")

            # Progress callback for error group
            if progress_callback:
                progress_callback({
                    'stage': 'fixing_error_group',
                    'complexity': complexity.value,
                    'group_errors': len(errors),
                    'processed_groups': processed_groups,
                    'total_groups': total_groups,
                    'session_id': session_id
                })

            # Fix errors in this complexity group
            group_results = self._fix_error_group(errors, session_id)
            session.results.extend(group_results)
            processed_groups += 1
        
        session.total_time = time.time() - start_time
        
        logger.info(f"Fix session {session_id} completed in {session.total_time:.2f}s")
        
        return session
    
    def _group_errors_by_complexity(self, errors: List[ErrorAnalysis]) -> Dict[FixComplexity, List[ErrorAnalysis]]:
        """Group errors by their fix complexity.
        
        Args:
            errors: List of error analyses
            
        Returns:
            Dictionary mapping complexity to error lists
        """
        groups = {complexity: [] for complexity in FixComplexity}
        
        for error in errors:
            groups[error.complexity].append(error)
        
        return groups
    
    def _fix_error_group(self, errors: List[ErrorAnalysis], session_id: str) -> List[FixResult]:
        """Fix a group of errors with similar complexity using intelligent batching.

        Args:
            errors: List of error analyses to fix
            session_id: Session identifier

        Returns:
            List of fix results
        """
        results = []

        if not errors:
            return results

        # Group errors by file (should all be the same file)
        file_path = errors[0].error.file_path

        # Split into batches if we have too many errors
        batches = self._create_error_batches(errors)

        logger.info(f"Processing {len(errors)} errors in {len(batches)} batches")

        for batch_num, batch_errors in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch_errors)} errors)")

            # Create a prompt for this batch
            prompt = self._create_fix_prompt(batch_errors)

            # Run aider to fix the errors in this batch
            aider_result = self._run_aider_fix(file_path, prompt, f"{session_id}-batch{batch_num}")

            # Create results for each error in this batch
            for error_analysis in batch_errors:
                result = FixResult(
                    error_analysis=error_analysis,
                    success=aider_result['success'],
                    changes_made=aider_result['changes_made'],
                    fix_description=aider_result['description'],
                    aider_output=aider_result['output'],
                    error_message=aider_result.get('error', '')
                )
                results.append(result)

            # Add delay between batches to avoid overwhelming the LLM
            if batch_num < len(batches):
                import time
                time.sleep(self.BATCH_DELAY)

        return results

    def _create_error_batches(self, errors: List[ErrorAnalysis]) -> List[List[ErrorAnalysis]]:
        """Split errors into manageable batches.

        Args:
            errors: List of error analyses

        Returns:
            List of error batches
        """
        batches = []
        current_batch = []
        current_prompt_length = 0

        for error in errors:
            # Estimate prompt length for this error
            error_prompt_length = len(f"{error.error.rule_id}: {error.error.message}")

            # Check if adding this error would exceed limits
            if (len(current_batch) >= self.MAX_ERRORS_PER_BATCH or
                current_prompt_length + error_prompt_length > self.MAX_PROMPT_LENGTH):

                # Start a new batch
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_prompt_length = 0

            current_batch.append(error)
            current_prompt_length += error_prompt_length

        # Add the last batch if it has errors
        if current_batch:
            batches.append(current_batch)

        return batches
    
    def _create_fix_prompt(self, errors: List[ErrorAnalysis]) -> str:
        """Create a comprehensive prompt for fixing errors.
        
        Args:
            errors: List of error analyses to fix
            
        Returns:
            Formatted prompt string
        """
        if not errors:
            return ""
        
        file_path = errors[0].error.file_path
        
        prompt_parts = [
            f"Please fix the following lint errors in {file_path}:",
            "",
            "LINT ERRORS TO FIX:",
        ]
        
        for i, error_analysis in enumerate(errors, 1):
            error = error_analysis.error
            
            prompt_parts.extend([
                f"{i}. {error.linter} - {error.rule_id}",
                f"   Line {error.line}, Column {error.column}",
                f"   Message: {error.message}",
                f"   Category: {error_analysis.category.value}",
                f"   Fix Strategy: {error_analysis.fix_strategy or 'Apply appropriate fix'}",
                ""
            ])
            
            # Add context if available
            if error_analysis.context_lines:
                prompt_parts.extend([
                    "   Context:",
                    *[f"   {line}" for line in error_analysis.context_lines],
                    ""
                ])
        
        prompt_parts.extend([
            "INSTRUCTIONS:",
            "1. Fix all the listed lint errors",
            "2. Maintain the existing code functionality",
            "3. Follow the project's coding style and conventions",
            "4. Make minimal changes necessary to fix the errors",
            "5. Ensure the fixes don't introduce new errors",
            "6. If multiple errors are related, fix them together efficiently",
            "",
            "Please analyze each error and apply the appropriate fix. "
            "Focus on the specific issues mentioned in the error messages."
        ])
        
        return "\n".join(prompt_parts)
    
    def _run_aider_fix(self, file_path: str, prompt: str, session_id: str) -> Dict[str, Any]:
        """Run aider to fix errors in a file.
        
        Args:
            file_path: Path to the file to fix
            prompt: Prompt describing the fixes needed
            session_id: Session identifier for logging
            
        Returns:
            Dictionary with fix results
        """
        try:
            # Prepare aider command with message
            command = self._build_aider_command(file_path, prompt)

            logger.debug(f"Running aider command: {' '.join(command)}")
            logger.debug(f"Prompt: {prompt[:200]}...")

            # Run aider with the message flag (better for scripting)
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.AIDER_TIMEOUT,
                cwd=self.project_root
            )

            stdout = process.stdout
            stderr = process.stderr

            # Log errors if any
            if process.returncode != 0:
                logger.error(f"Aider failed with return code {process.returncode}")
                if stderr:
                    logger.error(f"Aider error: {stderr[:200]}...")

            # Analyze the output
            success = process.returncode == 0
            changes_made = self._detect_changes_in_output(stdout)
            
            result = {
                'success': success,
                'changes_made': changes_made,
                'output': stdout,
                'error': stderr if not success else '',
                'description': self._extract_fix_description(stdout)
            }
            
            if success and changes_made:
                logger.info(f"Successfully fixed errors in {file_path}")
            elif success:
                logger.info(f"Aider completed but no changes made to {file_path}")
            else:
                logger.warning(f"Aider failed for {file_path}: {stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Aider timed out for {file_path}")
            return {
                'success': False,
                'changes_made': False,
                'output': '',
                'error': 'Aider execution timed out',
                'description': ''
            }
        except Exception as e:
            logger.error(f"Error running aider for {file_path}: {e}")
            return {
                'success': False,
                'changes_made': False,
                'output': '',
                'error': str(e),
                'description': ''
            }
    
    def _build_aider_command(self, file_path: str, message: str = None) -> List[str]:
        """Build the aider command with appropriate options.

        Args:
            file_path: Path to the file to fix
            message: Optional message to pass to aider

        Returns:
            List of command arguments
        """
        command = self.aider_executable.split()

        # Add model configuration
        llm_config = self.config.llm

        # Set up environment variables for aider subprocess
        self._setup_aider_environment(llm_config)

        if llm_config.provider == 'deepseek':
            command.extend(['--model', llm_config.model])
        elif llm_config.provider == 'openrouter':
            command.extend(['--model', llm_config.model])
        elif llm_config.provider == 'ollama':
            # Extract model name from full model string
            model_name = llm_config.model.split('/')[-1] if '/' in llm_config.model else llm_config.model
            command.extend(['--model', f'ollama_chat/{model_name}'])

        # Add scripting-friendly options
        command.extend([
            '--yes',           # Auto-confirm changes
            '--no-pretty',     # Disable pretty output for scripting
        ])

        # Handle commits properly (no conflicting flags)
        aider_config = self.config.aider
        if aider_config.auto_commit:
            command.append('--auto-commits')
        else:
            command.append('--no-auto-commits')

        # Add message if provided (better for scripting)
        if message:
            command.extend(['--message', message])

        # Add the file to edit (ensure path is relative to project root)
        if file_path.startswith('./'):
            # Remove ./ prefix since we're running from project root
            clean_file_path = file_path[2:]
        else:
            clean_file_path = file_path
        command.append(clean_file_path)
        
        return command

    def _setup_aider_environment(self, llm_config) -> None:
        """Set up environment variables for aider subprocess.

        Args:
            llm_config: LLM configuration object
        """
        # Get the API key for the current provider
        api_key = self._get_api_key_for_provider(llm_config.provider)

        if api_key:
            # Set the appropriate environment variable for aider
            if llm_config.provider == 'deepseek':
                os.environ['DEEPSEEK_API_KEY'] = api_key
            elif llm_config.provider == 'openrouter':
                os.environ['OPENROUTER_API_KEY'] = api_key
            elif llm_config.provider == 'ollama':
                os.environ['OLLAMA_API_KEY'] = api_key
        else:
            logger.error(f"No API key found for provider: {llm_config.provider}. Please check your environment variables.")

    def _create_aider_config(self, llm_config) -> None:
        """Create .aider.conf.yml file in the project root.

        Args:
            llm_config: LLM configuration object
        """
        import yaml

        config_path = self.project_root / '.aider.conf.yml'

        # Build aider configuration
        aider_config = {
            'model': llm_config.model,
        }

        # Add API keys based on provider
        api_keys = {}

        if llm_config.provider == 'deepseek':
            api_key = self._get_api_key_for_provider('deepseek')
            logger.debug(f"DeepSeek API key retrieved: {bool(api_key)}")
            if api_key:
                api_keys['deepseek'] = api_key
                logger.debug("Added DeepSeek API key to aider config")
            else:
                logger.warning("No DeepSeek API key found for aider config")
        elif llm_config.provider == 'openrouter':
            api_key = self._get_api_key_for_provider('openrouter')
            if api_key:
                api_keys['openrouter'] = api_key
        elif llm_config.provider == 'ollama':
            api_key = self._get_api_key_for_provider('ollama')
            if api_key:
                api_keys['ollama'] = api_key

        if api_keys:
            aider_config['api-key'] = api_keys

        # Add other aider settings
        aider_config.update({
            'auto-commits': self.config.aider.auto_commit,
            'yes': True,  # Auto-confirm for scripting
            'no-pretty': True,  # Disable pretty output for scripting
        })

        # Write config file
        try:
            with open(config_path, 'w') as f:
                yaml.dump(aider_config, f, default_flow_style=False)
            logger.debug(f"Created aider config at {config_path}")
        except Exception as e:
            logger.warning(f"Failed to create aider config: {e}")

    def _detect_changes_in_output(self, output: str) -> bool:
        """Detect if aider made changes to files.
        
        Args:
            output: Aider output text
            
        Returns:
            True if changes were made
        """
        change_indicators = [
            'Applied edit',
            'Committing changes',
            'Changes made',
            'Modified:',
            'Edited',
            'Updated'
        ]
        
        output_lower = output.lower()
        return any(indicator.lower() in output_lower for indicator in change_indicators)
    
    def _extract_fix_description(self, output: str) -> str:
        """Extract a description of the fixes made from aider output.
        
        Args:
            output: Aider output text
            
        Returns:
            Description of fixes made
        """
        lines = output.split('\n')
        
        # Look for lines that describe what was done
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in [
                'fixed', 'corrected', 'updated', 'changed', 'modified',
                'added', 'removed', 'formatted', 'imported'
            ]):
                description_lines.append(line)
        
        if description_lines:
            return '; '.join(description_lines[:3])  # Limit to first 3 descriptions
        
        return "Fixes applied"
    
    def verify_fixes(self, session: FixSession, lint_runner) -> Dict[str, Any]:
        """Verify that fixes were successful by re-running linters.
        
        Args:
            session: Fix session to verify
            lint_runner: LintRunner instance to re-run linters
            
        Returns:
            Verification results
        """
        logger.info(f"Verifying fixes for session {session.session_id}")
        
        # Re-run linters on the fixed file
        original_errors = [result.error_analysis.error for result in session.results]
        original_linters = list(set(error.linter for error in original_errors))
        
        verification_results = {}
        
        for linter in original_linters:
            result = lint_runner.run_linter(linter, [session.file_path])
            verification_results[linter] = result
        
        # Analyze the results
        remaining_errors = []
        for linter_result in verification_results.values():
            remaining_errors.extend(linter_result.errors + linter_result.warnings)
        
        # Check which original errors are still present
        fixed_errors = []
        still_present = []
        
        for original_error in original_errors:
            found = False
            for remaining_error in remaining_errors:
                if (remaining_error.line == original_error.line and 
                    remaining_error.rule_id == original_error.rule_id):
                    found = True
                    break
            
            if found:
                still_present.append(original_error)
            else:
                fixed_errors.append(original_error)
        
        verification_summary = {
            'total_original_errors': len(original_errors),
            'errors_fixed': len(fixed_errors),
            'errors_still_present': len(still_present),
            'new_errors': len(remaining_errors) - len(still_present),
            'success_rate': len(fixed_errors) / len(original_errors) if original_errors else 1.0,
            'fixed_errors': fixed_errors,
            'remaining_errors': still_present,
            'verification_results': verification_results
        }
        
        logger.info(f"Verification complete: {len(fixed_errors)}/{len(original_errors)} errors fixed")
        
        return verification_summary
    
    def fix_multiple_files(self, file_analyses: Dict[str, FileAnalysis],
                          max_files: Optional[int] = None,
                          max_errors_per_file: Optional[int] = None,
                          progress_callback: Optional[callable] = None) -> List[FixSession]:
        """Fix errors in multiple files with progress tracking.

        Args:
            file_analyses: Dictionary of file analyses
            max_files: Maximum number of files to process
            max_errors_per_file: Maximum errors to fix per file
            progress_callback: Optional callback for progress updates

        Returns:
            List of fix sessions
        """
        sessions = []

        # Sort files by complexity (easier files first)
        sorted_files = sorted(
            file_analyses.items(),
            key=lambda x: (x[1].complexity_score, len(x[1].error_analyses))
        )

        if max_files:
            sorted_files = sorted_files[:max_files]

        total_files = len(sorted_files)
        total_errors = sum(len(fa.error_analyses) for _, fa in sorted_files)
        processed_files = 0
        processed_errors = 0

        logger.info(f"Starting batch processing: {total_files} files, {total_errors} total errors")

        for file_path, file_analysis in sorted_files:
            if not file_analysis.error_analyses:
                continue

            file_errors = len(file_analysis.error_analyses)
            logger.info(f"Processing file {processed_files + 1}/{total_files}: {file_path} ({file_errors} errors)")

            # Progress callback
            if progress_callback:
                progress_callback({
                    'stage': 'processing_file',
                    'current_file': processed_files + 1,
                    'total_files': total_files,
                    'current_file_path': file_path,
                    'file_errors': file_errors,
                    'processed_errors': processed_errors,
                    'total_errors': total_errors
                })

            try:
                session = self.fix_errors_in_file(file_analysis, max_errors_per_file, progress_callback)
                sessions.append(session)

                processed_files += 1
                processed_errors += len(session.errors_to_fix)

                # Progress update after file completion
                if progress_callback:
                    progress_callback({
                        'stage': 'file_completed',
                        'completed_files': processed_files,
                        'total_files': total_files,
                        'processed_errors': processed_errors,
                        'total_errors': total_errors,
                        'session_results': len([r for r in session.results if r.success])
                    })

                # Add a small delay between files to avoid overwhelming the LLM
                import time
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Process interrupted by user")
                break
            except Exception as e:
                logger.error(f"Failed to fix errors in {file_path}: {e}")
                processed_files += 1
                continue

        logger.info(f"Batch processing complete: {processed_files}/{total_files} files processed")
        return sessions

