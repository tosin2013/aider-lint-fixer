#!/usr/bin/env python3
"""
Cost Monitoring and Budget Control System

This module implements comprehensive tracking of AI token usage and associated costs
with configurable budget limits and automatic termination when cost thresholds are exceeded.

Based on research findings that continuous loop execution can become economically prohibitive
without proper cost controls, ranging from $50-500 for processing 100+ errors through multiple iterations.

Key Features:
- Real-time cost tracking and prediction
- Configurable budget limits (per-iteration and total operation)
- Automatic termination when cost thresholds are exceeded
- Cost optimization recommendations
- Integration with existing progress tracking system
- Predictive cost modeling based on current iteration patterns
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CostModel(Enum):
    """AI model cost tiers."""

    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"


@dataclass
class TokenUsage:
    """Token usage tracking."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens


@dataclass
class CostBreakdown:
    """Detailed cost breakdown."""

    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    model: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BudgetLimits:
    """Budget configuration."""

    max_total_cost: float = 100.0  # Maximum total cost for operation
    max_iteration_cost: float = 20.0  # Maximum cost per iteration
    max_file_cost: float = 10.0  # Maximum cost per file
    warning_threshold: float = 0.8  # Warn at 80% of budget
    emergency_stop_threshold: float = 0.95  # Emergency stop at 95%


@dataclass
class CostPrediction:
    """Cost prediction based on current patterns."""

    predicted_total_cost: float
    predicted_iterations_remaining: int
    confidence: float  # 0.0 to 1.0
    based_on_iterations: int
    recommendation: str


class CostMonitor:
    """Comprehensive cost monitoring and budget control system."""

    # Model pricing (per 1K tokens) - Updated as of January 2025
    MODEL_PRICING = {
        CostModel.GPT_4: {"input": 0.03, "output": 0.06},
        CostModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
        CostModel.GPT_3_5_TURBO: {"input": 0.0015, "output": 0.002},
        CostModel.CLAUDE_3_OPUS: {"input": 0.015, "output": 0.075},
        CostModel.CLAUDE_3_SONNET: {"input": 0.003, "output": 0.015},
        CostModel.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},
    }

    def __init__(self, project_path: str, budget_limits: Optional[BudgetLimits] = None):
        self.project_path = project_path
        self.budget_limits = budget_limits or BudgetLimits()

        # Cost tracking
        self.session_costs: List[CostBreakdown] = []
        self.iteration_costs: Dict[int, CostBreakdown] = {}
        self.file_costs: Dict[str, CostBreakdown] = {}

        # Token tracking
        self.total_usage = TokenUsage()
        self.iteration_usage: Dict[int, TokenUsage] = {}

        # Session info
        self.session_start = datetime.now()
        self.current_iteration = 0
        self.current_model = CostModel.GPT_4_TURBO  # Default model

        # Cache directory for cost persistence
        self.cache_dir = Path(project_path) / ".aider-lint-cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Load existing cost data if available
        self._load_cost_history()

    def set_model(self, model: CostModel):
        """Set the AI model being used."""
        self.current_model = model
        logger.info(f"Cost monitor set to track {model.value} usage")

    def start_iteration(self, iteration: int):
        """Start tracking costs for a new iteration."""
        self.current_iteration = iteration
        if iteration not in self.iteration_usage:
            self.iteration_usage[iteration] = TokenUsage()
            self.iteration_costs[iteration] = CostBreakdown(
                model=self.current_model.value
            )

        logger.debug(f"Started cost tracking for iteration {iteration}")

    def record_token_usage(
        self, input_tokens: int, output_tokens: int, file_path: Optional[str] = None
    ) -> CostBreakdown:
        """Record token usage and calculate costs."""
        # Update total usage
        self.total_usage.add_usage(input_tokens, output_tokens)

        # Update iteration usage
        if self.current_iteration in self.iteration_usage:
            self.iteration_usage[self.current_iteration].add_usage(
                input_tokens, output_tokens
            )

        # Calculate costs
        cost_breakdown = self._calculate_cost(input_tokens, output_tokens)

        # Update iteration costs
        if self.current_iteration in self.iteration_costs:
            iter_cost = self.iteration_costs[self.current_iteration]
            iter_cost.input_cost += cost_breakdown.input_cost
            iter_cost.output_cost += cost_breakdown.output_cost
            iter_cost.total_cost += cost_breakdown.total_cost

        # Update file costs if specified
        if file_path:
            if file_path not in self.file_costs:
                self.file_costs[file_path] = CostBreakdown(
                    model=self.current_model.value
                )

            file_cost = self.file_costs[file_path]
            file_cost.input_cost += cost_breakdown.input_cost
            file_cost.output_cost += cost_breakdown.output_cost
            file_cost.total_cost += cost_breakdown.total_cost

        # Add to session costs
        self.session_costs.append(cost_breakdown)

        # Check budget limits
        self._check_budget_limits()

        # Save cost data
        self._save_cost_data()

        return cost_breakdown

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> CostBreakdown:
        """Calculate cost for token usage."""
        pricing = self.MODEL_PRICING[self.current_model]

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost

        return CostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model=self.current_model.value,
        )

    def get_total_cost(self) -> float:
        """Get total cost for the session."""
        return sum(cost.total_cost for cost in self.session_costs)

    def get_iteration_cost(self, iteration: int) -> float:
        """Get cost for a specific iteration."""
        if iteration in self.iteration_costs:
            return self.iteration_costs[iteration].total_cost
        return 0.0

    def get_file_cost(self, file_path: str) -> float:
        """Get cost for a specific file."""
        if file_path in self.file_costs:
            return self.file_costs[file_path].total_cost
        return 0.0

    def check_budget_status(self) -> Dict[str, any]:
        """Check current budget status."""
        total_cost = self.get_total_cost()
        current_iter_cost = self.get_iteration_cost(self.current_iteration)

        total_usage_pct = total_cost / self.budget_limits.max_total_cost
        iter_usage_pct = current_iter_cost / self.budget_limits.max_iteration_cost

        return {
            "total_cost": total_cost,
            "total_budget": self.budget_limits.max_total_cost,
            "total_usage_percentage": total_usage_pct * 100,
            "iteration_cost": current_iter_cost,
            "iteration_budget": self.budget_limits.max_iteration_cost,
            "iteration_usage_percentage": iter_usage_pct * 100,
            "within_budget": total_usage_pct < 1.0 and iter_usage_pct < 1.0,
            "warning_triggered": total_usage_pct
            >= self.budget_limits.warning_threshold,
            "emergency_stop_needed": total_usage_pct
            >= self.budget_limits.emergency_stop_threshold,
        }

    def _check_budget_limits(self):
        """Check if budget limits are exceeded and take action."""
        status = self.check_budget_status()

        if status["emergency_stop_needed"]:
            logger.error(
                f"EMERGENCY STOP: Budget exceeded! Total cost: ${status['total_cost']:.2f}"
            )
            raise BudgetExceededException(
                f"Emergency stop triggered. Total cost ${status['total_cost']:.2f} "
                f"exceeds {self.budget_limits.emergency_stop_threshold*100}% of budget "
                f"${self.budget_limits.max_total_cost:.2f}"
            )

        if status["warning_triggered"]:
            logger.warning(
                f"Budget warning: ${status['total_cost']:.2f} / ${status['total_budget']:.2f} "
                f"({status['total_usage_percentage']:.1f}%)"
            )

    def predict_total_cost(self) -> CostPrediction:
        """Predict total cost based on current iteration patterns."""
        if len(self.iteration_costs) < 2:
            return CostPrediction(
                predicted_total_cost=self.get_total_cost(),
                predicted_iterations_remaining=0,
                confidence=0.1,
                based_on_iterations=len(self.iteration_costs),
                recommendation="Insufficient data for prediction",
            )

        # Calculate average cost per iteration
        iteration_costs = [cost.total_cost for cost in self.iteration_costs.values()]
        avg_cost_per_iteration = sum(iteration_costs) / len(iteration_costs)

        # Estimate remaining iterations (simple heuristic)
        # In practice, this would integrate with the iterative force mode's convergence detection
        estimated_remaining = max(
            0, 10 - self.current_iteration
        )  # Assume max 10 iterations

        predicted_additional_cost = avg_cost_per_iteration * estimated_remaining
        predicted_total = self.get_total_cost() + predicted_additional_cost

        # Calculate confidence based on cost variance
        if len(iteration_costs) > 1:
            variance = sum(
                (cost - avg_cost_per_iteration) ** 2 for cost in iteration_costs
            ) / len(iteration_costs)
            confidence = max(0.1, 1.0 - (variance / avg_cost_per_iteration))
        else:
            confidence = 0.5

        # Generate recommendation
        recommendation = self._generate_cost_recommendation(predicted_total, confidence)

        return CostPrediction(
            predicted_total_cost=predicted_total,
            predicted_iterations_remaining=estimated_remaining,
            confidence=confidence,
            based_on_iterations=len(iteration_costs),
            recommendation=recommendation,
        )

    def _generate_cost_recommendation(
        self, predicted_total: float, confidence: float
    ) -> str:
        """Generate cost optimization recommendation."""
        if predicted_total > self.budget_limits.max_total_cost:
            return f"⚠️ Predicted cost ${predicted_total:.2f} exceeds budget. Consider reducing scope or switching to cheaper model."
        elif predicted_total > self.budget_limits.max_total_cost * 0.8:
            return f"💡 Predicted cost ${predicted_total:.2f} is high. Monitor closely or consider optimization."
        else:
            return f"✅ Predicted cost ${predicted_total:.2f} is within budget."

    def _save_cost_data(self):
        """Save cost data to cache for persistence."""
        cost_file = (
            self.cache_dir
            / f"costs_{self.session_start.strftime('%Y%m%d_%H%M%S')}.json"
        )

        data = {
            "session_start": self.session_start.isoformat(),
            "current_model": self.current_model.value,
            "budget_limits": asdict(self.budget_limits),
            "total_usage": asdict(self.total_usage),
            "total_cost": self.get_total_cost(),
            "iteration_costs": {
                str(k): asdict(v) for k, v in self.iteration_costs.items()
            },
            "file_costs": {k: asdict(v) for k, v in self.file_costs.items()},
        }

        with open(cost_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_cost_history(self):
        """Load existing cost data if available."""
        # Look for recent cost files
        cost_files = list(self.cache_dir.glob("costs_*.json"))
        if not cost_files:
            return

        # Load the most recent cost file
        latest_file = max(cost_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, "r") as f:
                data = json.load(f)

            # Only load if from the same session (within last hour)
            session_start = datetime.fromisoformat(data["session_start"])
            if datetime.now() - session_start < timedelta(hours=1):
                logger.info(f"Loaded cost history from {latest_file}")
                # Restore relevant data
                self.total_usage = TokenUsage(**data["total_usage"])

        except Exception as e:
            logger.warning(f"Failed to load cost history: {e}")


class BudgetExceededException(Exception):
    """Exception raised when budget limits are exceeded."""

    pass


def create_cost_monitor(
    project_path: str, max_total_cost: float = 100.0, max_iteration_cost: float = 20.0
) -> CostMonitor:
    """Create a cost monitor with specified budget limits."""
    budget_limits = BudgetLimits(
        max_total_cost=max_total_cost, max_iteration_cost=max_iteration_cost
    )

    return CostMonitor(project_path, budget_limits)
