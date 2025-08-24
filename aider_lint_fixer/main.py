"""
Main Module for Aider Lint Fixer
This module provides the command-line interface and orchestrates the entire
lint detection and fixing workflow.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from colorama import Fore, Style, init

from . import __version__
from .aider_integration import AiderIntegration
from .community_issue_reporter import integrate_community_issue_reporting
from .config_manager import ConfigManager
from .context_manager import ContextManager
from .cost_monitor import BudgetLimits, CostModel, CostMonitor
from .enhanced_interactive import (
    CommunityLearningIntegration,
    enhanced_interactive_mode,
    integrate_with_error_analyzer,
)
from .error_analyzer import ErrorAnalyzer
from .lint_runner import LintRunner
from .pre_lint_assessment import PreLintAssessor, display_risk_assessment
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
    banner = """
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
    languages = ", ".join(project_info.languages) if project_info.languages else "None detected"
    print(f"   Languages: {languages}")

    package_managers = (
        ", ".join(project_info.package_managers)
        if project_info.package_managers
        else "None detected"
    )
    print(f"   Package Managers: {package_managers}")

    lint_configs = (
        ", ".join(project_info.lint_configs.keys())
        if project_info.lint_configs
        else "None detected"
    )
    print(f"   Lint Configs: {lint_configs}")
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
                    f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings "
                    f"(baseline: {baseline_error_count} errors, {baseline_warning_count} warnings)"
                )
            else:
                print(f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings")
        else:
            print(f"   {status} {linter_name}: {error_count} errors, {warning_count} warnings")
    if baseline_total and baseline_total != total_errors:
        print(f"\n   Processing Total: {total_errors} errors, {total_warnings} warnings")
        print(
            f"   Baseline Total: {baseline_total} errors (showing "
            f"{total_errors / baseline_total * 100:.1f}% of all errors)"
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
            print("      🎯 Errors Attempted:")
            for i, error_analysis in enumerate(
                session.errors_to_fix[:5]
            ):  # Show first 5 attempted errors
                error = error_analysis.error
                print(
                    f"         {i + 1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
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
        errors_fixed = result["errors_fixed"]
        total_errors = result["total_original_errors"]
        print(
            f"   📄 Session {session_id[:8]}: {errors_fixed}/{total_errors} "
            f"fixed ({success_rate:.1f}%)"
        )
        # Show detailed information about what was fixed
        if result["fixed_errors"]:
            print("      ✅ Successfully Fixed:")
            for i, error in enumerate(result["fixed_errors"][:5]):  # Show first 5 fixed errors
                print(
                    f"         {i + 1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
                )
            if len(result["fixed_errors"]) > 5:
                print(f"         ... and {len(result['fixed_errors']) - 5} more")
        # Show remaining errors if any
        if result["remaining_errors"]:
            print("      ❌ Still Present:")
            for i, error in enumerate(
                result["remaining_errors"][:3]
            ):  # Show first 3 remaining errors
                print(
                    f"         {i + 1}. {error.linter} {error.rule_id}: {error.message} (line {error.line})"
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
@click.option(
    "--loop",
    is_flag=True,
    help="Iterative mode: run force mode in intelligent loops until convergence or diminishing returns detected",
)
@click.option(
    "--max-iterations",
    type=int,
    default=10,
    help="Maximum iterations for loop mode (default: 10)",
)
@click.option(
    "--improvement-threshold",
    type=float,
    default=5.0,
    help="Minimum improvement percentage to continue looping (default: 5.0%)",
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
    "--enable-enhanced-analysis",
    is_flag=True,
    help="Enable research-based enhanced strategic analysis (experimental)",
)
@click.option(
    "--quantify-debt",
    is_flag=True,
    help="Quantify technical debt using SQALE methodology",
)
@click.option(
    "--predict-outcomes",
    is_flag=True,
    help="Use ML-based prediction for fix success probability",
)
@click.option(
    "--export-for-llm",
    help="Export structured data for external LLM analysis (claude, gpt4, etc.)",
)
@click.option(
    "--chaos-dimensions",
    default="basic",
    help="Chaos analysis depth: basic, enhanced, all (default: basic)",
)
@click.option(
    "--export-cross-communication",
    help="Export for external LLM cross-communication analysis (claude, gpt4, o1)",
)
@click.option(
    "--import-llm-response",
    help="Import and process external LLM response file",
)
@click.option(
    "--enable-file-relationships",
    is_flag=True,
    help="Enable detailed file relationship analysis for external LLMs",
)
@click.option(
    "--read-cot-analysis",
    help="Read and enhance existing COT analysis file (path to .md file)",
)
@click.option(
    "--update-cot-framework",
    is_flag=True,
    help="Update COT analysis with enhanced framework capabilities",
)
@click.option(
    "--export-structured-format",
    help="Export structured format for external LLM processing (claude, gpt4, o1)",
)
@click.option(
    "--process-llm-fixes",
    help="Process external LLM response with applied fixes (path to response JSON)",
)
@click.option(
    "--skip-pre-lint-assessment",
    is_flag=True,
    help="Skip pre-lint risk assessment and proceed directly to linting",
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
@click.option(
    "--use-architect-mode",
    is_flag=True,
    help="Use architect mode for dangerous error types (no-undef, etc.)",
)
@click.option(
    "--architect-model",
    help="Model to use for architect reasoning (e.g., o1-mini, claude-3-5-sonnet)",
)
@click.option(
    "--editor-model",
    help="Model to use for file editing in architect mode (e.g., gpt-4o)",
)
@click.option(
    "--architect-only",
    is_flag=True,
    help="Only run architect mode for dangerous errors, skip safe automation",
)
@click.option(
    "--max-cost",
    type=float,
    default=100.0,
    help="Maximum total cost budget for AI operations (default: $100.00)",
)
@click.option(
    "--max-iteration-cost",
    type=float,
    default=20.0,
    help="Maximum cost per iteration in loop mode (default: $20.00)",
)
@click.option(
    "--ai-model",
    type=click.Choice(
        [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
        ]
    ),
    default="gpt-4-turbo",
    help="AI model to use for cost calculations (default: gpt-4-turbo)",
)
@click.option(
    "--show-cost-prediction",
    is_flag=True,
    help="Show cost predictions before starting operations",
)
# Smart Linter Selection Options
@click.option(
    "--smart-linter-selection/--no-smart-linter-selection",
    default=True,
    help="Enable/disable smart linter selection (default: enabled)",
)
@click.option(
    "--max-linter-time",
    type=float,
    help="Maximum time budget for linters in seconds (smart selection only)",
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.7,
    help="Minimum confidence threshold for linter selection (0.0-1.0, default: 0.7)",
)
# DAG Workflow Options
@click.option(
    "--dag-workflow/--no-dag-workflow",
    default=True,
    help="Enable/disable DAG workflow parallel execution (default: enabled)",
)
@click.option(
    "--max-workers",
    type=int,
    default=4,
    help="Maximum number of parallel workers for DAG execution (default: 4)",
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
    loop: bool,
    max_iterations: int,
    improvement_threshold: float,
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
    enable_enhanced_analysis: bool,
    quantify_debt: bool,
    predict_outcomes: bool,
    export_for_llm: Optional[str],
    chaos_dimensions: str,
    export_cross_communication: Optional[str],
    import_llm_response: Optional[str],
    enable_file_relationships: bool,
    read_cot_analysis: Optional[str],
    update_cot_framework: bool,
    export_structured_format: Optional[str],
    process_llm_fixes: Optional[str],
    skip_pre_lint_assessment: bool,
    resume_session: Optional[str],
    list_sessions: bool,
    use_architect_mode: bool,
    architect_model: Optional[str],
    editor_model: Optional[str],
    architect_only: bool,
    max_cost: float,
    max_iteration_cost: float,
    ai_model: str,
    show_cost_prediction: bool,
    # Smart Linter Selection Parameters
    smart_linter_selection: bool,
    max_linter_time: Optional[float],
    confidence_threshold: float,
    # DAG Workflow Parameters
    dag_workflow: bool,
    max_workers: int,
):
    """Aider Lint Fixer - Automated lint error detection and fixing.
    PROJECT_PATH: Path to the project directory (default: current directory)
    """

    # Set up color helpers for this function
    def c(color_attr):
        return get_color(color_attr, no_color)

    def s(style_attr):
        return get_style(style_attr, no_color)

    # Define actual_project_path early for use in all command handlers
    if target_dir:
        actual_project_path = str(Path(project_path) / target_dir)
    else:
        actual_project_path = project_path
    # Validate loop mode parameters
    if loop and not force:
        print(f"{Fore.RED}❌ Error: --loop requires --force mode{Style.RESET_ALL}")
        print("   Loop mode runs iterative force fixing until convergence")
        return 1
    if loop:
        if max_iterations < 1:
            print(f"{Fore.RED}❌ Error: --max-iterations must be at least 1{Style.RESET_ALL}")
            return 1
        if improvement_threshold < 0:
            print(
                f"{Fore.RED}❌ Error: --improvement-threshold must be non-negative{Style.RESET_ALL}"
            )
            return 1
    # Handle version flag
    if version:
        print(f"aider-lint-fixer {__version__}")
        return
    # Handle list-linters flag
    if list_linters:
        import platform

        from .project_detector import ProjectDetector as LocalProjectDetector
        from .supported_versions import (
            get_platform_compatibility_info,
            get_supported_linters,
        )

        # Get project info for availability detection
        project_detector = LocalProjectDetector()
        project_info = project_detector.detect_project(project_path)

        # Create lint runner to check actual availability
        lint_runner = LintRunner(project_info)

        # Get static list of supported linters
        static_linters_list = get_supported_linters()

        # Check actual availability
        available_linters = lint_runner._detect_available_linters(static_linters_list)

        # Separate available and unavailable linters
        actually_available = [
            linter for linter, available in available_linters.items() if available
        ]
        unavailable = [linter for linter, available in available_linters.items() if not available]

        compatibility_info = get_platform_compatibility_info()

        if output_format == "json":
            import json

            output_data = {
                "available_linters": actually_available,
                "unavailable_linters": unavailable,
                "platform": platform.system(),
                "platform_notes": compatibility_info,
            }
            print(json.dumps(output_data, indent=2))
        else:
            print(f"Available linters on {platform.system()}:")
            for linter in actually_available:
                print(f"  ✅ {linter}")

            if unavailable:
                print("\nUnavailable linters (not installed):")
                for linter in unavailable:
                    print(f"  ❌ {linter}")

            # Show platform compatibility notes if any
            if compatibility_info:
                print("\nPlatform compatibility notes:")
                for linter, note in compatibility_info.items():
                    print(f"  ⚠️  {linter}: {note}")
            print(
                f"\nTotal: {len(actually_available)} linters available, {len(unavailable)} unavailable"
            )
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
            print("\n💡 Resume with: --resume-session <session_id>")
        return 0
    # Handle cross-communication export
    if export_cross_communication:
        print(
            f"\n{Fore.CYAN}🔄 Cross-Communication Export for {export_cross_communication.upper()}{Style.RESET_ALL}"
        )
        try:
            from .external_llm_integration import ExternalLLMIntegrationFramework

            # Create mock dangerous errors for demonstration
            mock_dangerous_errors = {
                "src/mcp-server.mjs": [
                    {"message": "'HttpServerTransport' is not defined", "line": 15},
                    {"message": "'app' is not defined", "line": 25},
                    {"message": "'mcpServer' is not defined", "line": 35},
                ],
                "src/controller/edit.js": [{"message": "'fieldName' is not defined", "line": 12}],
            }
            # Create mock file analyses
            mock_file_analyses = {
                "src/mcp-server.mjs": type("MockAnalysis", (), {"error_analyses": []})(),
                "src/controller/edit.js": type("MockAnalysis", (), {"error_analyses": []})(),
                "src/controller/list.js": type("MockAnalysis", (), {"error_analyses": []})(),
                "src/main.js": type("MockAnalysis", (), {"error_analyses": []})(),
            }
            integration_framework = ExternalLLMIntegrationFramework(str(actual_project_path))
            export_file = integration_framework.export_for_external_analysis(
                mock_dangerous_errors, mock_file_analyses, export_cross_communication
            )
            print(f"   ✅ Export created: {export_file}")
            print(f"   📝 Prompt file created for {export_cross_communication.upper()} analysis")
            print("   🔄 Send the export to external LLM for analysis")
            print("   📥 Use --import-llm-response to process the response")
        except Exception as e:
            print(f"   ❌ Export failed: {e}")
        return 0
    # Handle LLM response import
    if import_llm_response:
        print(f"\n{Fore.CYAN}📥 Importing External LLM Response{Style.RESET_ALL}")
        try:
            from .external_llm_integration import ExternalLLMIntegrationFramework

            integration_framework = ExternalLLMIntegrationFramework(str(actual_project_path))
            response = integration_framework.import_external_response(import_llm_response)
            processing_result = integration_framework.process_external_feedback(response)
            print(f"   🤖 Analysis ID: {response.analysis_id}")
            print(f"   📊 Confidence Score: {response.confidence_score:.0%}")
            print(f"   🔧 LLM Model: {response.llm_model}")
            print("\n📊 Processing Results:")
            print(
                f"   ✅ High-confidence automated fixes: {processing_result['confidence_metrics']['high_confidence_fixes']}"
            )
            print(
                f"   ⚠️  Medium-confidence fixes: {processing_result['confidence_metrics']['medium_confidence_fixes']}"
            )
            print(
                f"   🔍 Manual review required: {len(processing_result['manual_review_required'])}"
            )
            if processing_result["automated_fixes_ready"]:
                print("\n🚀 Automated Fixes Applied:")
                for fix in processing_result["automated_fixes_ready"]:
                    print(
                        f"   ✅ {fix.get('fix_type', 'Fix')}: {fix.get('fix_content', 'Applied')[:60]}..."
                    )
            if processing_result["manual_review_required"]:
                print("\n🔍 Manual Review Required:")
                for item in processing_result["manual_review_required"]:
                    print(f"   📁 {item.get('file_path', 'Unknown file')}")
                    print(f"   🔍 {item.get('issue', 'Review needed')}")
            if processing_result["architectural_insights"]:
                print("\n🏗️  Architectural Insights:")
                for insight in processing_result["architectural_insights"]:
                    print(f"   💡 {insight.get('pattern', 'Pattern identified')}")
        except Exception as e:
            print(f"   ❌ Import failed: {e}")
        return 0
    # Handle COT analysis reading and enhancement
    if read_cot_analysis:
        print(f"\n{Fore.CYAN}📖 Reading COT Analysis File{Style.RESET_ALL}")
        try:
            from .cot_analysis_framework import COTAnalysisFramework

            if not Path(read_cot_analysis).exists():
                print(f"   ❌ COT analysis file not found: {read_cot_analysis}")
                return 1
            framework = COTAnalysisFramework(str(actual_project_path))
            print(f"   📄 Reading: {read_cot_analysis}")
            cot_analysis = framework.read_cot_analysis_file(read_cot_analysis)
            print("   📊 Analysis Summary:")
            print(f"      Total dangerous files: {cot_analysis.total_dangerous_files}")
            print(f"      Dangerous errors: {cot_analysis.dangerous_errors_count}")
            print(f"      Variables analyzed: {len(cot_analysis.variables)}")
            if update_cot_framework:
                print("\n🔧 Enhancing with Framework Capabilities...")
                enhanced_analysis = framework.enhance_cot_analysis(cot_analysis)
                # Export enhanced analysis
                json_file = framework.export_enhanced_analysis(enhanced_analysis)
                markdown_file = framework.create_updated_cot_file(enhanced_analysis)
                print(f"   ✅ Enhanced JSON exported: {json_file}")
                print(f"   ✅ Enhanced markdown created: {markdown_file}")
                # Show automation recommendations
                auto_recs = enhanced_analysis["automation_recommendations"]
                print("\n🤖 Automation Recommendations:")
                print(
                    f"   ✅ Safe for automation: {len(auto_recs['safe_for_automation'])} variables"
                )
                print(f"   ⚠️  Review needed: {len(auto_recs['review_needed'])} variables")
                print(f"   🔍 Manual only: {len(auto_recs['manual_only'])} variables")
                if auto_recs["safe_for_automation"]:
                    print("\n✅ Safe Automation Candidates:")
                    for item in auto_recs["safe_for_automation"]:
                        print(
                            f"      {item['variable']} ({item['file']}) - {item['confidence']:.0%} confidence"
                        )
                if auto_recs["review_needed"]:
                    print("\n⚠️  Review Needed:")
                    for item in auto_recs["review_needed"]:
                        print(
                            f"      {item['variable']} ({item['file']}) - {item['review_reason']}"
                        )
                # Show external LLM export readiness
                export_data = enhanced_analysis["external_llm_export"]
                print("\n🔄 External LLM Export Ready:")
                print(
                    f"   High confidence: {len(export_data['high_confidence_variables'])} variables"
                )
                print(
                    f"   Medium confidence: {len(export_data['medium_confidence_variables'])} variables"
                )
                print(
                    f"   Low confidence: {len(export_data['low_confidence_variables'])} variables"
                )
            else:
                print("\n💡 Use --update-cot-framework to enhance with framework capabilities")
                # Show basic analysis
                print("\n📋 Variables Found:")
                for var in cot_analysis.variables:
                    print(
                        f"   {var.name} ({var.file_name}) - {var.likely_type} ({var.confidence_level:.0%} confidence)"
                    )
        except Exception as e:
            print(f"   ❌ COT analysis failed: {e}")
            return 1
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
        # Print startup information with target directory if specified
        print(f"{c('GREEN')}🚀 Starting Aider Lint Fixer{s('RESET_ALL')}")
        print(f"   Project: {Path(project_path).resolve()}")
        if target_dir:
            print(f"   Target Directory: {target_dir}")
            print(f"   Actual Path: {Path(actual_project_path).resolve()}")
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
                # Enhanced analysis if requested
                if enable_enhanced_analysis or quantify_debt or predict_outcomes or export_for_llm:
                    print(
                        f"\n{Fore.CYAN}🔬 Enhanced Strategic Analysis (Research-Based){Style.RESET_ALL}"
                    )
                    preflight_result = checker.run_enhanced_preflight_check(
                        force_recheck=force_strategic_recheck,
                        enable_enhanced_analysis=enable_enhanced_analysis,
                        quantify_debt=quantify_debt,
                        predict_outcomes=predict_outcomes,
                        export_for_llm=export_for_llm,
                        chaos_dimensions=chaos_dimensions,
                    )
                else:
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
        # Initialize assessment variable for architect mode
        assessment = None
        # Pre-Lint Risk Assessment (unless bypassed, but run in force mode for tracing)
        if (not check_only and not skip_pre_lint_assessment) or force:
            if force:
                print(
                    f"\n{Fore.CYAN}🔍 Pre-Lint Risk Assessment (for undefined variable tracing)...{Style.RESET_ALL}"
                )
            else:
                print(f"\n{Fore.CYAN}🔍 Pre-Lint Risk Assessment...{Style.RESET_ALL}")
            try:
                assessor = PreLintAssessor(actual_project_path)
                # Convert linters string to list if needed
                linters_list = (
                    [linter.strip() for linter in linters.split(",")]
                    if linters
                    else ["eslint", "flake8"]
                )
                assessment = assessor.assess_project(linters_list)
                if not force:
                    # Display assessment and get user decision (only if not force mode)
                    should_proceed = display_risk_assessment(assessment)
                    if not should_proceed:
                        print(
                            f"\n{Fore.YELLOW}⚠️  Lint fixing cancelled by user based on risk assessment.{Style.RESET_ALL}"
                        )
                        print(
                            f"{Fore.CYAN}💡 Consider using --check-only to preview changes first.{Style.RESET_ALL}"
                        )
                        return
                else:
                    # In force mode, just collect the assessment data for tracing
                    print("   ✅ Assessment completed (force mode - proceeding regardless)")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Pre-lint assessment failed: {e}{Style.RESET_ALL}")
                if not force:
                    print(f"{Fore.CYAN}💡 Proceeding with caution...{Style.RESET_ALL}")
                assessment = None  # Ensure assessment is None if failed
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
            enabled_linters = [linter.strip() for linter in linters.split(",")]
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
        print("   📊 Running baseline scan to establish error count...")
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
        print("   🔍 Running processing scan...")
        results = lint_runner.run_all_available_linters(enabled_linters, **linter_options)
        # Handle output format
        if output_format == "json":
            import json

            json_results = {}
            for linter, result in results.items():
                json_results[linter] = {
                    "errors": [
                        {
                            "file": e.file,
                            "line": e.line,
                            "message": e.message,
                            "rule_id": e.rule_id,
                        }
                        for e in result.errors
                    ],
                    "warnings": [
                        {
                            "file": w.file,
                            "line": w.line,
                            "message": w.message,
                            "rule_id": w.rule_id,
                        }
                        for w in result.warnings
                    ],
                }
            print(json.dumps(json_results, indent=2))
        else:
            print_lint_summary(
                results,
                baseline_results=baseline_results,
                baseline_total=baseline_total_errors,
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
        analyzer = ErrorAnalyzer(project_path=str(project_info.root_path))
        file_analyses = analyzer.analyze_errors(results)
        # Check for structural problems and display insights
        if analyzer.has_structural_problems():
            structural_analysis = analyzer.get_structural_analysis()
            print(f"\n{Fore.YELLOW}🏗️  STRUCTURAL ANALYSIS RESULTS{Style.RESET_ALL}")
            print(f"   Architectural Score: {structural_analysis.architectural_score:.1f}/100")
            print(f"   Structural Issues: {len(structural_analysis.structural_issues)}")
            print(f"   Hotspot Files: {len(structural_analysis.hotspot_files)}")
            print(f"   Refactoring Candidates: {len(structural_analysis.refactoring_candidates)}")
            # Display key recommendations
            recommendations = analyzer.get_structural_recommendations()
            if recommendations:
                print(f"\n{Fore.CYAN}📋 Structural Recommendations:{Style.RESET_ALL}")
                for rec in recommendations[:5]:  # Show top 5 recommendations
                    print(f"   • {rec}")
                if len(recommendations) > 5:
                    print(f"   ... and {len(recommendations) - 5} more recommendations")
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
                all_error_analyses,
                max_errors=max_errors,
                enable_community_learning=True,
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
                        "FileAnalysis",
                        (),
                        {"error_analyses": [], "file_path": file_path},
                    )()
                selected_file_analyses[file_path].error_analyses.append(error_analysis)
            file_analyses = selected_file_analyses
            prioritized_errors = errors_to_fix
            print(f"\n{Fore.CYAN}📋 Enhanced Interactive Summary:{Style.RESET_ALL}")
            print(f"   Selected {len(prioritized_errors)} errors for fixing")
        elif force:
            if loop:
                # Iterative Intelligent Force Mode
                print(f"\n{Fore.CYAN}🔄 ITERATIVE INTELLIGENT FORCE MODE ENABLED{Style.RESET_ALL}")
                print(
                    f"   {Fore.YELLOW}Running force mode in intelligent loops until convergence{Style.RESET_ALL}"
                )
                print(f"   Max iterations: {max_iterations}")
                print(f"   Improvement threshold: {improvement_threshold}%")
                # Initialize cost monitoring and context management
                budget_limits = BudgetLimits(
                    max_total_cost=max_cost, max_iteration_cost=max_iteration_cost
                )
                cost_monitor = CostMonitor(actual_project_path, budget_limits)
                context_manager = ContextManager(max_tokens=8000, target_tokens=6000)
                # Set AI model for cost calculations
                model_mapping = {
                    "gpt-4": CostModel.GPT_4,
                    "gpt-4-turbo": CostModel.GPT_4_TURBO,
                    "gpt-3.5-turbo": CostModel.GPT_3_5_TURBO,
                    "claude-3-opus": CostModel.CLAUDE_3_OPUS,
                    "claude-3-sonnet": CostModel.CLAUDE_3_SONNET,
                    "claude-3-haiku": CostModel.CLAUDE_3_HAIKU,
                }
                cost_monitor.set_model(model_mapping.get(ai_model, CostModel.GPT_4_TURBO))
                # Show cost prediction if requested
                if show_cost_prediction:
                    total_errors = sum(
                        len(analysis.error_analyses) for analysis in file_analyses.values()
                    )
                    estimated_tokens_per_error = 500  # Conservative estimate
                    estimated_total_tokens = (
                        total_errors * estimated_tokens_per_error * max_iterations
                    )
                    # Rough cost estimation
                    pricing = cost_monitor.MODEL_PRICING[cost_monitor.current_model]
                    estimated_cost = (
                        (estimated_total_tokens / 1000) * (pricing["input"] + pricing["output"]) / 2
                    )
                    print(f"\n{Fore.CYAN}💰 COST PREDICTION{Style.RESET_ALL}")
                    print(f"   Model: {ai_model}")
                    print(f"   Estimated total cost: ${estimated_cost:.2f}")
                    print(f"   Budget limit: ${max_cost:.2f}")
                    print(f"   Per-iteration limit: ${max_iteration_cost:.2f}")
                    if estimated_cost > max_cost:
                        print(f"   {Fore.YELLOW}⚠️  Estimated cost exceeds budget!{Style.RESET_ALL}")
                # Import iterative force mode
                try:
                    from .iterative_force_mode import (
                        IterativeForceMode,
                    )

                    iterative_mode = IterativeForceMode(
                        actual_project_path, cost_monitor, context_manager
                    )
                    iterative_mode.max_iterations = max_iterations
                    iterative_mode.improvement_threshold = improvement_threshold
                    # Run iterative loop
                    iteration = 1
                    continue_loop = True
                    while continue_loop and iteration <= max_iterations:
                        print(f"\n{Fore.CYAN}🔄 ITERATION {iteration}{Style.RESET_ALL}")
                        print("=" * 50)
                        # Run single force iteration (this will be the existing force mode logic)

                        # Store the force mode logic result for this iteration
                        # (The existing force mode logic will continue below)
                        break  # Exit to run existing force mode logic once
                except ImportError:
                    print(
                        f"\n{Fore.YELLOW}⚠️  Iterative mode not available, falling back to single force mode{Style.RESET_ALL}"
                    )
                    loop = False  # Disable loop mode
            if not loop:
                # Single Intelligent Force Mode
                print(f"\n{Fore.CYAN}🧠 INTELLIGENT FORCE MODE ENABLED{Style.RESET_ALL}")
                print(
                    f"   {Fore.YELLOW}Using ML to safely manage force mode for chaotic codebases{Style.RESET_ALL}"
                )
            # Get ALL errors for force mode analysis
            all_error_analyses = []
            for file_path, analysis in file_analyses.items():
                all_error_analyses.extend(analysis.error_analyses)
            if not all_error_analyses:
                print(f"\n{Fore.GREEN}✅ No errors found!{Style.RESET_ALL}")
                return 0
            # Initialize Intelligent Force Mode
            try:
                from .intelligent_force_mode import IntelligentForceMode

                intelligent_force = IntelligentForceMode(actual_project_path)
                # Analyze force strategy using ML
                print(
                    f"\n{Fore.CYAN}🔍 Analyzing {len(all_error_analyses)} errors with ML...{Style.RESET_ALL}"
                )
                force_strategy = intelligent_force.analyze_force_strategy(all_error_analyses)
                # Display intelligent force strategy
                print(f"\n{Fore.CYAN}🧠 INTELLIGENT FORCE STRATEGY{Style.RESET_ALL}")
                print("=" * 60)
                if force_strategy["is_chaotic"]:
                    print(f"{Fore.YELLOW}🏥 CHAOTIC CODEBASE DETECTED{Style.RESET_ALL}")
                    print(f"   Total errors: {force_strategy['total_errors']}")
                else:
                    print(f"{Fore.GREEN}📊 MANAGEABLE CODEBASE{Style.RESET_ALL}")
                    print(f"   Total errors: {force_strategy['total_errors']}")
                # Show action breakdown
                breakdown = force_strategy["action_breakdown"]
                print("\n📊 ML-Powered Action Plan:")
                if breakdown.get("auto_force", 0) > 0:
                    print(f"   🤖 Auto-force (no confirmation): {breakdown['auto_force']} errors")
                if breakdown.get("batch_confirm", 0) > 0:
                    print(f"   📦 Batch confirmation: {breakdown['batch_confirm']} errors")
                if breakdown.get("manual_review", 0) > 0:
                    print(f"   👤 Manual review required: {breakdown['manual_review']} errors")
                if breakdown.get("skip", 0) > 0:
                    print(f"   ⏭️  Skip (too risky): {breakdown['skip']} errors")
                print(f"\n⏱️  Estimated time: {force_strategy['estimated_time_minutes']} minutes")
                # Show recommendations
                if force_strategy["recommendations"]:
                    print("\n💡 ML Recommendations:")
                    for rec in force_strategy["recommendations"]:
                        print(f"   {rec}")
                # Show batch plans
                batch_plans = force_strategy["batch_plans"]
                if len(batch_plans) > 1:
                    print("\n📦 Batch Execution Plan:")
                    for batch in batch_plans:
                        if batch.batch_id == 0:
                            print(
                                f"   Batch 0 (Auto-Force): {len(batch.errors)} errors - {batch.risk_level} risk"
                            )
                        else:
                            print(
                                f"   Batch {batch.batch_id}: {len(batch.errors)} errors - {batch.risk_level} risk - {batch.estimated_time}min"
                            )
                # Get user confirmation for the strategy
                auto_force_count = breakdown.get("auto_force", 0)
                batch_count = breakdown.get("batch_confirm", 0)
                manual_count = breakdown.get("manual_review", 0)
                if auto_force_count > 0:
                    print(
                        f"\n{Fore.GREEN}🤖 {auto_force_count} high-confidence errors will be fixed automatically{Style.RESET_ALL}"
                    )
                if batch_count > 0 or manual_count > 0:
                    confirm_msg = "Proceed with intelligent force strategy?"
                    if not click.confirm(confirm_msg):
                        print("Aborted by user.")
                        return 0
                # Execute the intelligent force strategy
                prioritized_errors = []
                # Add auto-force errors (these will be processed without individual confirmation)
                auto_force_decisions = [
                    d for d in force_strategy["force_decisions"] if d.action == "auto_force"
                ]
                prioritized_errors.extend([d.error_analysis for d in auto_force_decisions])
                # Add batch-confirm errors (these will be processed in batches)
                batch_decisions = [
                    d for d in force_strategy["force_decisions"] if d.action == "batch_confirm"
                ]
                prioritized_errors.extend([d.error_analysis for d in batch_decisions])
                # Apply max_errors limit if specified
                if max_errors:
                    prioritized_errors = prioritized_errors[:max_errors]
                # Rebuild file_analyses with prioritized errors
                force_file_analyses = {}
                for error_analysis in prioritized_errors:
                    file_path = error_analysis.error.file_path
                    if file_path not in force_file_analyses:
                        force_file_analyses[file_path] = type(
                            "FileAnalysis",
                            (),
                            {"error_analyses": [], "file_path": file_path},
                        )()
                    force_file_analyses[file_path].error_analyses.append(error_analysis)
                file_analyses = force_file_analyses
                print(f"\n{Fore.GREEN}✅ Intelligent force strategy activated{Style.RESET_ALL}")
                print(f"   Processing {len(prioritized_errors)} prioritized errors")
                # Store force strategy for later use during fixing
                globals()["_intelligent_force_strategy"] = force_strategy
            except ImportError:
                print(
                    f"\n{Fore.YELLOW}⚠️  Intelligent force mode not available, falling back to basic force mode{Style.RESET_ALL}"
                )
                # Fall back to original force mode logic
                prioritized_errors = (
                    all_error_analyses[:max_errors] if max_errors else all_error_analyses
                )
                # Basic confirmation
                warning_msg = f"\n{Fore.RED}Are you sure you want to force-fix {len(prioritized_errors)} errors? This may cause issues.{Style.RESET_ALL}"
                print(warning_msg)
                if not click.confirm("Proceed with basic force mode?"):
                    print("Aborted by user.")
                    return 0
        elif not prioritized_errors:
            print(f"\n{Fore.YELLOW}⚠️  No automatically fixable errors found.{Style.RESET_ALL}")
            print("   💡 Try --enhanced-interactive to review and override classifications")
            print("   💡 Or use --force to attempt fixing all errors (risky)")
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
        # Step 4: Fix errors with hybrid workflow (safe automation + architect mode)
        print(f"\n{Fore.CYAN}Step 4: Fixing errors with aider.chat...{Style.RESET_ALL}")
        try:
            aider_integration = AiderIntegration(project_config, project_path, config_manager)
        except RuntimeError as e:
            print(f"{Fore.RED}❌ {e}{Style.RESET_ALL}")
            print("   Please install aider-chat: pip install aider-chat")
            return 1
        # Check if architect mode should be used
        architect_results = []
        if (
            use_architect_mode
            and hasattr(assessment, "architect_guidance")
            and assessment.architect_guidance
        ):
            guidance = assessment.architect_guidance
            if guidance.get("has_dangerous_errors"):
                print(f"\n{Fore.CYAN}🏗️  Architect Mode Phase:{Style.RESET_ALL}")
                print("   Dangerous errors detected - using architect mode for manual review")
                # Execute architect mode for dangerous errors
                architect_results = aider_integration.execute_architect_guidance(
                    guidance, architect_model=architect_model, editor_model=editor_model
                )
                # If architect-only mode, skip regular automation
                if architect_only:
                    print(
                        f"\n{Fore.CYAN}🏗️  Architect-only mode: Skipping safe automation{Style.RESET_ALL}"
                    )
                    # Show architect mode summary
                    successful_architect = sum(1 for r in architect_results if r.success)
                    print(f"\n{Fore.GREEN}🎉 Architect Mode Complete!{Style.RESET_ALL}")
                    print(f"   Files processed: {len(architect_results)}")
                    print(f"   Successful fixes: {successful_architect}")
                    return 0 if successful_architect > 0 else 1
            else:
                print(
                    f"\n{Fore.CYAN}ℹ️  No dangerous errors found - proceeding with standard automation{Style.RESET_ALL}"
                )
        elif use_architect_mode:
            print(
                f"\n{Fore.YELLOW}⚠️  Architect mode requested but no risk assessment available{Style.RESET_ALL}"
            )
            print("   Run without --skip-pre-lint-assessment to enable architect mode")
        # Continue with standard/safe automation (unless architect-only mode)
        if not architect_only:
            print(f"\n{Fore.CYAN}🤖 Standard Automation Phase:{Style.RESET_ALL}")
            if (
                use_architect_mode
                and hasattr(assessment, "architect_guidance")
                and assessment.architect_guidance
            ):
                guidance = assessment.architect_guidance
                safe_plan = guidance.get("safe_automation_plan", {})
                if safe_plan:
                    safe_count = safe_plan.get("safe_errors_count", 0)
                    print(f"   Focusing on {safe_count} safe errors (excluding dangerous types)")
                else:
                    print("   Processing all errors with standard automation")
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
            project_path=project_path,
            total_errors=total_error_count,
            verbose=effective_verbose,
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
            integrate_community_issue_reporting(
                community_learning, community_learning.manual_attempts
            )
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
