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
from .community_issue_reporter import integrate_community_issue_reporting
from .config_manager import ConfigManager
from .enhanced_interactive import (
    CommunityLearningIntegration,
    enhanced_interactive_mode,
    integrate_with_error_analyzer,
)
from .error_analyzer import ErrorAnalyzer
from .lint_runner import LintRunner
from .progress_tracker import EnhancedProgressTracker, create_enhanced_progress_callback
from .project_detector import ProjectDetector

# Initialize colorama for cross-platform colored output
init()

logger = logging.getLogger(__name__)


# Global color helper functions
def get_color(color_attr, no_color=False):
    """Get color code safely, respecting no_color setting."""
    if no_color or os.environ.get("NO_COLOR"):
        return ""
    return getattr(Fore, color_attr, "") if hasattr(Fore, color_attr) else ""


def get_style(style_attr, no_color=False):
    """Get style code safely, respecting no_color setting."""
    if no_color or os.environ.get("NO_COLOR"):
        return ""
    return getattr(Style, style_attr, "") if hasattr(Style, style_attr) else ""


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


def print_lint_summary(results, baseline_results=None, baseline_total=None):
    """Print lint results summary.

    Args:
        results: Dictionary of lint results (processing scan)
        baseline_results: Dictionary of baseline lint results (optional)
        baseline_total: Total baseline error count (optional)
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

        # Show baseline vs processing counts if available
        if baseline_results and linter_name in baseline_results:
            baseline_result = baseline_results[linter_name]
            baseline_error_count = len(baseline_result.errors)
            baseline_warning_count = len(baseline_result.warnings)

            if baseline_error_count != error_count or baseline_warning_count != warning_count:
                print(
                    f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings (baseline: {baseline_error_count} errors, {baseline_warning_count} warnings)"
                )
            else:
                print(f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings")
        else:
            print(f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings")

    if baseline_total and baseline_total != total_errors:
        print(f"\n   Processing Total: {total_errors} errors, {total_warnings} warnings")
        print(
            f"   Baseline Total: {baseline_total} errors (showing {total_errors/baseline_total*100:.1f}% of all errors)"
        )
    else:
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
@click.option(
    "--enhanced-interactive",
    is_flag=True,
    help="Enhanced per-error interactive mode with override capabilities",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force fix all errors, including those classified as unfixable (use with caution)",
)
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
@click.option("--stats", is_flag=True, help="Show learning statistics and exit")
@click.option(
    "--skip-strategic-check",
    is_flag=True,
    help="Skip strategic pre-flight analysis for messy codebases",
)
@click.option(
    "--force-strategic-recheck",
    is_flag=True,
    help="Force re-run of strategic analysis (ignores cache)",
)
@click.option(
    "--bypass-strategic-check",
    is_flag=True,
    help="Bypass strategic check warnings and proceed anyway (not recommended)",
)
@click.option(
    "--resume-session",
    help="Resume a previous progress session by session ID",
)
@click.option(
    "--list-sessions",
    is_flag=True,
    help="List recoverable progress sessions and exit",
)
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
    enhanced_interactive: bool,
    force: bool,
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
    stats: bool,
    skip_strategic_check: bool,
    force_strategic_recheck: bool,
    bypass_strategic_check: bool,
    resume_session: Optional[str],
    list_sessions: bool,
):
    """Aider Lint Fixer - Automated lint error detection and fixing.

    PROJECT_PATH: Path to the project directory (default: current directory)
    """

    # Set up color helpers for this function
    def c(color_attr):
        return get_color(color_attr, no_color)

    def s(style_attr):
        return get_style(style_attr, no_color)

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

    # Handle stats flag
    if stats:
        from .pattern_matcher import SmartErrorClassifier

        cache_dir = Path(project_path) / ".aider-lint-cache"
        classifier = SmartErrorClassifier(cache_dir)
        stats_data = classifier.get_statistics()

        if output_format == "json":
            import json

            print(json.dumps(stats_data, indent=2))
        else:
            print(f"\n{c('CYAN')}📊 Pattern Cache Statistics{s('RESET_ALL')}")
            print(f"   Cache directory: {stats_data['cache']['cache_dir']}")

            cache_sizes = stats_data["cache"]["cache_sizes"]
            print(f"   Training files: {cache_sizes['training_files']:,} bytes")
            print(f"   Model files: {cache_sizes['model_files']:,} bytes")
            print(f"   Total size: {cache_sizes['total_files']:,} bytes")

            print(f"\n{c('CYAN')}🧠 Pattern Matching{s('RESET_ALL')}")
            print(f"   Languages: {', '.join(stats_data['pattern_matcher']['languages'])}")
            print(f"   Total patterns: {stats_data['pattern_matcher']['total_patterns']}")
            print(
                f"   Aho-Corasick available: {stats_data['pattern_matcher']['ahocorasick_available']}"
            )

            print(f"\n{c('CYAN')}🤖 Machine Learning{s('RESET_ALL')}")
            print(f"   scikit-learn available: {stats_data['ml_classifier']['sklearn_available']}")
            print(
                f"   Trained languages: {', '.join(stats_data['ml_classifier']['trained_languages'])}"
            )

            # Show training data counts
            for key, value in stats_data["ml_classifier"].items():
                if key.endswith("_training_examples"):
                    language = key.replace("_training_examples", "")
                    print(f"   {language}: {value} training examples")
        return

    # Handle progress session management
    if list_sessions:
        sessions = EnhancedProgressTracker.list_recoverable_sessions(project_path)
        if not sessions:
            print(f"{Fore.YELLOW}No recoverable progress sessions found.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.CYAN}📋 Recoverable Progress Sessions:{Style.RESET_ALL}")
            for session in sessions:
                from datetime import datetime

                start_time = datetime.fromisoformat(session["start_time"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                progress = f"{session['processed_errors']}/{session['total_errors']}"
                size_indicator = "🔥 Large" if session["is_large_project"] else "📁 Small"
                print(
                    f"   {session['session_id']}: {start_time} - {progress} errors ({size_indicator})"
                )
            print(f"\n💡 Resume with: --resume-session <session_id>")
        return 0

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
            print(f"{c('GREEN')}🚀 Starting Aider Lint Fixer{s('RESET_ALL')}")
            print(f"   Project: {Path(project_path).resolve()}")
            print(f"   Target Directory: {target_dir}")
            print(f"   Actual Path: {Path(actual_project_path).resolve()}")
        else:
            actual_project_path = project_path
            print(f"{c('GREEN')}🚀 Starting Aider Lint Fixer{s('RESET_ALL')}")
            print(f"   Project: {Path(project_path).resolve()}")

        print(f"   LLM Provider: {project_config.llm.provider}")
        print(f"   Model: {project_config.llm.model}")

        if exclude:
            print(f"   Exclude Patterns: {list(exclude)}")

        # Strategic Pre-Flight Check for messy codebases
        if not skip_strategic_check:
            print(f"\n{Fore.YELLOW}🔍 Strategic Pre-Flight Check...{Style.RESET_ALL}")

            try:
                from .strategic_preflight_check import StrategicPreFlightChecker

                checker = StrategicPreFlightChecker(str(actual_project_path), config_manager)
                preflight_result = checker.run_preflight_check(
                    force_recheck=force_strategic_recheck
                )

                if not preflight_result.should_proceed:
                    if bypass_strategic_check:
                        print(
                            f"\n{Fore.YELLOW}⚠️  BYPASSING strategic check - proceeding anyway{Style.RESET_ALL}"
                        )
                        print(
                            f"{Fore.RED}   This is not recommended for chaotic codebases!{Style.RESET_ALL}"
                        )
                    else:
                        print(
                            f"\n{Fore.RED}🛑 Strategic issues detected - automated fixing blocked{Style.RESET_ALL}"
                        )
                        print(
                            f"{Fore.CYAN}💡 Address the issues above or use --bypass-strategic-check{Style.RESET_ALL}"
                        )
                        print(
                            f"{Fore.CYAN}🔄 Re-run with --force-strategic-recheck after making changes{Style.RESET_ALL}"
                        )
                        return 1

            except ImportError:
                print(f"{Fore.YELLOW}⚠️  Strategic pre-flight check not available{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Strategic pre-flight check failed: {e}{Style.RESET_ALL}")

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

        # Step 2a: Run baseline scan to get true error count
        print(f"   📊 Running baseline scan to establish error count...")
        baseline_options = linter_options.copy()
        # Remove any limits for baseline scan
        baseline_options.pop("max_errors", None)
        baseline_options.pop("max_files", None)

        baseline_results = lint_runner.run_all_available_linters(
            enabled_linters, **baseline_options
        )
        baseline_total_errors = sum(
            len(result.errors) + len(result.warnings) for result in baseline_results.values()
        )

        # Step 2b: Run processing scan (may be limited)
        print(f"   🔍 Running processing scan...")
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
            print_lint_summary(
                results, baseline_results=baseline_results, baseline_total=baseline_total_errors
            )

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
        if baseline_total_errors > 0:
            fixable_rate = len(prioritized_errors) / baseline_total_errors * 100
            print(
                f"   Found {len(prioritized_errors)} fixable errors ({fixable_rate:.1f}% of {baseline_total_errors} total baseline errors)"
            )
        else:
            print(f"   Found {len(prioritized_errors)} fixable errors")

        # Enhanced interactive mode - allow user to override classifications
        community_learning = None
        if enhanced_interactive:
            # Get ALL errors (fixable and unfixable) for enhanced interactive mode
            all_error_analyses = []
            for file_path, analysis in file_analyses.items():
                all_error_analyses.extend(analysis.error_analyses)

            if not all_error_analyses:
                print(f"\n{Fore.GREEN}✅ No errors found!{Style.RESET_ALL}")
                return 0

            # Run enhanced interactive mode
            interactive_choices = enhanced_interactive_mode(
                all_error_analyses, max_errors=max_errors, enable_community_learning=True
            )

            # Initialize community learning integration
            community_learning = CommunityLearningIntegration(project_path)
            community_learning.record_interactive_choices(interactive_choices)

            # Integrate choices with error analyzer learning
            integrate_with_error_analyzer(interactive_choices, analyzer)

            # Filter errors based on user choices
            errors_to_fix = [
                choice.error_analysis
                for choice in interactive_choices
                if choice.choice.value == "fix"
            ]

            if not errors_to_fix:
                print(f"\n{Fore.YELLOW}No errors selected for fixing.{Style.RESET_ALL}")
                return 0

            # Rebuild file_analyses with only selected errors
            selected_file_analyses = {}
            for error_analysis in errors_to_fix:
                file_path = error_analysis.error.file_path
                if file_path not in selected_file_analyses:
                    selected_file_analyses[file_path] = type(
                        "FileAnalysis", (), {"error_analyses": [], "file_path": file_path}
                    )()
                selected_file_analyses[file_path].error_analyses.append(error_analysis)

            file_analyses = selected_file_analyses
            prioritized_errors = errors_to_fix

            print(f"\n{Fore.CYAN}📋 Enhanced Interactive Summary:{Style.RESET_ALL}")
            print(f"   Selected {len(prioritized_errors)} errors for fixing")

        elif force:
            # Force mode - include ALL errors (fixable and unfixable)
            print(f"\n{Fore.RED}⚠️  FORCE MODE ENABLED{Style.RESET_ALL}")
            print(
                f"   {Fore.YELLOW}WARNING: Attempting to fix ALL errors, including those classified as unfixable{Style.RESET_ALL}"
            )

            # Get ALL errors for force mode
            all_error_analyses = []
            for file_path, analysis in file_analyses.items():
                all_error_analyses.extend(analysis.error_analyses)

            if not all_error_analyses:
                print(f"\n{Fore.GREEN}✅ No errors found!{Style.RESET_ALL}")
                return 0

            # Apply max_errors limit if specified
            if max_errors:
                all_error_analyses = all_error_analyses[:max_errors]

            # Rebuild file_analyses with all errors
            force_file_analyses = {}
            for error_analysis in all_error_analyses:
                file_path = error_analysis.error.file_path
                if file_path not in force_file_analyses:
                    force_file_analyses[file_path] = type(
                        "FileAnalysis", (), {"error_analyses": [], "file_path": file_path}
                    )()
                force_file_analyses[file_path].error_analyses.append(error_analysis)

            file_analyses = force_file_analyses
            prioritized_errors = all_error_analyses

            print(f"   Forcing fixes for {len(prioritized_errors)} errors")

            # Confirmation for force mode
            if not click.confirm(
                f"\n{Fore.RED}Are you sure you want to force-fix {len(prioritized_errors)} errors? This may cause issues.{Style.RESET_ALL}"
            ):
                print("Aborted by user.")
                return 0

        elif not prioritized_errors:
            print(f"\n{Fore.YELLOW}⚠️  No automatically fixable errors found.{Style.RESET_ALL}")
            print(f"   💡 Try --enhanced-interactive to review and override classifications")
            print(f"   💡 Or use --force to attempt fixing all errors (risky)")
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

        # Create enhanced progress tracker for long-running operations
        total_error_count = len(prioritized_errors)

        # Force verbose progress for enhanced interactive mode
        effective_verbose = verbose or enhanced_interactive

        progress_tracker = EnhancedProgressTracker(
            project_path=project_path, total_errors=total_error_count, verbose=effective_verbose
        )

        # Set total files for progress tracking
        progress_tracker.set_total_files(len(file_analyses))

        # Import ProgressStage for stage updates
        from .progress_tracker import ProgressStage

        progress_tracker.update_stage(ProgressStage.PROCESSING_FILES)

        # Create enhanced progress callback
        progress_callback = create_enhanced_progress_callback(progress_tracker, verbose)

        # Fix errors with enhanced progress tracking
        sessions = aider_integration.fix_multiple_files(
            file_analyses, max_files, max_errors, progress_callback
        )

        # Close progress tracker
        progress_tracker.close()

        print_fix_summary(sessions)

        # Step 5: Verify fixes
        print(f"\n{Fore.CYAN}Step 5: Verifying fixes...{Style.RESET_ALL}")

        total_fixed = 0
        total_attempted = 0
        verification_results = {}

        for session in sessions:
            verification = aider_integration.verify_fixes(session, lint_runner, analyzer)
            verification_results[session.session_id] = verification
            total_fixed += verification["errors_fixed"]
            total_attempted += verification["total_original_errors"]

        # Print detailed verification results
        print_verification_summary(verification_results)

        # Update community learning with actual fix results
        if community_learning:
            # Create fix results mapping for community learning
            fix_results = {}
            for session in sessions:
                verification = verification_results[session.session_id]
                for result in session.results:
                    error_key = (
                        f"{result.error.file_path}:{result.error.line}:{result.error.rule_id}"
                    )
                    fix_results[error_key] = result.success

            # Update community learning with actual results
            community_learning.update_fix_results(fix_results)

            # Generate and save community feedback
            feedback = community_learning.generate_learning_feedback()
            community_learning.save_community_data()

            print(f"\n{Fore.CYAN}🌍 Community Learning Summary:{Style.RESET_ALL}")
            print(f"   Total attempts: {feedback['total_attempts']}")
            print(f"   Successful overrides: {feedback['successful_overrides']}")
            print(f"   Failed overrides: {feedback['failed_overrides']}")
            if feedback["classification_improvements"]:
                print(
                    f"   Classification improvements identified: {len(feedback['classification_improvements'])}"
                )

            # Integrate community issue reporting
            integrate_community_issue_reporting(community_learning, community_learning.manual_attempts)

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
        print(f"\n{c('YELLOW')}⚠️  Interrupted by user{s('RESET_ALL')}")
        return 1
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n{c('RED')}❌ Error: {e}{s('RESET_ALL')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
