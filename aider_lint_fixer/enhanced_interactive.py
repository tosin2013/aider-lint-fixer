"""
Enhanced Interactive Mode for Aider Lint Fixer

This module provides an enhanced interactive mode that allows users to:
1. Review each error individually with detailed information
2. Override fixability classifications with proper warnings
3. Feed back into the community learning system
4. Force-fix errors that are classified as unfixable
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import click
from colorama import Fore, Style

from .error_analyzer import ErrorAnalysis, FixComplexity
from .lint_runner import LintError


class UserChoice(Enum):
    """User choices for error fixing."""

    FIX = "fix"
    SKIP = "skip"
    ABORT = "abort"


@dataclass
class InteractiveChoice:
    """User's choice for a specific error."""

    error_analysis: ErrorAnalysis
    choice: UserChoice
    override_classification: bool = False
    user_confidence: int = 5  # 1-10 scale for community learning


@dataclass
class ManualFixAttempt:
    """Record of a manual fix attempt for community learning."""

    error: LintError
    original_classification: bool
    user_attempted: bool
    fix_successful: Optional[bool] = None
    fix_description: Optional[str] = None
    time_to_fix_minutes: Optional[int] = None
    user_confidence: int = 5


def enhanced_interactive_mode(
    all_errors: List[ErrorAnalysis],
    max_errors: Optional[int] = None,
    enable_community_learning: bool = True,
) -> List[InteractiveChoice]:
    """
    Enhanced interactive mode that allows users to override fixability classifications.

    Args:
        all_errors: All error analyses (both fixable and unfixable)
        max_errors: Maximum number of errors to process
        enable_community_learning: Whether to collect data for community learning

    Returns:
        List of user choices for each error
    """
    choices = []

    # Separate fixable and unfixable errors
    fixable_errors = [e for e in all_errors if e.fixable]
    unfixable_errors = [e for e in all_errors if not e.fixable]

    print(f"\n{Fore.CYAN}📋 Enhanced Interactive Error Review{Style.RESET_ALL}")
    print(f"   Found {len(fixable_errors)} automatically fixable errors")
    print(f"   Found {len(unfixable_errors)} unfixable errors")

    if enable_community_learning:
        print(
            f"   {Fore.GREEN}🌍 Community learning enabled - your choices help improve the system{Style.RESET_ALL}"
        )
    print()

    # Process fixable errors first
    if fixable_errors:
        print(f"{Fore.GREEN}✅ Automatically Fixable Errors:{Style.RESET_ALL}")

        for i, error_analysis in enumerate(fixable_errors, 1):
            if max_errors and len(choices) >= max_errors:
                break

            choice = _process_fixable_error(error_analysis, i, enable_community_learning)
            if choice.choice == UserChoice.ABORT:
                break
            choices.append(choice)

    # Process unfixable errors with warnings
    if unfixable_errors and (not max_errors or len(choices) < max_errors):
        print(f"\n{Fore.YELLOW}⚠️  Unfixable Errors (Manual Review Recommended):{Style.RESET_ALL}")

        for i, error_analysis in enumerate(unfixable_errors, 1):
            if max_errors and len(choices) >= max_errors:
                break

            choice = _process_unfixable_error(error_analysis, i, enable_community_learning)
            if choice.choice == UserChoice.ABORT:
                break
            choices.append(choice)

    return choices


def _process_fixable_error(
    error_analysis: ErrorAnalysis, index: int, enable_community_learning: bool
) -> InteractiveChoice:
    """Process a fixable error with user interaction."""
    error = error_analysis.error

    print(f"\n{index}. {Fore.GREEN}[FIXABLE]{Style.RESET_ALL} {error.file_path}:{error.line}")
    print(f"   {error.linter} {error.rule_id}: {error.message}")
    print(
        f"   Category: {error_analysis.category.value}, Complexity: {error_analysis.complexity.value}"
    )

    # Show confidence score if available
    if hasattr(error_analysis, "confidence_score"):
        print(f"   Confidence: {error_analysis.confidence_score:.1f}%")

    choice = click.prompt(
        "   Action", type=click.Choice(["fix", "skip", "abort"]), default="fix", show_default=True
    )

    user_confidence = 5
    if enable_community_learning and choice == "fix":
        user_confidence = click.prompt(
            "   How confident are you this will fix correctly? (1-10)",
            type=click.IntRange(1, 10),
            default=8,
            show_default=True,
        )

    return InteractiveChoice(
        error_analysis=error_analysis,
        choice=UserChoice(choice),
        override_classification=False,
        user_confidence=user_confidence,
    )


def _process_unfixable_error(
    error_analysis: ErrorAnalysis, index: int, enable_community_learning: bool
) -> InteractiveChoice:
    """Process an unfixable error with warnings and override options."""
    error = error_analysis.error

    print(f"\n{index}. {Fore.YELLOW}[UNFIXABLE]{Style.RESET_ALL} {error.file_path}:{error.line}")
    print(f"   {error.linter} {error.rule_id}: {error.message}")
    print(
        f"   Category: {error_analysis.category.value}, Complexity: {error_analysis.complexity.value}"
    )

    # Show warning based on complexity
    if error_analysis.complexity == FixComplexity.MANUAL:
        print(f"   {Fore.RED}⚠️  WARNING: This error requires manual intervention{Style.RESET_ALL}")
    elif error_analysis.complexity == FixComplexity.COMPLEX:
        print(
            f"   {Fore.YELLOW}⚠️  WARNING: This error is complex and may need domain knowledge{Style.RESET_ALL}"
        )

    print(
        f"   {Fore.CYAN}💡 Reason not fixable: {_get_unfixable_reason(error_analysis)}{Style.RESET_ALL}"
    )

    choice = click.prompt(
        "   Action",
        type=click.Choice(["try-fix", "skip", "abort"]),
        default="skip",
        show_default=True,
    )

    override = choice == "try-fix"
    user_confidence = 5

    if override:
        # Additional confirmation for risky fixes
        if error_analysis.complexity in [FixComplexity.MANUAL, FixComplexity.COMPLEX]:
            confirmed = click.confirm(
                f"   {Fore.RED}⚠️  Are you sure you want to attempt this risky fix?{Style.RESET_ALL}",
                default=False,
            )
            if not confirmed:
                choice = "skip"
                override = False

        if override and enable_community_learning:
            user_confidence = click.prompt(
                "   How confident are you this can be fixed? (1-10)",
                type=click.IntRange(1, 10),
                default=3,
                show_default=True,
            )

    return InteractiveChoice(
        error_analysis=error_analysis,
        choice=UserChoice("fix" if override else "skip"),
        override_classification=override,
        user_confidence=user_confidence,
    )


def _get_unfixable_reason(error_analysis: ErrorAnalysis) -> str:
    """Get human-readable reason why an error is not fixable."""
    error = error_analysis.error

    if error_analysis.complexity == FixComplexity.MANUAL:
        return "Requires manual code review and intervention"
    elif error_analysis.complexity == FixComplexity.COMPLEX:
        return "Complex logic that may require domain knowledge"
    elif "unsupported parameters" in error.message.lower():
        return "Module parameter error - needs API knowledge"
    elif "syntax error" in error.message.lower():
        return "Syntax error - may break functionality if auto-fixed"
    elif "template error" in error.message.lower():
        return "Template logic error - needs business context"
    else:
        return "Conservative classification - may be fixable with user oversight"


def create_manual_fix_attempt(choice: InteractiveChoice) -> ManualFixAttempt:
    """Create a ManualFixAttempt record from an InteractiveChoice."""
    return ManualFixAttempt(
        error=choice.error_analysis.error,
        original_classification=choice.error_analysis.fixable,
        user_attempted=choice.choice == UserChoice.FIX,
        user_confidence=choice.user_confidence,
    )


class CommunityLearningIntegration:
    """Integrates enhanced interactive mode with community learning system."""

    def __init__(self, project_root: str):
        """Initialize community learning integration."""
        self.project_root = project_root
        self.manual_attempts: List[ManualFixAttempt] = []

    def record_interactive_choices(self, choices: List[InteractiveChoice]) -> None:
        """Record user choices for community learning."""
        for choice in choices:
            attempt = create_manual_fix_attempt(choice)
            self.manual_attempts.append(attempt)

            # Log the choice for debugging
            print(
                f"   📝 Recorded choice: {choice.choice.value} for {choice.error_analysis.error.rule_id}"
            )

    def update_fix_results(self, fix_results: Dict[str, bool]) -> None:
        """Update manual fix attempts with actual results."""
        for attempt in self.manual_attempts:
            error_key = f"{attempt.error.file_path}:{attempt.error.line}:{attempt.error.rule_id}"
            if error_key in fix_results:
                attempt.fix_successful = fix_results[error_key]

                # Estimate fix time based on complexity
                if attempt.fix_successful:
                    if attempt.error.rule_id in ["yaml[trailing-spaces]", "yaml[line-length]"]:
                        attempt.time_to_fix_minutes = 1
                    elif "syntax" in attempt.error.message.lower():
                        attempt.time_to_fix_minutes = 10
                    else:
                        attempt.time_to_fix_minutes = 5

                print(f"   ✅ Updated result: {error_key} -> {attempt.fix_successful}")

    def generate_learning_feedback(self) -> Dict[str, any]:
        """Generate feedback for the learning system."""
        feedback = {
            "total_attempts": len(self.manual_attempts),
            "successful_overrides": 0,
            "failed_overrides": 0,
            "classification_improvements": [],
        }

        for attempt in self.manual_attempts:
            if attempt.override_classification and attempt.fix_successful is not None:
                if attempt.fix_successful:
                    feedback["successful_overrides"] += 1
                    # This error should be reclassified as fixable
                    feedback["classification_improvements"].append(
                        {
                            "linter": attempt.error.linter,
                            "rule_id": attempt.error.rule_id,
                            "message_pattern": attempt.error.message[:50],
                            "should_be_fixable": True,
                            "user_confidence": attempt.user_confidence,
                        }
                    )
                else:
                    feedback["failed_overrides"] += 1

        return feedback

    def save_community_data(self) -> None:
        """Save data for potential community contribution."""
        import json
        from pathlib import Path

        if not self.manual_attempts:
            return

        # Save to community learning cache
        cache_dir = Path(self.project_root) / ".aider-lint-cache"
        cache_dir.mkdir(exist_ok=True)

        community_file = cache_dir / "community_feedback.json"

        # Load existing data
        existing_data = []
        if community_file.exists():
            try:
                with open(community_file, "r") as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []

        # Add new attempts
        for attempt in self.manual_attempts:
            attempt_data = {
                "timestamp": str(datetime.now()),
                "file_path": attempt.error.file_path,
                "linter": attempt.error.linter,
                "rule_id": attempt.error.rule_id,
                "message": attempt.error.message,
                "original_classification": attempt.original_classification,
                "user_attempted": attempt.user_attempted,
                "fix_successful": attempt.fix_successful,
                "user_confidence": attempt.user_confidence,
                "time_to_fix_minutes": attempt.time_to_fix_minutes,
            }
            existing_data.append(attempt_data)

        # Save updated data
        with open(community_file, "w") as f:
            json.dump(existing_data, f, indent=2)

        print(f"   💾 Saved {len(self.manual_attempts)} community feedback records")


def integrate_with_error_analyzer(choices: List[InteractiveChoice], error_analyzer) -> None:
    """Integrate interactive choices with the error analyzer's learning system."""
    for choice in choices:
        if choice.choice == UserChoice.FIX:
            # This will be updated with actual results later
            error_analyzer.learn_from_fix_result(
                choice.error_analysis.error,
                fix_successful=True,  # Optimistic, will be corrected later
            )
