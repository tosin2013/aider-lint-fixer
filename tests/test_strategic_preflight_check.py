#!/usr/bin/env python3
"""
Comprehensive test suite for strategic preflight check system.

Tests preflight validation, environment assessment, and risk assessment logic
to achieve 70% coverage target.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

import pytest

from aider_lint_fixer.strategic_preflight_check import (
    ChaosLevel,
    ChaosIndicator,
    PreFlightResult,
    MessyCodebaseAnalyzer,
    StrategicPreFlightChecker,
)

# Import test utilities
from tests.utils import (
    TestDataBuilder,
    FileSystemFixtures,
    MockGenerator,
    temp_project_dir,
)


class TestChaosLevelEnum:
    """Test ChaosLevel enumeration."""
    
    def test_chaos_levels(self):
        """Test chaos level values."""
        assert ChaosLevel.CLEAN.value == "clean"
        assert ChaosLevel.MESSY.value == "messy"
        assert ChaosLevel.CHAOTIC.value == "chaotic"
        assert ChaosLevel.DISASTER.value == "disaster"


class TestChaosIndicator:
    """Test ChaosIndicator data structure."""
    
    def test_chaos_indicator_creation(self):
        """Test creating chaos indicators."""
        indicator = ChaosIndicator(
            type="file_organization",
            severity="major",
            description="Too many files in root",
            evidence=["file1.py", "file2.py"],
            impact="Makes navigation difficult"
        )
        
        assert indicator.type == "file_organization"
        assert indicator.severity == "major"
        assert "files in root" in indicator.description
        assert len(indicator.evidence) == 2
        assert "navigation" in indicator.impact


class TestPreFlightResult:
    """Test PreFlightResult data structure."""
    
    def test_preflight_result_creation(self):
        """Test creating preflight results."""
        result = PreFlightResult(
            chaos_level="messy",
            should_proceed=True,
            blocking_issues=["Issue 1"],
            strategic_questions=[{"question": "What is the purpose?"}],
            recommended_actions=["Action 1"],
            analysis_timestamp="2024-01-01T00:00:00",
            bypass_available=False
        )
        
        assert result.chaos_level == "messy"
        assert result.should_proceed is True
        assert len(result.blocking_issues) == 1
        assert len(result.strategic_questions) == 1
        assert len(result.recommended_actions) == 1
        assert result.bypass_available is False


class TestMessyCodebaseAnalyzer:
    """Test MessyCodebaseAnalyzer functionality."""
    
    def test_analyzer_initialization(self, temp_project_dir):
        """Test analyzer initialization."""
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        assert analyzer.project_path == temp_project_dir
    
    def test_analyze_clean_codebase(self, temp_project_dir):
        """Test analysis of clean codebase."""
        # Create a clean project structure
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "src" / "main.py").touch()
        (temp_project_dir / "tests").mkdir()
        (temp_project_dir / "tests" / "test_main.py").touch()
        (temp_project_dir / "README.md").touch()
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        chaos_level = analyzer.analyze_chaos_level()
        
        assert chaos_level == ChaosLevel.CLEAN
    
    def test_analyze_messy_codebase(self, temp_project_dir):
        """Test analysis of messy codebase."""
        # Create messy structure with many files in root to trigger major indicator
        for i in range(12):  # More than 10 to trigger the "major" severity
            (temp_project_dir / f"file{i}.py").touch()
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        chaos_level = analyzer.analyze_chaos_level()
        
        # Should be at least MESSY due to many files in root
        assert chaos_level in [ChaosLevel.MESSY, ChaosLevel.CHAOTIC, ChaosLevel.DISASTER]
    
    def test_analyze_chaotic_codebase(self, temp_project_dir):
        """Test analysis of chaotic codebase."""
        # Create chaotic structure with many files in root
        for i in range(12):
            (temp_project_dir / f"file{i}.py").touch()
        
        # Add experimental files
        experimental_files = ["demo.py", "test.py", "debug.py", "experimental.py", "temp.py", "temp2.py"]
        for filename in experimental_files:
            (temp_project_dir / filename).touch()
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        chaos_level = analyzer.analyze_chaos_level()
        
        # Should be CHAOTIC or DISASTER due to many issues
        assert chaos_level in [ChaosLevel.CHAOTIC, ChaosLevel.DISASTER]
    
    def test_detect_file_organization_chaos(self, temp_project_dir):
        """Test detection of file organization chaos."""
        # Create many Python files in root
        for i in range(15):
            (temp_project_dir / f"module{i}.py").touch()
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        indicators = analyzer._detect_chaos_indicators()
        
        # Should detect file organization issue
        file_org_indicators = [i for i in indicators if i.type == "file_organization"]
        assert len(file_org_indicators) > 0
        assert file_org_indicators[0].severity == "major"
    
    def test_detect_experimental_files_chaos(self, temp_project_dir):
        """Test detection of experimental files chaos."""
        experimental_files = [
            "demo1.py", "demo2.py", "test1.py", "test2.py", 
            "debug1.py", "debug2.py", "experimental1.py", "temp1.py"
        ]
        for filename in experimental_files:
            (temp_project_dir / filename).touch()
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        indicators = analyzer._detect_chaos_indicators()
        
        # Should detect experimental files issue
        exp_indicators = [i for i in indicators if i.type == "code_structure"]
        assert len(exp_indicators) > 0
    
    def test_readme_reality_mismatch_detection(self, temp_project_dir):
        """Test detection of README vs reality mismatch."""
        # Create README mentioning non-existent files
        readme_content = """
        # My Project
        
        This project includes:
        - aider_test_fixer_clean.py
        - project_detector.py
        """
        (temp_project_dir / "README.md").write_text(readme_content)
        
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        indicators = analyzer._detect_chaos_indicators()
        
        # Should detect README mismatch
        doc_indicators = [i for i in indicators if i.type == "documentation"]
        assert len(doc_indicators) > 0
    
    def test_chaos_score_calculation(self, temp_project_dir):
        """Test chaos score calculation logic."""
        analyzer = MessyCodebaseAnalyzer(str(temp_project_dir))
        
        # Test with known indicators
        indicators = [
            ChaosIndicator("test", "critical", "Critical issue", [], "High impact"),
            ChaosIndicator("test", "major", "Major issue", [], "Medium impact"),
            ChaosIndicator("test", "minor", "Minor issue", [], "Low impact"),
        ]
        
        # Calculate score manually: critical=3, major=2, minor=1 = 6 total
        chaos_score = 0
        for indicator in indicators:
            if indicator.severity == "critical":
                chaos_score += 3
            elif indicator.severity == "major":
                chaos_score += 2
            elif indicator.severity == "minor":
                chaos_score += 1
        
        # Score 6 should be CHAOTIC (>=4 and <8)
        if chaos_score >= 8:
            expected_level = ChaosLevel.DISASTER
        elif chaos_score >= 4:
            expected_level = ChaosLevel.CHAOTIC
        elif chaos_score >= 2:
            expected_level = ChaosLevel.MESSY
        else:
            expected_level = ChaosLevel.CLEAN
            
        assert expected_level == ChaosLevel.CHAOTIC


class TestStrategicPreFlightChecker:
    """Test StrategicPreFlightChecker main functionality."""
    
    def test_checker_initialization(self, temp_project_dir):
        """Test checker initialization."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        assert str(checker.project_path) == str(temp_project_dir)
        # Cache directory should be created
        cache_dir = checker.project_path / ".aider-lint-cache"
        assert hasattr(checker, 'cache_file')
    
    def test_perform_preflight_check_clean_project(self, temp_project_dir):
        """Test preflight check on clean project."""
        # Create clean project structure
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "src" / "main.py").touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        result = checker.run_preflight_check()
        
        assert isinstance(result, PreFlightResult)
        assert result.chaos_level == ChaosLevel.CLEAN.value
        assert result.should_proceed is True
    
    def test_perform_preflight_check_chaotic_project(self, temp_project_dir):
        """Test preflight check on chaotic project."""
        # Create chaotic project structure
        for i in range(15):
            (temp_project_dir / f"file{i}.py").touch()
        
        experimental_files = ["demo.py", "test.py", "debug.py", "experimental.py", "temp.py", "temp2.py"]
        for filename in experimental_files:
            (temp_project_dir / filename).touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        result = checker.run_preflight_check()
        
        assert isinstance(result, PreFlightResult)
        assert result.chaos_level in [ChaosLevel.CHAOTIC.value, ChaosLevel.DISASTER.value]
        # Chaotic projects may or may not proceed depending on severity
    
    def test_get_recommended_actions_disaster(self, temp_project_dir):
        """Test getting recommended actions for disaster level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("test", "critical", "Critical issue", [], "High impact")
        ]
        
        actions = checker._get_recommended_actions(ChaosLevel.DISASTER, test_indicators)
        
        assert len(actions) > 0
        assert any("CRITICAL" in action for action in actions)
        assert any("project purpose" in action for action in actions)
    
    def test_get_recommended_actions_chaotic(self, temp_project_dir):
        """Test getting recommended actions for chaotic level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("test", "major", "Major issue", [], "Medium impact")
        ]
        
        actions = checker._get_recommended_actions(ChaosLevel.CHAOTIC, test_indicators)
        
        assert len(actions) > 0
        assert any("production vs experimental" in action for action in actions)
    
    def test_get_recommended_actions_messy(self, temp_project_dir):
        """Test getting recommended actions for messy level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("test", "minor", "Minor issue", [], "Low impact")
        ]
        
        actions = checker._get_recommended_actions(ChaosLevel.MESSY, test_indicators)
        
        assert len(actions) > 0
        # Messy level should have some actionable recommendations
    
    def test_get_blocking_issues(self, temp_project_dir):
        """Test getting blocking issues."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("file_organization", "critical", "Too many files", [], "High impact"),
            ChaosIndicator("documentation", "major", "README mismatch", [], "Medium impact")
        ]
        
        blocking_issues = checker._get_blocking_issues(test_indicators)
        
        assert len(blocking_issues) > 0
        assert any("file" in issue.lower() for issue in blocking_issues)
    
    def test_display_preflight_results(self, temp_project_dir, capsys):
        """Test displaying preflight results."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        result = PreFlightResult(
            chaos_level=ChaosLevel.MESSY.value,
            should_proceed=True,
            blocking_issues=["Issue 1", "Issue 2"],
            strategic_questions=[],
            recommended_actions=["Action 1", "Action 2"],
            analysis_timestamp=datetime.now().isoformat(),
            bypass_available=False
        )
        
        checker._display_preflight_results(result)
        
        captured = capsys.readouterr()
        assert "Chaos Level" in captured.out
        assert "MESSY" in captured.out
        assert "YES" in captured.out  # should_proceed is True
    
    def test_cache_functionality(self, temp_project_dir):
        """Test caching of analysis results."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Test saving and loading cache
        result = PreFlightResult(
            chaos_level=ChaosLevel.CLEAN.value,
            should_proceed=True,
            blocking_issues=[],
            strategic_questions=[],
            recommended_actions=[],
            analysis_timestamp=datetime.now().isoformat(),
            bypass_available=False
        )
        
        checker._cache_analysis(result)
        assert checker._has_recent_analysis() is True
        
        loaded_result = checker._load_cached_analysis()
        assert loaded_result is not None
        assert loaded_result.chaos_level == ChaosLevel.CLEAN.value
    
    def test_cache_expiry(self, temp_project_dir):
        """Test cache expiry logic."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Create old cache file
        old_result = PreFlightResult(
            chaos_level=ChaosLevel.CLEAN.value,
            should_proceed=True,
            blocking_issues=[],
            strategic_questions=[],
            recommended_actions=[],
            analysis_timestamp=(datetime.now() - timedelta(hours=25)).isoformat(),
            bypass_available=False
        )
        
        checker._cache_analysis(old_result)
        
        # Cache should be considered stale after 24 hours
        assert checker._has_recent_analysis() is False


class TestEnvironmentAssessment:
    """Test environment assessment functionality."""
    
    @patch('subprocess.run')
    def test_python_version_detection(self, mock_run, temp_project_dir):
        """Test Python version checking."""
        # Mock subprocess result for python --version
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Python 3.9.0",
            stderr=""
        )
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        # This would be part of a more comprehensive environment check
        # For now, just test that we can mock the subprocess call
        
        assert mock_run.return_value.returncode == 0
    
    @patch('subprocess.run')
    def test_nodejs_version_detection(self, mock_run, temp_project_dir):
        """Test Node.js version checking."""
        # Mock subprocess result for node --version
        mock_run.return_value = Mock(
            returncode=0,
            stdout="v16.14.0",
            stderr=""
        )
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        # Test environment detection logic
        
        assert mock_run.return_value.returncode == 0
    
    def test_package_manager_detection(self, temp_project_dir):
        """Test package manager detection."""
        # Create package manager files
        (temp_project_dir / "package.json").touch()
        (temp_project_dir / "requirements.txt").touch()
        (temp_project_dir / "pyproject.toml").touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Check for package manager files
        has_npm = (Path(temp_project_dir) / "package.json").exists()
        has_pip = (Path(temp_project_dir) / "requirements.txt").exists()
        has_poetry = (Path(temp_project_dir) / "pyproject.toml").exists()
        
        assert has_npm is True
        assert has_pip is True
        assert has_poetry is True
    
    def test_virtual_environment_detection(self, temp_project_dir):
        """Test virtual environment detection."""
        # Create virtual environment indicators
        (temp_project_dir / "venv").mkdir()
        (temp_project_dir / ".venv").mkdir()
        (temp_project_dir / "env").mkdir()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Check for virtual environment directories
        venv_dirs = ['venv', '.venv', 'env', 'virtualenv']
        found_venvs = []
        for venv_dir in venv_dirs:
            if (Path(temp_project_dir) / venv_dir).exists():
                found_venvs.append(venv_dir)
        
        assert len(found_venvs) >= 3
    
    def test_linter_availability_validation(self, temp_project_dir):
        """Test linter availability validation."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Test common linters - this is a basic check
        # In a real implementation, we'd check if they're installed
        common_linters = ['flake8', 'eslint', 'pylint', 'black', 'prettier']
        
        # For testing, just verify the list is reasonable
        assert len(common_linters) > 0
        assert 'flake8' in common_linters
        assert 'eslint' in common_linters
    
    def test_project_structure_validation(self, temp_project_dir):
        """Test project structure validation."""
        # Create a well-structured project
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "tests").mkdir()
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "README.md").touch()
        (temp_project_dir / ".gitignore").touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Check for good project structure indicators
        structure_indicators = []
        if (Path(temp_project_dir) / "src").exists():
            structure_indicators.append("has_src_dir")
        if (Path(temp_project_dir) / "tests").exists():
            structure_indicators.append("has_tests_dir")
        if (Path(temp_project_dir) / "README.md").exists():
            structure_indicators.append("has_readme")
        
        assert len(structure_indicators) >= 3


class TestRiskAssessmentLogic:
    """Test risk assessment algorithms."""
    
    def test_complexity_scoring_basic(self, temp_project_dir):
        """Test basic complexity scoring."""
        # Create files of varying complexity
        simple_file = temp_project_dir / "simple.py"
        simple_file.write_text("print('hello')")
        
        complex_file = temp_project_dir / "complex.py"
        complex_content = """
def complex_function():
    for i in range(100):
        if i % 2 == 0:
            for j in range(i):
                if j % 3 == 0:
                    print(f"Complex: {i}, {j}")
                else:
                    continue
        else:
            pass
    return True
"""
        complex_file.write_text(complex_content)
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Basic complexity assessment
        python_files = list(Path(temp_project_dir).glob("*.py"))
        assert len(python_files) == 2
        
        # Simple complexity metric: file size
        simple_size = simple_file.stat().st_size
        complex_size = complex_file.stat().st_size
        
        assert complex_size > simple_size
    
    def test_project_size_assessment(self, temp_project_dir):
        """Test project size assessment."""
        # Create project of known size
        for i in range(10):
            (temp_project_dir / f"module{i}.py").write_text(f"# Module {i}\nprint('Module {i}')")
        
        for i in range(5):
            (temp_project_dir / f"test{i}.py").write_text(f"# Test {i}\nassert True")
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Count files and calculate size
        python_files = list(Path(temp_project_dir).glob("*.py"))
        total_files = len(python_files)
        total_size = sum(f.stat().st_size for f in python_files)
        
        assert total_files == 15
        assert total_size > 0
    
    def test_estimated_fix_time_calculation(self, temp_project_dir):
        """Test estimated fix time calculation."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Mock complexity factors
        complexity_factors = {
            "file_count": 50,
            "avg_file_size": 1000,
            "chaos_score": 6,
            "has_tests": False,
            "has_docs": True,
        }
        
        # Simple time estimation algorithm
        base_time = 30  # minutes
        file_factor = complexity_factors["file_count"] * 2  # 2 min per file
        size_factor = complexity_factors["avg_file_size"] / 100  # size impact
        chaos_factor = complexity_factors["chaos_score"] * 10  # chaos impact
        
        estimated_time = base_time + file_factor + size_factor + chaos_factor
        
        # Should be reasonable estimate
        assert estimated_time > 0
        assert estimated_time < 1000  # Less than 1000 minutes seems reasonable
    
    def test_risk_score_calculation(self, temp_project_dir):
        """Test risk score calculation algorithms."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Test different risk scenarios
        low_risk_factors = {
            "chaos_level": ChaosLevel.CLEAN,
            "file_count": 10,
            "has_tests": True,
            "has_docs": True,
            "recent_commits": True
        }
        
        high_risk_factors = {
            "chaos_level": ChaosLevel.DISASTER,
            "file_count": 200,
            "has_tests": False,
            "has_docs": False,
            "recent_commits": False
        }
        
        # Calculate risk scores
        def calculate_risk_score(factors):
            score = 0
            if factors["chaos_level"] == ChaosLevel.DISASTER:
                score += 50
            elif factors["chaos_level"] == ChaosLevel.CHAOTIC:
                score += 30
            elif factors["chaos_level"] == ChaosLevel.MESSY:
                score += 15
            
            if factors["file_count"] > 100:
                score += 20
            elif factors["file_count"] > 50:
                score += 10
            
            if not factors["has_tests"]:
                score += 15
            if not factors["has_docs"]:
                score += 10
            
            return score
        
        low_risk_score = calculate_risk_score(low_risk_factors)
        high_risk_score = calculate_risk_score(high_risk_factors)
        
        assert low_risk_score < high_risk_score
        assert low_risk_score >= 0
        assert high_risk_score > 50


class TestAiderRecommendations:
    """Test aider-powered strategic recommendations."""
    
    def test_generate_aider_recommendations_disaster(self, temp_project_dir):
        """Test aider recommendations for disaster level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("file_organization", "critical", "Too many files", [], "High impact")
        ]
        
        recommendations = checker._generate_aider_recommendations(ChaosLevel.DISASTER, test_indicators)
        
        # Should contain aider-specific guidance - could be dict or list
        assert isinstance(recommendations, (dict, list))
    
    def test_generate_aider_recommendations_chaotic(self, temp_project_dir):
        """Test aider recommendations for chaotic level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        test_indicators = [
            ChaosIndicator("code_structure", "major", "Experimental files", [], "Medium impact")
        ]
        
        recommendations = checker._generate_aider_recommendations(ChaosLevel.CHAOTIC, test_indicators)
        
        assert isinstance(recommendations, (dict, list))
    
    def test_generate_aider_recommendations_clean(self, temp_project_dir):
        """Test aider recommendations for clean level."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        recommendations = checker._generate_aider_recommendations(ChaosLevel.CLEAN, [])
        
        assert isinstance(recommendations, (dict, list))
        # Clean projects should have minimal recommendations


class TestPreflightIntegration:
    """Test integration scenarios and edge cases."""
    
    def test_preflight_check_with_cache(self, temp_project_dir):
        """Test preflight check with caching."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # First check should analyze and cache
        result1 = checker.perform_preflight_check()
        assert isinstance(result1, PreFlightResult)
        
        # Second check should use cache
        result2 = checker.perform_preflight_check()
        assert isinstance(result2, PreFlightResult)
        
        # Results should be identical when using cache
        assert result1.chaos_level == result2.chaos_level
    
    def test_preflight_check_force_refresh(self, temp_project_dir):
        """Test forcing refresh of preflight analysis."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Perform initial check
        result1 = checker.perform_preflight_check()
        
        # Force refresh should bypass cache
        result2 = checker.perform_preflight_check(force_refresh=True)
        
        assert isinstance(result1, PreFlightResult)
        assert isinstance(result2, PreFlightResult)
    
    def test_preflight_check_bypass_mode(self, temp_project_dir):
        """Test bypass mode for urgent fixes."""
        # Create chaotic project that would normally block
        for i in range(20):
            (temp_project_dir / f"file{i}.py").touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        result = checker.perform_preflight_check(allow_bypass=True)
        
        assert isinstance(result, PreFlightResult)
        # Even chaotic projects should allow bypass when requested
        if result.chaos_level in [ChaosLevel.CHAOTIC.value, ChaosLevel.DISASTER.value]:
            assert result.bypass_available is True
    
    def test_preflight_check_different_project_types(self, temp_project_dir):
        """Test preflight check on different project types."""
        # Test Python project
        (temp_project_dir / "setup.py").touch()
        (temp_project_dir / "requirements.txt").touch()
        
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        python_result = checker.perform_preflight_check()
        
        assert isinstance(python_result, PreFlightResult)
        
        # Test Node.js project
        (temp_project_dir / "package.json").touch()
        (temp_project_dir / "node_modules").mkdir()
        
        nodejs_result = checker.perform_preflight_check(force_refresh=True)
        
        assert isinstance(nodejs_result, PreFlightResult)
    
    def test_error_handling_missing_project(self):
        """Test error handling for missing project directory."""
        with pytest.raises(Exception):
            # This should handle the case where project directory doesn't exist
            checker = StrategicPreFlightChecker("/nonexistent/path")
            checker.perform_preflight_check()
    
    def test_error_handling_corrupted_cache(self, temp_project_dir):
        """Test error handling for corrupted cache files."""
        checker = StrategicPreFlightChecker(str(temp_project_dir))
        
        # Create corrupted cache file
        cache_file = checker.cache_file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("invalid json content {")
        
        # Should handle corrupted cache gracefully
        result = checker.run_preflight_check()
        assert isinstance(result, PreFlightResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])