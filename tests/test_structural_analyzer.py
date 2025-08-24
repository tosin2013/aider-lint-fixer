"""
Test suite for the Structural Analyzer module.

This module tests:
1. Structural problem detection
2. Architectural hotspot identification
3. Technical debt measurement
4. Complexity clustering analysis
5. Refactoring recommendation generation
6. Maintenance bottleneck detection
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.structural_analyzer import (
    ArchitecturalAnalysis,
    FileStructuralMetrics,
    StructuralIssue,
    StructuralProblemDetector,
    StructuralProblemType,
)


class TestStructuralProblemType:
    """Test StructuralProblemType enumeration."""

    def test_structural_problem_types(self):
        """Test that structural problem types are correctly defined."""
        assert StructuralProblemType.MONOLITHIC_FILES.value == "monolithic_files"
        assert StructuralProblemType.TIGHT_COUPLING.value == "tight_coupling"
        assert StructuralProblemType.POOR_SEPARATION.value == "poor_separation"
        assert StructuralProblemType.COMPLEXITY_HOTSPOTS.value == "complexity_hotspots"
        assert StructuralProblemType.DEPENDENCY_CYCLES.value == "dependency_cycles"
        assert StructuralProblemType.ARCHITECTURAL_VIOLATIONS.value == "architectural_violations"
        assert StructuralProblemType.TECHNICAL_DEBT_CLUSTERS.value == "technical_debt_clusters"


class TestStructuralIssue:
    """Test StructuralIssue data structure."""

    def test_structural_issue_initialization(self):
        """Test StructuralIssue initialization."""
        issue = StructuralIssue(
            problem_type=StructuralProblemType.MONOLITHIC_FILES,
            severity="high",
            description="Large monolithic file detected",
            affected_files=["large_file.py"],
            error_count=50,
            confidence=0.8,
            recommendations=["Break down into smaller modules"],
            metrics={"lines_of_code": 1000, "error_density": 0.05},
        )

        assert issue.problem_type == StructuralProblemType.MONOLITHIC_FILES
        assert issue.severity == "high"
        assert issue.description == "Large monolithic file detected"
        assert "large_file.py" in issue.affected_files
        assert issue.error_count == 50
        assert issue.confidence == 0.8
        assert "Break down into smaller modules" in issue.recommendations
        assert issue.metrics["lines_of_code"] == 1000


class TestFileStructuralMetrics:
    """Test FileStructuralMetrics data structure."""

    def test_file_structural_metrics_initialization(self):
        """Test FileStructuralMetrics initialization."""
        metrics = FileStructuralMetrics(
            file_path="test.py",
            error_count=25,
            error_density=0.05,
            error_types={"no-undef", "import/no-unresolved"},
            complexity_indicators={"max-len": 5, "max-statements": 3},
            coupling_score=0.7,
            cohesion_score=0.6,
            lines_of_code=500,
        )

        assert metrics.file_path == "test.py"
        assert metrics.error_count == 25
        assert metrics.error_density == 0.05
        assert "no-undef" in metrics.error_types
        assert metrics.complexity_indicators["max-len"] == 5
        assert metrics.coupling_score == 0.7
        assert metrics.cohesion_score == 0.6
        assert metrics.lines_of_code == 500


class TestArchitecturalAnalysis:
    """Test ArchitecturalAnalysis data structure."""

    def test_architectural_analysis_initialization(self):
        """Test ArchitecturalAnalysis initialization."""
        analysis = ArchitecturalAnalysis(
            total_files=10,
            total_errors=150,
            structural_issues=[],
            hotspot_files=["hotspot.py"],
            refactoring_candidates=["candidate.py"],
            architectural_score=75.0,
            recommendations=["Implement clean architecture"],
        )

        assert analysis.total_files == 10
        assert analysis.total_errors == 150
        assert len(analysis.structural_issues) == 0
        assert "hotspot.py" in analysis.hotspot_files
        assert "candidate.py" in analysis.refactoring_candidates
        assert analysis.architectural_score == 75.0
        assert "Implement clean architecture" in analysis.recommendations


class TestStructuralProblemDetector:
    """Test StructuralProblemDetector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.detector = StructuralProblemDetector(self.temp_dir)

    def test_initialization(self):
        """Test StructuralProblemDetector initialization."""
        assert self.detector.project_path == self.temp_dir
        assert self.detector.high_error_threshold == 100
        assert self.detector.error_density_threshold == 0.05
        assert self.detector.monolithic_file_threshold == 500
        assert "undefined_variables" in self.detector.structural_patterns
        assert "import_issues" in self.detector.structural_patterns

    def test_lines_of_code_estimation(self):
        """Test lines of code estimation."""
        # Create a test file
        test_content = "\n".join([f"line {i}" for i in range(50)])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            f.flush()

            lines = self.detector._estimate_lines_of_code(f.name)
            assert lines == 50

    def test_lines_of_code_estimation_fallback(self):
        """Test lines of code estimation fallback for non-existent files."""
        lines = self.detector._estimate_lines_of_code("non_existent_file.py")
        assert lines == 100  # Default fallback

    def test_complexity_indicators_calculation(self):
        """Test complexity indicators calculation."""
        # Mock error analyses
        mock_errors = [
            MagicMock(error=MagicMock(rule_id="max-len")),
            MagicMock(error=MagicMock(rule_id="max-len")),
            MagicMock(error=MagicMock(rule_id="max-statements")),
            MagicMock(error=MagicMock(rule_id="other-rule")),
        ]

        indicators = self.detector._calculate_complexity_indicators(mock_errors)

        assert indicators["max-len"] == 2
        assert indicators["max-statements"] == 1
        assert "other-rule" not in indicators

    def test_coupling_score_calculation(self):
        """Test coupling score calculation."""
        error_types = {"import/no-cycle", "no-global-assign", "other-error"}
        mock_errors = [MagicMock() for _ in range(10)]

        coupling_score = self.detector._calculate_coupling_score(error_types, mock_errors)

        assert 0 <= coupling_score <= 1
        assert coupling_score > 0  # Should have some coupling indicators

    def test_cohesion_score_calculation(self):
        """Test cohesion score calculation."""
        error_types = {"unused-import", "unused-variable", "other-error"}
        mock_errors = [MagicMock() for _ in range(10)]

        cohesion_score = self.detector._calculate_cohesion_score(error_types, mock_errors)

        assert 0 <= cohesion_score <= 1

    def test_file_metrics_calculation(self):
        """Test file-level metrics calculation."""
        # Create mock file analyses
        mock_file_analyses = {
            "test.py": MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="no-undef")),
                    MagicMock(error=MagicMock(rule_id="max-len")),
                    MagicMock(error=MagicMock(rule_id="import/no-cycle")),
                ]
            )
        }

        with patch.object(self.detector, "_estimate_lines_of_code", return_value=200):
            metrics = self.detector._calculate_file_metrics(mock_file_analyses)

        assert len(metrics) == 1
        file_metric = metrics[0]
        assert file_metric.file_path == "test.py"
        assert file_metric.error_count == 3
        assert file_metric.lines_of_code == 200
        assert file_metric.error_density == 3 / 200

    def test_monolithic_files_detection(self):
        """Test detection of monolithic files."""
        # Create metrics for a monolithic file
        metrics = [
            FileStructuralMetrics(
                file_path="monolithic.py",
                error_count=30,
                error_density=0.06,  # Above threshold
                lines_of_code=600,  # Above threshold
                error_types=set(),
                complexity_indicators={},
                coupling_score=0.5,
                cohesion_score=0.5,
            )
        ]

        issues = self.detector._detect_monolithic_files(metrics)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.problem_type == StructuralProblemType.MONOLITHIC_FILES
        assert issue.severity in ["high", "critical"]
        assert "monolithic.py" in issue.affected_files

    def test_tight_coupling_detection(self):
        """Test detection of tight coupling."""
        # Create metrics indicating tight coupling
        metrics = [
            FileStructuralMetrics(
                file_path=f"file_{i}.py",
                error_count=10,
                error_density=0.02,
                lines_of_code=200,
                error_types={"import/no-cycle", "no-global-assign"},
                complexity_indicators={},
                coupling_score=0.8,  # High coupling
                cohesion_score=0.5,
            )
            for i in range(5)  # Multiple files with high coupling
        ]

        # Mock file analyses for import pattern detection
        mock_file_analyses = {
            f"file_{i}.py": MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="import/no-cycle")),
                    MagicMock(error=MagicMock(rule_id="no-global-assign")),
                ]
            )
            for i in range(5)
        }

        issues = self.detector._detect_tight_coupling(metrics, mock_file_analyses)

        assert len(issues) >= 1
        issue = issues[0]
        assert issue.problem_type == StructuralProblemType.TIGHT_COUPLING
        assert len(issue.affected_files) > 0

    def test_complexity_hotspots_detection(self):
        """Test detection of complexity hotspots."""
        # Create metrics with high complexity
        metrics = [
            FileStructuralMetrics(
                file_path="complex.py",
                error_count=20,
                error_density=0.08,  # High density
                lines_of_code=250,
                error_types=set(),
                complexity_indicators={
                    "max-len": 15,
                    "max-statements": 8,
                },  # High complexity
                coupling_score=0.5,
                cohesion_score=0.5,
            )
        ]

        issues = self.detector._detect_complexity_hotspots(metrics)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.problem_type == StructuralProblemType.COMPLEXITY_HOTSPOTS
        assert "complex.py" in issue.affected_files

    def test_architectural_violations_detection(self):
        """Test detection of architectural violations."""
        # Create file analyses with many undefined variables
        mock_file_analyses = {}
        for i in range(3):  # 30% of 10 files
            mock_file_analyses[f"file_{i}.py"] = MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="no-undef"))
                    for _ in range(6)  # More than 5 undefined errors
                ]
            )

        # Add some files without undefined errors
        for i in range(3, 10):
            mock_file_analyses[f"file_{i}.py"] = MagicMock(
                error_analyses=[MagicMock(error=MagicMock(rule_id="other-rule"))]
            )

        metrics = [
            FileStructuralMetrics(
                file_path=f"file_{i}.py",
                error_count=5,
                error_density=0.02,
                lines_of_code=200,
                error_types=set(),
                complexity_indicators={},
                coupling_score=0.5,
                cohesion_score=0.5,
            )
            for i in range(10)
        ]

        issues = self.detector._detect_architectural_violations(metrics, mock_file_analyses)

        assert len(issues) >= 1
        issue = issues[0]
        assert issue.problem_type == StructuralProblemType.ARCHITECTURAL_VIOLATIONS

    def test_technical_debt_clusters_detection(self):
        """Test detection of technical debt clusters."""
        # Create metrics indicating high technical debt
        metrics = [
            FileStructuralMetrics(
                file_path="debt.py",
                error_count=25,
                error_density=0.1,  # High density
                lines_of_code=250,
                error_types=set(),
                complexity_indicators={"max-len": 10},
                coupling_score=0.8,  # High coupling
                cohesion_score=0.2,  # Low cohesion
            )
        ]

        issues = self.detector._detect_technical_debt_clusters(metrics)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.problem_type == StructuralProblemType.TECHNICAL_DEBT_CLUSTERS
        assert "debt.py" in issue.affected_files

    def test_hotspot_files_identification(self):
        """Test identification of hotspot files."""
        metrics = [
            FileStructuralMetrics(
                file_path="hotspot.py",
                error_count=50,  # High error count
                error_density=0.1,  # High density
                lines_of_code=500,
                error_types=set(),
                complexity_indicators={"max-len": 20},  # High complexity
                coupling_score=0.5,
                cohesion_score=0.5,
            ),
            FileStructuralMetrics(
                file_path="normal.py",
                error_count=5,  # Low error count
                error_density=0.01,  # Low density
                lines_of_code=500,
                error_types=set(),
                complexity_indicators={},
                coupling_score=0.3,
                cohesion_score=0.7,
            ),
        ]

        hotspots = self.detector._identify_hotspot_files(metrics)

        assert "hotspot.py" in hotspots
        assert "normal.py" not in hotspots

    def test_refactoring_candidates_identification(self):
        """Test identification of refactoring candidates."""
        metrics = [
            FileStructuralMetrics(
                file_path="candidate.py",
                error_count=15,
                error_density=0.06,  # Above threshold
                lines_of_code=250,  # Manageable size
                error_types=set(),
                complexity_indicators={},
                coupling_score=0.5,
                cohesion_score=0.5,
            )
        ]

        # Create a structural issue affecting this file
        structural_issues = [
            StructuralIssue(
                problem_type=StructuralProblemType.COMPLEXITY_HOTSPOTS,
                severity="high",
                description="High complexity",
                affected_files=["candidate.py"],
                error_count=15,
                confidence=0.8,
                recommendations=[],
                metrics={},
            )
        ]

        candidates = self.detector._identify_refactoring_candidates(metrics, structural_issues)

        assert "candidate.py" in candidates

    def test_architectural_score_calculation(self):
        """Test architectural health score calculation."""
        metrics = [
            FileStructuralMetrics(
                file_path="test.py",
                error_count=10,
                error_density=0.02,  # Low density
                lines_of_code=500,
                error_types=set(),
                complexity_indicators={},
                coupling_score=0.3,  # Low coupling
                cohesion_score=0.8,  # High cohesion
            )
        ]

        structural_issues = []  # No structural issues

        score = self.detector._calculate_architectural_score(metrics, structural_issues)

        assert 0 <= score <= 100
        assert score > 70  # Should be high with good metrics

    def test_architectural_recommendations_generation(self):
        """Test generation of architectural recommendations."""
        structural_issues = [
            StructuralIssue(
                problem_type=StructuralProblemType.MONOLITHIC_FILES,
                severity="high",
                description="Monolithic files detected",
                affected_files=["large.py"],
                error_count=50,
                confidence=0.8,
                recommendations=[],
                metrics={},
            )
        ]

        hotspot_files = ["hotspot1.py", "hotspot2.py"]
        total_errors = 150  # Above threshold

        recommendations = self.detector._generate_architectural_recommendations(
            structural_issues, hotspot_files, total_errors
        )

        assert len(recommendations) > 0
        assert any("CHAOTIC CODEBASE" in rec for rec in recommendations)
        assert any("monolithic" in rec.lower() for rec in recommendations)

    def test_full_structural_analysis_below_threshold(self):
        """Test structural analysis with error count below threshold."""
        # Mock file analyses with low error count
        mock_file_analyses = {
            "test.py": MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="minor-issue"))
                    for _ in range(5)  # Below 100 error threshold
                ]
            )
        }

        with patch.object(self.detector, "_estimate_lines_of_code", return_value=200):
            analysis = self.detector.analyze_structural_problems(mock_file_analyses)

        assert analysis.total_files == 1
        assert analysis.total_errors == 5
        assert len(analysis.structural_issues) == 0  # No structural analysis below threshold

    def test_full_structural_analysis_above_threshold(self):
        """Test structural analysis with error count above threshold."""
        # Mock file analyses with high error count
        mock_file_analyses = {}
        for i in range(10):
            mock_file_analyses[f"file_{i}.py"] = MagicMock(
                error_analyses=[
                    MagicMock(error=MagicMock(rule_id="error-type"))
                    for _ in range(15)  # 150 total errors, above threshold
                ]
            )

        with patch.object(self.detector, "_estimate_lines_of_code", return_value=200):
            analysis = self.detector.analyze_structural_problems(mock_file_analyses)

        assert analysis.total_files == 10
        assert analysis.total_errors == 150
        assert analysis.architectural_score >= 0
        assert len(analysis.recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__])
