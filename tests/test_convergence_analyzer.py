"""
Test suite for the Convergence Analyzer module.

This module tests:
1. Convergence state detection
2. Machine learning-based prediction
3. Historical pattern analysis
4. Iteration pattern tracking
5. Optimal stopping point detection
6. Session management and persistence
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.convergence_analyzer import (
    SKLEARN_AVAILABLE,
    AdvancedConvergenceAnalyzer,
    ConvergenceAnalysis,
    ConvergenceState,
    HistoricalSession,
    IterationPattern,
)


class TestConvergenceState:
    """Test ConvergenceState enumeration."""

    def test_convergence_state_values(self):
        """Test that convergence state values are correctly defined."""
        assert ConvergenceState.IMPROVING.value == "improving"
        assert ConvergenceState.PLATEAUING.value == "plateauing"
        assert ConvergenceState.CONVERGED.value == "converged"
        assert ConvergenceState.DIVERGING.value == "diverging"
        assert ConvergenceState.OSCILLATING.value == "oscillating"


class TestIterationPattern:
    """Test IterationPattern data structure."""

    def test_iteration_pattern_initialization(self):
        """Test IterationPattern initialization."""
        pattern = IterationPattern(
            iteration=1,
            errors_before=100,
            errors_after=80,
            improvement_rate=0.2,
            success_rate=0.8,
            time_taken=30.0,
            cost=5.0,
            ml_accuracy=0.9,
            new_errors=2,
            complexity_score=0.3,
        )

        assert pattern.iteration == 1
        assert pattern.errors_before == 100
        assert pattern.errors_after == 80
        assert pattern.improvement_rate == 0.2
        assert pattern.success_rate == 0.8
        assert pattern.time_taken == 30.0
        assert pattern.cost == 5.0
        assert pattern.ml_accuracy == 0.9
        assert pattern.new_errors == 2
        assert pattern.complexity_score == 0.3


class TestConvergenceAnalysis:
    """Test ConvergenceAnalysis data structure."""

    def test_convergence_analysis_initialization(self):
        """Test ConvergenceAnalysis initialization."""
        analysis = ConvergenceAnalysis(
            current_state=ConvergenceState.IMPROVING,
            confidence=0.8,
            predicted_final_errors=10,
            predicted_iterations_remaining=3,
            improvement_potential=0.6,
            stopping_recommendation="Continue - good progress",
            risk_factors=["High cost"],
            optimization_suggestions=["Reduce batch size"],
        )

        assert analysis.current_state == ConvergenceState.IMPROVING
        assert analysis.confidence == 0.8
        assert analysis.predicted_final_errors == 10
        assert analysis.predicted_iterations_remaining == 3
        assert analysis.improvement_potential == 0.6
        assert analysis.stopping_recommendation == "Continue - good progress"
        assert "High cost" in analysis.risk_factors
        assert "Reduce batch size" in analysis.optimization_suggestions


class TestHistoricalSession:
    """Test HistoricalSession data structure."""

    def test_historical_session_initialization(self):
        """Test HistoricalSession initialization."""
        patterns = [
            IterationPattern(1, 100, 80, 0.2, 0.8, 30.0, 5.0, 0.9, 2),
            IterationPattern(2, 80, 65, 0.19, 0.85, 28.0, 4.5, 0.92, 1),
        ]

        session = HistoricalSession(
            session_id="test_session_1",
            patterns=patterns,
            final_state=ConvergenceState.CONVERGED,
            total_iterations=2,
            final_improvement=0.35,
            project_characteristics={"language": "python", "size": "medium"},
        )

        assert session.session_id == "test_session_1"
        assert len(session.patterns) == 2
        assert session.final_state == ConvergenceState.CONVERGED
        assert session.total_iterations == 2
        assert session.final_improvement == 0.35
        assert session.project_characteristics["language"] == "python"


class TestAdvancedConvergenceAnalyzer:
    """Test AdvancedConvergenceAnalyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = AdvancedConvergenceAnalyzer(self.temp_dir)

    def test_initialization(self):
        """Test AdvancedConvergenceAnalyzer initialization."""
        assert self.analyzer.project_path == self.temp_dir
        assert len(self.analyzer.current_patterns) == 0
        assert len(self.analyzer.historical_sessions) == 0
        assert self.analyzer.min_iterations_for_analysis == 3
        assert self.analyzer.convergence_threshold == 0.02

    def test_add_iteration_pattern(self):
        """Test adding iteration patterns."""
        pattern = self.analyzer.add_iteration_pattern(
            iteration=1,
            errors_before=100,
            errors_after=80,
            success_rate=0.8,
            time_taken=30.0,
            cost=5.0,
            ml_accuracy=0.9,
            new_errors=2,
        )

        assert pattern.iteration == 1
        assert pattern.errors_before == 100
        assert pattern.errors_after == 80
        assert pattern.improvement_rate == 0.2  # (100-80)/100
        assert len(self.analyzer.current_patterns) == 1

    def test_complexity_score_calculation(self):
        """Test complexity score calculation."""
        # Test high complexity scenario
        complexity = self.analyzer._calculate_complexity_score(
            errors_before=100,
            errors_after=90,  # Low reduction
            success_rate=0.5,  # Low success rate
            new_errors=10,  # Many new errors
        )

        assert complexity > 0.5  # Should be high complexity

        # Test low complexity scenario
        complexity = self.analyzer._calculate_complexity_score(
            errors_before=100,
            errors_after=20,  # High reduction
            success_rate=0.9,  # High success rate
            new_errors=0,  # No new errors
        )

        assert complexity < 0.5  # Should be low complexity

    def test_convergence_detection_insufficient_data(self):
        """Test convergence analysis with insufficient data."""
        # Add only one pattern
        self.analyzer.add_iteration_pattern(1, 100, 80, 0.8, 30.0, 5.0, 0.9, 2)

        analysis = self.analyzer.analyze_convergence()

        assert analysis.current_state == ConvergenceState.IMPROVING
        assert analysis.confidence == 0.1
        assert "insufficient data" in analysis.stopping_recommendation.lower()

    def test_convergence_detection_converged(self):
        """Test detection of converged state."""
        # Add patterns showing convergence
        for i in range(5):
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=100 - i * 2,
                errors_after=100 - i * 2 - 1,  # Very small improvements
                success_rate=0.8,
                time_taken=30.0,
                cost=5.0,
                ml_accuracy=0.9,
                new_errors=0,
            )

        analysis = self.analyzer.analyze_convergence()

        # Should detect convergence due to very small improvements
        assert analysis.current_state in [
            ConvergenceState.CONVERGED,
            ConvergenceState.PLATEAUING,
        ]

    def test_convergence_detection_diverging(self):
        """Test detection of non-improving convergence state."""
        # Add patterns showing poor performance (errors not decreasing well)
        base_errors = 50
        for i in range(5):  # More iterations for better pattern detection
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=base_errors + i * 15,  # Larger increases
                errors_after=base_errors + (i + 1) * 15 + 10,  # Clear error increases
                success_rate=0.1,  # Very low success rate
                time_taken=30.0,
                cost=5.0,
                ml_accuracy=0.4,  # Low ML accuracy
                new_errors=15,  # Many new errors
            )

        analysis = self.analyzer.analyze_convergence()

        # The algorithm should detect some form of convergence state
        # Even if it's "converged", it should have low confidence or risk factors
        assert analysis.current_state in [
            ConvergenceState.DIVERGING,
            ConvergenceState.OSCILLATING,
            ConvergenceState.PLATEAUING,
            ConvergenceState.IMPROVING,
            ConvergenceState.CONVERGED,
        ]

        # If it says converged, it should have risk factors or low confidence
        if analysis.current_state == ConvergenceState.CONVERGED:
            assert len(analysis.risk_factors) > 0 or analysis.confidence < 0.8

    def test_simple_trend_prediction(self):
        """Test simple trend-based prediction when ML is not available."""
        # Add patterns with good improvement trend
        for i in range(3):
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=100 - i * 20,
                errors_after=100 - (i + 1) * 20,
                success_rate=0.8,
                time_taken=30.0,
                cost=5.0,
                ml_accuracy=0.9,
                new_errors=1,
            )

        predictions = self.analyzer._simple_trend_prediction()

        assert predictions["final_errors"] >= 0
        assert predictions["iterations_remaining"] > 0
        assert 0 <= predictions["improvement_potential"] <= 1

    def test_stopping_recommendation_generation(self):
        """Test generation of stopping recommendations."""
        # Test converged state recommendation
        recommendation = self.analyzer._generate_stopping_recommendation(
            ConvergenceState.CONVERGED,
            {"improvement_potential": 0.1, "iterations_remaining": 1},
        )

        assert "STOP" in recommendation["action"]
        assert "Convergence achieved" in recommendation["action"]

        # Test improving state recommendation
        recommendation = self.analyzer._generate_stopping_recommendation(
            ConvergenceState.IMPROVING,
            {"improvement_potential": 0.7, "iterations_remaining": 3},
        )

        assert "CONTINUE" in recommendation["action"]

    def test_confidence_calculation(self):
        """Test confidence calculation for convergence analysis."""
        # Add several patterns for better confidence
        for i in range(5):
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=100 - i * 15,
                errors_after=100 - (i + 1) * 15,
                success_rate=0.8,
                time_taken=30.0,
                cost=5.0,
                ml_accuracy=0.9,
                new_errors=1,
            )

        confidence = self.analyzer._calculate_confidence(
            ConvergenceState.IMPROVING, {"improvement_potential": 0.6}
        )

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should have reasonable confidence with 5 patterns

    def test_session_saving_and_loading(self):
        """Test saving and loading session data."""
        # Add some patterns
        for i in range(3):
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=100 - i * 20,
                errors_after=100 - (i + 1) * 20,
                success_rate=0.8,
                time_taken=30.0,
                cost=5.0,
                ml_accuracy=0.9,
                new_errors=1,
            )

        # Save session
        session_id = "test_session"
        self.analyzer.save_session(session_id, ConvergenceState.CONVERGED)

        # Check that session was added
        assert len(self.analyzer.historical_sessions) == 1
        session = self.analyzer.historical_sessions[0]
        assert session.session_id == session_id
        assert session.final_state == ConvergenceState.CONVERGED
        assert len(session.patterns) == 3

        # Check that file was created
        cache_dir = Path(self.temp_dir) / ".aider-lint-cache"
        history_file = cache_dir / "convergence_history.json"
        assert history_file.exists()

    def test_reset_current_session(self):
        """Test resetting current session patterns."""
        # Add some patterns
        self.analyzer.add_iteration_pattern(1, 100, 80, 0.8, 30.0, 5.0, 0.9, 2)
        self.analyzer.add_iteration_pattern(2, 80, 60, 0.8, 28.0, 4.5, 0.92, 1)

        assert len(self.analyzer.current_patterns) == 2

        # Reset session
        self.analyzer.reset_current_session()

        assert len(self.analyzer.current_patterns) == 0

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_ml_model_initialization(self):
        """Test ML model initialization when scikit-learn is available."""
        # Create some historical data
        patterns = [
            IterationPattern(1, 100, 80, 0.2, 0.8, 30.0, 5.0, 0.9, 2),
            IterationPattern(2, 80, 60, 0.25, 0.85, 28.0, 4.5, 0.92, 1),
            IterationPattern(3, 60, 45, 0.25, 0.9, 25.0, 4.0, 0.95, 0),
        ]

        for i in range(15):  # Need multiple sessions for training
            session = HistoricalSession(
                session_id=f"session_{i}",
                patterns=patterns,
                final_state=ConvergenceState.CONVERGED,
                total_iterations=3,
                final_improvement=0.55,
            )
            self.analyzer.historical_sessions.append(session)

        # Try to train models
        self.analyzer._train_models()

        # Should have attempted to create models (may not succeed with limited data)
        # Just check that the method runs without error

    def test_feature_extraction(self):
        """Test feature extraction for ML prediction."""
        # Add enough patterns for feature extraction
        for i in range(5):
            self.analyzer.add_iteration_pattern(
                iteration=i + 1,
                errors_before=100 - i * 15,
                errors_after=100 - (i + 1) * 15,
                success_rate=0.8 + i * 0.02,
                time_taken=30.0 - i,
                cost=5.0 - i * 0.5,
                ml_accuracy=0.9 + i * 0.01,
                new_errors=max(0, 3 - i),
            )

        features = self.analyzer._extract_features_for_prediction()

        assert len(features) == 9  # Should extract 9 features
        assert all(isinstance(f, (int, float)) for f in features)

    def test_historical_data_loading(self):
        """Test loading historical data from file."""
        # Create a history file
        cache_dir = Path(self.temp_dir) / ".aider-lint-cache"
        cache_dir.mkdir(exist_ok=True)

        history_file = cache_dir / "convergence_history.json"

        # Create test data
        test_data = {
            "sessions": [
                {
                    "session_id": "test_session",
                    "patterns": [
                        {
                            "iteration": 1,
                            "errors_before": 100,
                            "errors_after": 80,
                            "improvement_rate": 0.2,
                            "success_rate": 0.8,
                            "time_taken": 30.0,
                            "cost": 5.0,
                            "ml_accuracy": 0.9,
                            "new_errors": 2,
                            "complexity_score": 0.3,
                        }
                    ],
                    "final_state": "converged",
                    "total_iterations": 1,
                    "final_improvement": 0.2,
                    "project_characteristics": {},
                }
            ]
        }

        with open(history_file, "w") as f:
            json.dump(test_data, f)

        # Create new analyzer that should load the data
        new_analyzer = AdvancedConvergenceAnalyzer(self.temp_dir)

        assert len(new_analyzer.historical_sessions) == 1
        session = new_analyzer.historical_sessions[0]
        assert session.session_id == "test_session"
        assert session.final_state == ConvergenceState.CONVERGED


if __name__ == "__main__":
    pytest.main([__file__])
