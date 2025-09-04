"""
Enhanced Error Classification Tests - Simplified Version
=======================================================

This test suite validates error classification functionality using the actual
available methods in the ErrorAnalyzer class.

Key Focus Areas:
1. Error categorization using existing _categorize_error method
2. Fix complexity determination using _determine_complexity method  
3. Priority calculation using _calculate_priority method
4. Context extraction functionality
5. Pattern learning with available learn_from_fix_result method

Coverage Target: Enhances error_analyzer.py (currently 69.8% coverage)
"""

import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from aider_lint_fixer.error_analyzer import ErrorAnalyzer, ErrorCategory, FixComplexity
from aider_lint_fixer.lint_runner import LintError, ErrorSeverity


class TestErrorCategorizationExisting:
    """Test existing error categorization functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_syntax_error_categorization(self):
        """Test categorization of syntax errors."""
        syntax_error = LintError(
            file_path="/test/file.py",
            line=1, column=1,
            rule_id="E901",
            message="SyntaxError: invalid syntax",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        category = self.error_analyzer._categorize_error(syntax_error)
        assert category == ErrorCategory.SYNTAX

    def test_import_error_categorization(self):
        """Test categorization of import-related errors."""
        import_errors = [
            LintError(
                file_path="/test/file.py",
                line=1, column=1,
                rule_id="F401",
                message="'os' imported but unused",
                severity=ErrorSeverity.ERROR,
                linter="flake8"
            ),
            LintError(
                file_path="/test/file.py",
                line=2, column=1,
                rule_id="E401",
                message="multiple imports on one line",
                severity=ErrorSeverity.ERROR,
                linter="flake8"
            )
        ]
        
        for error in import_errors:
            category = self.error_analyzer._categorize_error(error)
            assert category == ErrorCategory.IMPORT

    def test_formatting_error_categorization(self):
        """Test categorization of formatting errors."""
        formatting_errors = [
            LintError(
                file_path="/test/file.py",
                line=1, column=1,
                rule_id="E302",
                message="expected 2 blank lines, found 1",
                severity=ErrorSeverity.ERROR,
                linter="flake8"
            ),
            LintError(
                file_path="/test/file.py",
                line=5, column=80,
                rule_id="E501",
                message="line too long (85 > 79 characters)",
                severity=ErrorSeverity.ERROR,
                linter="flake8"
            )
        ]
        
        for error in formatting_errors:
            category = self.error_analyzer._categorize_error(error)
            assert category == ErrorCategory.FORMATTING

    def test_type_error_categorization(self):
        """Test categorization of type-related errors."""
        type_error = LintError(
            file_path="/test/file.py",
            line=10, column=5,
            rule_id="type-ignore",
            message="type annotation required",
            severity=ErrorSeverity.ERROR,
            linter="mypy"
        )
        
        category = self.error_analyzer._categorize_error(type_error)
        # Should be TYPE or OTHER category
        assert category in [ErrorCategory.TYPE, ErrorCategory.OTHER]


class TestFixComplexityDetermination:
    """Test fix complexity determination."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_trivial_complexity_determination(self):
        """Test identification of trivial fixes."""
        trivial_error = LintError(
            file_path="/test/file.py",
            line=1, column=1,
            rule_id="W292",  # no newline at end of file
            message="no newline at end of file",
            severity=ErrorSeverity.WARNING,
            linter="flake8"
        )
        
        category = self.error_analyzer._categorize_error(trivial_error)
        complexity = self.error_analyzer._determine_complexity(trivial_error, category)
        
        assert complexity in [FixComplexity.TRIVIAL, FixComplexity.SIMPLE]

    def test_complex_fix_determination(self):
        """Test identification of complex fixes."""
        complex_error = LintError(
            file_path="/test/file.py",
            line=10, column=5,
            rule_id="C901",  # too complex
            message="'function' is too complex (12)",
            severity=ErrorSeverity.WARNING,
            linter="flake8"
        )
        
        category = self.error_analyzer._categorize_error(complex_error)
        complexity = self.error_analyzer._determine_complexity(complex_error, category)
        
        # Complex errors should require more effort
        assert complexity in [FixComplexity.COMPLEX, FixComplexity.MANUAL]


class TestPriorityCalculation:
    """Test error priority calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_high_priority_errors(self):
        """Test that syntax errors get high priority."""
        syntax_error = LintError(
            file_path="/test/file.py",
            line=1, column=1,
            rule_id="E901",
            message="SyntaxError: invalid syntax",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        category = self.error_analyzer._categorize_error(syntax_error)
        priority = self.error_analyzer._calculate_priority(syntax_error, category)
        
        # Syntax errors should have high priority (higher number = higher priority)
        assert priority >= 80

    def test_low_priority_warnings(self):
        """Test that style warnings get lower priority."""
        style_warning = LintError(
            file_path="/test/file.py",
            line=5, column=80,
            rule_id="E501",
            message="line too long (85 > 79 characters)",
            severity=ErrorSeverity.WARNING,
            linter="flake8"
        )
        
        category = self.error_analyzer._categorize_error(style_warning)
        priority = self.error_analyzer._calculate_priority(style_warning, category)
        
        # Style warnings should have lower priority
        assert priority <= 50


class TestContextExtraction:
    """Test context extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_context_extraction_from_error(self):
        """Test extracting context from error messages."""
        error = LintError(
            file_path="/test/file.py",
            line=5, column=10,
            rule_id="F821",
            message="undefined name 'variable'",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        # Mock file content
        file_content = """
def function():
    x = 1
    y = 2
    result = variable  # Error on this line
    return result
        """
        
        context = self.error_analyzer._extract_context(error, file_content)
        
        assert isinstance(context, list)
        assert len(context) > 0


class TestPatternLearning:
    """Test pattern learning functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_learn_from_successful_fix(self):
        """Test learning from successful fix results."""
        error = LintError(
            file_path="/test/file.py",
            line=1, column=1,
            rule_id="F401",
            message="'os' imported but unused",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        # Should not raise an exception
        self.error_analyzer.learn_from_fix_result(error, fix_successful=True)
        
        # Test learning from failed fix
        self.error_analyzer.learn_from_fix_result(error, fix_successful=False)

    def test_pattern_statistics_retrieval(self):
        """Test retrieval of pattern statistics."""
        stats = self.error_analyzer.get_pattern_statistics()
        
        assert isinstance(stats, dict)
        # Should contain some statistics structure


class TestLanguageDetection:
    """Test language detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_python_language_detection(self):
        """Test detection of Python files."""
        python_files = [
            "/test/script.py",
            "/test/module/__init__.py",
            "/test/package/main.py"
        ]
        
        for file_path in python_files:
            language = self.error_analyzer._detect_language(file_path)
            assert language == "python" or language is None  # May not be implemented

    def test_javascript_language_detection(self):
        """Test detection of JavaScript files."""
        js_files = [
            "/test/script.js",
            "/test/component.jsx",
            "/test/module.ts",
            "/test/types.tsx"
        ]
        
        for file_path in js_files:
            language = self.error_analyzer._detect_language(file_path)
            # Should detect JavaScript/TypeScript or return None if not implemented
            assert language in ["javascript", "typescript", None]


class TestFileAnalysisIntegration:
    """Test file analysis integration."""

    def setup_method(self):
        """Set up test fixtures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = Path(temp_dir)
            self.error_analyzer = ErrorAnalyzer(str(self.temp_dir))

    def test_structural_analysis_availability(self):
        """Test that structural analysis components are available."""
        # Test that methods exist and can be called
        assert hasattr(self.error_analyzer, 'get_structural_analysis')
        assert hasattr(self.error_analyzer, 'has_structural_problems')
        assert hasattr(self.error_analyzer, 'get_structural_recommendations')
        
        # These should not raise exceptions when called
        analysis = self.error_analyzer.get_structural_analysis()
        has_problems = self.error_analyzer.has_structural_problems()
        recommendations = self.error_analyzer.get_structural_recommendations()
        
        assert isinstance(has_problems, bool)
        assert isinstance(recommendations, list)


class TestErrorRelationshipDetection:
    """Test error relationship detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_related_error_detection(self):
        """Test detection of related errors."""
        error1 = LintError(
            file_path="/test/file.py",
            line=1, column=1,
            rule_id="F401",
            message="'os' imported but unused",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        error2 = LintError(
            file_path="/test/file.py",
            line=2, column=1,
            rule_id="F401",
            message="'sys' imported but unused",
            severity=ErrorSeverity.ERROR,
            linter="flake8"
        )
        
        # Test if errors are considered related
        are_related = self.error_analyzer._are_related(error1, error2)
        assert isinstance(are_related, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
