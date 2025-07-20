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
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

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
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        
        # Loop configuration
        self.max_iterations = 10
        self.improvement_threshold = 5  # Minimum % improvement to continue
        self.diminishing_returns_threshold = 2  # % improvement considered diminishing
        self.convergence_window = 3  # Iterations to check for convergence
        self.max_error_increase_tolerance = 5  # Max errors that can increase
        
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
        
        if current_iteration >= self.max_iterations:
            return False, LoopExitReason.MAX_ITERATIONS_REACHED, \
                   f"Reached maximum iterations ({self.max_iterations})"
        
        if len(self.iteration_results) < 2:
            return True, None, "Need at least 2 iterations for analysis"
        
        latest = self.iteration_results[-1]
        previous = self.iteration_results[-2]
        
        # Check for error increase
        if latest.errors_after > previous.errors_after + self.max_error_increase_tolerance:
            return False, LoopExitReason.ERROR_INCREASE, \
                   f"Errors increased by {latest.errors_after - previous.errors_after}"
        
        # Check for no improvement
        if latest.improvement_percentage <= 0:
            return False, LoopExitReason.NO_IMPROVEMENT, \
                   "No improvement in latest iteration"
        
        # Check improvement threshold
        if latest.improvement_percentage < self.improvement_threshold:
            return False, LoopExitReason.IMPROVEMENT_THRESHOLD_NOT_MET, \
                   f"Improvement {latest.improvement_percentage:.1f}% below threshold {self.improvement_threshold}%"
        
        # Check for diminishing returns
        if len(self.iteration_results) >= 3:
            recent_improvements = [r.improvement_percentage for r in self.iteration_results[-3:]]
            avg_improvement = sum(recent_improvements) / len(recent_improvements)
            
            if avg_improvement < self.diminishing_returns_threshold:
                return False, LoopExitReason.DIMINISHING_RETURNS, \
                       f"Average improvement {avg_improvement:.1f}% indicates diminishing returns"
        
        # Check for convergence
        if len(self.iteration_results) >= self.convergence_window:
            recent_errors = [r.errors_after for r in self.iteration_results[-self.convergence_window:]]
            error_variance = max(recent_errors) - min(recent_errors)
            
            if error_variance <= 2:  # Very small variance indicates convergence
                return False, LoopExitReason.CONVERGENCE_DETECTED, \
                       f"Error count converged (variance: {error_variance})"
        
        # Check if refactor is recommended
        if self.should_recommend_refactor():
            return False, LoopExitReason.REFACTOR_RECOMMENDED, \
                   "Codebase complexity suggests refactoring needed"
        
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
    
    def analyze_iteration_patterns(self) -> Dict:
        """Analyze patterns across iterations for insights."""
        if len(self.iteration_results) < 2:
            return {}
        
        # Calculate trends
        improvements = [r.improvement_percentage for r in self.iteration_results]
        success_rates = [r.success_rate for r in self.iteration_results]
        ml_accuracies = [r.ml_accuracy for r in self.iteration_results]
        
        analysis = {
            'total_iterations': len(self.iteration_results),
            'total_errors_eliminated': self.iteration_results[0].errors_before - self.iteration_results[-1].errors_after,
            'average_improvement_per_iteration': sum(improvements) / len(improvements),
            'improvement_trend': 'increasing' if improvements[-1] > improvements[0] else 'decreasing',
            'success_rate_trend': 'improving' if success_rates[-1] > success_rates[0] else 'declining',
            'ml_learning_trend': 'improving' if ml_accuracies[-1] > ml_accuracies[0] else 'stable',
            'total_time': self.total_time,
            'efficiency': self.total_errors_fixed / self.total_time if self.total_time > 0 else 0
        }
        
        return analysis
    
    def generate_recommendations(self, exit_reason: LoopExitReason, exit_message: str) -> LoopRecommendation:
        """Generate intelligent recommendations based on loop results."""
        
        analysis = self.analyze_iteration_patterns()
        latest = self.iteration_results[-1] if self.iteration_results else None
        
        if exit_reason == LoopExitReason.MAX_ITERATIONS_REACHED:
            if analysis.get('improvement_trend') == 'increasing':
                return LoopRecommendation(
                    action='continue',
                    reason='Still showing improvement at max iterations',
                    specific_suggestions=[
                        'Increase --max-iterations to allow more cycles',
                        'Consider running with --max-errors increased',
                        'Focus on remaining high-priority errors'
                    ],
                    estimated_effort='medium',
                    priority_files=[],
                    dangerous_patterns=[]
                )
            else:
                return LoopRecommendation(
                    action='manual_review',
                    reason='Reached iteration limit with declining improvement',
                    specific_suggestions=[
                        'Review remaining errors manually',
                        'Consider architect mode for complex errors',
                        'Focus on dangerous undefined variables'
                    ],
                    estimated_effort='high',
                    priority_files=[],
                    dangerous_patterns=['no-undef', 'no-global-assign']
                )
        
        elif exit_reason == LoopExitReason.REFACTOR_RECOMMENDED:
            return LoopRecommendation(
                action='refactor',
                reason='High error density and complexity suggest architectural issues',
                specific_suggestions=[
                    'Consider breaking large files into smaller modules',
                    'Implement proper TypeScript for better type safety',
                    'Establish consistent coding standards',
                    'Add comprehensive linting configuration',
                    'Consider migrating to modern framework patterns'
                ],
                estimated_effort='very_high',
                priority_files=[],
                dangerous_patterns=['no-undef', 'max-len', 'no-unused-vars']
            )
        
        elif exit_reason == LoopExitReason.DIMINISHING_RETURNS:
            return LoopRecommendation(
                action='architect_mode',
                reason='Remaining errors require expert analysis',
                specific_suggestions=[
                    'Use architect mode for complex undefined variables',
                    'Generate Chain of Thought prompts for external AI review',
                    'Focus on structural issues rather than style',
                    'Consider pair programming for difficult errors'
                ],
                estimated_effort='high',
                priority_files=[],
                dangerous_patterns=['no-undef', 'no-global-assign']
            )
        
        elif exit_reason == LoopExitReason.CONVERGENCE_DETECTED:
            return LoopRecommendation(
                action='manual_review',
                reason='Automated fixes have reached their limit',
                specific_suggestions=[
                    'Remaining errors likely require human judgment',
                    'Review architectural decisions for remaining issues',
                    'Consider if remaining errors are acceptable technical debt',
                    'Document decisions for future reference'
                ],
                estimated_effort='medium',
                priority_files=[],
                dangerous_patterns=[]
            )
        
        elif exit_reason == LoopExitReason.ERROR_INCREASE:
            return LoopRecommendation(
                action='manual_review',
                reason='Automated fixes are introducing new errors',
                specific_suggestions=[
                    'Review recent changes for unintended side effects',
                    'Consider rolling back last iteration',
                    'Use more conservative fix strategies',
                    'Increase test coverage before continuing'
                ],
                estimated_effort='high',
                priority_files=[],
                dangerous_patterns=[]
            )
        
        else:
            return LoopRecommendation(
                action='manual_review',
                reason=exit_message,
                specific_suggestions=[
                    'Review current state and determine next steps',
                    'Consider different approach or tools',
                    'Consult with team on remaining errors'
                ],
                estimated_effort='medium',
                priority_files=[],
                dangerous_patterns=[]
            )
    
    def display_loop_summary(self, exit_reason: LoopExitReason, exit_message: str):
        """Display comprehensive summary of iterative loop results."""
        
        print(f"\n🔄 ITERATIVE FORCE MODE SUMMARY")
        print("=" * 60)
        
        if not self.iteration_results:
            print("No iterations completed.")
            return
        
        analysis = self.analyze_iteration_patterns()
        first = self.iteration_results[0]
        last = self.iteration_results[-1]
        
        # Overall results
        print(f"📊 Overall Results:")
        print(f"   Iterations completed: {analysis['total_iterations']}")
        print(f"   Total errors eliminated: {analysis['total_errors_eliminated']}")
        print(f"   Error reduction: {first.errors_before} → {last.errors_after}")
        print(f"   Overall improvement: {((first.errors_before - last.errors_after) / first.errors_before * 100):.1f}%")
        print(f"   Total time: {analysis['total_time']:.1f} minutes")
        print(f"   Efficiency: {analysis['efficiency']:.1f} errors/minute")
        
        # Iteration breakdown
        print(f"\n📈 Iteration Breakdown:")
        for result in self.iteration_results:
            print(f"   Iteration {result.iteration}: {result.errors_before} → {result.errors_after} "
                  f"({result.improvement_percentage:+.1f}%, {result.success_rate:.1f}% success)")
        
        # Exit reason
        print(f"\n🛑 Loop Exit Reason:")
        print(f"   {exit_reason.value}: {exit_message}")
        
        # Trends
        print(f"\n📊 Trends:")
        print(f"   Improvement trend: {analysis['improvement_trend']}")
        print(f"   Success rate trend: {analysis['success_rate_trend']}")
        print(f"   ML learning trend: {analysis['ml_learning_trend']}")
        
        # Generate and display recommendations
        recommendations = self.generate_recommendations(exit_reason, exit_message)
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   Recommended action: {recommendations.action.upper()}")
        print(f"   Reason: {recommendations.reason}")
        print(f"   Estimated effort: {recommendations.estimated_effort}")
        
        print(f"\n🎯 Specific Suggestions:")
        for i, suggestion in enumerate(recommendations.specific_suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        if recommendations.dangerous_patterns:
            print(f"\n⚠️  Focus on these error patterns:")
            for pattern in recommendations.dangerous_patterns:
                print(f"   • {pattern}")
        
        return recommendations
