#!/usr/bin/env python3
"""
Enhanced Interactive Mode Proposal

This demonstrates how we could enhance the interactive mode to allow users
to attempt fixing unfixable errors with proper warnings and confirmation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from aider_lint_fixer.error_analyzer import ErrorAnalysis, FixComplexity


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


def enhanced_interactive_mode(
    all_errors: List[ErrorAnalysis], max_errors: int = None
) -> List[InteractiveChoice]:
    """
    Enhanced interactive mode that allows users to override fixability classifications.

    Args:
        all_errors: All error analyses (both fixable and unfixable)
        max_errors: Maximum number of errors to process

    Returns:
        List of user choices for each error
    """
    import click
    from colorama import Fore, Style

    choices = []

    # Separate fixable and unfixable errors
    fixable_errors = [e for e in all_errors if e.fixable]
    unfixable_errors = [e for e in all_errors if not e.fixable]

    print(f"\n{Fore.CYAN}📋 Interactive Error Review{Style.RESET_ALL}")
    print(f"   Found {len(fixable_errors)} automatically fixable errors")
    print(f"   Found {len(unfixable_errors)} unfixable errors")
    print()

    # Process fixable errors first
    if fixable_errors:
        print(f"{Fore.GREEN}✅ Automatically Fixable Errors:{Style.RESET_ALL}")

        for i, error_analysis in enumerate(fixable_errors, 1):
            if max_errors and len(choices) >= max_errors:
                break

            error = error_analysis.error
            print(f"\n{i}. {error.file_path}:{error.line}")
            print(f"   {error.linter} {error.rule_id}: {error.message}")
            print(
                f"   Category: {error_analysis.category.value}, Complexity: {error_analysis.complexity.value}"
            )

            choice = click.prompt(
                "   Action",
                type=click.Choice(["fix", "skip", "abort"]),
                default="fix",
                show_default=True,
            )

            if choice == "abort":
                break

            choices.append(
                InteractiveChoice(
                    error_analysis=error_analysis,
                    choice=UserChoice(choice),
                    override_classification=False,
                )
            )

    # Process unfixable errors with warnings
    if unfixable_errors and (not max_errors or len(choices) < max_errors):
        print(
            f"\n{Fore.YELLOW}⚠️  Unfixable Errors (Manual Review Recommended):{Style.RESET_ALL}"
        )

        for i, error_analysis in enumerate(unfixable_errors, 1):
            if max_errors and len(choices) >= max_errors:
                break

            error = error_analysis.error
            print(f"\n{i}. {error.file_path}:{error.line}")
            print(f"   {error.linter} {error.rule_id}: {error.message}")
            print(
                f"   Category: {error_analysis.category.value}, Complexity: {error_analysis.complexity.value}"
            )

            # Show warning based on complexity
            if error_analysis.complexity == FixComplexity.MANUAL:
                print(
                    f"   {Fore.RED}⚠️  WARNING: This error requires manual intervention{Style.RESET_ALL}"
                )
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

            if choice == "abort":
                break

            override = choice == "try-fix"
            if override:
                # Additional confirmation for risky fixes
                if error_analysis.complexity in [
                    FixComplexity.MANUAL,
                    FixComplexity.COMPLEX,
                ]:
                    confirmed = click.confirm(
                        f"   {Fore.RED}⚠️  Are you sure you want to attempt this risky fix?{Style.RESET_ALL}",
                        default=False,
                    )
                    if not confirmed:
                        choice = "skip"
                        override = False

            choices.append(
                InteractiveChoice(
                    error_analysis=error_analysis,
                    choice=UserChoice("fix" if override else "skip"),
                    override_classification=override,
                )
            )

    return choices


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


def demonstrate_enhanced_interactive():
    """Demonstrate the enhanced interactive mode."""
    print("🎯 Enhanced Interactive Mode Demo")
    print("=" * 50)

    # This would be called from main.py like:
    # if enhanced_interactive:
    #     choices = enhanced_interactive_mode(all_error_analyses, max_errors)
    #     # Process only the errors user chose to fix
    #     errors_to_fix = [choice.error_analysis for choice in choices if choice.choice == UserChoice.FIX]

    print("Example workflow:")
    print("1. Show all errors (fixable + unfixable)")
    print("2. Let user choose per-error with warnings")
    print("3. Allow override with confirmation for risky fixes")
    print("4. Process only user-approved errors")
    print()
    print("Benefits:")
    print("✅ User has full control over what gets fixed")
    print("✅ Clear warnings about risks")
    print("✅ Can attempt 'unfixable' errors with oversight")
    print("✅ Conservative by default, permissive by choice")


if __name__ == "__main__":
    demonstrate_enhanced_interactive()
