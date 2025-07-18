"""
Main Module for Aider Lint Fixer

This module provides the command-line interface and orchestrates the entire
lint detection and fixing workflow.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import click
from colorama import Fore, Style, init

from . import __version__
from .aider_integration import AiderIntegration
from .config_manager import ConfigManager
from .error_analyzer import ErrorAnalyzer
from .lint_runner import LintRunner
from .project_detector import ProjectDetector

# Initialize colorama for cross-platform colored output
init()

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Set up logging configuration.

    Args:
        level: Logging level
        log_file: Optional log file path
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def print_banner():
    """Print the application banner."""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    Aider Lint Fixer v{__version__}                  ║
║              Automated Lint Error Detection & Fixing         ║
║                   Powered by aider.chat                      ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def print_project_info(project_info):
    """Print detected project information.

    Args:
        project_info: ProjectInfo object
    """
    print(f"\n{Fore.GREEN}📁 Project Detection Results:{Style.RESET_ALL}")
    print(f"   Root: {project_info.root_path}")
    print(
        f"   Languages: {', '.join(project_info.languages) if project_info.languages else 'None detected'}"
    )
    print(
        f"   Package Managers: {', '.join(project_info.package_managers) if project_info.package_managers else 'None detected'}"
    )
    print(
        f"   Lint Configs: {', '.join(project_info.lint_configs.keys()) if project_info.lint_configs else 'None detected'}"
    )
    print(f"   Source Files: {len(project_info.source_files)}")


def print_lint_summary(results):
    """Print lint results summary.

    Args:
        results: Dictionary of lint results
    """
    print(f"\n{Fore.YELLOW}🔍 Lint Results Summary:{Style.RESET_ALL}")

    total_errors = 0
    total_warnings = 0

    for linter_name, result in results.items():
        error_count = len(result.errors)
        warning_count = len(result.warnings)
        total_errors += error_count
        total_warnings += warning_count

        status = "✅" if result.success else "❌"
        print(f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings")

    print(f"\n   Total: {total_errors} errors, {total_warnings} warnings")


def print_fix_summary(sessions):
    """Print fix session summary.

    Args:
        sessions: List of fix sessions
    """
    print(f"\n{Fore.BLUE}🔧 Fix Results Summary:{Style.RESET_ALL}")

    total_files = len(sessions)
    total_errors_attempted = sum(len(session.errors_to_fix) for session in sessions)
    # Count successful aider executions (not actual fixes)
    total_aider_successful = sum(
        len([r for r in session.results if r.success]) for session in sessions
    )

    print(f"   Files processed: {total_files}")
    print(f"   Errors attempted: {total_errors_attempted}")
    print(f"   Aider executions successful: {total_aider_successful}")

    for session in sessions:
        aider_successful = len([r for r in session.results if r.success])
        print(
            f"   📄 {Path(session.file_path).name}: {aider_successful}/{len(session.errors_to_fix)} attempted"
        )

        # Show what errors were attempted to be fixed
        if session.errors_to_fix:
            print(f"      🎯 Errors Attempted:")
            for i, error_analysis in enumerate(
                session.errors_to_fix[:5]
            ):  # Show first 5 attempted errors
                error = error_analysis.error
                print(
                    f"         {i+1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
                )
            if len(session.errors_to_fix) > 5:
                print(f"         ... and {len(session.errors_to_fix) - 5} more")


def create_progress_callback(verbose: bool = False):
    """Create a progress callback function for long-running operations.

    Args:
        verbose: Whether to show detailed progress information

    Returns:
        Progress callback function
    """

    def progress_callback(progress_info: dict):
        """Handle progress updates during lint fixing."""
        stage = progress_info.get("stage", "unknown")

        if stage == "processing_file":
            current = progress_info.get("current_file", 0)
            total = progress_info.get("total_files", 0)
            file_path = progress_info.get("current_file_path", "unknown")
            file_errors = progress_info.get("file_errors", 0)

            print(
                f"\n{Fore.CYAN}📁 Processing file {current}/{total}: {Path(file_path).name} ({file_errors} errors){Style.RESET_ALL}"
            )

        elif stage == "fixing_error_group":
            complexity = progress_info.get("complexity", "unknown")
            group_errors = progress_info.get("group_errors", 0)
            session_id = progress_info.get("session_id", "unknown")[:8]

            if verbose:
                print(f"   🔧 Fixing {group_errors} {complexity} errors (session {session_id})...")
            else:
                print(f"   🔧 Fixing {group_errors} {complexity} errors...")

        elif stage == "file_completed":
            completed = progress_info.get("completed_files", 0)
            total = progress_info.get("total_files", 0)
            processed_errors = progress_info.get("processed_errors", 0)
            total_errors = progress_info.get("total_errors", 0)
            session_results = progress_info.get("session_results", 0)

            print(f"   ✅ File completed: {session_results} successful fixes")

            # Show overall progress
            file_progress = (completed / total * 100) if total > 0 else 0
            error_progress = (processed_errors / total_errors * 100) if total_errors > 0 else 0

            print(
                f"   📊 Progress: {completed}/{total} files ({file_progress:.1f}%), {processed_errors}/{total_errors} errors ({error_progress:.1f}%)"
            )

    return progress_callback


def print_verification_summary(verification_results):
    """Print verification summary showing actual fixes.

    Args:
        verification_results: Dictionary of verification results per session
    """
    print(f"\n{Fore.BLUE}📊 Verification Results (Actual Fixes):{Style.RESET_ALL}")

    total_attempted = 0
    total_fixed = 0

    for session_id, result in verification_results.items():
        total_attempted += result["total_original_errors"]
        total_fixed += result["errors_fixed"]

        success_rate = result["success_rate"] * 100
        print(
            f"   📄 Session {session_id[:8]}: {result['errors_fixed']}/{result['total_original_errors']} fixed ({success_rate:.1f}%)"
        )

        # Show detailed information about what was fixed
        if result["fixed_errors"]:
            print(f"      ✅ Successfully Fixed:")
            for i, error in enumerate(result["fixed_errors"][:5]):  # Show first 5 fixed errors
                print(
                    f"         {i+1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
                )
            if len(result["fixed_errors"]) > 5:
                print(f"         ... and {len(result['fixed_errors']) - 5} more")

        # Show remaining errors if any
        if result["remaining_errors"]:
            print(f"      ❌ Still Present:")
            for i, error in enumerate(
                result["remaining_errors"][:3]
            ):  # Show first 3 remaining errors
                print(
                    f"         {i+1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
                )
            if len(result["remaining_errors"]) > 3:
                print(f"         ... and {len(result['remaining_errors']) - 3} more")

        # Show new errors if any
        if result["new_errors"] > 0:
            print(f"      ⚠️  New errors introduced: {result['new_errors']}")

    overall_rate = (total_fixed / total_attempted * 100) if total_attempted > 0 else 0
    print(
        f"   🎯 Overall: {total_fixed}/{total_attempted} errors actually fixed ({overall_rate:.1f}%)"
    )


@click.command()
@click.argument("project_path", default=".", type=click.Path(exists=True))
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--llm", help="LLM provider (deepseek, openrouter, ollama)")
@click.option("--model", help="Specific model to use")
@click.option("--linters", help="Comma-separated list of linters to run")
@click.option("--max-files", type=int, help="Maximum number of files to process")
@click.option("--max-errors", type=int, help="Maximum number of errors to fix per file")
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without making changes")
@click.option("--interactive", is_flag=True, help="Confirm each fix before applying")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--log-file", help="Path to log file")
@click.option("--no-banner", is_flag=True, help="Disable banner output")
@click.option("--check-only", is_flag=True, help="Only check for issues, don't fix them")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.option("--list-linters", is_flag=True, help="List all available linters and exit")
@click.option(
    "--ansible-profile",
    default="basic",
    type=click.Choice(["basic", "production"]),
    help="Ansible-lint profile to use (basic or production)",
)
@click.option(
    "--profile",
    default="default",
    type=click.Choice(["basic", "default", "strict"]),
    help="Linter profile to use (basic, default, or strict)",
)
@click.option(
    "--include",
    multiple=True,
    help="Include patterns (can be used multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude patterns (can be used multiple times)",
)
@click.option(
    "--extensions",
    help="Comma-separated list of file extensions to process (e.g., py,js,yml)",
)
@click.option("--target-dir", help="Target directory to lint (e.g., roles/)")
def main(
    project_path: str,
    version: bool,
    config: Optional[str],
    llm: Optional[str],
    model: Optional[str],
    linters: Optional[str],
    max_files: Optional[int],
    max_errors: Optional[int],
    dry_run: bool,
    interactive: bool,
    verbose: bool,
    quiet: bool,
    no_color: bool,
    log_file: Optional[str],
    no_banner: bool,
    check_only: bool,
    output_format: str,
    list_linters: bool,
    ansible_profile: str,
    profile: str,
    include: tuple,
    exclude: tuple,
    extensions: Optional[str],
    target_dir: Optional[str],
):
    """Aider Lint Fixer - Automated lint error detection and fixing.

    PROJECT_PATH: Path to the project directory (default: current directory)
    """
    # Handle version flag
    if version:
        from . import __version__

        print(f"aider-lint-fixer {__version__}")
        return

    # Handle list-linters flag
    if list_linters:
        import platform

        from .supported_versions import get_platform_compatibility_info, get_supported_linters

        linters_list = get_supported_linters()
        compatibility_info = get_platform_compatibility_info()

        if output_format == "json":
            import json

            output_data = {
                "available_linters": linters_list,
                "platform": platform.system(),
                "platform_notes": compatibility_info,
            }
            print(json.dumps(output_data, indent=2))
        else:
            print(f"Available linters on {platform.system()}:")
            for linter in linters_list:
                print(f"  • {linter}")

            # Show platform compatibility notes if any
            if compatibility_info:
                print(f"\nPlatform compatibility notes:")
                for linter, note in compatibility_info.items():
                    print(f"  ⚠️  {linter}: {note}")

            print(f"\nTotal: {len(linters_list)} linters available")
            print("Use --linters <name1,name2> to specify which linters to run")
        return

    # Handle quiet mode
    if quiet:
        import logging

        logging.getLogger().setLevel(logging.ERROR)

    try:
        # Set up logging
        log_level = "DEBUG" if verbose else ("ERROR" if quiet else "INFO")
        setup_logging(log_level, log_file)

        # Handle color output
        if no_color:
            # Disable colorama colors
            import os

            os.environ["NO_COLOR"] = "1"
            # Reset colorama colors to empty strings
            for attr in dir(Fore):
                if not attr.startswith("_"):
                    setattr(Fore, attr, "")
            for attr in dir(Style):
                if not attr.startswith("_"):
                    setattr(Style, attr, "")

        # Print banner
        if not no_banner and not quiet:
            print_banner()

        # Load configuration
        config_manager = ConfigManager()
        if config:
            # Load specific config file
            project_config = config_manager._load_config_file(Path(config).parent)
        else:
            # Load default configuration
            project_config = config_manager.load_config(project_path)

        # Override config with command line options
        if llm:
            project_config.llm.provider = llm
        if model:
            project_config.llm.model = model

        # Handle target directory
        if target_dir:
            actual_project_path = str(Path(project_path) / target_dir)
            print(f"{Fore.GREEN}🚀 Starting Aider Lint Fixer{Style.RESET_ALL}")
            print(f"   Project: {Path(project_path).resolve()}")
            print(f"   Target Directory: {target_dir}")
            print(f"   Actual Path: {Path(actual_project_path).resolve()}")
        else:
            actual_project_path = project_path
            print(f"{Fore.GREEN}🚀 Starting Aider Lint Fixer{Style.RESET_ALL}")
            print(f"   Project: {Path(project_path).resolve()}")

        print(f"   LLM Provider: {project_config.llm.provider}")
        print(f"   Model: {project_config.llm.model}")

        if exclude:
            print(f"   Exclude Patterns: {list(exclude)}")

        # Step 1: Detect project structure
        print(f"\n{Fore.CYAN}Step 1: Detecting project structure...{Style.RESET_ALL}")

        detector = ProjectDetector(exclude_patterns=project_config.project.exclude_patterns)
        project_info = detector.detect_project(actual_project_path)

        print_project_info(project_info)

        if not project_info.languages:
            print(f"{Fore.RED}❌ No supported programming languages detected.{Style.RESET_ALL}")
            return 1

        # Step 2: Run linters
        print(f"\n{Fore.CYAN}Step 2: Running linters...{Style.RESET_ALL}")

        lint_runner = LintRunner(project_info)

        # Determine which linters to run
        if linters:
            enabled_linters = [l.strip() for l in linters.split(",")]
        else:
            enabled_linters = (
                project_config.linters.enabled if project_config.linters.auto_detect else None
            )

        # Prepare linter options
        linter_options = {"ansible_profile": ansible_profile, "profile": profile}

        # Add include/exclude patterns and extensions
        if include:
            linter_options["include"] = list(include)
        if exclude:
            linter_options["exclude"] = list(exclude)
        if extensions:
            linter_options["extensions"] = [ext.strip() for ext in extensions.split(",")]

        results = lint_runner.run_all_available_linters(enabled_linters, **linter_options)

        # Handle output format
        if output_format == "json":
            import json

            json_results = {}
            for linter, result in results.items():
                json_results[linter] = {
                    "errors": [
                        {"file": e.file, "line": e.line, "message": e.message, "rule_id": e.rule_id}
                        for e in result.errors
                    ],
                    "warnings": [
                        {"file": w.file, "line": w.line, "message": w.message, "rule_id": w.rule_id}
                        for w in result.warnings
                    ],
                }
            print(json.dumps(json_results, indent=2))
        else:
            print_lint_summary(results)

        # Check if there are any errors to fix
        total_errors = sum(len(result.errors) + len(result.warnings) for result in results.values())

        if total_errors == 0:
            if not quiet:
                print(
                    f"\n{Fore.GREEN}🎉 No lint errors found! Your code is clean.{Style.RESET_ALL}"
                )
            return 0

        # Handle check-only mode
        if check_only:
            if not quiet:
                print(
                    f"\n{Fore.YELLOW}Check-only mode: Found {total_errors} issues. Exiting without fixing.{Style.RESET_ALL}"
                )
            return 1 if total_errors > 0 else 0

        # Step 3: Analyze errors
        print(f"\n{Fore.CYAN}Step 3: Analyzing errors...{Style.RESET_ALL}")

        analyzer = ErrorAnalyzer(project_root=str(project_info.root_path))
        file_analyses = analyzer.analyze_errors(results)

        # Get prioritized errors
        prioritized_errors = analyzer.get_prioritized_errors(file_analyses, max_errors)

        print(f"   Analyzed {len(file_analyses)} files")
        print(f"   Found {len(prioritized_errors)} fixable errors")

        if not prioritized_errors:
            print(f"\n{Fore.YELLOW}⚠️  No automatically fixable errors found.{Style.RESET_ALL}")
            return 0

        # Show what would be fixed in dry-run mode
        if dry_run:
            print(f"\n{Fore.YELLOW}🔍 Dry Run - Errors that would be fixed:{Style.RESET_ALL}")

            for i, error_analysis in enumerate(prioritized_errors[:10], 1):  # Show first 10
                error = error_analysis.error
                print(f"   {i}. {error.file_path}:{error.line} - {error.linter} {error.rule_id}")
                print(f"      {error.message}")
                print(
                    f"      Category: {error_analysis.category.value}, Complexity: {error_analysis.complexity.value}"
                )

            if len(prioritized_errors) > 10:
                print(f"   ... and {len(prioritized_errors) - 10} more errors")

            return 0

        # Step 4: Fix errors
        print(f"\n{Fore.CYAN}Step 4: Fixing errors with aider.chat...{Style.RESET_ALL}")

        try:
            aider_integration = AiderIntegration(project_config, project_path, config_manager)
        except RuntimeError as e:
            print(f"{Fore.RED}❌ {e}{Style.RESET_ALL}")
            print(f"   Please install aider-chat: pip install aider-chat")
            return 1

        # Interactive confirmation
        if interactive:
            files_to_fix = list(file_analyses.keys())
            if max_files:
                files_to_fix = files_to_fix[:max_files]

            print(f"\n   Files to process: {len(files_to_fix)}")
            for file_path in files_to_fix:
                print(f"     - {file_path}")

            if not click.confirm(f"\nProceed with fixing {len(prioritized_errors)} errors?"):
                print("Aborted by user.")
                return 0

        # Create progress callback for long-running operations
        progress_callback = create_progress_callback(verbose)

        # Fix errors with progress tracking
        sessions = aider_integration.fix_multiple_files(
            file_analyses, max_files, max_errors, progress_callback
        )

        print_fix_summary(sessions)

        # Step 5: Verify fixes
        print(f"\n{Fore.CYAN}Step 5: Verifying fixes...{Style.RESET_ALL}")

        total_fixed = 0
        total_attempted = 0
        verification_results = {}

        for session in sessions:
            verification = aider_integration.verify_fixes(session, lint_runner)
            verification_results[session.session_id] = verification
            total_fixed += verification["errors_fixed"]
            total_attempted += verification["total_original_errors"]

        # Print detailed verification results
        print_verification_summary(verification_results)

        # Final summary
        overall_success_rate = (total_fixed / total_attempted * 100) if total_attempted > 0 else 0

        print(f"\n{Fore.GREEN}✅ Fixing Complete!{Style.RESET_ALL}")
        print(f"   Total errors fixed: {total_fixed}/{total_attempted}")
        print(f"   Overall success rate: {overall_success_rate:.1f}%")

        if overall_success_rate >= 80:
            print(
                f"\n{Fore.GREEN}🎉 Excellent! Most errors were successfully fixed.{Style.RESET_ALL}"
            )
        elif overall_success_rate >= 50:
            print(
                f"\n{Fore.YELLOW}👍 Good progress! Some errors may need manual attention.{Style.RESET_ALL}"
            )
        else:
            print(f"\n{Fore.RED}⚠️  Many errors may require manual fixing.{Style.RESET_ALL}")

        return 0

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Interrupted by user{Style.RESET_ALL}")
        return 1
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
