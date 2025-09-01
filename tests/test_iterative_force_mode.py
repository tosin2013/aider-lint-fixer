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
        self.assertIn("Maximum iterations", message)

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
        self.assertEqual(exit_reason, LoopExitReason.MAX_ITERATIONS_REACHED)  # Default
        self.assertIn("Continue iteration", message)

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
        
        # Add previous result with low improvement
        previous_result = IterationResult(
            iteration=1,
            errors_before=100,
            errors_after=98,  # Only 2% improvement
            errors_fixed=2,
            errors_attempted=10,
            success_rate=0.2,
            time_taken=60.0,
            new_errors_introduced=0,
            improvement_percentage=2.0,
            ml_accuracy=0.5,
            fixable_errors=50
        )
        self.iterative_mode.iteration_results = [previous_result]
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(2)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET)
        self.assertIn("Insufficient improvement", message)

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
        
        # Add previous result with error increase
        previous_result = IterationResult(
            iteration=1,
            errors_before=50,
            errors_after=60,  # Errors increased by 10
            errors_fixed=0,
            errors_attempted=5,
            success_rate=0.0,
            time_taken=60.0,
            new_errors_introduced=10,
            improvement_percentage=-20.0,
            ml_accuracy=0.3,
            fixable_errors=40
        )
        self.iterative_mode.iteration_results = [previous_result]
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(2)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.ERROR_INCREASE)
        self.assertIn("Errors increased", message)

    def test_should_continue_loop_convergence_detected(self):
        """Test should_continue_loop with convergence detected."""
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
        
        # Add sufficient results for convergence detection
        results = []
        for i in range(5):
            result = IterationResult(
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
            results.append(result)
        self.iterative_mode.iteration_results = results
        
        # Mock convergence analyzer to detect convergence
        mock_convergence_state = Mock()
        mock_convergence_state.is_converged = True
        self.iterative_mode.convergence_analyzer.analyze_iteration_data.return_value = mock_convergence_state
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(6)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.CONVERGENCE_DETECTED)
        self.assertIn("Convergence detected", message)

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
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80),  # Good progress
            IterationResult(2, 85, 82, 3, 10, 0.3, 60.0, 0, 3.5, 0.7, 75),   # Diminishing
            IterationResult(3, 82, 81, 1, 8, 0.125, 60.0, 0, 1.2, 0.6, 70),  # Very low
        ]
        self.iterative_mode.iteration_results = results
        
        # Mock convergence analyzer
        mock_convergence_state = Mock()
        mock_convergence_state.is_converged = False
        self.iterative_mode.convergence_analyzer.analyze_iteration_data.return_value = mock_convergence_state
        
        should_continue, exit_reason, message = self.iterative_mode.should_continue_loop(4)
        
        self.assertFalse(should_continue)
        self.assertEqual(exit_reason, LoopExitReason.DIMINISHING_RETURNS)
        self.assertIn("Diminishing returns", message)

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
        """Test _detect_diminishing_returns returns True."""
        # Add results showing diminishing returns
        results = [
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80),  # Good
            IterationResult(2, 85, 82, 3, 10, 0.3, 60.0, 0, 3.5, 0.7, 75),     # Low
            IterationResult(3, 82, 81, 1, 8, 0.125, 60.0, 0, 1.2, 0.6, 70),    # Very low
        ]
        self.iterative_mode.iteration_results = results
        
        is_diminishing = self.iterative_mode._detect_diminishing_returns()
        
        self.assertTrue(is_diminishing)

    def test_detect_diminishing_returns_false(self):
        """Test _detect_diminishing_returns returns False."""
        # Add results showing good progress
        results = [
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80),
            IterationResult(2, 85, 70, 15, 18, 0.83, 60.0, 0, 17.6, 0.85, 65),
        ]
        self.iterative_mode.iteration_results = results
        
        is_diminishing = self.iterative_mode._detect_diminishing_returns()
        
        self.assertFalse(is_diminishing)

    def test_detect_diminishing_returns_insufficient_data(self):
        """Test _detect_diminishing_returns with insufficient data."""
        # Only one result
        results = [
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80),
        ]
        self.iterative_mode.iteration_results = results
        
        is_diminishing = self.iterative_mode._detect_diminishing_returns()
        
        self.assertFalse(is_diminishing)

    def test_add_iteration_result(self):
        """Test add_iteration_result method."""
        result = IterationResult(
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
            fixable_errors=80,
            cost=25.50,
            tokens_used=1500
        )
        
        self.iterative_mode.add_iteration_result(result)
        
        self.assertEqual(len(self.iterative_mode.iteration_results), 1)
        self.assertEqual(self.iterative_mode.iteration_results[0], result)
        self.assertEqual(self.iterative_mode.total_time, 120.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 15)

    def test_add_multiple_iteration_results(self):
        """Test adding multiple iteration results."""
        results = [
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80, 10.0, 500),
            IterationResult(2, 85, 70, 15, 18, 0.83, 90.0, 0, 17.6, 0.85, 65, 15.0, 750),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        self.assertEqual(len(self.iterative_mode.iteration_results), 2)
        self.assertEqual(self.iterative_mode.total_time, 150.0)  # 60 + 90
        self.assertEqual(self.iterative_mode.total_errors_fixed, 30)  # 15 + 15

    def test_get_performance_summary(self):
        """Test get_performance_summary method."""
        # Add some iteration results
        results = [
            IterationResult(1, 100, 85, 15, 20, 0.75, 60.0, 0, 15.0, 0.8, 80, 10.0, 500),
            IterationResult(2, 85, 70, 15, 18, 0.83, 90.0, 0, 17.6, 0.85, 65, 15.0, 750),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        summary = self.iterative_mode.get_performance_summary()
        
        self.assertIn("total_iterations", summary)
        self.assertIn("total_errors_fixed", summary)
        self.assertIn("total_time_seconds", summary)
        self.assertIn("average_improvement_per_iteration", summary)
        self.assertIn("overall_success_rate", summary)
        self.assertIn("total_cost", summary)
        self.assertIn("total_tokens_used", summary)
        self.assertIn("average_ml_accuracy", summary)
        self.assertIn("errors_per_minute", summary)
        
        self.assertEqual(summary["total_iterations"], 2)
        self.assertEqual(summary["total_errors_fixed"], 30)
        self.assertEqual(summary["total_time_seconds"], 150.0)
        self.assertAlmostEqual(summary["average_improvement_per_iteration"], 16.3, places=1)
        self.assertAlmostEqual(summary["overall_success_rate"], 0.79, places=2)
        self.assertEqual(summary["total_cost"], 25.0)
        self.assertEqual(summary["total_tokens_used"], 1250)

    def test_get_performance_summary_empty(self):
        """Test get_performance_summary with no results."""
        summary = self.iterative_mode.get_performance_summary()
        
        self.assertEqual(summary["total_iterations"], 0)
        self.assertEqual(summary["total_errors_fixed"], 0)
        self.assertEqual(summary["total_time_seconds"], 0.0)
        self.assertEqual(summary["average_improvement_per_iteration"], 0.0)
        self.assertEqual(summary["overall_success_rate"], 0.0)

    def test_generate_recommendations_continue(self):
        """Test generate_recommendations for continue case."""
        exit_reason = LoopExitReason.MAX_ITERATIONS_REACHED
        
        # Add good results
        results = [
            IterationResult(1, 100, 80, 20, 25, 0.8, 60.0, 0, 20.0, 0.85, 75, 10.0, 500),
            IterationResult(2, 80, 60, 20, 22, 0.91, 70.0, 0, 25.0, 0.87, 55, 12.0, 600),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason)
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "continue")
        self.assertIn("good progress", recommendation.reason.lower())

    def test_generate_recommendations_refactor(self):
        """Test generate_recommendations for refactor case."""
        exit_reason = LoopExitReason.DIMINISHING_RETURNS
        
        # Add results showing poor progress over many iterations
        results = []
        for i in range(6):
            result = IterationResult(
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
            results.append(result)
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason)
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "refactor")
        self.assertIn("refactor", recommendation.reason.lower())

    def test_generate_recommendations_manual_review(self):
        """Test generate_recommendations for manual_review case."""
        exit_reason = LoopExitReason.ERROR_INCREASE
        
        # Add result with error increase
        result = IterationResult(
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
        
        self.iterative_mode.add_iteration_result(result)
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason)
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "manual_review")
        self.assertIn("manual review", recommendation.reason.lower())

    def test_generate_recommendations_architect_mode(self):
        """Test generate_recommendations for architect_mode case."""
        exit_reason = LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET
        
        # Add results with very low success rate
        results = []
        for i in range(3):
            result = IterationResult(
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
            results.append(result)
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        recommendation = self.iterative_mode.generate_recommendations(exit_reason)
        
        self.assertIsInstance(recommendation, LoopRecommendation)
        self.assertEqual(recommendation.action, "architect_mode")
        self.assertIn("architect mode", recommendation.reason.lower())

    def test_display_performance_summary_with_data(self):
        """Test display_performance_summary with data."""
        # Add iteration results
        results = [
            IterationResult(1, 100, 80, 20, 25, 0.8, 60.0, 0, 20.0, 0.85, 75, 10.0, 500),
            IterationResult(2, 80, 60, 20, 22, 0.91, 70.0, 0, 25.0, 0.87, 55, 12.0, 600),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        with patch('builtins.print') as mock_print:
            self.iterative_mode.display_performance_summary()
            
            # Check that print was called
            self.assertTrue(mock_print.called)
            
            # Check for expected content in print calls
            print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
            
            summary_found = any("Iterative Force Mode Performance Summary" in str(call) for call in print_calls)
            self.assertTrue(summary_found)

    def test_display_performance_summary_empty(self):
        """Test display_performance_summary with no data."""
        with patch('builtins.print') as mock_print:
            self.iterative_mode.display_performance_summary()
            
            # Should still print something
            self.assertTrue(mock_print.called)

    def test_reset_state(self):
        """Test reset_state method."""
        # Add some data
        results = [
            IterationResult(1, 100, 80, 20, 25, 0.8, 60.0, 0, 20.0, 0.85, 75, 10.0, 500),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        # Verify data exists
        self.assertEqual(len(self.iterative_mode.iteration_results), 1)
        self.assertEqual(self.iterative_mode.total_time, 60.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 20)
        
        # Reset state
        self.iterative_mode.reset_state()
        
        # Verify reset
        self.assertEqual(len(self.iterative_mode.iteration_results), 0)
        self.assertEqual(self.iterative_mode.total_time, 0.0)
        self.assertEqual(self.iterative_mode.total_errors_fixed, 0)

    def test_get_iteration_insights(self):
        """Test get_iteration_insights method."""
        # Add iteration results with patterns
        results = [
            IterationResult(1, 100, 80, 20, 25, 0.8, 60.0, 0, 20.0, 0.85, 75, 10.0, 500),
            IterationResult(2, 80, 65, 15, 20, 0.75, 70.0, 0, 18.8, 0.82, 60, 12.0, 600),
            IterationResult(3, 65, 50, 15, 18, 0.83, 65.0, 0, 23.1, 0.88, 45, 11.0, 550),
        ]
        
        for result in results:
            self.iterative_mode.add_iteration_result(result)
        
        insights = self.iterative_mode.get_iteration_insights()
        
        self.assertIn("total_iterations", insights)
        self.assertIn("improvement_trend", insights)
        self.assertIn("success_rate_trend", insights)
        self.assertIn("ml_accuracy_trend", insights)
        self.assertIn("time_per_iteration_trend", insights)
        self.assertIn("best_iteration", insights)
        self.assertIn("worst_iteration", insights)
        
        self.assertEqual(insights["total_iterations"], 3)
        self.assertEqual(insights["best_iteration"]["iteration"], 3)  # Highest improvement
        self.assertEqual(insights["worst_iteration"]["iteration"], 2)  # Lowest improvement

    def test_get_iteration_insights_empty(self):
        """Test get_iteration_insights with no data."""
        insights = self.iterative_mode.get_iteration_insights()
        
        self.assertEqual(insights["total_iterations"], 0)
        self.assertEqual(insights["improvement_trend"], [])
        self.assertIsNone(insights["best_iteration"])
        self.assertIsNone(insights["worst_iteration"])


if __name__ == "__main__":
    unittest.main()