"""
Error Analyzer Module

This module analyzes lint errors and provides categorization, prioritization,
and context extraction for better fixing strategies.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .lint_runner import ErrorSeverity, LintError, LintResult
from .pattern_matcher import SmartErrorClassifier, detect_language_from_file_path

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories for different types of lint errors."""

    SYNTAX = "syntax"
    IMPORT = "import"
    FORMATTING = "formatting"
    STYLE = "style"
    TYPE = "type"
    LOGIC = "logic"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    UNUSED = "unused"
    COMPLEXITY = "complexity"
    OTHER = "other"


class FixComplexity(Enum):
    """Complexity levels for fixing errors."""

    TRIVIAL = "trivial"  # Simple formatting, whitespace
    SIMPLE = "simple"  # Import fixes, simple style changes
    MODERATE = "moderate"  # Type annotations, refactoring
    COMPLEX = "complex"  # Logic changes, major refactoring
    MANUAL = "manual"  # Requires human intervention


@dataclass
class ErrorAnalysis:
    """Analysis of a lint error."""

    error: LintError
    category: ErrorCategory
    complexity: FixComplexity
    priority: int  # 1-10, higher is more important
    fixable: bool
    context_lines: List[str] = field(default_factory=list)
    related_errors: List[LintError] = field(default_factory=list)
    fix_strategy: Optional[str] = None
    estimated_effort: int = 1  # 1-5 scale


@dataclass
class FileAnalysis:
    """Analysis of errors in a single file."""

    file_path: str
    total_errors: int
    error_analyses: List[ErrorAnalysis] = field(default_factory=list)
    file_content: Optional[str] = None
    file_exists: bool = True
    language: Optional[str] = None
    complexity_score: float = 0.0


class ErrorAnalyzer:
    """Analyzes lint errors and provides fixing strategies."""

    # Rule patterns for categorization
    RULE_CATEGORIES = {
        # Python rules
        "flake8": {
            ErrorCategory.SYNTAX: ["E9", "F82", "F83"],
            ErrorCategory.IMPORT: ["F4", "I"],
            ErrorCategory.FORMATTING: ["E1", "E2", "E3", "W1", "W2", "W3"],
            ErrorCategory.STYLE: ["E7", "W5"],
            ErrorCategory.UNUSED: ["F8"],
            ErrorCategory.COMPLEXITY: ["C9"],
        },
        "pylint": {
            ErrorCategory.SYNTAX: ["syntax-error", "parse-error"],
            ErrorCategory.IMPORT: [
                "import-error",
                "no-name-in-module",
                "relative-beyond-top-level",
            ],
            ErrorCategory.FORMATTING: ["line-too-long", "trailing-whitespace"],
            ErrorCategory.STYLE: ["invalid-name", "missing-docstring"],
            ErrorCategory.TYPE: ["no-member", "maybe-no-member"],
            ErrorCategory.UNUSED: ["unused-import", "unused-variable"],
            ErrorCategory.LOGIC: ["unreachable", "pointless-statement"],
        },
        "mypy": {
            ErrorCategory.TYPE: ["type-arg", "attr-defined", "assignment", "return-value"],
            ErrorCategory.IMPORT: ["import"],
        },
        # JavaScript/TypeScript rules
        "eslint": {
            ErrorCategory.SYNTAX: ["parsing-error"],
            ErrorCategory.FORMATTING: ["indent", "quotes", "semi"],
            ErrorCategory.STYLE: ["camelcase", "no-console"],
            ErrorCategory.UNUSED: ["no-unused-vars"],
            ErrorCategory.SECURITY: ["no-eval", "no-implied-eval"],
        },
        # Go rules
        "golint": {
            ErrorCategory.STYLE: ["exported", "comment"],
            ErrorCategory.FORMATTING: ["should"],
        },
        "govet": {
            ErrorCategory.LOGIC: ["unreachable", "printf"],
            ErrorCategory.TYPE: ["assign"],
        },
        # Rust rules
        "clippy": {
            ErrorCategory.STYLE: ["style"],
            ErrorCategory.PERFORMANCE: ["perf"],
            ErrorCategory.COMPLEXITY: ["complexity"],
        },
        # Ansible rules
        "ansible-lint": {
            ErrorCategory.SYNTAX: ["yaml", "syntax", "parse", "invalid", "malformed"],
            ErrorCategory.STYLE: ["name", "description", "meta", "tags", "formatting"],
            ErrorCategory.SECURITY: [
                "risky-file-permissions",
                "risky-shell-pipe",
                "command-instead-of-shell",
                "no-changed-when",
                "no-handler",
                "deprecated",
            ],
            ErrorCategory.LOGIC: [
                "always-run",
                "become-user-without-become",
                "empty-string-compare",
                "literal-compare",
                "no-jinja-when",
                "octal-values",
            ],
            ErrorCategory.IMPORT: ["role-name", "galaxy", "requirements"],
        },
    }

    # Complexity mapping for different rule types
    COMPLEXITY_MAPPING = {
        ErrorCategory.FORMATTING: FixComplexity.TRIVIAL,
        ErrorCategory.STYLE: FixComplexity.SIMPLE,
        ErrorCategory.IMPORT: FixComplexity.SIMPLE,
        ErrorCategory.UNUSED: FixComplexity.SIMPLE,
        ErrorCategory.TYPE: FixComplexity.MODERATE,
        ErrorCategory.DOCUMENTATION: FixComplexity.MODERATE,
        ErrorCategory.LOGIC: FixComplexity.COMPLEX,
        ErrorCategory.SECURITY: FixComplexity.COMPLEX,
        ErrorCategory.SYNTAX: FixComplexity.MANUAL,
        ErrorCategory.COMPLEXITY: FixComplexity.COMPLEX,
    }

    # Priority mapping
    PRIORITY_MAPPING = {
        ErrorSeverity.ERROR: 8,
        ErrorSeverity.WARNING: 5,
        ErrorSeverity.INFO: 3,
        ErrorSeverity.STYLE: 2,
    }

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the error analyzer.

        Args:
            project_root: Root directory of the project for resolving relative paths
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()

        # Initialize smart pattern matching system
        cache_dir = self.project_root / ".aider-lint-cache"
        self.smart_classifier = SmartErrorClassifier(cache_dir)

    def analyze_errors(self, results: Dict[str, LintResult]) -> Dict[str, FileAnalysis]:
        """Analyze all lint errors and group by file.

        Args:
            results: Dictionary of lint results from different linters

        Returns:
            Dictionary mapping file paths to their analysis
        """
        file_analyses = {}

        # Collect all errors by file
        errors_by_file = {}
        for linter_name, result in results.items():
            for error in result.errors + result.warnings:
                if error.file_path not in errors_by_file:
                    errors_by_file[error.file_path] = []
                errors_by_file[error.file_path].append(error)

        # Analyze each file
        for file_path, errors in errors_by_file.items():
            file_analysis = self._analyze_file(file_path, errors)
            file_analyses[file_path] = file_analysis

        logger.info(f"Analyzed {len(file_analyses)} files with lint errors")

        return file_analyses

    def _analyze_file(self, file_path: str, errors: List[LintError]) -> FileAnalysis:
        """Analyze errors in a single file.

        Args:
            file_path: Path to the file
            errors: List of errors in the file

        Returns:
            FileAnalysis object
        """
        file_analysis = FileAnalysis(
            file_path=file_path, total_errors=len(errors), language=self._detect_language(file_path)
        )

        # Load file content for context
        # Resolve file path relative to project root
        if Path(file_path).is_absolute():
            full_path = Path(file_path)
        else:
            full_path = self.project_root / file_path

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                file_analysis.file_content = f.read()
        except FileNotFoundError:
            logger.debug(f"File not found (referenced but doesn't exist): {full_path}")
            file_analysis.file_content = ""
            file_analysis.file_exists = False
        except Exception as e:
            logger.warning(f"Could not read file {full_path}: {e}")
            file_analysis.file_content = ""
            file_analysis.file_exists = False

        # Analyze each error
        for error in errors:
            error_analysis = self._analyze_error(error, file_analysis.file_content)
            file_analysis.error_analyses.append(error_analysis)

        # Find related errors
        self._find_related_errors(file_analysis.error_analyses)

        # Calculate complexity score
        file_analysis.complexity_score = self._calculate_file_complexity(file_analysis)

        return file_analysis

    def _analyze_error(self, error: LintError, file_content: Optional[str]) -> ErrorAnalysis:
        """Analyze a single error.

        Args:
            error: The lint error to analyze
            file_content: Content of the file (if available)

        Returns:
            ErrorAnalysis object
        """
        # Categorize the error
        category = self._categorize_error(error)

        # Determine complexity
        complexity = self._determine_complexity(error, category)

        # Calculate priority
        priority = self._calculate_priority(error, category)

        # Check if fixable
        fixable = self._is_fixable(error, category, complexity)

        # Extract context
        context_lines = self._extract_context(error, file_content)

        # Determine fix strategy
        fix_strategy = self._determine_fix_strategy(error, category)

        # Estimate effort
        effort = self._estimate_effort(complexity, category)

        return ErrorAnalysis(
            error=error,
            category=category,
            complexity=complexity,
            priority=priority,
            fixable=fixable,
            context_lines=context_lines,
            fix_strategy=fix_strategy,
            estimated_effort=effort,
        )

    def _categorize_error(self, error: LintError) -> ErrorCategory:
        """Categorize an error based on its rule and message.

        Args:
            error: The lint error

        Returns:
            ErrorCategory enum value
        """
        linter = error.linter
        rule_id = error.rule_id.lower()
        message = error.message.lower()

        # Check rule-based categorization
        if linter in self.RULE_CATEGORIES:
            for category, patterns in self.RULE_CATEGORIES[linter].items():
                for pattern in patterns:
                    if pattern.lower() in rule_id:
                        return category

        # Check message-based categorization
        if any(word in message for word in ["import", "module"]):
            return ErrorCategory.IMPORT
        elif any(word in message for word in ["format", "indent", "whitespace", "spacing"]):
            return ErrorCategory.FORMATTING
        elif any(word in message for word in ["type", "annotation"]):
            return ErrorCategory.TYPE
        elif any(word in message for word in ["unused", "defined but never used"]):
            return ErrorCategory.UNUSED
        elif any(word in message for word in ["syntax", "parse"]):
            return ErrorCategory.SYNTAX
        elif any(word in message for word in ["security", "eval", "dangerous"]):
            return ErrorCategory.SECURITY
        elif any(word in message for word in ["performance", "slow", "inefficient"]):
            return ErrorCategory.PERFORMANCE
        elif any(word in message for word in ["docstring", "documentation", "comment"]):
            return ErrorCategory.DOCUMENTATION
        elif any(word in message for word in ["complex", "too many"]):
            return ErrorCategory.COMPLEXITY
        elif any(word in message for word in ["style", "convention", "naming"]):
            return ErrorCategory.STYLE

        return ErrorCategory.OTHER

    def _determine_complexity(self, error: LintError, category: ErrorCategory) -> FixComplexity:
        """Determine the complexity of fixing an error.

        Args:
            error: The lint error
            category: The error category

        Returns:
            FixComplexity enum value
        """
        # Use category-based mapping as default
        base_complexity = self.COMPLEXITY_MAPPING.get(category, FixComplexity.MODERATE)

        # Adjust based on specific rules or messages
        message = error.message.lower()
        rule_id = error.rule_id.lower()

        # Special handling for Jinja2 template errors
        if error.linter == "ansible-lint" and "jinja[invalid]" in rule_id:
            # Simple quote syntax errors are easily fixable
            if "expected token ','" in message and (
                "got 'n'" in message or "got 'not'" in message or "got 'qubinode'" in message
            ):
                return FixComplexity.SIMPLE
            # Other template errors might be more complex
            elif "template error" in message:
                return FixComplexity.MODERATE

        # Ansible-lint specific complexity adjustments
        if error.linter == "ansible-lint":
            # YAML formatting issues are trivial to fix
            if any(
                pattern in message
                for pattern in [
                    "trailing spaces",
                    "trailing whitespace",
                    "forbidden document start",
                    "found forbidden document start",
                    "duplication of key",
                    "duplicate key",
                ]
            ):
                return FixComplexity.TRIVIAL

            # YAML structure issues are simple to fix
            if any(
                pattern in rule_id
                for pattern in [
                    "yaml[trailing-spaces]",
                    "yaml[document-start]",
                    "yaml[key-duplicates]",
                    "yaml[indentation]",
                ]
            ):
                return FixComplexity.TRIVIAL

        if "missing" in message and "docstring" in message:
            return FixComplexity.SIMPLE
        elif "line too long" in message:
            return FixComplexity.TRIVIAL
        elif "trailing whitespace" in message:
            return FixComplexity.TRIVIAL
        elif "trailing spaces" in message:
            return FixComplexity.TRIVIAL
        elif "undefined name" in message:
            return FixComplexity.COMPLEX
        elif "syntax error" in message:
            return FixComplexity.MANUAL

        return base_complexity

    def _calculate_priority(self, error: LintError, category: ErrorCategory) -> int:
        """Calculate priority for fixing an error.

        Args:
            error: The lint error
            category: The error category

        Returns:
            Priority score (1-10, higher is more important)
        """
        # Base priority from severity
        base_priority = self.PRIORITY_MAPPING.get(error.severity, 5)

        # Adjust based on category
        category_adjustments = {
            ErrorCategory.SYNTAX: +3,
            ErrorCategory.SECURITY: +2,
            ErrorCategory.LOGIC: +1,
            ErrorCategory.TYPE: +1,
            ErrorCategory.FORMATTING: -1,
            ErrorCategory.STYLE: -2,
        }

        adjustment = category_adjustments.get(category, 0)
        priority = max(1, min(10, base_priority + adjustment))

        return priority

    def _is_fixable(
        self, error: LintError, category: ErrorCategory, complexity: FixComplexity
    ) -> bool:
        """Determine if an error is automatically fixable using smart classification.

        Args:
            error: The lint error
            category: The error category
            complexity: The fix complexity

        Returns:
            True if the error can be automatically fixed
        """
        # Manual complexity errors are not automatically fixable
        if complexity == FixComplexity.MANUAL:
            return False

        # Detect language from file path
        language = detect_language_from_file_path(error.file_path)

        # Use smart classifier for enhanced pattern matching
        result = self.smart_classifier.classify_error(error.message, language, error.linter)

        # High confidence predictions override default logic
        if result.confidence > 0.8:
            logger.debug(
                f"Smart classifier: {result.method} -> {result.fixable} "
                f"(confidence: {result.confidence:.2f}) for: {error.message[:50]}..."
            )
            return result.fixable

        # Medium confidence: combine with traditional logic
        if result.confidence > 0.5:
            smart_fixable = result.fixable
            traditional_fixable = self._traditional_is_fixable(error, category, complexity)

            # If both agree, use that result
            if smart_fixable == traditional_fixable:
                return smart_fixable

            # If they disagree, be conservative for syntax errors
            # Exception: trivial YAML formatting errors are safe to fix
            if category == ErrorCategory.SYNTAX:
                if complexity == FixComplexity.TRIVIAL and error.linter == "ansible-lint":
                    # Trust smart classifier for trivial YAML formatting issues
                    return smart_fixable
                return False

            # For other categories, trust the smart classifier if it says fixable
            return smart_fixable

        # Low confidence: fall back to traditional logic
        return self._traditional_is_fixable(error, category, complexity)

    def _traditional_is_fixable(
        self, error: LintError, category: ErrorCategory, complexity: FixComplexity
    ) -> bool:
        """Traditional fixability logic (preserved for fallback)."""
        # Special handling for Jinja2 template syntax errors
        if (
            error.linter == "ansible-lint"
            and category == ErrorCategory.SYNTAX
            and "jinja[invalid]" in error.rule_id.lower()
        ):
            # Simple quote syntax errors are fixable
            message = error.message.lower()
            if "expected token ','" in message and (
                "got 'n'" in message or "got 'not'" in message or "got 'qubinode'" in message
            ):
                return True
            # YAML key duplicates are also fixable
            elif "yaml[key-duplicates]" in error.rule_id.lower():
                return True

        # Syntax errors usually require manual intervention
        if category == ErrorCategory.SYNTAX:
            return False

        # Most other categories can be fixed automatically
        return True

    def learn_from_fix_result(self, error: LintError, fix_successful: bool):
        """Learn from fix attempt results to improve future predictions.

        Args:
            error: The lint error that was attempted to be fixed
            fix_successful: Whether the fix was successful
        """
        language = detect_language_from_file_path(error.file_path)

        # Special case: if linter is ansible-lint, treat as ansible regardless of file extension
        if error.linter == "ansible-lint":
            language = "ansible"

        self.smart_classifier.learn_from_fix(error.message, language, error.linter, fix_successful)

        logger.debug(
            f"Learned from fix: {error.linter} -> {fix_successful} "
            f"(language: {language}) for: {error.message[:50]}..."
        )

    def get_pattern_statistics(self) -> Dict:
        """Get statistics about the pattern matching system."""
        return self.smart_classifier.get_statistics()

    def _extract_context(self, error: LintError, file_content: Optional[str]) -> List[str]:
        """Extract context lines around an error.

        Args:
            error: The lint error
            file_content: Content of the file

        Returns:
            List of context lines
        """
        if not file_content or error.line <= 0:
            return []

        lines = file_content.split("\n")

        # Extract 3 lines before and after the error
        start_line = max(0, error.line - 4)
        end_line = min(len(lines), error.line + 3)

        context_lines = []
        for i in range(start_line, end_line):
            prefix = ">>> " if i == error.line - 1 else "    "
            context_lines.append(f"{prefix}{i+1:4d}: {lines[i]}")

        return context_lines

    def _determine_fix_strategy(self, error: LintError, category: ErrorCategory) -> Optional[str]:
        """Determine the strategy for fixing an error.

        Args:
            error: The lint error
            category: The error category

        Returns:
            Fix strategy description
        """
        strategies = {
            ErrorCategory.FORMATTING: "Apply automatic formatting using appropriate formatter",
            ErrorCategory.IMPORT: "Fix import statements and organize imports",
            ErrorCategory.UNUSED: "Remove unused variables, imports, or code",
            ErrorCategory.STYLE: "Apply style conventions and naming standards",
            ErrorCategory.TYPE: "Add or fix type annotations",
            ErrorCategory.DOCUMENTATION: "Add missing docstrings and comments",
            ErrorCategory.LOGIC: "Review and fix logical issues",
            ErrorCategory.SECURITY: "Address security vulnerabilities",
            ErrorCategory.PERFORMANCE: "Optimize for better performance",
        }

        return strategies.get(category, "Apply appropriate fix based on error message")

    def _estimate_effort(self, complexity: FixComplexity, category: ErrorCategory) -> int:
        """Estimate the effort required to fix an error.

        Args:
            complexity: The fix complexity
            category: The error category

        Returns:
            Effort score (1-5)
        """
        effort_mapping = {
            FixComplexity.TRIVIAL: 1,
            FixComplexity.SIMPLE: 2,
            FixComplexity.MODERATE: 3,
            FixComplexity.COMPLEX: 4,
            FixComplexity.MANUAL: 5,
        }

        return effort_mapping.get(complexity, 3)

    def _find_related_errors(self, error_analyses: List[ErrorAnalysis]) -> None:
        """Find related errors that might be fixed together.

        Args:
            error_analyses: List of error analyses to process
        """
        for i, analysis in enumerate(error_analyses):
            for j, other_analysis in enumerate(error_analyses):
                if i != j and self._are_related(analysis.error, other_analysis.error):
                    analysis.related_errors.append(other_analysis.error)

    def _are_related(self, error1: LintError, error2: LintError) -> bool:
        """Check if two errors are related.

        Args:
            error1: First error
            error2: Second error

        Returns:
            True if errors are related
        """
        # Same line or adjacent lines
        if abs(error1.line - error2.line) <= 1:
            return True

        # Same rule type
        if error1.rule_id == error2.rule_id and error1.rule_id:
            return True

        # Import-related errors
        if "import" in error1.message.lower() and "import" in error2.message.lower():
            return True

        return False

    def _calculate_file_complexity(self, file_analysis: FileAnalysis) -> float:
        """Calculate complexity score for a file.

        Args:
            file_analysis: The file analysis

        Returns:
            Complexity score (0.0-10.0)
        """
        if not file_analysis.error_analyses:
            return 0.0

        # Base score from number of errors
        error_score = min(5.0, len(file_analysis.error_analyses) / 10.0)

        # Complexity score from error types
        complexity_score = 0.0
        for analysis in file_analysis.error_analyses:
            complexity_weights = {
                FixComplexity.TRIVIAL: 0.1,
                FixComplexity.SIMPLE: 0.3,
                FixComplexity.MODERATE: 0.6,
                FixComplexity.COMPLEX: 1.0,
                FixComplexity.MANUAL: 1.5,
            }
            complexity_score += complexity_weights.get(analysis.complexity, 0.5)

        complexity_score = min(5.0, complexity_score / len(file_analysis.error_analyses))

        return error_score + complexity_score

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }

        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang

        return None

    def get_prioritized_errors(
        self, file_analyses: Dict[str, FileAnalysis], max_errors: Optional[int] = None
    ) -> List[ErrorAnalysis]:
        """Get prioritized list of errors for fixing.

        Args:
            file_analyses: Dictionary of file analyses
            max_errors: Maximum number of errors to return

        Returns:
            List of error analyses sorted by priority
        """
        all_analyses = []

        for file_analysis in file_analyses.values():
            all_analyses.extend(file_analysis.error_analyses)

        # Sort by priority (descending), then by complexity (ascending)
        all_analyses.sort(key=lambda x: (-x.priority, x.complexity.value, x.error.line))

        # Filter to only fixable errors
        fixable_analyses = [a for a in all_analyses if a.fixable]

        if max_errors:
            fixable_analyses = fixable_analyses[:max_errors]

        return fixable_analyses
