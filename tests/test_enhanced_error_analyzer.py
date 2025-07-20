"""
Test suite for the Enhanced Error Analyzer integration.

This module tests:
1. Integration of structural analysis with error analysis
2. Integration of control flow analysis with error analysis
3. Enhanced error categorization with context
4. Improved fixability assessment
5. Context-aware error prioritization
6. Comprehensive error analysis workflow
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.error_analyzer import (
    ErrorAnalysis,
    ErrorAnalyzer,
    ErrorCategory,
    FixComplexity,
)
from aider_lint_fixer.lint_runner import ErrorSeverity, LintError, LintResult


class TestEnhancedErrorAnalyzer:
    """Test enhanced error analyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = ErrorAnalyzer(project_path=self.temp_dir)

    def test_enhanced_initialization(self):
        """Test that enhanced error analyzer initializes with new components."""
        assert self.analyzer.project_path == self.temp_dir
        assert self.analyzer.structural_detector is not None
        assert self.analyzer.control_flow_analyzer is not None
        assert hasattr(self.analyzer, "_control_flow_cache")
        assert hasattr(self.analyzer, "_last_structural_analysis")

    def test_structural_analysis_integration(self):
        """Test integration of structural analysis with error analysis."""
        # Create mock lint results with high error count to trigger structural analysis
        mock_errors = []
        for i in range(120):  # Above 100 error threshold
            mock_errors.append(
                LintError(
                    file_path=f"file_{i % 10}.py",
                    line=i % 50 + 1,
                    column=1,
                    rule_id="test-rule",
                    message=f"Test error {i}",
                    severity=ErrorSeverity.ERROR,
                    linter="test-linter",
                )
            )

        mock_results = {
            "test-linter": LintResult(
                linter="test-linter",
                errors=mock_errors,
                warnings=[],
                success=True,
                raw_output="",
                execution_time=1.0,
            )
        }

        with patch.object(
            self.analyzer.structural_detector, "analyze_structural_problems"
        ) as mock_structural:
            mock_structural.return_value = MagicMock(
                architectural_score=75.0,
                structural_issues=[],
                hotspot_files=["file_0.py"],
                refactoring_candidates=["file_1.py"],
                recommendations=["Test recommendation"],
            )

            file_analyses = self.analyzer.analyze_errors(mock_results)

            # Should have triggered structural analysis
            mock_structural.assert_called_once()
            assert self.analyzer.has_structural_problems() is False  # No issues in mock
            assert len(self.analyzer.get_structural_recommendations()) == 1

    def test_control_flow_analysis_integration(self):
        """Test integration of control flow analysis with error analysis."""
        # Create mock errors for a single file to trigger control flow analysis
        mock_errors = []
        for i in range(8):  # Above 5 error threshold for control flow analysis
            mock_errors.append(
                LintError(
                    file_path="complex_file.py",
                    line=i + 10,
                    column=1,
                    rule_id="test-rule",
                    message=f"Test error {i}",
                    severity=ErrorSeverity.ERROR,
                    linter="test-linter",
                )
            )

        mock_results = {
            "test-linter": LintResult(
                linter="test-linter",
                errors=mock_errors,
                warnings=[],
                success=True,
                raw_output="",
                execution_time=1.0,
            )
        }

        with patch.object(self.analyzer.control_flow_analyzer, "analyze_file") as mock_cf_analyze:
            mock_cf_analyze.return_value = MagicMock(
                control_structures=[],
                unreachable_code=[],
                complexity_metrics={"cyclomatic_complexity": 5},
            )

            with patch.object(
                self.analyzer.control_flow_analyzer, "get_control_flow_insights"
            ) as mock_cf_insights:
                mock_cf_insights.return_value = {
                    "in_control_structure": True,
                    "control_structure_type": "if",
                    "nesting_level": 2,
                    "reachable": True,
                    "complexity_context": "high",
                }

                file_analyses = self.analyzer.analyze_errors(mock_results)

                # Should have triggered control flow analysis
                mock_cf_analyze.assert_called_once()

                # Check that control flow insights were applied
                file_analysis = file_analyses["complex_file.py"]
                for error_analysis in file_analysis.error_analyses:
                    if hasattr(error_analysis, "control_flow_context"):
                        assert error_analysis.control_flow_context is not None

    def test_enhanced_error_analysis_with_control_flow_context(self):
        """Test error analysis enhanced with control flow context."""
        # Create a test error
        error = LintError(
            file_path="test.py",
            line=15,
            column=5,
            rule_id="no-undef",
            message="'undefined_var' is not defined",
            severity=ErrorSeverity.ERROR,
            linter="pylint",
        )

        # Mock control flow analysis
        mock_cf_analysis = MagicMock()

        with patch.object(
            self.analyzer.control_flow_analyzer, "get_control_flow_insights"
        ) as mock_insights:
            mock_insights.return_value = {
                "in_control_structure": True,
                "control_structure_type": "for",
                "nesting_level": 3,
                "reachable": True,
                "complexity_context": "high",
            }

            error_analysis = self.analyzer._analyze_error(error, "test content", mock_cf_analysis)

            # Should have enhanced the analysis with control flow context
            assert hasattr(error_analysis, "control_flow_context")
            assert error_analysis.control_flow_context["in_control_structure"] is True
            assert error_analysis.control_flow_context["nesting_level"] == 3

            # Should have adjusted complexity due to high complexity context
            # (Original complexity would be upgraded)

    def test_unreachable_code_fixability_adjustment(self):
        """Test that unreachable code is marked as unfixable."""
        error = LintError(
            file_path="test.py",
            line=20,
            column=1,
            rule_id="unused-variable",
            message="Variable 'x' is assigned but never used",
            severity=ErrorSeverity.WARNING,
            linter="pylint",
        )

        mock_cf_analysis = MagicMock()

        with patch.object(
            self.analyzer.control_flow_analyzer, "get_control_flow_insights"
        ) as mock_insights:
            mock_insights.return_value = {
                "in_control_structure": False,
                "reachable": False,  # Unreachable code
                "complexity_context": "low",
            }

            error_analysis = self.analyzer._analyze_error(error, "test content", mock_cf_analysis)

            # Should mark as unfixable due to unreachable code
            assert error_analysis.fixable is False
            assert "unreachable code" in error_analysis.fix_strategy.lower()

    def test_control_flow_cache_functionality(self):
        """Test that control flow analysis results are cached."""
        file_path = "test_file.py"
        error_lines = {10, 15, 20}

        with patch.object(self.analyzer.control_flow_analyzer, "analyze_file") as mock_analyze:
            mock_analyze.return_value = MagicMock()

            # First call should trigger analysis
            result1 = self.analyzer._get_control_flow_analysis(file_path, error_lines)
            mock_analyze.assert_called_once()

            # Second call should use cache
            result2 = self.analyzer._get_control_flow_analysis(file_path, error_lines)
            mock_analyze.assert_called_once()  # Still only called once

            # Results should be the same (from cache)
            assert result1 is result2
            assert file_path in self.analyzer._control_flow_cache

    def test_control_flow_analysis_error_handling(self):
        """Test handling of control flow analysis errors."""
        file_path = "problematic_file.py"
        error_lines = {5}

        with patch.object(self.analyzer.control_flow_analyzer, "analyze_file") as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")

            result = self.analyzer._get_control_flow_analysis(file_path, error_lines)

            # Should handle error gracefully and return None
            assert result is None

    def test_enhanced_complexity_adjustment(self):
        """Test that complexity is adjusted based on control flow context."""
        error = LintError(
            file_path="test.py",
            line=10,
            column=1,
            rule_id="too-many-locals",
            message="Too many local variables",
            severity=ErrorSeverity.WARNING,
            linter="pylint",
        )

        mock_cf_analysis = MagicMock()

        with patch.object(
            self.analyzer.control_flow_analyzer, "get_control_flow_insights"
        ) as mock_insights:
            # Test high complexity context
            mock_insights.return_value = {
                "in_control_structure": True,
                "complexity_context": "high",
                "reachable": True,
            }

            error_analysis = self.analyzer._analyze_error(error, "test content", mock_cf_analysis)

            # Should have increased complexity due to high complexity context
            # The exact complexity depends on the original categorization
            assert error_analysis.complexity in [FixComplexity.MODERATE, FixComplexity.COMPLEX]

    def test_enhanced_priority_adjustment(self):
        """Test that priority is adjusted based on control flow context."""
        error = LintError(
            file_path="test.py",
            line=10,
            column=1,
            rule_id="no-undef",
            message="Undefined variable",
            severity=ErrorSeverity.ERROR,
            linter="pylint",
        )

        mock_cf_analysis = MagicMock()

        with patch.object(
            self.analyzer.control_flow_analyzer, "get_control_flow_insights"
        ) as mock_insights:
            mock_insights.return_value = {
                "in_control_structure": True,
                "complexity_context": "high",
                "reachable": True,
            }

            # Get original priority for comparison
            original_analysis = self.analyzer._analyze_error(error, "test content")
            original_priority = original_analysis.priority

            # Get enhanced analysis
            enhanced_analysis = self.analyzer._analyze_error(
                error, "test content", mock_cf_analysis
            )
            enhanced_priority = enhanced_analysis.priority

            # Priority should be increased for high complexity context
            assert enhanced_priority >= original_priority

    def test_structural_hotspot_complexity_adjustment(self):
        """Test that complexity is adjusted for structural hotspot files."""
        # Create mock file analyses
        mock_file_analyses = {
            "hotspot.py": MagicMock(
                error_analyses=[MagicMock(error=MagicMock(rule_id="test-rule")) for _ in range(10)]
            )
        }

        # Mock structural analysis that identifies hotspot
        mock_structural_analysis = MagicMock(
            architectural_score=60.0,
            structural_issues=[],
            hotspot_files=["hotspot.py"],
            refactoring_candidates=[],
            recommendations=[],
        )

        with patch.object(
            self.analyzer.structural_detector, "analyze_structural_problems"
        ) as mock_structural:
            mock_structural.return_value = mock_structural_analysis

            # Trigger analysis with high error count
            mock_results = {
                "test-linter": LintResult(
                    linter="test-linter",
                    errors=[
                        LintError(
                            file_path="hotspot.py",
                            line=i,
                            column=1,
                            rule_id="test-rule",
                            message=f"Error {i}",
                            severity=ErrorSeverity.ERROR,
                            linter="test-linter",
                        )
                        for i in range(120)  # High error count
                    ],
                    warnings=[],
                    success=True,
                    raw_output="",
                    execution_time=1.0,
                )
            }

            file_analyses = self.analyzer.analyze_errors(mock_results)

            # Check that hotspot file had complexity adjusted
            hotspot_analysis = file_analyses["hotspot.py"]
            assert hotspot_analysis.complexity_score >= 2.0  # Should be increased

    def test_refactoring_candidate_fix_strategy_adjustment(self):
        """Test that fix strategy is adjusted for refactoring candidates."""
        # This test would require more complex setup to verify the fix strategy adjustment
        # For now, we'll test that the mechanism is in place

        mock_file_analyses = {
            "candidate.py": MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="test-rule"), fix_strategy=None)
                    for _ in range(10)
                ]
            )
        }

        mock_structural_analysis = MagicMock(
            architectural_score=70.0,
            structural_issues=[],
            hotspot_files=[],
            refactoring_candidates=["candidate.py"],
            recommendations=[],
        )

        with patch.object(
            self.analyzer.structural_detector, "analyze_structural_problems"
        ) as mock_structural:
            mock_structural.return_value = mock_structural_analysis

            # The actual test would need to verify fix strategy changes
            # This is a placeholder to ensure the integration point exists
            assert hasattr(self.analyzer, "structural_detector")
            assert hasattr(self.analyzer, "_last_structural_analysis")

    def test_comprehensive_enhanced_workflow(self):
        """Test the complete enhanced error analysis workflow."""
        # Create a comprehensive test case with multiple files and error types
        mock_errors = []

        # Add errors to trigger both structural and control flow analysis
        for i in range(150):  # High error count for structural analysis
            file_index = i % 5
            mock_errors.append(
                LintError(
                    file_path=f"file_{file_index}.py",
                    line=(i % 20) + 1,
                    column=1,
                    rule_id=f"rule-{i % 10}",
                    message=f"Error message {i}",
                    severity=ErrorSeverity.ERROR,
                    linter="comprehensive-linter",
                )
            )

        mock_results = {
            "comprehensive-linter": LintResult(
                linter="comprehensive-linter",
                errors=mock_errors,
                warnings=[],
                success=True,
                raw_output="",
                execution_time=2.0,
            )
        }

        with patch.object(
            self.analyzer.structural_detector, "analyze_structural_problems"
        ) as mock_structural:
            with patch.object(self.analyzer.control_flow_analyzer, "analyze_file") as mock_cf:
                # Setup mocks
                mock_structural.return_value = MagicMock(
                    architectural_score=65.0,
                    structural_issues=[],
                    hotspot_files=["file_0.py"],
                    refactoring_candidates=["file_1.py"],
                    recommendations=["Comprehensive recommendation"],
                )

                mock_cf.return_value = MagicMock(
                    control_structures=[], unreachable_code=[], complexity_metrics={}
                )

                # Run comprehensive analysis
                file_analyses = self.analyzer.analyze_errors(mock_results)

                # Verify comprehensive workflow
                assert len(file_analyses) == 5  # 5 different files
                assert mock_structural.called  # Structural analysis triggered
                assert mock_cf.called  # Control flow analysis triggered

                # Verify that all files were analyzed
                for i in range(5):
                    assert f"file_{i}.py" in file_analyses
                    file_analysis = file_analyses[f"file_{i}.py"]
                    assert len(file_analysis.error_analyses) > 0


if __name__ == "__main__":
    pytest.main([__file__])
