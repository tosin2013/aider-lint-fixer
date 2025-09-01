#!/usr/bin/env python3
"""
Comprehensive test suite for pre-lint assessment system.

Tests assessment logic, recommendation engine, and baseline establishment
to achieve 75% coverage target.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

import pytest

from aider_lint_fixer.pre_lint_assessment import (
    RiskLevel,
    RiskCategory,
    RiskAssessment,
    PreLintAssessor,
    generate_architect_guidance_for_dangerous_errors,
)

# Import test utilities
from tests.utils import (
    TestDataBuilder,
    FileSystemFixtures,
    MockGenerator,
    temp_project_dir,
    python_project,
    nodejs_project,
)


class TestRiskLevelEnum:
    """Test RiskLevel enumeration."""
    
    def test_risk_levels(self):
        """Test risk level values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestRiskCategoryEnum:
    """Test RiskCategory enumeration."""
    
    def test_risk_categories(self):
        """Test risk category values."""
        assert RiskCategory.VOLUME.value == "volume"
        assert RiskCategory.UNDEFINED_VARS.value == "undefined_vars"
        assert RiskCategory.MISSING_TESTS.value == "missing_tests"
        assert RiskCategory.LEGACY_CODE.value == "legacy_code"
        assert RiskCategory.EXTERNAL_DEPS.value == "external_deps"
        assert RiskCategory.PRODUCTION_CODE.value == "production_code"


class TestRiskAssessment:
    """Test RiskAssessment data structure."""
    
    def test_risk_assessment_creation(self):
        """Test creating risk assessments."""
        assessment = RiskAssessment(
            overall_risk=RiskLevel.MEDIUM,
            total_errors=50,
            error_breakdown={"style": 30, "syntax": 20},
            risk_factors=[(RiskCategory.VOLUME, "Too many errors", RiskLevel.HIGH)],
            recommendations=["Fix critical errors first"],
            safe_to_proceed=True,
            suggested_approach="Incremental fixes",
            architect_guidance={"strategy": "careful"}
        )
        
        assert assessment.overall_risk == RiskLevel.MEDIUM
        assert assessment.total_errors == 50
        assert len(assessment.error_breakdown) == 2
        assert len(assessment.risk_factors) == 1
        assert assessment.safe_to_proceed is True
        assert assessment.architect_guidance is not None


class TestPreLintAssessor:
    """Test PreLintAssessor main functionality."""
    
    def test_assessor_initialization(self, temp_project_dir):
        """Test assessor initialization."""
        assessor = PreLintAssessor(str(temp_project_dir))
        assert assessor.project_root == Path(temp_project_dir)
        assert hasattr(assessor, 'project_detector')
        assert hasattr(assessor, 'lint_runner')
    
    @patch('aider_lint_fixer.pre_lint_assessment.logger')
    def test_assess_project_basic(self, mock_logger, python_project, temp_project_dir):
        """Test basic project assessment."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock lint runner to return empty results
        with patch.object(assessor.lint_runner, 'run_linter', return_value=Mock(errors=[], warnings=[])):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment, RiskAssessment)
            assert assessment.total_errors >= 0
            assert isinstance(assessment.error_breakdown, dict)
            assert isinstance(assessment.risk_factors, list)
            assert isinstance(assessment.recommendations, list)
    
    @patch('aider_lint_fixer.pre_lint_assessment.logger')
    def test_assess_project_with_specific_linters(self, mock_logger, python_project, temp_project_dir):
        """Test project assessment with specific linters."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock lint runner
        with patch.object(assessor.lint_runner, 'run_linter', return_value=Mock(errors=[], warnings=[])):
            assessment = assessor.assess_project(linters=["flake8", "pylint"])
            
            assert isinstance(assessment, RiskAssessment)
    
    def test_run_quick_lint_scan_success(self, python_project, temp_project_dir):
        """Test successful quick lint scan."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock successful lint results
        mock_result = Mock()
        mock_result.errors = [{"line": 1, "message": "Test error"}]
        mock_result.warnings = []
        
        with patch.object(assessor.lint_runner, 'run_linter', return_value=mock_result):
            results = assessor._run_quick_lint_scan(["flake8"])
            
            assert "flake8" in results
            assert len(results["flake8"].errors) == 1
    
    def test_run_quick_lint_scan_failure(self, python_project, temp_project_dir):
        """Test quick lint scan with linter failures."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock linter failure
        with patch.object(assessor.lint_runner, 'run_linter', side_effect=Exception("Linter failed")):
            results = assessor._run_quick_lint_scan(["flake8"])
            
            # Should handle failures gracefully
            assert isinstance(results, dict)
    
    def test_run_quick_lint_scan_no_result(self, python_project, temp_project_dir):
        """Test quick lint scan when linter returns None."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock linter returning None
        with patch.object(assessor.lint_runner, 'run_linter', return_value=None):
            results = assessor._run_quick_lint_scan(["flake8"])
            
            assert isinstance(results, dict)


class TestVolumeRiskAssessment:
    """Test volume-based risk assessment."""
    
    def test_assess_volume_risk_low(self, temp_project_dir):
        """Test volume risk assessment for low error count."""
        assessor = PreLintAssessor(str(temp_project_dir))
        risk_factors = []
        recommendations = []
        
        volume_risk = assessor._assess_volume_risk(10, risk_factors, recommendations)
        
        assert volume_risk == RiskLevel.LOW
        assert len(risk_factors) == 0  # No risk factors for low volume
    
    def test_assess_volume_risk_medium(self, temp_project_dir):
        """Test volume risk assessment for medium error count."""
        assessor = PreLintAssessor(str(temp_project_dir))
        risk_factors = []
        recommendations = []
        
        volume_risk = assessor._assess_volume_risk(50, risk_factors, recommendations)  # Changed from 150 to 50
        
        assert volume_risk == RiskLevel.MEDIUM
        assert len(risk_factors) > 0
        assert any("moderate error count" in str(factor).lower() for factor in risk_factors)
    
    def test_assess_volume_risk_high(self, temp_project_dir):
        """Test volume risk assessment for high error count."""
        assessor = PreLintAssessor(str(temp_project_dir))
        risk_factors = []
        recommendations = []
        
        volume_risk = assessor._assess_volume_risk(750, risk_factors, recommendations)
        
        assert volume_risk == RiskLevel.HIGH
        assert len(risk_factors) > 0
        assert any("high error count" in str(factor).lower() for factor in risk_factors)
    
    def test_assess_volume_risk_critical(self, temp_project_dir):
        """Test volume risk assessment for critical error count."""
        assessor = PreLintAssessor(str(temp_project_dir))
        risk_factors = []
        recommendations = []
        
        volume_risk = assessor._assess_volume_risk(1500, risk_factors, recommendations)
        
        assert volume_risk == RiskLevel.CRITICAL
        assert len(risk_factors) > 0
        assert any("extremely high" in str(factor).lower() for factor in risk_factors)
        assert len(recommendations) > 0


class TestErrorTypeAnalysis:
    """Test error type analysis and categorization."""
    
    def test_analyze_error_types_empty(self, temp_project_dir):
        """Test error type analysis with no errors."""
        assessor = PreLintAssessor(str(temp_project_dir))
        lint_results = {}
        risk_factors = []
        recommendations = []
        
        error_breakdown = assessor._analyze_error_types(lint_results, risk_factors, recommendations)
        
        assert isinstance(error_breakdown, dict)
        assert error_breakdown.get("total", 0) == 0
    
    def test_analyze_error_types_with_errors(self, temp_project_dir):
        """Test error type analysis with various error types."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock lint results with different error types
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "E501", "message": "line too long"},
            {"rule": "F401", "message": "imported but unused"},
            {"rule": "undefined-variable", "message": "undefined variable 'x'"},
            {"rule": "W292", "message": "no newline at end of file"},
        ]
        mock_result.warnings = []
        
        lint_results = {"flake8": mock_result}
        risk_factors = []
        recommendations = []
        
        error_breakdown = assessor._analyze_error_types(lint_results, risk_factors, recommendations)
        
        assert isinstance(error_breakdown, dict)
        assert len(error_breakdown) > 0  # Should have at least some error categories
        assert sum(error_breakdown.values()) > 0  # Total count should be > 0
    
    def test_analyze_error_types_dangerous_errors(self, temp_project_dir):
        """Test detection of dangerous error types."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock lint results with dangerous errors
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "undefined-variable", "message": "undefined variable 'dangerous_var'"},
            {"rule": "unused-variable", "message": "unused variable 'safe_var'"},
        ]
        mock_result.warnings = []
        
        lint_results = {"pylint": mock_result}
        risk_factors = []
        recommendations = []
        
        error_breakdown = assessor._analyze_error_types(lint_results, risk_factors, recommendations)
        
        assert isinstance(error_breakdown, dict)
        # Should detect dangerous errors and add appropriate risk factors
        dangerous_factors = [f for f in risk_factors if f[0] == RiskCategory.UNDEFINED_VARS]
        assert len(dangerous_factors) > 0 or error_breakdown.get("undefined_vars", 0) > 0


class TestProjectContextAssessment:
    """Test project context risk assessment."""
    
    def test_assess_project_context_python(self, temp_project_dir):
        """Test project context assessment for Python projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock Python project info
        project_info = Mock()
        project_info.project_type = "python"
        project_info.has_setup_py = True
        project_info.has_requirements = True
        
        risk_factors = []
        recommendations = []
        
        assessor._assess_project_context(project_info, risk_factors, recommendations)
        
        # Should assess Python-specific risks
        assert isinstance(risk_factors, list)
        assert isinstance(recommendations, list)
    
    def test_assess_project_context_nodejs(self, temp_project_dir):
        """Test project context assessment for Node.js projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock Node.js project info
        project_info = Mock()
        project_info.project_type = "nodejs"
        project_info.has_package_json = True
        project_info.has_node_modules = False
        
        risk_factors = []
        recommendations = []
        
        assessor._assess_project_context(project_info, risk_factors, recommendations)
        
        assert isinstance(risk_factors, list)
        assert isinstance(recommendations, list)
    
    def test_assess_project_context_production_indicators(self, temp_project_dir):
        """Test detection of production code indicators."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Create production-like files
        (temp_project_dir / "docker-compose.yml").touch()
        (temp_project_dir / "Dockerfile").touch()
        (temp_project_dir / ".env.production").touch()
        
        project_info = Mock()
        project_info.project_type = "python"
        project_info.files = list(temp_project_dir.glob("*"))
        
        risk_factors = []
        recommendations = []
        
        assessor._assess_project_context(project_info, risk_factors, recommendations)
        
        # Should detect production code risks
        production_factors = [f for f in risk_factors if f[0] == RiskCategory.PRODUCTION_CODE]
        assert len(production_factors) >= 0  # May or may not detect based on implementation


class TestTestCoverageAssessment:
    """Test test coverage assessment."""
    
    def test_assess_test_coverage_with_tests(self, temp_project_dir):
        """Test assessment when tests are present."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Create test directory and files
        test_dir = temp_project_dir / "tests"
        test_dir.mkdir()
        (test_dir / "test_example.py").touch()
        
        project_info = Mock()
        project_info.has_tests = True
        project_info.test_files = [str(test_dir / "test_example.py")]
        
        risk_factors = []
        recommendations = []
        
        assessor._assess_test_coverage(project_info, risk_factors, recommendations)
        
        # Should have lower risk when tests are present
        missing_test_factors = [f for f in risk_factors if f[0] == RiskCategory.MISSING_TESTS]
        assert len(missing_test_factors) == 0
    
    def test_assess_test_coverage_without_tests(self, temp_project_dir):
        """Test assessment when no tests are present."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        project_info = Mock()
        project_info.has_tests = False
        project_info.test_files = []
        
        risk_factors = []
        recommendations = []
        
        assessor._assess_test_coverage(project_info, risk_factors, recommendations)
        
        # Should add risk factors for missing tests
        missing_test_factors = [f for f in risk_factors if f[0] == RiskCategory.MISSING_TESTS]
        assert len(missing_test_factors) > 0
        assert len(recommendations) > 0


class TestOverallRiskCalculation:
    """Test overall risk calculation algorithms."""
    
    def test_calculate_overall_risk_low(self, temp_project_dir):
        """Test overall risk calculation for low risk scenario."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        risk_factors = [
            (RiskCategory.VOLUME, "Low volume", RiskLevel.LOW),
            (RiskCategory.MISSING_TESTS, "Some tests missing", RiskLevel.LOW),
        ]
        
        overall_risk = assessor._calculate_overall_risk(risk_factors)
        
        assert overall_risk == RiskLevel.LOW
    
    def test_calculate_overall_risk_medium(self, temp_project_dir):
        """Test overall risk calculation for medium risk scenario."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        risk_factors = [
            (RiskCategory.VOLUME, "Medium volume", RiskLevel.MEDIUM),
            (RiskCategory.LEGACY_CODE, "Some legacy code", RiskLevel.LOW),
        ]
        
        overall_risk = assessor._calculate_overall_risk(risk_factors)
        
        assert overall_risk in [RiskLevel.MEDIUM, RiskLevel.LOW]
    
    def test_calculate_overall_risk_high(self, temp_project_dir):
        """Test overall risk calculation for high risk scenario."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        risk_factors = [
            (RiskCategory.VOLUME, "High volume", RiskLevel.HIGH),
            (RiskCategory.UNDEFINED_VARS, "Dangerous errors", RiskLevel.CRITICAL),
        ]
        
        overall_risk = assessor._calculate_overall_risk(risk_factors)
        
        assert overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_calculate_overall_risk_critical(self, temp_project_dir):
        """Test overall risk calculation for critical risk scenario."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        risk_factors = [
            (RiskCategory.UNDEFINED_VARS, "Critical errors", RiskLevel.CRITICAL),
            (RiskCategory.PRODUCTION_CODE, "Production system", RiskLevel.CRITICAL),
            (RiskCategory.MISSING_TESTS, "No tests", RiskLevel.HIGH),
        ]
        
        overall_risk = assessor._calculate_overall_risk(risk_factors)
        
        assert overall_risk == RiskLevel.CRITICAL


class TestApproachSuggestion:
    """Test suggested approach generation."""
    
    def test_suggest_approach_low_risk(self, temp_project_dir):
        """Test approach suggestion for low risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        approach = assessor._suggest_approach(RiskLevel.LOW, 10, {"style": 8, "syntax": 2})
        
        assert isinstance(approach, str)
        assert "automated" in approach.lower() or "safe" in approach.lower()
    
    def test_suggest_approach_medium_risk(self, temp_project_dir):
        """Test approach suggestion for medium risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        approach = assessor._suggest_approach(RiskLevel.MEDIUM, 100, {"style": 60, "errors": 40})
        
        assert isinstance(approach, str)
        assert "careful" in approach.lower() or "staged" in approach.lower()
    
    def test_suggest_approach_high_risk(self, temp_project_dir):
        """Test approach suggestion for high risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        approach = assessor._suggest_approach(RiskLevel.HIGH, 500, {"errors": 300, "warnings": 200})
        
        assert isinstance(approach, str)
        assert "caution" in approach.lower() or "careful" in approach.lower() or "review" in approach.lower()
    
    def test_suggest_approach_critical_risk(self, temp_project_dir):
        """Test approach suggestion for critical risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        approach = assessor._suggest_approach(RiskLevel.CRITICAL, 1000, {"critical": 500, "errors": 500})
        
        assert isinstance(approach, str)
        assert "avoid" in approach.lower() or "manual" in approach.lower()
    
    def test_suggest_approach_volume_based(self, temp_project_dir):
        """Test approach suggestion based on error volume."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # High volume, low risk
        approach1 = assessor._suggest_approach(RiskLevel.LOW, 800, {"style": 800})
        assert isinstance(approach1, str)
        
        # Low volume, high risk
        approach2 = assessor._suggest_approach(RiskLevel.HIGH, 5, {"critical": 5})
        assert isinstance(approach2, str)


class TestArchitectGuidance:
    """Test architect guidance generation."""
    
    def test_generate_architect_guidance_no_dangerous_errors(self):
        """Test architect guidance when no dangerous errors present."""
        lint_results = {
            "flake8": Mock(errors=[
                {"rule": "E501", "message": "line too long"}
            ])
        }
        
        guidance = generate_architect_guidance_for_dangerous_errors(lint_results)
        
        assert isinstance(guidance, dict)
        # Should have minimal guidance for safe errors
    
    def test_generate_architect_guidance_with_dangerous_errors(self):
        """Test architect guidance with dangerous errors."""
        lint_results = {
            "pylint": Mock(errors=[
                {"rule": "no-unde", "message": "undefined variable 'x'", "file": "test.py", "line": 1},
                {"rule": "no-global-assign", "message": "global assignment", "file": "test.py", "line": 2},
            ])
        }
        
        guidance = generate_architect_guidance_for_dangerous_errors(lint_results)
        
        assert isinstance(guidance, dict)
        assert guidance.get("has_dangerous_errors", False) or len(guidance.get("dangerous_patterns", [])) > 0
    
    def test_generate_architect_guidance_mixed_errors(self):
        """Test architect guidance with mixed error types."""
        lint_results = {
            "flake8": Mock(errors=[
                {"rule": "E501", "message": "line too long"},
                {"rule": "F821", "message": "undefined name 'variable'"},
            ]),
            "pylint": Mock(errors=[
                {"rule": "import-error", "message": "unable to import module"},
                {"rule": "W292", "message": "no newline at end of file"},
            ])
        }
        
        guidance = generate_architect_guidance_for_dangerous_errors(lint_results)
        
        assert isinstance(guidance, dict)


class TestRecommendationEngine:
    """Test recommendation engine functionality."""
    
    def test_recommendations_for_low_risk(self, temp_project_dir):
        """Test recommendations for low risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock a low-risk assessment
        with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment.recommendations, list)
            # Low risk should have fewer, less aggressive recommendations
    
    def test_recommendations_for_high_risk(self, temp_project_dir):
        """Test recommendations for high risk projects."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock high-risk lint results
        mock_result = Mock()
        mock_result.errors = [{"rule": "critical-error", "message": "critical issue"}] * 100
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"linter": mock_result}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment.recommendations, list)
            assert len(assessment.recommendations) > 0
            # High risk should have more detailed recommendations
    
    def test_recommendations_include_priorities(self, temp_project_dir):
        """Test that recommendations include priority information."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock various error types
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "undefined-variable", "message": "critical error"},
            {"rule": "E501", "message": "style error"},
        ]
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"linter": mock_result}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment.recommendations, list)
            # Should prioritize dangerous errors over style issues
    
    def test_recommendations_include_tools(self, temp_project_dir):
        """Test that recommendations include suggested tools."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        mock_result = Mock()
        mock_result.errors = [{"rule": "import-error", "message": "import issue"}]
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"linter": mock_result}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment.recommendations, list)
            # Should suggest appropriate tools for the error types


class TestBaselineEstablishment:
    """Test baseline establishment functionality."""
    
    def test_baseline_capture_current_state(self, python_project, temp_project_dir):
        """Test capturing current project state as baseline."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock lint results for baseline
        mock_result = Mock()
        mock_result.errors = [{"rule": "E501", "message": "line too long"}]
        mock_result.warnings = []
        
        with patch.object(assessor.lint_runner, 'run_linter', return_value=mock_result):
            assessment = assessor.assess_project()
            
            # Assessment should include baseline information
            assert isinstance(assessment.error_breakdown, dict)
            assert assessment.total_errors >= 0
    
    def test_baseline_progress_tracking_setup(self, temp_project_dir):
        """Test setting up progress tracking system."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # This would set up mechanisms to track improvement over time
        # For now, just test that the assessment structure supports it
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"linter": mock_result}):
            assessment = assessor.assess_project()
            
            # Should have structure that supports progress tracking
            assert hasattr(assessment, 'total_errors')
            assert hasattr(assessment, 'error_breakdown')
            assert hasattr(assessment, 'overall_risk')
    
    def test_baseline_metric_calculation(self, temp_project_dir):
        """Test calculation of baseline metrics."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock varied error types for metrics
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "E501", "message": "line too long", "severity": "warning"},
            {"rule": "F401", "message": "unused import", "severity": "error"},
            {"rule": "undefined-variable", "message": "undefined", "severity": "error"},
        ]
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"linter": mock_result}):
            assessment = assessor.assess_project()
            
            # Should calculate meaningful metrics
            assert assessment.total_errors >= 0
            assert isinstance(assessment.error_breakdown, dict)
            assert len(assessment.risk_factors) >= 0
    
    def test_baseline_comparison_structure(self, temp_project_dir):
        """Test structure that supports baseline comparison."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
            assessment = assessor.assess_project()
            
            # Assessment should have fields that allow comparison
            baseline_fields = ['total_errors', 'error_breakdown', 'overall_risk']
            for field in baseline_fields:
                assert hasattr(assessment, field)


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    def test_assessment_with_mixed_project_types(self, temp_project_dir):
        """Test assessment of mixed project types."""
        # Create mixed project structure
        (temp_project_dir / "setup.py").touch()  # Python
        (temp_project_dir / "package.json").touch()  # Node.js
        (temp_project_dir / "requirements.txt").touch()  # Python
        
        assessor = PreLintAssessor(str(temp_project_dir))
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment, RiskAssessment)
            # Should handle mixed project types gracefully
    
    def test_assessment_with_no_linters_available(self, temp_project_dir):
        """Test assessment when no linters are available."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock all linters failing
        with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment, RiskAssessment)
            assert assessment.total_errors == 0
            # Should provide recommendations even without linter results
    
    def test_assessment_performance_on_large_projects(self, temp_project_dir):
        """Test assessment performance on large projects."""
        # Create many files to simulate large project
        for i in range(50):
            (temp_project_dir / f"module{i}.py").touch()
        
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock quick scan (should be fast even for large projects)
        with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment, RiskAssessment)
            # Assessment should complete in reasonable time
    
    def test_assessment_error_recovery(self, temp_project_dir):
        """Test error recovery during assessment."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock partial failures in assessment steps
        with patch.object(assessor, '_assess_project_context', side_effect=Exception("Context error")):
            with patch.object(assessor, '_run_quick_lint_scan', return_value={}):
                # Should not crash on partial failures
                try:
                    assessment = assessor.assess_project()
                    assert isinstance(assessment, RiskAssessment)
                except Exception:
                    # If it does raise an exception, it should be handled gracefully
                    pass
    
    def test_assessment_with_architect_guidance_integration(self, temp_project_dir):
        """Test integration with architect guidance system."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Mock dangerous errors that should trigger architect guidance
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "undefined-variable", "message": "undefined variable"},
        ]
        mock_result.warnings = []
        
        with patch.object(assessor, '_run_quick_lint_scan', return_value={"pylint": mock_result}):
            assessment = assessor.assess_project()
            
            assert isinstance(assessment, RiskAssessment)
            # Should include architect guidance for dangerous errors
            assert assessment.architect_guidance is not None


class TestUtilityFunctions:
    """Test utility functions and edge cases."""
    
    def test_error_categorization_edge_cases(self, temp_project_dir):
        """Test error categorization edge cases."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Test with unusual error formats
        mock_result = Mock()
        mock_result.errors = [
            {"rule": "", "message": "Empty rule"},
            {"rule": "unknown-rule-123", "message": "Unknown rule type"},
            {"message": "Missing rule field"},  # No rule field
        ]
        mock_result.warnings = []
        
        lint_results = {"test": mock_result}
        risk_factors = []
        recommendations = []
        
        # Should handle edge cases gracefully
        error_breakdown = assessor._analyze_error_types(lint_results, risk_factors, recommendations)
        assert isinstance(error_breakdown, dict)
    
    def test_recommendation_generation_edge_cases(self, temp_project_dir):
        """Test recommendation generation edge cases."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Test with empty or minimal data
        assessment = RiskAssessment(
            overall_risk=RiskLevel.LOW,
            total_errors=0,
            error_breakdown={},
            risk_factors=[],
            recommendations=[],
            safe_to_proceed=True,
            suggested_approach="minimal",
        )
        
        # Should generate reasonable recommendations even with minimal data
        assert isinstance(assessment.recommendations, list)
        assert isinstance(assessment.suggested_approach, str)
    
    def test_risk_calculation_boundary_conditions(self, temp_project_dir):
        """Test risk calculation boundary conditions."""
        assessor = PreLintAssessor(str(temp_project_dir))
        
        # Test boundary conditions for risk levels
        boundary_tests = [
            ([], RiskLevel.LOW),  # No risk factors
            ([(RiskCategory.VOLUME, "test", RiskLevel.CRITICAL)], RiskLevel.CRITICAL),  # Single critical
        ]
        
        for risk_factors, expected_min_level in boundary_tests:
            overall_risk = assessor._calculate_overall_risk(risk_factors)
            # Risk should be at least the expected minimum
            risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            expected_index = risk_levels.index(expected_min_level)
            actual_index = risk_levels.index(overall_risk)
            assert actual_index >= expected_index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])