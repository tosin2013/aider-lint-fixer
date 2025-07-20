"""
Aider Integration Module

This module integrates with aider.chat to automatically fix lint errors using LLMs.
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    MAX_PROMPT_LENGTH = 8000  # Maximum prompt length to avoid token limits
    AIDER_TIMEOUT = 300  # 5 minutes timeout for aider operations
    BATCH_DELAY = 2  # Seconds to wait between batches

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
            "aider",
            "python -m aider",
            str(Path.cwd() / "venv" / "bin" / "aider"),
            str(Path.home() / ".local" / "bin" / "aider"),
        ]

        for path in possible_paths:
            try:
                result = subprocess.run(
                    path.split() + ["--version"], capture_output=True, text=True, timeout=10
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
        if llm_config.provider == "deepseek":
            api_key = self._get_api_key_for_provider("deepseek")
            if api_key:
                os.environ["DEEPSEEK_API_KEY"] = api_key
                # Also set as generic API key for aider
                os.environ["OPENAI_API_KEY"] = api_key
                os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

        elif llm_config.provider == "openrouter":
            api_key = self._get_api_key_for_provider("openrouter")
            if api_key:
                os.environ["OPENROUTER_API_KEY"] = api_key

        elif llm_config.provider == "ollama":
            api_key = self._get_api_key_for_provider("ollama")
            if api_key:
                os.environ["OLLAMA_API_KEY"] = api_key

            if llm_config.api_base:
                os.environ["OLLAMA_API_BASE"] = llm_config.api_base
            else:
                os.environ["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"

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
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "ollama": "OLLAMA_API_KEY",
            "openai": "OPENAI_API_KEY",
        }

        if provider in env_vars:
            return os.getenv(env_vars[provider])

        return None

    def fix_errors_in_file(
        self,
        file_analysis: FileAnalysis,
        max_errors: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> FixSession:
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
            analysis
            for analysis in file_analysis.error_analyses
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
            session_id=session_id,
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
                progress_callback(
                    {
                        "stage": "fixing_error_group",
                        "complexity": complexity.value,
                        "group_errors": len(errors),
                        "processed_groups": processed_groups,
                        "total_groups": total_groups,
                        "session_id": session_id,
                    }
                )

            # Fix errors in this complexity group
            group_results = self._fix_error_group(errors, session_id)
            session.results.extend(group_results)
            processed_groups += 1

        session.total_time = time.time() - start_time

        logger.info(f"Fix session {session_id} completed in {session.total_time:.2f}s")

        return session

    def _group_errors_by_complexity(
        self, errors: List[ErrorAnalysis]
    ) -> Dict[FixComplexity, List[ErrorAnalysis]]:
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
                    success=aider_result["success"],
                    changes_made=aider_result["changes_made"],
                    fix_description=aider_result["description"],
                    aider_output=aider_result["output"],
                    error_message=aider_result.get("error", ""),
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
            if (
                len(current_batch) >= self.MAX_ERRORS_PER_BATCH
                or current_prompt_length + error_prompt_length > self.MAX_PROMPT_LENGTH
            ):

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

            prompt_parts.extend(
                [
                    f"{i}. {error.linter} - {error.rule_id}",
                    f"   Line {error.line}, Column {error.column}",
                    f"   Message: {error.message}",
                    f"   Category: {error_analysis.category.value}",
                    f"   Fix Strategy: {error_analysis.fix_strategy or 'Apply appropriate fix'}",
                    "",
                ]
            )

            # Add context if available
            if error_analysis.context_lines:
                prompt_parts.extend(
                    ["   Context:", *[f"   {line}" for line in error_analysis.context_lines], ""]
                )

        prompt_parts.extend(
            [
                "INSTRUCTIONS:",
                "1. Fix all the listed lint errors",
                "2. Maintain the existing code functionality",
                "3. Follow the project's coding style and conventions",
                "4. Make minimal changes necessary to fix the errors",
                "5. Ensure the fixes don't introduce new errors",
                "6. If multiple errors are related, fix them together efficiently",
                "",
                "Please analyze each error and apply the appropriate fix. "
                "Focus on the specific issues mentioned in the error messages.",
            ]
        )

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
                cwd=self.project_root,
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
                "success": success,
                "changes_made": changes_made,
                "output": stdout,
                "error": stderr if not success else "",
                "description": self._extract_fix_description(stdout),
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
                "success": False,
                "changes_made": False,
                "output": "",
                "error": "Aider execution timed out",
                "description": "",
            }
        except Exception as e:
            logger.error(f"Error running aider for {file_path}: {e}")
            return {
                "success": False,
                "changes_made": False,
                "output": "",
                "error": str(e),
                "description": "",
            }

    def _build_aider_command(self, file_path: str, message: str = None, architect_mode: bool = False,
                           architect_model: str = None, editor_model: str = None) -> List[str]:
        """Build the aider command with appropriate options.

        Args:
            file_path: Path to the file to fix
            message: Optional message to pass to aider
            architect_mode: Whether to use architect mode
            architect_model: Model to use for architect reasoning
            editor_model: Model to use for file editing (when in architect mode)

        Returns:
            List of command arguments
        """
        command = self.aider_executable.split()

        # Add model configuration
        llm_config = self.config.llm

        # Set up environment variables for aider subprocess
        self._setup_aider_environment(llm_config)

        # Configure models based on mode
        if architect_mode:
            # Use architect mode with separate models
            command.append("--architect")

            # Set architect model (main reasoning model)
            architect_model_name = architect_model or llm_config.model
            command.extend(["--model", architect_model_name])

            # Set editor model (for file editing)
            if editor_model:
                command.extend(["--editor-model", editor_model])
            else:
                # Default editor models based on architect model
                default_editor = self._get_default_editor_model(architect_model_name)
                if default_editor:
                    command.extend(["--editor-model", default_editor])

            # Use recommended edit format for architect mode
            command.extend(["--editor-edit-format", "editor-diff"])
        else:
            # Standard mode - single model
            if llm_config.provider == "deepseek":
                command.extend(["--model", llm_config.model])
            elif llm_config.provider == "openrouter":
                command.extend(["--model", llm_config.model])
            elif llm_config.provider == "ollama":
                # Extract model name from full model string
                model_name = (
                    llm_config.model.split("/")[-1] if "/" in llm_config.model else llm_config.model
                )
                command.extend(["--model", f"ollama_chat/{model_name}"])

        # Add scripting-friendly options
        command.extend(
            [
                "--yes",  # Auto-confirm changes
                "--no-pretty",  # Disable pretty output for scripting
            ]
        )

        # Handle commits properly (no conflicting flags)
        aider_config = self.config.aider
        if aider_config.auto_commit:
            command.append("--auto-commits")
        else:
            command.append("--no-auto-commits")

        # Add message if provided (better for scripting)
        if message:
            command.extend(["--message", message])

        # Add the file to edit (ensure path is relative to project root)
        if file_path.startswith("./"):
            # Remove ./ prefix since we're running from project root
            clean_file_path = file_path[2:]
        else:
            clean_file_path = file_path
        command.append(clean_file_path)

        return command

    def _get_default_editor_model(self, architect_model: str) -> Optional[str]:
        """Get the recommended editor model for a given architect model.

        Args:
            architect_model: The architect model being used

        Returns:
            Recommended editor model name or None
        """
        # Recommended pairings based on aider documentation
        editor_model_map = {
            # OpenAI o1 models work best with GPT-4o editor
            "o1-mini": "gpt-4o",
            "o1-preview": "gpt-4o",
            "openai/o1-mini": "gpt-4o",
            "openai/o1-preview": "gpt-4o",

            # Claude models can use GPT-4o or same model
            "claude-3-5-sonnet-20241022": "gpt-4o",
            "anthropic/claude-3-5-sonnet-20241022": "gpt-4o",

            # DeepSeek models can use GPT-4o for editing
            "deepseek/deepseek-chat": "gpt-4o",
            "deepseek/deepseek-coder": "gpt-4o",

            # For other models, let aider choose default
        }

        return editor_model_map.get(architect_model)

    def _create_architect_prompt_file(self, prompt_data: Dict) -> str:
        """Create temporary file with architect prompt for complex instructions.

        Args:
            prompt_data: Dictionary containing architect prompt information

        Returns:
            Path to the created temporary prompt file
        """
        try:
            # Create temporary file with .md extension for better formatting
            prompt_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.md',
                prefix='architect_prompt_',
                delete=False,
                dir=self.project_root
            )

            # Write the architect prompt content
            architect_prompt = prompt_data.get("architect_prompt", "")
            if not architect_prompt:
                # Fallback to basic prompt if no specific architect prompt
                file_name = prompt_data.get("file", "unknown").split('/')[-1]
                undefined_vars = prompt_data.get("undefined_variables", [])
                architect_prompt = f"""# Fix undefined variables in {file_name}

Please analyze and fix the undefined variable issues in this file.

Undefined variables detected: {', '.join(undefined_vars)}

Instructions:
1. Examine each undefined variable in context
2. Determine the correct solution (import, global, typo, scope)
3. Apply fixes while preserving functionality
4. Ensure no runtime errors are introduced
"""

            prompt_file.write(architect_prompt)
            prompt_file.close()

            logger.debug(f"Created architect prompt file: {prompt_file.name}")
            return prompt_file.name

        except Exception as e:
            logger.error(f"Failed to create architect prompt file: {e}")
            raise

    def _cleanup_prompt_file(self, prompt_file_path: str) -> None:
        """Clean up temporary prompt file.

        Args:
            prompt_file_path: Path to the prompt file to clean up
        """
        try:
            if os.path.exists(prompt_file_path):
                os.unlink(prompt_file_path)
                logger.debug(f"Cleaned up prompt file: {prompt_file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup prompt file {prompt_file_path}: {e}")

    def _run_architect_mode(self, file_path: str, prompt_data: Dict,
                          architect_model: str = None, editor_model: str = None) -> Dict:
        """Execute aider in architect mode with structured prompt.

        Args:
            file_path: Path to the file to fix
            prompt_data: Dictionary containing architect prompt and metadata
            architect_model: Model to use for architect reasoning
            editor_model: Model to use for file editing

        Returns:
            Dictionary with execution results
        """
        prompt_file_path = None

        try:
            # Create temporary prompt file
            prompt_file_path = self._create_architect_prompt_file(prompt_data)

            # Build architect mode command
            # Use @filename syntax to load prompt from file
            message = f"@{prompt_file_path}"
            command = self._build_aider_command(
                file_path,
                message,
                architect_mode=True,
                architect_model=architect_model,
                editor_model=editor_model
            )

            logger.info(f"Running architect mode for {file_path}")
            logger.debug(f"Architect command: {' '.join(command)}")

            # Execute the command
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.AIDER_TIMEOUT,
                cwd=self.project_root,
            )

            stdout = process.stdout
            stderr = process.stderr

            # Analyze results
            success = process.returncode == 0
            changes_made = self._detect_changes_made(stdout)

            if success:
                logger.info(f"Architect mode completed successfully for {file_path}")
                description = f"Fixed undefined variables using architect mode"
            else:
                logger.error(f"Architect mode failed for {file_path}: {stderr}")
                description = f"Architect mode failed: {stderr[:100]}..."

            return {
                "success": success,
                "changes_made": changes_made,
                "output": stdout,
                "error": stderr if not success else "",
                "description": description,
                "mode": "architect"
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Architect mode timed out for {file_path}")
            return {
                "success": False,
                "changes_made": False,
                "output": "",
                "error": "Architect mode execution timed out",
                "description": "Timed out during architect mode execution",
                "mode": "architect"
            }
        except Exception as e:
            logger.error(f"Error running architect mode for {file_path}: {e}")
            return {
                "success": False,
                "changes_made": False,
                "output": "",
                "error": str(e),
                "description": f"Architect mode error: {str(e)}",
                "mode": "architect"
            }
        finally:
            # Always cleanup the temporary prompt file
            if prompt_file_path:
                self._cleanup_prompt_file(prompt_file_path)

    def execute_architect_guidance(self, guidance: Dict, architect_model: str = None,
                                 editor_model: str = None) -> List[FixResult]:
        """Execute architect mode for all dangerous files identified in guidance.

        Args:
            guidance: Architect guidance from Pre-Lint Risk Assessment
            architect_model: Model to use for architect reasoning
            editor_model: Model to use for file editing

        Returns:
            List of FixResult objects for each file processed
        """
        results = []

        if not guidance.get("has_dangerous_errors"):
            logger.info("No dangerous errors found - skipping architect mode")
            return results

        architect_prompts = guidance.get("architect_prompts", [])
        if not architect_prompts:
            logger.warning("No architect prompts found in guidance")
            return results

        logger.info(f"🏗️  Executing architect mode for {len(architect_prompts)} files")

        for i, prompt_data in enumerate(architect_prompts, 1):
            file_path = prompt_data.get("file", "")
            if not file_path:
                logger.warning(f"Skipping prompt {i}: no file path specified")
                continue

            file_name = file_path.split('/')[-1]
            undefined_vars = prompt_data.get("undefined_variables", [])

            print(f"\n🏗️  [{i}/{len(architect_prompts)}] Architect mode: {file_name}")
            print(f"   📁 File: {file_path}")
            print(f"   🔍 Undefined variables: {', '.join(undefined_vars)}")

            try:
                # Execute architect mode for this file
                result = self._run_architect_mode(
                    file_path,
                    prompt_data,
                    architect_model=architect_model,
                    editor_model=editor_model
                )

                # Create FixResult from architect mode result
                # Note: We don't have ErrorAnalysis objects for architect mode,
                # so we'll create a simplified result
                fix_result = FixResult(
                    error_analysis=None,  # Architect mode doesn't use ErrorAnalysis
                    success=result["success"],
                    changes_made=result["changes_made"],
                    fix_description=result["description"],
                    aider_output=result["output"],
                    error_message=result.get("error", "")
                )

                results.append(fix_result)

                if result["success"]:
                    print(f"   ✅ Architect mode completed successfully")
                    if result["changes_made"]:
                        print(f"   📝 Changes were made to the file")
                    else:
                        print(f"   ℹ️  No changes needed")
                else:
                    print(f"   ❌ Architect mode failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error executing architect mode for {file_path}: {e}")

                # Create failed result
                fix_result = FixResult(
                    error_analysis=None,
                    success=False,
                    changes_made=False,
                    fix_description=f"Architect mode error: {str(e)}",
                    aider_output="",
                    error_message=str(e)
                )
                results.append(fix_result)

                print(f"   ❌ Error: {str(e)}")

        # Summary
        successful = sum(1 for r in results if r.success)
        with_changes = sum(1 for r in results if r.changes_made)

        print(f"\n🏗️  Architect Mode Summary:")
        print(f"   📊 Files processed: {len(results)}")
        print(f"   ✅ Successful: {successful}")
        print(f"   📝 Files changed: {with_changes}")

        return results

    def execute_safe_automation(self, guidance: Dict, enabled_linters: List[str],
                              max_errors: int = None) -> List[FixResult]:
        """Execute safe automation for non-dangerous error types.

        Args:
            guidance: Architect guidance from Pre-Lint Risk Assessment
            enabled_linters: List of enabled linters
            max_errors: Maximum errors to fix per file

        Returns:
            List of FixResult objects for safe automation
        """
        results = []

        safe_plan = guidance.get("safe_automation_plan", {})
        if not safe_plan:
            logger.info("No safe automation plan found")
            return results

        safe_errors_count = safe_plan.get("safe_errors_count", 0)
        if safe_errors_count == 0:
            logger.info("No safe errors to automate")
            return results

        print(f"\n🤖 Safe Automation Phase:")
        print(f"   📊 Safe errors to fix: {safe_errors_count}")
        print(f"   🔧 Linters: {', '.join(enabled_linters)}")

        # Use the existing fix_errors method but with exclusions for dangerous rules
        dangerous_rules = ["no-undef", "no-global-assign", "no-implicit-globals", "no-redeclare"]

        # This would integrate with the existing lint runner and error fixing logic
        # For now, we'll return a placeholder that indicates safe automation was attempted
        logger.info(f"Safe automation would exclude rules: {', '.join(dangerous_rules)}")
        logger.info(f"Safe automation would fix up to {max_errors or 'unlimited'} errors per file")

        # TODO: Integrate with existing LintRunner and error fixing workflow
        # This requires coordination with the main lint fixing pipeline

        return results

    def create_enhanced_prompt_for_dangerous_errors(self, error_analyses: List,
                                                   undefined_vars_context: Dict = None) -> str:
        """Create enhanced prompt for dangerous errors with undefined variable context.

        Args:
            error_analyses: List of ErrorAnalysis objects
            undefined_vars_context: Context about undefined variables from risk assessment

        Returns:
            Enhanced prompt string with context about dangerous errors
        """
        prompt_parts = ["# Enhanced Fix for Dangerous Errors", ""]

        # Group errors by file
        files_with_errors = {}
        for error_analysis in error_analyses:
            file_path = error_analysis.error.file_path
            if file_path not in files_with_errors:
                files_with_errors[file_path] = []
            files_with_errors[file_path].append(error_analysis)

        for file_path, file_errors in files_with_errors.items():
            file_name = file_path.split('/')[-1]
            prompt_parts.append(f"## File: {file_name}")
            prompt_parts.append(f"Path: {file_path}")
            prompt_parts.append("")

            # Check for undefined variables in this file
            undefined_vars = []
            no_undef_errors = []

            for error_analysis in file_errors:
                error = error_analysis.error
                if error.rule_id == "no-undef":
                    no_undef_errors.append(error)
                    # Extract variable name from error message
                    import re
                    match = re.search(r"'([^']+)' is not defined", error.message)
                    if match:
                        undefined_vars.append(match.group(1))

            if undefined_vars:
                prompt_parts.append("### ⚠️ CRITICAL: Undefined Variables Detected")
                prompt_parts.append("These variables are undefined and may break functionality:")
                prompt_parts.append("")

                for var in undefined_vars:
                    prompt_parts.append(f"- `{var}` - undefined variable")

                    # Add context if available
                    if undefined_vars_context and file_path in undefined_vars_context:
                        file_context = undefined_vars_context[file_path]
                        if var in file_context.get("undefined_vars", set()):
                            # Find suggestions for this variable
                            suggestions = self._get_variable_suggestions(var, file_name)
                            if suggestions:
                                prompt_parts.append(f"  💡 Suggestion: {suggestions[0]}")

                prompt_parts.append("")
                prompt_parts.append("### Instructions for Undefined Variables:")
                prompt_parts.append("1. **DO NOT** create dummy variables or empty objects")
                prompt_parts.append("2. **ANALYZE CONTEXT** - determine what each variable should be:")
                prompt_parts.append("   - Missing import statements")
                prompt_parts.append("   - Global variables from HTML/external scripts")
                prompt_parts.append("   - Typos in variable names")
                prompt_parts.append("   - Variables that should be function parameters")
                prompt_parts.append("3. **PRESERVE FUNCTIONALITY** - ensure fixes don't break the code")
                prompt_parts.append("4. **ADD COMMENTS** explaining your reasoning for each fix")
                prompt_parts.append("")

            # List other errors
            other_errors = [e for e in file_errors if e.error.rule_id != "no-undef"]
            if other_errors:
                prompt_parts.append("### Other Errors to Fix:")
                for error_analysis in other_errors:
                    error = error_analysis.error
                    prompt_parts.append(f"- Line {error.line}: {error.rule_id} - {error.message}")
                prompt_parts.append("")

        prompt_parts.extend([
            "## General Instructions:",
            "1. Fix all errors while preserving code functionality",
            "2. Pay special attention to undefined variables - these are dangerous",
            "3. Add appropriate imports, globals, or parameter declarations",
            "4. Test your understanding by explaining each undefined variable fix",
            "5. If unsure about a variable's purpose, add a comment asking for clarification",
            "",
            "## Example Fixes:",
            "```javascript",
            "// BAD: Creating dummy variables",
            "const globalConfig = {}; // This breaks functionality!",
            "",
            "// GOOD: Adding proper import",
            "import { globalConfig } from './config.js';",
            "",
            "// GOOD: Declaring as global (if from HTML)",
            "/* global globalConfig */",
            "",
            "// GOOD: Adding as parameter (if should be passed in)",
            "function processData(globalConfig) {",
            "```"
        ])

        return "\n".join(prompt_parts)

    def _get_variable_suggestions(self, var_name: str, file_name: str) -> List[str]:
        """Get suggestions for fixing an undefined variable."""
        suggestions = []

        if var_name.lower() in ['console', 'window', 'document', 'global', 'process']:
            suggestions.append(f"'{var_name}' is a global - add /* global {var_name} */ comment")
        elif var_name.lower().endswith('callback') or 'callback' in var_name.lower():
            suggestions.append(f"'{var_name}' might be a missing function parameter")
        elif file_name.endswith('.mjs') or 'module' in file_name:
            suggestions.append(f"'{var_name}' might need an import statement")
        elif 'config' in var_name.lower():
            suggestions.append(f"'{var_name}' might be imported from a config file")
        else:
            suggestions.append(f"'{var_name}' needs investigation - could be import, global, or typo")

        return suggestions

    def _setup_aider_environment(self, llm_config) -> None:
        """Set up environment variables for aider subprocess.

        Args:
            llm_config: LLM configuration object
        """
        # Get the API key for the current provider
        api_key = self._get_api_key_for_provider(llm_config.provider)

        if api_key:
            # Set the appropriate environment variable for aider
            if llm_config.provider == "deepseek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            elif llm_config.provider == "openrouter":
                os.environ["OPENROUTER_API_KEY"] = api_key
            elif llm_config.provider == "ollama":
                os.environ["OLLAMA_API_KEY"] = api_key
        else:
            logger.error(
                f"No API key found for provider: {llm_config.provider}. Please check your environment variables."
            )

    def _create_aider_config(self, llm_config) -> None:
        """Create .aider.conf.yml file in the project root.

        Args:
            llm_config: LLM configuration object
        """
        import yaml

        config_path = self.project_root / ".aider.conf.yml"

        # Build aider configuration
        aider_config = {
            "model": llm_config.model,
        }

        # Add API keys based on provider
        api_keys = {}

        if llm_config.provider == "deepseek":
            api_key = self._get_api_key_for_provider("deepseek")
            logger.debug(f"DeepSeek API key retrieved: {bool(api_key)}")
            if api_key:
                api_keys["deepseek"] = api_key
                logger.debug("Added DeepSeek API key to aider config")
            else:
                logger.warning("No DeepSeek API key found for aider config")
        elif llm_config.provider == "openrouter":
            api_key = self._get_api_key_for_provider("openrouter")
            if api_key:
                api_keys["openrouter"] = api_key
        elif llm_config.provider == "ollama":
            api_key = self._get_api_key_for_provider("ollama")
            if api_key:
                api_keys["ollama"] = api_key

        if api_keys:
            aider_config["api-key"] = api_keys

        # Add other aider settings
        aider_config.update(
            {
                "auto-commits": self.config.aider.auto_commit,
                "yes": True,  # Auto-confirm for scripting
                "no-pretty": True,  # Disable pretty output for scripting
            }
        )

        # Write config file
        try:
            with open(config_path, "w") as f:
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
            "Applied edit",
            "Committing changes",
            "Changes made",
            "Modified:",
            "Edited",
            "Updated",
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
        lines = output.split("\n")

        # Look for lines that describe what was done
        description_lines = []

        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "fixed",
                    "corrected",
                    "updated",
                    "changed",
                    "modified",
                    "added",
                    "removed",
                    "formatted",
                    "imported",
                ]
            ):
                description_lines.append(line)

        if description_lines:
            return "; ".join(description_lines[:3])  # Limit to first 3 descriptions

        return "Fixes applied"

    def verify_fixes(self, session: FixSession, lint_runner, error_analyzer=None) -> Dict[str, Any]:
        """Verify that fixes were successful by re-running linters.

        Args:
            session: Fix session to verify
            lint_runner: LintRunner instance to re-run linters
            error_analyzer: Optional ErrorAnalyzer for learning from results

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
                if (
                    remaining_error.line == original_error.line
                    and remaining_error.rule_id == original_error.rule_id
                ):
                    found = True
                    break

            if found:
                still_present.append(original_error)
            else:
                fixed_errors.append(original_error)

        # Learn from fix results if error_analyzer is provided
        if error_analyzer:
            for error in fixed_errors:
                error_analyzer.learn_from_fix_result(error, fix_successful=True)

            for error in still_present:
                error_analyzer.learn_from_fix_result(error, fix_successful=False)

            logger.debug(
                f"Learned from {len(fixed_errors)} successful and {len(still_present)} failed fixes"
            )

        verification_summary = {
            "total_original_errors": len(original_errors),
            "errors_fixed": len(fixed_errors),
            "errors_still_present": len(still_present),
            "new_errors": len(remaining_errors) - len(still_present),
            "success_rate": len(fixed_errors) / len(original_errors) if original_errors else 1.0,
            "fixed_errors": fixed_errors,
            "remaining_errors": still_present,
            "verification_results": verification_results,
        }

        logger.info(
            f"Verification complete: {len(fixed_errors)}/{len(original_errors)} errors fixed"
        )

        return verification_summary

    def fix_multiple_files(
        self,
        file_analyses: Dict[str, FileAnalysis],
        max_files: Optional[int] = None,
        max_errors_per_file: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> List[FixSession]:
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
        # Use getattr with default to handle cases where complexity_score might be missing
        sorted_files = sorted(
            file_analyses.items(),
            key=lambda x: (getattr(x[1], 'complexity_score', 0.0), len(x[1].error_analyses))
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
            logger.info(
                f"Processing file {processed_files + 1}/{total_files}: {file_path} ({file_errors} errors)"
            )

            # Progress callback
            if progress_callback:
                progress_callback(
                    {
                        "stage": "processing_file",
                        "current_file": processed_files + 1,
                        "total_files": total_files,
                        "current_file_path": file_path,
                        "file_errors": file_errors,
                        "processed_errors": processed_errors,
                        "total_errors": total_errors,
                    }
                )

            try:
                session = self.fix_errors_in_file(
                    file_analysis, max_errors_per_file, progress_callback
                )
                sessions.append(session)

                processed_files += 1
                processed_errors += len(session.errors_to_fix)

                # Progress update after file completion
                if progress_callback:
                    progress_callback(
                        {
                            "stage": "file_completed",
                            "completed_files": processed_files,
                            "total_files": total_files,
                            "processed_errors": processed_errors,
                            "total_errors": total_errors,
                            "session_results": len([r for r in session.results if r.success]),
                        }
                    )

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
