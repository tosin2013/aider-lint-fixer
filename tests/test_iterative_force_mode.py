#!/usr/bin/env python3
"""
Tests for iterative_force_mode module.

Tests the IterativeForceMode class for intelligent iterative
force mode with loop detection and convergence analysis.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aider_lint_fixer.iterative_force_mode import (
    IterationResult,
    IterativeForceMode,
    LoopExitReason,
    LoopRecommendation,
)


class TestLoopExitReason(unittest.TestCase):
    """Test LoopExitReason enum."""

    def test_loop_exit_reason_values(self):
        """Test LoopExitReason enum values."""
        expected_values = [
            "max_iterations_reached",
            "improvement_threshold_not_met",
            "no_improvement",
            "diminishing_returns",
            "convergence_detected",
            "error_increase",
            "user_requested",
            "refactor_recommended",
            "budget_exceeded",
            "budget_predicted_exceeded",
        ]
        
        for value in expected_values:
            # Should be able to access the enum value
            self.assertTrue(hasattr(LoopExitReason, value.upper()))
            
        # Test specific enum values
        self.assertEqual(LoopExitReason.MAX_ITERATIONS_REACHED.value, "max_iterations_reached")
        self.assertEqual(LoopExitReason.BUDGET_EXCEEDED.value, "budget_exceeded")


class TestIterationResult(unittest.TestCase):
    """Test IterationResult dataclass."""

    def test_iteration_result_creation(self):
        """Test creating IterationResult objects."""
        result = IterationResult(
            iteration=1,
            errors_before=100,
            errors_after=80,
            errors_fixed=20,
            errors_attempted=25,
            success_rate=0.8,
            time_taken=120.5,
            new_errors_introduced=0,
            improvement_percentage=20.0,
            ml_accuracy=0.85,
            fixable_errors=75,
            cost=15.50,
            tokens_used=2500
        )

        self.assertEqual(result.iteration, 1)
        self.assertEqual(result.errors_before, 100)
        self.assertEqual(result.errors_after, 80)
        self.assertEqual(result.errors_fixed, 20)
        self.assertEqual(result.errors_attempted, 25)
        self.assertEqual(result.success_rate, 0.8)
        self.assertEqual(result.time_taken, 120.5)
        self.assertEqual(result.new_errors_introduced, 0)
        self.assertEqual(result.improvement_percentage, 20.0)
        self.assertEqual(result.ml_accuracy, 0.85)
        self.assertEqual(result.fixable_errors, 75)
        self.assertEqual(result.cost, 15.50)
        self.assertEqual(result.tokens_used, 2500)

    def test_iteration_result_defaults(self):
        """Test IterationResult with default values."""
        result = IterationResult(
            iteration=0,
            errors_before=50,
            errors_after=40,
            errors_fixed=10,
            errors_attempted=12,
            success_rate=0.83,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=20.0,
            ml_accuracy=0.75,
            fixable_errors=35
        )

        self.assertEqual(result.cost, 0.0)  # Default value
        self.assertEqual(result.tokens_used, 0)  # Default value


class TestLoopRecommendation(unittest.TestCase):
    """Test LoopRecommendation dataclass."""

    def test_loop_recommendation_creation(self):
        """Test creating LoopRecommendation objects."""
        recommendation = LoopRecommendation(
            action="continue",
            reason="Good progress being made",
            specific_suggestions=["Focus on file1.py", "Review error pattern X"],
            estimated_effort="medium",
            priority_files=["file1.py", "file2.py"],
            dangerous_patterns=["undefined_variable", "global_assignment"]
        )

        self.assertEqual(recommendation.action, "continue")
        self.assertEqual(recommendation.reason, "Good progress being made")
        self.assertEqual(len(recommendation.specific_suggestions), 2)
        self.assertEqual(recommendation.estimated_effort, "medium")
        self.assertEqual(len(recommendation.priority_files), 2)
        self.assertEqual(len(recommendation.dangerous_patterns), 2)

    def test_loop_recommendation_all_actions(self):
        """Test LoopRecommendation with different action types."""
        actions = ["continue", "manual_review", "refactor", "architect_mode"]
        
        for action in actions:
            recommendation = LoopRecommendation(
                action=action,
                reason=f"Reason for {action}",
                specific_suggestions=[f"Suggestion for {action}"],
                estimated_effort="low",
                priority_files=[],
                dangerous_patterns=[]
            )
            self.assertEqual(recommendation.action, action)


class TestIterativeForceMode(unittest.TestCase):
    """Test IterativeForceMode class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock dependencies
        self.mock_cost_monitor = Mock()
        self.mock_cost_monitor.get_iteration_cost.return_value = 0.0
        self.mock_cost_monitor.iteration_usage = {}  # Empty dict for iteration lookup
        self.mock_cost_monitor.check_budget_status.return_value = {"emergency_stop_needed": False}
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        self.mock_context_manager = Mock()
        
        with patch('aider_lint_fixer.iterative_force_mode.ContextManager'), \
             patch('aider_lint_fixer.iterative_force_mode.AdvancedConvergenceAnalyzer'):
            self.iterative_mode = IterativeForceMode(
                self.temp_dir,
                cost_monitor=self.mock_cost_monitor,
                context_manager=self.mock_context_manager
            )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    def test_initialization(self):
        """Test IterativeForceMode initialization."""
        self.assertEqual(self.iterative_mode.project_root, self.temp_dir)
        self.assertEqual(self.iterative_mode.max_iterations, 10)
        self.assertEqual(self.iterative_mode.improvement_threshold, 5)
        self.assertEqual(self.iterative_mode.diminishing_returns_threshold, 2)
        self.assertEqual(self.iterative_mode.convergence_window, 3)
        self.assertEqual(self.iterative_mode.max_error_increase_tolerance, 5)
        self.assertEqual(self.iterative_mode.cost_monitor, self.mock_cost_monitor)
        self.assertEqual(self.iterative_mode.context_manager, self.mock_context_manager)
        self.assertEqual(self.iterative_mode.iteration_results, [])
        self.assertEqual(self.iterative_mode.total_time, 0.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 0)

    def test_initialization_without_dependencies(self):
        """Test IterativeForceMode initialization without optional dependencies."""
        with patch('aider_lint_fixer.iterative_force_mode.ContextManager') as mock_cm_class, \
             patch('aider_lint_fixer.iterative_force_mode.AdvancedConvergenceAnalyzer'):
            mock_cm_instance = Mock()
            mock_cm_class.return_value = mock_cm_instance
            
            mode = IterativeForceMode(self.temp_dir)
            
            self.assertEqual(mode.project_root, self.temp_dir)
            self.assertIsNone(mode.cost_monitor)
            self.assertEqual(mode.context_manager, mock_cm_instance)

    def test_should_continue_loop_budget_exceeded(self):
        """Test should_continue_loop with budget exceeded."""
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": True,
            "total_cost": 150.0,
            "total_budget": 100.0
        }
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(1)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.BUDGET_EXCEEDED)
        self.assertIn("Budget exceeded", message)
        self.assertIn("$150.00", message)
        self.assertIn("$100.00", message)

    def test_should_continue_loop_budget_predicted_exceeded(self):
        """Test should_continue_loop with predicted budget exceeded."""
        # Setup mock for budget check (no emergency stop)
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False,
            "total_cost": 80.0,
            "total_budget": 100.0
        }
        
        # Setup mock for cost prediction
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 120.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        
        # Setup budget limits
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(1)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.BUDGET_PREDICTED_EXCEEDED)
        self.assertIn("Predicted cost", message)

    def test_should_continue_loop_max_iterations(self):
        """Test should_continue_loop with max iterations reached."""
        # Setup cost monitor to not trigger budget limits
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(
            self.iterative_mode.max_iterations
        )
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.MAX_ITERATIONS_REACHED)
        self.assertIn("Reached maximum iterations", message)

    def test_should_continue_loop_no_previous_results(self):
        """Test should_continue_loop with no previous iteration results."""
        # Setup cost monitor to not trigger budget limits
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(1)
        
        self.assertTrue(should_continue)
        self.assertIsNone(exit_reason)  # No exit reason when continuing
        self.assertIn("Need at least 2 iterations", message)

    def test_should_continue_loop_insufficient_improvement(self):
        """Test should_continue_loop with insufficient improvement."""
        # Setup cost monitor
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        # Add previous results with low improvement 
        first_result = IterationResult(
            iteration=1,
            errors_before=100,
            errors_after=99,
            errors_fixed=1,
            errors_attempted=10,
            success_rate=0.1,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=1.0,
            ml_accuracy=0.5,
            fixable_errors=50
        )
        
        second_result = IterationResult(
            iteration=2,
            errors_before=99,
            errors_after=98,  # Only 1% improvement
            errors_fixed=1,
            errors_attempted=10,
            success_rate=0.1,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=1.0,
            ml_accuracy=0.5,
            fixable_errors=50
        )
        self.iterative_mode.iteration_results = [first_result, second_result]
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(3)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET)
        self.assertIn("below threshold", message)

    def test_should_continue_loop_error_increase(self):
        """Test should_continue_loop with error increase."""
        # Setup cost monitor
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        # Add previous results with error increase
        initial_result = IterationResult(
            iteration=1,
            errors_before=100,
            errors_after=50,  # Initial improvement
            errors_fixed=50,
            errors_attempted=50,
            success_rate=1.0,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=50.0,
            ml_accuracy=0.8,
            fixable_errors=50
        )
        
        error_increase_result = IterationResult(
            iteration=2,
            errors_before=50,
            errors_after=60,  # Errors increased by 10 (more than tolerance of 5)
            errors_fixed=0,
            errors_attempted=5,
            success_rate=0.0,
            time_taken=60.0,
            new_errors_introduced=10,
            improvement_percentage=-20.0,
            ml_accuracy=0.3,
            fixable_errors=40
        )
        self.iterative_mode.iteration_results = [initial_result, error_increase_result]
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(3)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.ERROR_INCREASE)
        self.assertIn("Errors increased", message)

    def test_should_continue_loop_convergence_detected(self):
        """Test should_continue_loop with convergence detected."""
        # Setup cost monitor with proper mocking
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        self.mock_cost_monitor.get_iteration_cost.return_value = 10.0
        self.mock_cost_monitor.iteration_usage = {}  # Empty dict for iteration lookup
        
        # Add sufficient results for convergence detection using record_iteration_result
        for i in range(5):
            self.iterative_mode.record_iteration_result(
                iteration=i+1,
                errors_before=100-i*10,
                errors_after=90-i*10,
                errors_fixed=10,
                errors_attempted=15,
                success_rate=0.67,
                time_taken=60.0,
                new_errors_introduced=0,
                improvement_percentage=11.0,  # Good improvement
                ml_accuracy=0.8,
                fixable_errors=80-i*10
            )
        
        # Mock convergence analyzer to detect convergence - fix the return structure
        from aider_lint_fixer.convergence_analyzer import ConvergenceAnalysis, ConvergenceState
        mock_convergence_analysis = ConvergenceAnalysis(
            current_state=ConvergenceState.CONVERGED,
            confidence=0.95,
            predicted_final_errors=50,
            predicted_iterations_remaining=0,
            improvement_potential=0.1,
            stopping_recommendation="Stop - converged"
        )
        self.iterative_mode.convergence_analyzer.analyze_convergence.return_value = mock_convergence_analysis
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(6)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.CONVERGENCE_DETECTED)

    def test_should_continue_loop_diminishing_returns(self):
        """Test should_continue_loop with diminishing returns."""
        # Setup cost monitor
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        # Add results showing diminishing returns
        results = [
            IterationResult(1, 100, 99, 1, 10, 0.1, 60.0, 0, 1.0, 0.8, 80),   # Low progress
            IterationResult(2, 99, 98, 1, 10, 0.1, 60.0, 0, 1.0, 0.7, 75),    # Low progress  
            IterationResult(3, 98, 93, 5, 8, 0.625, 60.0, 0, 5.1, 0.6, 70),   # Just above threshold
        ]
        self.iterative_mode.iteration_results = results
        
        # Set threshold higher than average improvement to trigger diminishing returns
        # Average of [1.0, 1.0, 5.1] = 2.37, so set threshold to 3.0
        self.iterative_mode.diminishing_returns_threshold = 3.0
        
        # Mock convergence analyzer
        mock_convergence_state = Mock()
        mock_convergence_state.is_converged = False
        self.iterative_mode.convergence_analyzer.analyze_iteration_data.return_value = mock_convergence_state
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(4)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.DIMINISHING_RETURNS)
        self.assertIn("diminishing returns", message.lower())

    def test_should_continue_loop_continue_case(self):
        """Test should_continue_loop when it should continue."""
        # Setup cost monitor
        self.mock_cost_monitor.check_budget_status.return_value = {
            "emergency_stop_needed": False
        }
        mock_prediction = Mock()
        mock_prediction.predicted_total_cost = 50.0
        self.mock_cost_monitor.predict_total_cost.return_value = mock_prediction
        mock_budget_limits = Mock()
        mock_budget_limits.max_total_cost = 100.0
        self.mock_cost_monitor.budget_limits = mock_budget_limits
        
        # Add result with good improvement
        previous_result = IterationResult(
            iteration=1,
            errors_before=100,
            errors_after=80,  # 20% improvement
            errors_fixed=20,
            errors_attempted=25,
            success_rate=0.8,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=20.0,
            ml_accuracy=0.8,
            fixable_errors=75
        )
        self.iterative_mode.iteration_results = [previous_result]
        
        # Mock convergence analyzer
        mock_convergence_state = Mock()
        mock_convergence_state.is_converged = False
        self.iterative_mode.convergence_analyzer.analyze_iteration_data.return_value = mock_convergence_state
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(2)
        
        self.assertTrue(should_continue)

    def test_should_continue_loop_without_cost_monitor(self):
        """Test should_continue_loop without cost monitor."""
        # Create instance without cost monitor
        with patch('aider_lint_fixer.iterative_force_mode.ContextManager'), \
             patch('aider_lint_fixer.iterative_force_mode.AdvancedConvergenceAnalyzer'):
            mode = IterativeForceMode(self.temp_dir, cost_monitor=None)
        
        should_continue, exit_reason, message = mode.should_continue_loop(1)
        
        # Should continue since no budget constraints
        self.assertTrue(should_continue)

    def test_detect_diminishing_returns_true(self):
        """Test should_continue_loop detects diminishing returns."""
        # Add results showing diminishing returns - make sure current > 5% but average < 2%
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=99, errors_fixed=1, 
            errors_attempted=10, success_rate=0.1, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=1.0, 
            ml_accuracy=0.8, fixable_errors=80
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=99, errors_after=98, errors_fixed=1, 
            errors_attempted=10, success_rate=0.1, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=1.0, 
            ml_accuracy=0.7, fixable_errors=75
        )
        self.iterative_mode.record_iteration_result(
            iteration=3, errors_before=98, errors_after=90, errors_fixed=8, 
            errors_attempted=8, success_rate=1.0, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=8.2, 
            ml_accuracy=0.6, fixable_errors=70
        )
        
        # Set threshold high enough that average improvement triggers diminishing returns  
        # Average of [1.0, 1.0, 8.2] = 3.4, so set threshold to 4.0
        self.iterative_mode.diminishing_returns_threshold = 4.0
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(4)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.DIMINISHING_RETURNS)

    def test_detect_diminishing_returns_false(self):
        """Test should_continue_loop continues with good progress."""
        # Add results showing good progress
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=85, errors_fixed=15, 
            errors_attempted=20, success_rate=0.75, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=15.0, 
            ml_accuracy=0.8, fixable_errors=80
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=85, errors_after=70, errors_fixed=15, 
            errors_attempted=18, success_rate=0.83, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=17.6, 
            ml_accuracy=0.85, fixable_errors=65
        )
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(3)
        
        self.assertTrue(should_continue)

    def test_detect_diminishing_returns_insufficient_data(self):
        """Test should_continue_loop with insufficient data."""
        # Only one result
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=85, errors_fixed=15, 
            errors_attempted=20, success_rate=0.75, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=15.0, 
            ml_accuracy=0.8, fixable_errors=80
        )
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(2)
        
        self.assertTrue(should_continue)

    def test_add_iteration_result(self):
        """Test record_iteration_result method."""
        self.iterative_mode.record_iteration_result(
            iteration=1,
            errors_before=100,
            errors_after=85,
            errors_fixed=15,
            errors_attempted=20,
            success_rate=0.75,
            time_taken=120.0,
            new_errors_introduced=0,
            improvement_percentage=15.0,
            ml_accuracy=0.8,
            fixable_errors=80
        )
        
        self.assertEqual(len(self.iterative_mode.iteration_results), 1)
        recorded_result = self.iterative_mode.iteration_results[0]
        self.assertEqual(recorded_result.iteration, 1)
        self.assertEqual(recorded_result.errors_before, 100)
        self.assertEqual(recorded_result.errors_after, 85)
        self.assertEqual(recorded_result.errors_fixed, 15)
        self.assertEqual(recorded_result.success_rate, 0.75)
        self.assertEqual(self.iterative_mode.total_time, 120.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 15)

    def test_add_multiple_iteration_results(self):
        """Test adding multiple iteration results."""
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=85, errors_fixed=15, 
            errors_attempted=20, success_rate=0.75, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=15.0, 
            ml_accuracy=0.8, fixable_errors=80
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=85, errors_after=70, errors_fixed=15, 
            errors_attempted=18, success_rate=0.83, time_taken=90.0, 
            new_errors_introduced=0, improvement_percentage=17.6, 
            ml_accuracy=0.85, fixable_errors=65
        )
        
        self.assertEqual(len(self.iterative_mode.iteration_results), 2)
        self.assertEqual(self.iterative_mode.total_time, 150.0)  # 60 + 90
        self.assertEqual(self.iterative_mode.total_errors_fixed, 30)  # 15 + 15

    def test_get_performance_summary(self):
        """Test analyze_iteration_patterns method."""
        # Add some iteration results
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=85, errors_fixed=15, 
            errors_attempted=20, success_rate=0.75, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=15.0, 
            ml_accuracy=0.8, fixable_errors=80
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=85, errors_after=70, errors_fixed=15, 
            errors_attempted=18, success_rate=0.83, time_taken=90.0, 
            new_errors_introduced=0, improvement_percentage=17.6, 
            ml_accuracy=0.85, fixable_errors=65
        )
        
        summary = self.iterative_mode.analyze_iteration_patterns()
        
        self.assertIn("total_iterations", summary)
        self.assertIn("total_errors_eliminated", summary)
        self.assertIn("total_time", summary)
        self.assertIn("average_improvement_per_iteration", summary)
        self.assertIn("total_cost", summary)
        self.assertIn("total_tokens", summary)
        
        self.assertEqual(summary["total_iterations"], 2)
        self.assertEqual(summary["total_errors_eliminated"], 30)  # 100 - 70
        self.assertEqual(summary["total_time"], 150.0)
        self.assertAlmostEqual(summary["average_improvement_per_iteration"], 16.3, places=1)

    def test_get_performance_summary_empty(self):
        """Test analyze_iteration_patterns with no results."""
        summary = self.iterative_mode.analyze_iteration_patterns()
        
        self.assertEqual(summary, {})

    def test_generate_recommendations_continue(self):
        """Test generate_recommendations for continue case."""
        exit_reason = LoopExitReason.MAX_ITERATIONS_REACHED
        
        # Add good results
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=80, errors_fixed=20, 
            errors_attempted=25, success_rate=0.8, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=20.0, 
            ml_accuracy=0.85, fixable_errors=75
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=80, errors_after=60, errors_fixed=20, 
            errors_attempted=22, success_rate=0.91, time_taken=70.0, 
            new_errors_introduced=0, improvement_percentage=25.0, 
            ml_accuracy=0.87, fixable_errors=55
        )
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason, "Maximum iterations reached")
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "continue")
        self.assertIn("still showing improvement", recommendation.reason.lower())

    def test_generate_recommendations_refactor(self):
        """Test generate_recommendations for refactor case."""
        exit_reason = LoopExitReason.DIMINISHING_RETURNS
        
        # Add results showing poor progress over many iterations
        for i in range(6):
            self.iterative_mode.record_iteration_result(
                iteration=i+1,
                errors_before=100-i*2,
                errors_after=98-i*2,
                errors_fixed=2,
                errors_attempted=10,
                success_rate=0.2,
                time_taken=60.0,
                new_errors_introduced=0,
                improvement_percentage=2.0,
                ml_accuracy=0.5,
                fixable_errors=90-i*2
            )
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason, "Diminishing returns detected")
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "architect_mode")
        self.assertIn("expert analysis", recommendation.reason.lower())

    def test_generate_recommendations_manual_review(self):
        """Test generate_recommendations for manual_review case."""
        exit_reason = LoopExitReason.ERROR_INCREASE
        
        # Add result with error increase
        self.iterative_mode.record_iteration_result(
            iteration=1,
            errors_before=50,
            errors_after=60,
            errors_fixed=0,
            errors_attempted=10,
            success_rate=0.0,
            time_taken=60.0,
            new_errors_introduced=10,
            improvement_percentage=-20.0,
            ml_accuracy=0.3,
            fixable_errors=40
        )
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason, "Error increase detected")
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "manual_review")
        self.assertIn("introducing new errors", recommendation.reason.lower())

    def test_generate_recommendations_architect_mode(self):
        """Test generate_recommendations for architect_mode case."""
        exit_reason = LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET
        
        # Add results with very low success rate
        for i in range(3):
            self.iterative_mode.record_iteration_result(
                iteration=i+1,
                errors_before=100,
                errors_after=98,
                errors_fixed=2,
                errors_attempted=20,
                success_rate=0.1,  # Very low success rate
                time_taken=60.0,
                new_errors_introduced=0,
                improvement_percentage=2.0,
                ml_accuracy=0.3,
                fixable_errors=95
            )
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason, "Improvement threshold not met")
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "manual_review")
        self.assertIn("threshold not met", recommendation.reason.lower())

    def test_display_performance_summary_with_data(self):
        """Test display_loop_summary with data."""
        # Add iteration results
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=80, errors_fixed=20, 
            errors_attempted=25, success_rate=0.8, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=20.0, 
            ml_accuracy=0.85, fixable_errors=75
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=80, errors_after=60, errors_fixed=20, 
            errors_attempted=22, success_rate=0.91, time_taken=70.0, 
            new_errors_introduced=0, improvement_percentage=25.0, 
            ml_accuracy=0.87, fixable_errors=55
        )
        
        with patch('builtins.print') as mock_print:
            self.iterative_mode.display_loop_summary(
                LoopExitReason.MAX_ITERATIONS_REACHED, 
                "Reached maximum iterations"
            )
            
            # Check that print was called
            self.assertTrue(mock_print.called)
            
            # Check for expected content in print calls
            print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
            
            summary_found = any("ITERATIVE FORCE MODE SUMMARY" in str(call) for call in print_calls)
            self.assertTrue(summary_found)

    def test_display_performance_summary_empty(self):
        """Test display_loop_summary with no data."""
        with patch('builtins.print') as mock_print:
            self.iterative_mode.display_loop_summary(
                LoopExitReason.MAX_ITERATIONS_REACHED, 
                "No iterations completed"
            )
            
            # Should still print something
            self.assertTrue(mock_print.called)

    def test_reset_state(self):
        """Test that new IterativeForceMode starts with clean state."""
        # Add some data
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=80, errors_fixed=20, 
            errors_attempted=25, success_rate=0.8, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=20.0, 
            ml_accuracy=0.85, fixable_errors=75
        )
        
        # Verify data exists
        self.assertEqual(len(self.iterative_mode.iteration_results), 1)
        self.assertEqual(self.iterative_mode.total_time, 60.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 20)
        
        # Create new instance (simulates reset)
        new_iterative_mode = IterativeForceMode(self.temp_dir)
        
        # Verify new instance starts clean
        self.assertEqual(len(new_iterative_mode.iteration_results), 0)
        self.assertEqual(new_iterative_mode.total_time, 0.0)
        self.assertEqual(new_iterative_mode.total_errors_fixed, 0)

    def test_get_iteration_insights(self):
        """Test analyze_iteration_patterns method for insights."""
        # Add iteration results with patterns
        self.iterative_mode.record_iteration_result(
            iteration=1, errors_before=100, errors_after=80, errors_fixed=20, 
            errors_attempted=25, success_rate=0.8, time_taken=60.0, 
            new_errors_introduced=0, improvement_percentage=20.0, 
            ml_accuracy=0.85, fixable_errors=75
        )
        self.iterative_mode.record_iteration_result(
            iteration=2, errors_before=80, errors_after=65, errors_fixed=15, 
            errors_attempted=20, success_rate=0.75, time_taken=70.0, 
            new_errors_introduced=0, improvement_percentage=18.8, 
            ml_accuracy=0.82, fixable_errors=60
        )
        self.iterative_mode.record_iteration_result(
            iteration=3, errors_before=65, errors_after=50, errors_fixed=15, 
            errors_attempted=18, success_rate=0.83, time_taken=65.0, 
            new_errors_introduced=0, improvement_percentage=23.1, 
            ml_accuracy=0.88, fixable_errors=45
        )
        
        insights = self.iterative_mode.analyze_iteration_patterns()
        
        self.assertIn("total_iterations", insights)
        self.assertIn("improvement_trend", insights)
        self.assertIn("success_rate_trend", insights)
        self.assertIn("ml_learning_trend", insights)
        
        self.assertEqual(insights["total_iterations"], 3)
        # Check trends based on first vs last values
        self.assertIn(insights["improvement_trend"], ["increasing", "decreasing"])
        self.assertIn(insights["success_rate_trend"], ["improving", "declining"])

    def test_get_iteration_insights_empty(self):
        """Test analyze_iteration_patterns with no data."""
        insights = self.iterative_mode.analyze_iteration_patterns()
        
        self.assertEqual(insights, {})


if __name__ == "__main__":
    unittest.main()