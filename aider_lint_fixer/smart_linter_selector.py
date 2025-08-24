"""
Smart Linter Selection Module

This module provides intelligent linter selection based on project characteristics.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set

from .project_detector import ProjectInfo

logger = logging.getLogger(__name__)


@dataclass
class LinterSelectionResult:
    """Result of smart linter selection."""

    recommended_linters: List[str] = field(default_factory=list)
    skipped_linters: List[str] = field(default_factory=list)
    reasoning: Dict[str, str] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    estimated_time_saved: float = 0.0


class SmartLinterSelector:
    """Intelligently selects appropriate linters based on project characteristics."""

    # Mapping of languages to their preferred linters
    LANGUAGE_LINTERS = {
        "python": ["flake8", "pylint", "black", "isort"],
        "javascript": ["eslint", "jshint", "prettier"],
        "typescript": ["eslint", "tslint", "prettier"],
        "yaml": ["ansible-lint"],
        "json": ["jsonlint"],
        "css": ["stylelint"],
        "html": ["htmlhint"],
        "shell": ["shellcheck"],
        "dockerfile": ["hadolint"],
    }

    # High-priority linters that should be included if available
    HIGH_PRIORITY_LINTERS = {
        "python": ["flake8"],
        "javascript": ["eslint"],
        "typescript": ["eslint"],
    }

    def __init__(self, project_info: ProjectInfo):
        """Initialize the smart linter selector.

        Args:
            project_info: Information about the project to analyze
        """
        self.project_info = project_info

    def select_linters(
        self,
        available_linters: Dict[str, bool],
        max_linters: int = 5,
        prefer_fast: bool = False,
    ) -> LinterSelectionResult:
        """Select the most appropriate linters for the project.

        Args:
            available_linters: Dict mapping linter names to availability
            max_linters: Maximum number of linters to select
            prefer_fast: Whether to prefer faster linters

        Returns:
            LinterSelectionResult with selected linters and reasoning
        """
        recommended = []
        skipped = []
        reasoning = {}

        # Get relevant linters based on detected languages
        relevant_linters = self._get_relevant_linters()

        # Priority order: high-priority first, then others
        prioritized_linters = self._prioritize_linters(relevant_linters, prefer_fast)

        for linter in prioritized_linters:
            if len(recommended) >= max_linters:
                skipped.append(linter)
                reasoning[linter] = f"Skipped: reached max limit of {max_linters} linters"
                continue

            if linter not in available_linters:
                skipped.append(linter)
                reasoning[linter] = "Skipped: linter not available in system"
                continue

            if not available_linters[linter]:
                skipped.append(linter)
                reasoning[linter] = "Skipped: linter installation failed or not found"
                continue

            recommended.append(linter)
            reasoning[linter] = self._get_selection_reason(linter)

        # If no linters were selected, try to include at least one basic linter
        if not recommended and available_linters:
            fallback_linters = ["flake8", "eslint", "pylint"]
            for linter in fallback_linters:
                if linter in available_linters and available_linters[linter]:
                    recommended.append(linter)
                    reasoning[linter] = "Selected: fallback linter for basic coverage"
                    break

        return LinterSelectionResult(
            recommended_linters=recommended,
            skipped_linters=skipped,
            reasoning=reasoning,
        )

    def _get_relevant_linters(self) -> Set[str]:
        """Get linters relevant to the detected project languages."""
        relevant = set()

        for language in self.project_info.languages:
            if language.lower() in self.LANGUAGE_LINTERS:
                relevant.update(self.LANGUAGE_LINTERS[language.lower()])

        # Also check for specific file types
        for source_file in self.project_info.source_files:
            suffix = source_file.suffix.lower()
            if suffix == ".yml" or suffix == ".yaml":
                relevant.add("ansible-lint")
            elif suffix == ".json":
                relevant.add("jsonlint")
            elif suffix == ".css":
                relevant.add("stylelint")
            elif suffix == ".html":
                relevant.add("htmlhint")
            elif suffix == ".sh":
                relevant.add("shellcheck")

        return relevant

    def _prioritize_linters(self, linters: Set[str], prefer_fast: bool = False) -> List[str]:
        """Prioritize linters based on project characteristics and preferences."""
        prioritized = []
        remaining = set(linters)

        # Add high-priority linters first
        for language in self.project_info.languages:
            if language.lower() in self.HIGH_PRIORITY_LINTERS:
                for linter in self.HIGH_PRIORITY_LINTERS[language.lower()]:
                    if linter in remaining:
                        prioritized.append(linter)
                        remaining.remove(linter)

        # Sort remaining linters
        if prefer_fast:
            # Prefer faster linters (this is a simplified heuristic)
            fast_linters = ["flake8", "eslint", "jshint"]
            for linter in fast_linters:
                if linter in remaining:
                    prioritized.append(linter)
                    remaining.remove(linter)

        # Add remaining linters in alphabetical order
        prioritized.extend(sorted(remaining))

        return prioritized

    def _get_selection_reason(self, linter: str) -> str:
        """Get a human-readable reason for selecting a linter."""
        reasons = {
            "flake8": "Selected: excellent Python code quality checker",
            "pylint": "Selected: comprehensive Python static analysis",
            "eslint": "Selected: standard JavaScript/TypeScript linting",
            "jshint": "Selected: JavaScript code quality tool",
            "prettier": "Selected: code formatting consistency",
            "black": "Selected: Python code formatting",
            "isort": "Selected: Python import sorting",
            "ansible-lint": "Selected: Ansible playbook best practices",
            "tslint": "Selected: TypeScript specific linting",
            "stylelint": "Selected: CSS/SCSS style linting",
            "htmlhint": "Selected: HTML markup validation",
            "shellcheck": "Selected: shell script analysis",
            "hadolint": "Selected: Dockerfile best practices",
            "jsonlint": "Selected: JSON syntax validation",
        }

        return reasons.get(linter, f"Selected: {linter} linter for project analysis")
