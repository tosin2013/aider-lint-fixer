#!/usr/bin/env python3
"""
Iterative Force Mode with Intelligent Loop Detection
This module implements an intelligent iterative system that:
1. Runs force mode in loops
2. Measures improvement between iterations
3. Detects diminishing returns and convergence
4. Provides intelligent recommendations for next steps
5. Suggests refactoring when appropriate
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .context_manager import ContextManager, ContextPriority
from .convergence_analyzer import AdvancedConvergenceAnalyzer, ConvergenceState
from .cost_monitor import BudgetExceededException, CostMonitor

logger = logging.getLogger(__name__)


class LoopExitReason(Enum):
    """Reasons why the iterative loop exited."""

    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    IMPROVEMENT_THRESHOLD_NOT_MET = "improvement_threshold_not_met"
    NO_IMPROVEMENT = "no_improvement"
    DIMINISHING_RETURNS = "diminishing_returns"
    CONVERGENCE_DETECTED = "convergence_detected"
    ERROR_INCREASE = "error_increase"
    USER_REQUESTED = "user_requested"
    REFACTOR_RECOMMENDED = "refactor_recommended"
    BUDGET_EXCEEDED = "budget_exceeded"
    BUDGET_PREDICTED_EXCEEDED = "budget_predicted_exceeded"


@dataclass
class IterationResult:
    """Results from a single iteration."""

    iteration: int
    errors_before: int
    errors_after: int
    errors_fixed: int
    errors_attempted: int
    success_rate: float
    time_taken: float
    new_errors_introduced: int
    improvement_percentage: float
    ml_accuracy: float
    fixable_errors: int
    cost: float = 0.0  # Cost for this iteration
    tokens_used: int = 0  # Total tokens used in this iteration


@dataclass
class LoopRecommendation:
    """Recommendations for next steps after loop completion."""

    action: str  # 'continue', 'manual_review', 'refactor', 'architect_mode'
    reason: str
    specific_suggestions: List[str]
    estimated_effort: str  # 'low', 'medium', 'high', 'very_high'
    priority_files: List[str]
    dangerous_patterns: List[str]


class IterativeForceMode:
    """Intelligent iterative force mode with loop detection."""

    def __init__(
        self,
        project_root: str,
        cost_monitor: Optional[CostMonitor] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        self.project_root = project_root
        # Loop configuration
        self.max_iterations = 10
        self.improvement_threshold = 5  # Minimum % improvement to continue
        self.diminishing_returns_threshold = 2  # % improvement considered diminishing
        self.convergence_window = 3  # Iterations to check for convergence
        self.max_error_increase_tolerance = 5  # Max errors that can increase
        # Cost monitoring
        self.cost_monitor = cost_monitor
        # Context management for extended loops
        self.context_manager = context_manager or ContextManager()
        # Advanced convergence analysis
        self.convergence_analyzer = AdvancedConvergenceAnalyzer(project_root)
        # Tracking
        self.iteration_results: List[IterationResult] = []
        self.total_time = 0.0
        self.total_errors_fixed = 0
        # Refactor detection thresholds
        self.refactor_error_density_threshold = 50  # Errors per 1000 lines
        self.refactor_dangerous_error_ratio = 0.3  # 30% dangerous errors
        self.refactor_iteration_threshold = 5  # Iterations without major progress

    def should_continue_loop(self, current_iteration: int) -> Tuple[bool, LoopExitReason, str]:
        """Determine if the loop should continue based on intelligent analysis."""
        # Check budget limits first
        if self.cost_monitor:
            try:
                budget_status = self.cost_monitor.check_budget_status()
                if budget_status["emergency_stop_needed"]:
                    return (
                        False,
                        LoopExitReason.BUDGET_EXCEEDED,
                        f"Budget exceeded: ${budget_status['total_cost']:.2f} / ${budget_status['total_budget']:.2f}",
                    )
                # Predict future costs
                cost_prediction = self.cost_monitor.predict_total_cost()
                if (
                    cost_prediction.predicted_total_cost
                    > self.cost_monitor.budget_limits.max_total_cost
                ):
                    return (
                        False,
                        LoopExitReason.BUDGET_PREDICTED_EXCEEDED,
                        f"Predicted cost ${cost_prediction.predicted_total_cost:.2f} exceeds budget",
                    )
            except BudgetExceededException as e:
                return False, LoopExitReason.BUDGET_EXCEEDED, str(e)
        if current_iteration >= self.max_iterations:
            return (
                False,
                LoopExitReason.MAX_ITERATIONS_REACHED,
                f"Reached maximum iterations ({self.max_iterations})",
            )
        if len(self.iteration_results) < 2:
            return True, None, "Need at least 2 iterations for analysis"
        latest = self.iteration_results[-1]
        previous = self.iteration_results[-2]
        # Check for error increase
        if latest.errors_after > previous.errors_after + self.max_error_increase_tolerance:
            return (
                False,
                LoopExitReason.ERROR_INCREASE,
                f"Errors increased by {latest.errors_after - previous.errors_after}",
            )
        # Check for no improvement
        if latest.improvement_percentage <= 0:
            return (
                False,
                LoopExitReason.NO_IMPROVEMENT,
                "No improvement in latest iteration",
            )
        # Check improvement threshold
        if latest.improvement_percentage < self.improvement_threshold:
            return (
                False,
                LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET,
                f"Improvement {latest.improvement_percentage:.1f}% below threshold {self.improvement_threshold}%",
            )
        # Check for diminishing returns
        if len(self.iteration_results) >= 3:
            recent_improvements = [r.improvement_percentage for r in self.iteration_results[-3:]]
            avg_improvement = sum(recent_improvements) / len(recent_improvements)
            if avg_improvement < self.diminishing_returns_threshold:
                return (
                    False,
                    LoopExitReason.DIMINISHING_RETURNS,
                    f"Average improvement {avg_improvement:.1f}% indicates diminishing returns",
                )
        # Advanced convergence detection using ML analysis
        if len(self.iteration_results) >= 3:
            convergence_analysis = self.convergence_analyzer.analyze_convergence()
            # Check for ML-detected convergence
            if convergence_analysis.current_state == ConvergenceState.CONVERGED:
                return (
                    False,
                    LoopExitReason.CONVERGENCE_DETECTED,
                    f"ML convergence detected (confidence: {convergence_analysis.confidence:.2f})",
                )
            # Check for plateau with low improvement potential
            if (
                convergence_analysis.current_state == ConvergenceState.PLATEAUING
                and convergence_analysis.improvement_potential < 0.2
            ):
                return (
                    False,
                    LoopExitReason.DIMINISHING_RETURNS,
                    f"Plateau detected with low improvement potential ({convergence_analysis.improvement_potential:.2f})",
                )
            # Check for diverging performance
            if convergence_analysis.current_state == ConvergenceState.DIVERGING:
                return (
                    False,
                    LoopExitReason.ERROR_INCREASE,
                    "Performance diverging - fixes may be introducing errors",
                )
            # Add convergence insights to context
            convergence_context = (
                "Convergence Analysis:\n"
                f"- State: {convergence_analysis.current_state.value}\n"
                f"- Confidence: {convergence_analysis.confidence:.2f}\n"
                f"- Improvement potential: {convergence_analysis.improvement_potential:.2f}\n"
                f"- Predicted remaining: {convergence_analysis.predicted_iterations_remaining} iterations\n"
                f"- Recommendation: {convergence_analysis.stopping_recommendation}"
            )
            self.context_manager.add_context(
                convergence_context,
                ContextPriority.HIGH,
                "convergence_analysis",
                iteration=current_iteration,
            )
        # Fallback to simple convergence check
        if len(self.iteration_results) >= self.convergence_window:
            recent_errors = [
                r.errors_after for r in self.iteration_results[-self.convergence_window :]
            ]
            error_variance = max(recent_errors) - min(recent_errors)
            if error_variance <= 2:  # Very small variance indicates convergence
                return (
                    False,
                    LoopExitReason.CONVERGENCE_DETECTED,
                    f"Error count converged (variance: {error_variance})",
                )
        # Check if refactor is recommended
        if self.should_recommend_refactor():
            return (
                False,
                LoopExitReason.REFACTOR_RECOMMENDED,
                "Codebase complexity suggests refactoring needed",
            )
        return True, None, "Continue iterating"

    def should_recommend_refactor(self) -> bool:
        """Determine if a refactor should be recommended."""
        if len(self.iteration_results) < 3:
            return False
        latest = self.iteration_results[-1]
        # High error density
        # Note: This would need actual line count from project analysis
        estimated_lines = 10000  # Placeholder - should be calculated
        error_density = (latest.errors_after / estimated_lines) * 1000
        if error_density > self.refactor_error_density_threshold:
            return True
        # Many iterations without major progress
        if len(self.iteration_results) >= self.refactor_iteration_threshold:
            total_improvement = self.iteration_results[0].errors_before - latest.errors_after
            improvement_rate = total_improvement / len(self.iteration_results)
            if improvement_rate < 3:  # Less than 3 errors fixed per iteration
                return True
        # High ratio of dangerous errors (would need dangerous error tracking)
        # This is a placeholder for dangerous error ratio calculation
        return False

    def record_iteration_result(
        self,
        iteration: int,
        errors_before: int,
        errors_after: int,
        errors_fixed: int,
        errors_attempted: int,
        success_rate: float,
        time_taken: float,
        new_errors_introduced: int,
        improvement_percentage: float,
        ml_accuracy: float,
        fixable_errors: int,
        error_details: Optional[List] = None,
    ):
        """Record results from an iteration with cost tracking and context management."""
        # Start iteration context tracking
        self.context_manager.start_iteration(iteration)
        # Get cost information if cost monitor is available
        cost = 0.0
        tokens_used = 0
        if self.cost_monitor:
            cost = self.cost_monitor.get_iteration_cost(iteration)
            if iteration in self.cost_monitor.iteration_usage:
                tokens_used = self.cost_monitor.iteration_usage[iteration].total_tokens
        result = IterationResult(
            iteration=iteration,
            errors_before=errors_before,
            errors_after=errors_after,
            errors_fixed=errors_fixed,
            errors_attempted=errors_attempted,
            success_rate=success_rate,
            time_taken=time_taken,
            new_errors_introduced=new_errors_introduced,
            improvement_percentage=improvement_percentage,
            ml_accuracy=ml_accuracy,
            fixable_errors=fixable_errors,
            cost=cost,
            tokens_used=tokens_used,
        )
        self.iteration_results.append(result)
        self.total_time += time_taken
        self.total_errors_fixed += errors_fixed
        # Add iteration results to context
        iteration_summary = (
            f"Iteration {iteration} Results:\n"
            f"- Errors fixed: {errors_fixed}/{errors_attempted}\n"
            f"- Success rate: {success_rate:.1f}%\n"
            f"- Improvement: {improvement_percentage:.1f}%\n"
            f"- Time: {time_taken:.1f}s\n"
            f"- Cost: ${cost:.2f}\n"
            f"- New errors: {new_errors_introduced}"
        )
        # Determine context priority based on iteration success
        priority = ContextPriority.HIGH if success_rate > 0.8 else ContextPriority.MEDIUM
        self.context_manager.add_context(
            iteration_summary,
            priority,
            "iteration_result",
            iteration=iteration,
            success=success_rate > 0.5,
        )
        # Add successful patterns to context if available
        if error_details and success_rate > 0.7:
            for error_detail in error_details:
                if error_detail.get("success", False):
                    self.context_manager.preserve_successful_context(
                        error_detail.get("fix_description", ""),
                        error_detail.get("error_type", "unknown"),
                    )
        # Feed data to convergence analyzer
        self.convergence_analyzer.add_iteration_pattern(
            iteration=iteration,
            errors_before=errors_before,
            errors_after=errors_after,
            success_rate=success_rate,
            time_taken=time_taken,
            cost=cost,
            ml_accuracy=ml_accuracy,
            new_errors=new_errors_introduced,
        )
        logger.info(
            f"Iteration {iteration} completed: {errors_fixed} errors fixed, "
            f"${cost:.2f} cost, {tokens_used} tokens"
        )

    def analyze_iteration_patterns(self) -> Dict:
        """Analyze patterns across iterations for insights."""
        if len(self.iteration_results) < 2:
            return {}
        # Calculate trends
        improvements = [r.improvement_percentage for r in self.iteration_results]
        success_rates = [r.success_rate for r in self.iteration_results]
        ml_accuracies = [r.ml_accuracy for r in self.iteration_results]
        costs = [r.cost for r in self.iteration_results]
        tokens = [r.tokens_used for r in self.iteration_results]
        total_cost = sum(costs)
        total_tokens = sum(tokens)
        analysis = {
            "total_iterations": len(self.iteration_results),
            "total_errors_eliminated": self.iteration_results[0].errors_before
            - self.iteration_results[-1].errors_after,
            "average_improvement_per_iteration": sum(improvements) / len(improvements),
            "improvement_trend": (
                "increasing" if improvements[-1] > improvements[0] else "decreasing"
            ),
            "success_rate_trend": (
                "improving" if success_rates[-1] > success_rates[0] else "declining"
            ),
            "ml_learning_trend": (
                "improving" if ml_accuracies[-1] > ml_accuracies[0] else "stable"
            ),
            "total_time": self.total_time,
            "efficiency": (self.total_errors_fixed / self.total_time if self.total_time > 0 else 0),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "cost_per_error_fixed": (
                total_cost / self.total_errors_fixed if self.total_errors_fixed > 0 else 0
            ),
            "tokens_per_error_fixed": (
                total_tokens / self.total_errors_fixed if self.total_errors_fixed > 0 else 0
            ),
            "average_cost_per_iteration": total_cost / len(self.iteration_results),
            "cost_efficiency_trend": (
                "improving" if len(costs) > 1 and costs[-1] < costs[0] else "stable"
            ),
        }
        return analysis

    def get_optimized_context_for_ai(self) -> str:
        """Get optimized context for AI consumption in next iteration."""
        if not self.context_manager:
            return ""
        # Get current context optimized for AI
        context = self.context_manager.get_current_context(include_summaries=True)
        # Add context statistics for debugging
        stats = self.context_manager.get_context_stats()
        context_stats = (
            "\n\n[CONTEXT STATS]\n"
            f"- Items: {stats['total_items']}\n"
            f"- Tokens: {stats['total_tokens']} ({stats['token_usage_percentage']:.1f}%)\n"
            f"- Summaries: {stats['summaries_created']}\n"
            f"- Success patterns: {stats['successful_patterns']}\n"
        )
        return context + context_stats

    def finalize_session(self, session_id: str, exit_reason: LoopExitReason):
        """Finalize the iterative session and save convergence data."""
        # Determine final convergence state based on exit reason
        if exit_reason == LoopExitReason.CONVERGENCE_DETECTED:
            final_state = ConvergenceState.CONVERGED
        elif exit_reason == LoopExitReason.DIMINISHING_RETURNS:
            final_state = ConvergenceState.PLATEAUING
        elif exit_reason == LoopExitReason.ERROR_INCREASE:
            final_state = ConvergenceState.DIVERGING
        elif exit_reason == LoopExitReason.MAX_ITERATIONS_REACHED:
            # Determine state based on recent performance
            if len(self.iteration_results) >= 2:
                recent_improvement = self.iteration_results[-1].improvement_percentage
                if recent_improvement < 2:
                    final_state = ConvergenceState.PLATEAUING
                else:
                    final_state = ConvergenceState.IMPROVING
            else:
                final_state = ConvergenceState.IMPROVING
        else:
            final_state = ConvergenceState.IMPROVING
        # Save session data for future learning
        self.convergence_analyzer.save_session(session_id, final_state)
        # Add final session summary to context
        if self.iteration_results:
            total_improvement = (
                (self.iteration_results[0].errors_before - self.iteration_results[-1].errors_after)
                / self.iteration_results[0].errors_before
                if self.iteration_results[0].errors_before > 0
                else 0
            )
            session_summary = (
                "Session Completed:\n"
                f"- Total iterations: {len(self.iteration_results)}\n"
                f"- Total improvement: {total_improvement:.1%}\n"
                f"- Final state: {final_state.value}\n"
                f"- Exit reason: {exit_reason.value}\n"
                f"- Total cost: ${sum(r.cost for r in self.iteration_results):.2f}\n"
                f"- Total time: {self.total_time:.1f}s"
            )
            self.context_manager.add_context(
                session_summary,
                ContextPriority.CRITICAL,
                "session_summary",
                success=final_state in [ConvergenceState.CONVERGED, ConvergenceState.PLATEAUING],
            )
        logger.info(f"Session {session_id} finalized with state: {final_state.value}")

    def generate_recommendations(
        self, exit_reason: LoopExitReason, exit_message: str
    ) -> LoopRecommendation:
        """Generate intelligent recommendations based on loop results."""
        analysis = self.analyze_iteration_patterns()
        latest = self.iteration_results[-1] if self.iteration_results else None
        if exit_reason == LoopExitReason.MAX_ITERATIONS_REACHED:
            if analysis.get("improvement_trend") == "increasing":
                return LoopRecommendation(
                    action="continue",
                    reason="Still showing improvement at max iterations",
                    specific_suggestions=[
                        "Increase --max-iterations to allow more cycles",
                        "Consider running with --max-errors increased",
                        "Focus on remaining high-priority errors",
                    ],
                    estimated_effort="medium",
                    priority_files=[],
                    dangerous_patterns=[],
                )
            else:
                return LoopRecommendation(
                    action="manual_review",
                    reason="Reached iteration limit with declining improvement",
                    specific_suggestions=[
                        "Review remaining errors manually",
                        "Consider architect mode for complex errors",
                        "Focus on dangerous undefined variables",
                    ],
                    estimated_effort="high",
                    priority_files=[],
                    dangerous_patterns=["no-unde", "no-global-assign"],
                )
        elif exit_reason == LoopExitReason.BUDGET_EXCEEDED:
            return LoopRecommendation(
                action="budget_review",
                reason="Budget limits exceeded during iteration",
                specific_suggestions=[
                    f'Total cost: ${analysis.get("total_cost", 0):.2f}',
                    "Consider increasing budget limits if justified",
                    "Switch to a cheaper AI model (e.g., GPT-3.5-turbo)",
                    "Reduce scope by filtering to high-priority errors only",
                    "Use manual review for remaining errors",
                ],
                estimated_effort="low",
                priority_files=[],
                dangerous_patterns=[],
            )
        elif exit_reason == LoopExitReason.BUDGET_PREDICTED_EXCEEDED:
            return LoopRecommendation(
                action="budget_optimization",
                reason="Predicted costs would exceed budget",
                specific_suggestions=[
                    f'Current cost: ${analysis.get("total_cost", 0):.2f}',
                    f'Cost per error: ${analysis.get("cost_per_error_fixed", 0):.3f}',
                    "Consider switching to cheaper model for remaining iterations",
                    "Focus on highest-impact errors only",
                    "Set stricter error filtering criteria",
                ],
                estimated_effort="low",
                priority_files=[],
                dangerous_patterns=[],
            )
        elif exit_reason == LoopExitReason.REFACTOR_RECOMMENDED:
            return LoopRecommendation(
                action="refactor",
                reason="High error density and complexity suggest architectural issues",
                specific_suggestions=[
                    "Consider breaking large files into smaller modules",
                    "Implement proper TypeScript for better type safety",
                    "Establish consistent coding standards",
                    "Add comprehensive linting configuration",
                    "Consider migrating to modern framework patterns",
                ],
                estimated_effort="very_high",
                priority_files=[],
                dangerous_patterns=["no-unde", "max-len", "no-unused-vars"],
            )
        elif exit_reason == LoopExitReason.DIMINISHING_RETURNS:
            return LoopRecommendation(
                action="architect_mode",
                reason="Remaining errors require expert analysis",
                specific_suggestions=[
                    "Use architect mode for complex undefined variables",
                    "Generate Chain of Thought prompts for external AI review",
                    "Focus on structural issues rather than style",
                    "Consider pair programming for difficult errors",
                ],
                estimated_effort="high",
                priority_files=[],
                dangerous_patterns=["no-unde", "no-global-assign"],
            )
        elif exit_reason == LoopExitReason.CONVERGENCE_DETECTED:
            return LoopRecommendation(
                action="manual_review",
                reason="Automated fixes have reached their limit",
                specific_suggestions=[
                    "Remaining errors likely require human judgment",
                    "Review architectural decisions for remaining issues",
                    "Consider if remaining errors are acceptable technical debt",
                    "Document decisions for future reference",
                ],
                estimated_effort="medium",
                priority_files=[],
                dangerous_patterns=[],
            )
        elif exit_reason == LoopExitReason.ERROR_INCREASE:
            return LoopRecommendation(
                action="manual_review",
                reason="Automated fixes are introducing new errors",
                specific_suggestions=[
                    "Review recent changes for unintended side effects",
                    "Consider rolling back last iteration",
                    "Use more conservative fix strategies",
                    "Increase test coverage before continuing",
                ],
                estimated_effort="high",
                priority_files=[],
                dangerous_patterns=[],
            )
        else:
            return LoopRecommendation(
                action="manual_review",
                reason=exit_message,
                specific_suggestions=[
                    "Review current state and determine next steps",
                    "Consider different approach or tools",
                    "Consult with team on remaining errors",
                ],
                estimated_effort="medium",
                priority_files=[],
                dangerous_patterns=[],
            )

    def display_loop_summary(self, exit_reason: LoopExitReason, exit_message: str):
        """Display comprehensive summary of iterative loop results."""
        print("\n🔄 ITERATIVE FORCE MODE SUMMARY")
        print("=" * 60)
        if not self.iteration_results:
            print("No iterations completed.")
            return
        analysis = self.analyze_iteration_patterns()
        first = self.iteration_results[0]
        last = self.iteration_results[-1]
        # Overall results
        print("📊 Overall Results:")
        print(f"   Iterations completed: {analysis['total_iterations']}")
        print(f"   Total errors eliminated: {analysis['total_errors_eliminated']}")
        print(f"   Error reduction: {first.errors_before} → {last.errors_after}")
        print(
            f"   Overall improvement: {((first.errors_before - last.errors_after) / first.errors_before * 100):.1f}%"
        )
        print(f"   Total time: {analysis['total_time']:.1f} minutes")
        print(f"   Efficiency: {analysis['efficiency']:.1f} errors/minute")
        # Iteration breakdown
        print("\n📈 Iteration Breakdown:")
        for result in self.iteration_results:
            print(
                f"   Iteration {result.iteration}: {result.errors_before} → {result.errors_after} "
                f"({result.improvement_percentage:+.1f}%, {result.success_rate:.1f}% success)"
            )
        # Exit reason
        print("\n🛑 Loop Exit Reason:")
        print(f"   {exit_reason.value}: {exit_message}")
        # Trends
        print("\n📊 Trends:")
        print(f"   Improvement trend: {analysis['improvement_trend']}")
        print(f"   Success rate trend: {analysis['success_rate_trend']}")
        print(f"   ML learning trend: {analysis['ml_learning_trend']}")
        # Generate and display recommendations
        recommendations = self.generate_recommendations(exit_reason, exit_message)
        print("\n💡 RECOMMENDATIONS:")
        print(f"   Recommended action: {recommendations.action.upper()}")
        print(f"   Reason: {recommendations.reason}")
        print(f"   Estimated effort: {recommendations.estimated_effort}")
        print("\n🎯 Specific Suggestions:")
        for i, suggestion in enumerate(recommendations.specific_suggestions, 1):
            print(f"   {i}. {suggestion}")
        if recommendations.dangerous_patterns:
            print("\n⚠️  Focus on these error patterns:")
            for pattern in recommendations.dangerous_patterns:
                print(f"   • {pattern}")
        return recommendations
