"""
Test suite for the Cost Monitor module.

This module tests:
1. Cost tracking and calculation
2. Budget limit enforcement
3. Token usage monitoring
4. Cost prediction functionality
5. Model pricing accuracy
6. Emergency stop mechanisms
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.cost_monitor import (
    BudgetExceededException,
    BudgetLimits,
    CostModel,
    CostMonitor,
    TokenUsage,
    create_cost_monitor,
)


class TestTokenUsage:
    """Test TokenUsage data structure."""

    def test_token_usage_initialization(self):
        """Test TokenUsage initialization."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_add_usage(self):
        """Test adding token usage."""
        usage = TokenUsage()
        usage.add_usage(100, 50)

        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_cumulative_usage(self):
        """Test cumulative token usage tracking."""
        usage = TokenUsage()
        usage.add_usage(100, 50)
        usage.add_usage(200, 75)

        assert usage.input_tokens == 300
        assert usage.output_tokens == 125
        assert usage.total_tokens == 425


class TestBudgetLimits:
    """Test BudgetLimits configuration."""

    def test_default_budget_limits(self):
        """Test default budget limit values."""
        limits = BudgetLimits()
        assert limits.max_total_cost == 100.0
        assert limits.max_iteration_cost == 20.0
        assert limits.max_file_cost == 10.0
        assert limits.warning_threshold == 0.8
        assert limits.emergency_stop_threshold == 0.95

    def test_custom_budget_limits(self):
        """Test custom budget limit configuration."""
        limits = BudgetLimits(
            max_total_cost=50.0,
            max_iteration_cost=10.0,
            max_file_cost=5.0,
            warning_threshold=0.7,
            emergency_stop_threshold=0.9,
        )

        assert limits.max_total_cost == 50.0
        assert limits.max_iteration_cost == 10.0
        assert limits.max_file_cost == 5.0
        assert limits.warning_threshold == 0.7
        assert limits.emergency_stop_threshold == 0.9


class TestCostMonitor:
    """Test CostMonitor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = self.temp_dir
        self.budget_limits = BudgetLimits(max_total_cost=10.0, max_iteration_cost=5.0)
        self.monitor = CostMonitor(self.project_path, self.budget_limits)

    def test_initialization(self):
        """Test CostMonitor initialization."""
        assert self.monitor.project_path == self.project_path
        assert self.monitor.budget_limits == self.budget_limits
        assert self.monitor.current_model == CostModel.GPT_4_TURBO
        assert len(self.monitor.session_costs) == 0
        assert self.monitor.current_iteration == 0

    def test_set_model(self):
        """Test setting AI model for cost calculations."""
        self.monitor.set_model(CostModel.CLAUDE_3_SONNET)
        assert self.monitor.current_model == CostModel.CLAUDE_3_SONNET

    def test_start_iteration(self):
        """Test starting a new iteration."""
        self.monitor.start_iteration(1)
        assert self.monitor.current_iteration == 1
        assert 1 in self.monitor.iteration_usage
        assert 1 in self.monitor.iteration_costs

    def test_record_token_usage(self):
        """Test recording token usage and cost calculation."""
        self.monitor.start_iteration(1)
        cost_breakdown = self.monitor.record_token_usage(1000, 500)

        # Check cost calculation (GPT-4-turbo: $0.01 input, $0.03 output per 1K tokens)
        expected_input_cost = (1000 / 1000) * 0.01  # $0.01
        expected_output_cost = (500 / 1000) * 0.03  # $0.015
        expected_total = expected_input_cost + expected_output_cost  # $0.025

        assert abs(cost_breakdown.input_cost - expected_input_cost) < 0.001
        assert abs(cost_breakdown.output_cost - expected_output_cost) < 0.001
        assert abs(cost_breakdown.total_cost - expected_total) < 0.001

    def test_budget_status_tracking(self):
        """Test budget status monitoring."""
        self.monitor.start_iteration(1)
        self.monitor.record_token_usage(10000, 5000)  # Should be about $0.25

        status = self.monitor.check_budget_status()
        assert status["total_cost"] > 0
        assert status["total_usage_percentage"] < 100  # Should be well under budget
        assert status["within_budget"] is True

    def test_budget_warning_threshold(self):
        """Test budget warning threshold detection."""
        # Set up monitor with budget to trigger warning but not emergency stop
        low_budget = BudgetLimits(
            max_total_cost=1.0, warning_threshold=0.2, emergency_stop_threshold=0.9
        )
        monitor = CostMonitor(self.project_path, low_budget)

        monitor.start_iteration(1)
        monitor.record_token_usage(10000, 5000)  # About $0.25, over 20% of $1.0 budget

        status = monitor.check_budget_status()
        assert status["warning_triggered"] is True
        assert status["emergency_stop_needed"] is False

    def test_emergency_stop_exception(self):
        """Test emergency stop when budget is exceeded."""
        # Set up monitor with very low budget to trigger emergency stop
        low_budget = BudgetLimits(max_total_cost=0.01, emergency_stop_threshold=0.5)
        monitor = CostMonitor(self.project_path, low_budget)

        monitor.start_iteration(1)

        with pytest.raises(BudgetExceededException):
            monitor.record_token_usage(10000, 5000)  # About $0.25, way over $0.01 budget

    def test_cost_prediction(self):
        """Test cost prediction functionality."""
        self.monitor.start_iteration(1)
        self.monitor.record_token_usage(1000, 500)
        self.monitor.start_iteration(2)
        self.monitor.record_token_usage(1200, 600)

        prediction = self.monitor.predict_total_cost()
        assert prediction.predicted_total_cost > self.monitor.get_total_cost()
        assert prediction.predicted_iterations_remaining >= 0
        assert 0 <= prediction.confidence <= 1
        assert prediction.recommendation is not None

    def test_file_cost_tracking(self):
        """Test per-file cost tracking."""
        self.monitor.start_iteration(1)
        file_path = "test_file.py"

        self.monitor.record_token_usage(1000, 500, file_path=file_path)

        file_cost = self.monitor.get_file_cost(file_path)
        assert file_cost > 0
        assert file_path in self.monitor.file_costs

    def test_iteration_cost_tracking(self):
        """Test per-iteration cost tracking."""
        self.monitor.start_iteration(1)
        self.monitor.record_token_usage(1000, 500)

        iteration_cost = self.monitor.get_iteration_cost(1)
        assert iteration_cost > 0

    def test_model_pricing_accuracy(self):
        """Test that model pricing is accurate for different models."""
        # Test GPT-4
        self.monitor.set_model(CostModel.GPT_4)
        cost_gpt4 = self.monitor._calculate_cost(1000, 1000)
        expected_gpt4 = (1000 / 1000 * 0.03) + (1000 / 1000 * 0.06)  # $0.09
        assert abs(cost_gpt4.total_cost - expected_gpt4) < 0.001

        # Test Claude-3-Haiku (cheaper model)
        self.monitor.set_model(CostModel.CLAUDE_3_HAIKU)
        cost_haiku = self.monitor._calculate_cost(1000, 1000)
        expected_haiku = (1000 / 1000 * 0.00025) + (1000 / 1000 * 0.00125)  # $0.0015
        assert abs(cost_haiku.total_cost - expected_haiku) < 0.001

        # Haiku should be much cheaper than GPT-4
        assert cost_haiku.total_cost < cost_gpt4.total_cost

    def test_cost_data_persistence(self):
        """Test that cost data is saved and can be loaded."""
        self.monitor.start_iteration(1)
        self.monitor.record_token_usage(1000, 500)

        # Check that cache directory and files are created
        cache_dir = Path(self.project_path) / ".aider-lint-cache"
        assert cache_dir.exists()

        # Check that cost files are created
        cost_files = list(cache_dir.glob("costs_*.json"))
        assert len(cost_files) > 0

    @patch("aider_lint_fixer.cost_monitor.datetime")
    def test_cost_history_loading(self, mock_datetime):
        """Test loading cost history from previous sessions."""
        # Mock current time
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

        # Create a cost history file
        cache_dir = Path(self.project_path) / ".aider-lint-cache"
        cache_dir.mkdir(exist_ok=True)

        cost_file = cache_dir / "costs_20240101_110000.json"
        cost_data = {
            "session_start": (mock_now - timedelta(minutes=30)).isoformat(),
            "current_model": "gpt-4-turbo",
            "total_usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
            },
            "total_cost": 0.025,
        }

        with open(cost_file, "w") as f:
            json.dump(cost_data, f)

        # Create new monitor that should load the history
        new_monitor = CostMonitor(self.project_path, self.budget_limits)

        # Should have loaded previous usage
        assert new_monitor.total_usage.total_tokens == 1500


class TestCostMonitorIntegration:
    """Test CostMonitor integration functions."""

    def test_create_cost_monitor_function(self):
        """Test the create_cost_monitor convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = create_cost_monitor(temp_dir, max_total_cost=50.0, max_iteration_cost=10.0)

            assert monitor.project_path == temp_dir
            assert monitor.budget_limits.max_total_cost == 50.0
            assert monitor.budget_limits.max_iteration_cost == 10.0

    def test_cost_recommendation_generation(self):
        """Test cost optimization recommendation generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = CostMonitor(temp_dir, BudgetLimits(max_total_cost=1.0))

            # Test recommendation for high predicted cost
            recommendation = monitor._generate_cost_recommendation(2.0, 0.8)
            assert "exceeds budget" in recommendation.lower()

            # Test recommendation for acceptable cost
            recommendation = monitor._generate_cost_recommendation(0.5, 0.8)
            assert "within budget" in recommendation.lower()

    def test_multiple_iterations_cost_tracking(self):
        """Test cost tracking across multiple iterations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = CostMonitor(temp_dir, BudgetLimits())

            total_cost = 0
            for i in range(1, 4):
                monitor.start_iteration(i)
                cost = monitor.record_token_usage(1000, 500)
                total_cost += cost.total_cost

            assert abs(monitor.get_total_cost() - total_cost) < 0.001
            assert len(monitor.iteration_costs) == 3
            assert len(monitor.iteration_usage) == 3


if __name__ == "__main__":
    pytest.main([__file__])
