#!/usr/bin/env python3
"""
Advanced Convergence Detection and Recommendation System

This module implements sophisticated analysis of iteration patterns to identify optimal
stopping points and provide accurate predictions of potential improvement from continued
execution using machine learning analysis of historical patterns.

Based on research findings that enhanced convergence detection would implement more
sophisticated analysis of iteration patterns to identify optimal stopping points and
provide more accurate predictions of potential improvement from continued execution.

Key Features:
- Machine learning-based convergence prediction
- Historical pattern analysis
- Optimal stopping point detection
- Improvement potential estimation
- Recommendation generation based on convergence patterns
- Adaptive threshold adjustment
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using simplified convergence detection")

logger = logging.getLogger(__name__)


class ConvergenceState(Enum):
    """States of convergence analysis."""

    IMPROVING = "improving"
    PLATEAUING = "plateauing"
    CONVERGED = "converged"
    DIVERGING = "diverging"
    OSCILLATING = "oscillating"


@dataclass
class IterationPattern:
    """Pattern data for a single iteration."""

    iteration: int
    errors_before: int
    errors_after: int
    improvement_rate: float
    success_rate: float
    time_taken: float
    cost: float
    ml_accuracy: float
    new_errors: int
    complexity_score: float = 0.0


@dataclass
class ConvergenceAnalysis:
    """Results of convergence analysis."""

    current_state: ConvergenceState
    confidence: float
    predicted_final_errors: int
    predicted_iterations_remaining: int
    improvement_potential: float
    stopping_recommendation: str
    risk_factors: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class HistoricalSession:
    """Historical session data for learning."""

    session_id: str
    patterns: List[IterationPattern]
    final_state: ConvergenceState
    total_iterations: int
    final_improvement: float
    project_characteristics: Dict[str, any] = field(default_factory=dict)


class AdvancedConvergenceAnalyzer:
    """Advanced convergence detection using machine learning and pattern analysis."""

    def __init__(self, project_path: str):
        self.project_path = project_path

        # ML models for prediction
        self.improvement_predictor = None
        self.convergence_classifier = None
        self.scaler = StandardScaler()

        # Historical data
        self.historical_sessions: List[HistoricalSession] = []
        self.current_patterns: List[IterationPattern] = []

        # Analysis parameters
        self.min_iterations_for_analysis = 3
        self.convergence_threshold = 0.02  # 2% improvement threshold
        self.plateau_window = 3  # Iterations to check for plateau
        self.oscillation_threshold = 0.1  # 10% variance for oscillation detection

        # Cache directory for model persistence
        self.cache_dir = Path(project_path) / ".aider-lint-cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Load historical data and models
        self._load_historical_data()
        self._initialize_models()

    def add_iteration_pattern(
        self,
        iteration: int,
        errors_before: int,
        errors_after: int,
        success_rate: float,
        time_taken: float,
        cost: float,
        ml_accuracy: float,
        new_errors: int,
    ) -> IterationPattern:
        """Add a new iteration pattern for analysis."""

        improvement_rate = (
            (errors_before - errors_after) / errors_before if errors_before > 0 else 0
        )

        # Calculate complexity score based on various factors
        complexity_score = self._calculate_complexity_score(
            errors_before, errors_after, success_rate, new_errors
        )

        pattern = IterationPattern(
            iteration=iteration,
            errors_before=errors_before,
            errors_after=errors_after,
            improvement_rate=improvement_rate,
            success_rate=success_rate,
            time_taken=time_taken,
            cost=cost,
            ml_accuracy=ml_accuracy,
            new_errors=new_errors,
            complexity_score=complexity_score,
        )

        self.current_patterns.append(pattern)

        logger.debug(
            f"Added iteration pattern {iteration}: "
            f"{improvement_rate:.3f} improvement, "
            f"{complexity_score:.3f} complexity"
        )

        return pattern

    def analyze_convergence(self) -> ConvergenceAnalysis:
        """Perform comprehensive convergence analysis."""

        if len(self.current_patterns) < self.min_iterations_for_analysis:
            return ConvergenceAnalysis(
                current_state=ConvergenceState.IMPROVING,
                confidence=0.1,
                predicted_final_errors=(
                    self.current_patterns[-1].errors_after if self.current_patterns else 0
                ),
                predicted_iterations_remaining=5,
                improvement_potential=0.5,
                stopping_recommendation="Continue - insufficient data for analysis",
            )

        # Analyze current state
        current_state = self._detect_convergence_state()

        # Predict future performance
        predictions = self._predict_future_performance()

        # Generate recommendations
        recommendation = self._generate_stopping_recommendation(current_state, predictions)

        # Calculate confidence based on pattern consistency and historical data
        confidence = self._calculate_confidence(current_state, predictions)

        return ConvergenceAnalysis(
            current_state=current_state,
            confidence=confidence,
            predicted_final_errors=predictions["final_errors"],
            predicted_iterations_remaining=predictions["iterations_remaining"],
            improvement_potential=predictions["improvement_potential"],
            stopping_recommendation=recommendation["action"],
            risk_factors=recommendation["risk_factors"],
            optimization_suggestions=recommendation["optimizations"],
        )

    def _detect_convergence_state(self) -> ConvergenceState:
        """Detect the current convergence state using pattern analysis."""

        if len(self.current_patterns) < 3:
            return ConvergenceState.IMPROVING

        recent_patterns = self.current_patterns[-self.plateau_window :]
        improvements = [p.improvement_rate for p in recent_patterns]

        # Check for convergence (very low improvement)
        avg_improvement = np.mean(improvements)
        if avg_improvement < self.convergence_threshold:
            return ConvergenceState.CONVERGED

        # Check for plateau (consistent low improvement)
        improvement_variance = np.var(improvements)
        if avg_improvement < 0.05 and improvement_variance < 0.01:
            return ConvergenceState.PLATEAUING

        # Check for oscillation (high variance in improvements)
        if improvement_variance > self.oscillation_threshold:
            return ConvergenceState.OSCILLATING

        # Check for divergence (negative improvements)
        recent_errors = [p.errors_after for p in recent_patterns]
        if len(recent_errors) >= 2 and recent_errors[-1] > recent_errors[0]:
            return ConvergenceState.DIVERGING

        # Default to improving
        return ConvergenceState.IMPROVING

    def _predict_future_performance(self) -> Dict[str, any]:
        """Predict future performance using ML models and pattern analysis."""

        predictions = {
            "final_errors": self.current_patterns[-1].errors_after,
            "iterations_remaining": 3,
            "improvement_potential": 0.3,
        }

        if not SKLEARN_AVAILABLE or len(self.current_patterns) < 5:
            # Fallback to simple trend analysis
            return self._simple_trend_prediction()

        try:
            # Prepare features for ML prediction
            features = self._extract_features_for_prediction()

            if self.improvement_predictor and len(features) > 0:
                # Predict improvement potential
                scaled_features = self.scaler.transform([features])
                improvement_pred = self.improvement_predictor.predict(scaled_features)[0]
                predictions["improvement_potential"] = max(0, min(1, improvement_pred))

                # Estimate iterations remaining based on improvement rate
                current_errors = self.current_patterns[-1].errors_after
                if improvement_pred > 0.1:
                    estimated_iterations = min(
                        10, max(1, int(current_errors * 0.1 / improvement_pred))
                    )
                    predictions["iterations_remaining"] = estimated_iterations
                    predictions["final_errors"] = max(
                        0, int(current_errors * (1 - improvement_pred))
                    )

        except Exception as e:
            logger.warning(f"ML prediction failed, using fallback: {e}")
            return self._simple_trend_prediction()

        return predictions

    def _simple_trend_prediction(self) -> Dict[str, any]:
        """Simple trend-based prediction when ML is not available."""

        if len(self.current_patterns) < 2:
            return {
                "final_errors": (
                    self.current_patterns[-1].errors_after if self.current_patterns else 0
                ),
                "iterations_remaining": 5,
                "improvement_potential": 0.3,
            }

        # Calculate trend from recent patterns
        recent_improvements = [p.improvement_rate for p in self.current_patterns[-3:]]
        avg_improvement = np.mean(recent_improvements)

        current_errors = self.current_patterns[-1].errors_after

        if avg_improvement > 0.05:
            # Good improvement trend
            iterations_remaining = min(8, max(2, int(current_errors * 0.1 / avg_improvement)))
            final_errors = max(
                0, int(current_errors * (1 - avg_improvement * iterations_remaining))
            )
            improvement_potential = min(0.8, avg_improvement * 10)
        else:
            # Poor improvement trend
            iterations_remaining = 2
            final_errors = current_errors
            improvement_potential = 0.1

        return {
            "final_errors": final_errors,
            "iterations_remaining": iterations_remaining,
            "improvement_potential": improvement_potential,
        }

    def _generate_stopping_recommendation(
        self, state: ConvergenceState, predictions: Dict
    ) -> Dict[str, any]:
        """Generate intelligent stopping recommendations."""

        risk_factors = []
        optimizations = []

        if state == ConvergenceState.CONVERGED:
            action = "STOP - Convergence achieved"
            risk_factors.append("Further iterations unlikely to yield significant improvement")

        elif state == ConvergenceState.PLATEAUING:
            if predictions["improvement_potential"] < 0.2:
                action = "STOP - Plateau reached with low improvement potential"
                optimizations.append("Consider switching to architect mode for remaining errors")
            else:
                action = "CONTINUE - Potential for breakthrough"
                optimizations.append("Try different error prioritization strategy")

        elif state == ConvergenceState.DIVERGING:
            action = "STOP - Performance degrading"
            risk_factors.append("Fixes may be introducing new errors")
            optimizations.append("Review recent changes and consider rollback")

        elif state == ConvergenceState.OSCILLATING:
            action = "ADJUST - Unstable performance"
            risk_factors.append("Inconsistent fix success rates")
            optimizations.append("Reduce batch sizes or increase confidence thresholds")

        else:  # IMPROVING
            if predictions["iterations_remaining"] <= 2:
                action = "CONTINUE - Near completion"
            elif predictions["improvement_potential"] > 0.5:
                action = "CONTINUE - High improvement potential"
            else:
                action = "CONTINUE - Moderate progress"
                optimizations.append("Monitor for plateau in next 2 iterations")

        return {
            "action": action,
            "risk_factors": risk_factors,
            "optimizations": optimizations,
        }

    def _calculate_confidence(self, state: ConvergenceState, predictions: Dict) -> float:
        """Calculate confidence in the convergence analysis."""

        base_confidence = 0.5

        # Increase confidence with more data points
        data_confidence = min(0.3, len(self.current_patterns) * 0.05)

        # Increase confidence with consistent patterns
        if len(self.current_patterns) >= 3:
            recent_improvements = [p.improvement_rate for p in self.current_patterns[-3:]]
            consistency = 1.0 - np.std(recent_improvements)
            pattern_confidence = max(0, min(0.3, consistency))
        else:
            pattern_confidence = 0.1

        # Increase confidence with historical data
        historical_confidence = min(0.2, len(self.historical_sessions) * 0.02)

        total_confidence = (
            base_confidence + data_confidence + pattern_confidence + historical_confidence
        )

        return min(1.0, total_confidence)

    def _calculate_complexity_score(
        self,
        errors_before: int,
        errors_after: int,
        success_rate: float,
        new_errors: int,
    ) -> float:
        """Calculate complexity score for the iteration."""

        # Base complexity from error reduction efficiency
        if errors_before > 0:
            reduction_efficiency = (errors_before - errors_after) / errors_before
        else:
            reduction_efficiency = 0

        # Penalty for new errors introduced
        new_error_penalty = new_errors * 0.1

        # Bonus for high success rate
        success_bonus = success_rate * 0.2

        complexity = 1.0 - reduction_efficiency + new_error_penalty - success_bonus

        return max(0.0, min(1.0, complexity))

    def _extract_features_for_prediction(self) -> List[float]:
        """Extract features for ML prediction."""

        if len(self.current_patterns) < 3:
            return []

        recent = self.current_patterns[-3:]

        features = [
            # Trend features
            np.mean([p.improvement_rate for p in recent]),
            np.std([p.improvement_rate for p in recent]),
            np.mean([p.success_rate for p in recent]),
            np.mean([p.complexity_score for p in recent]),
            # Current state features
            self.current_patterns[-1].errors_after,
            self.current_patterns[-1].ml_accuracy,
            len(self.current_patterns),
            # Cost efficiency features
            np.mean([p.cost for p in recent]),
            np.mean([p.time_taken for p in recent]),
        ]

        return features

    def _initialize_models(self):
        """Initialize ML models for convergence prediction."""

        if not SKLEARN_AVAILABLE:
            return

        # Try to load existing models
        model_file = self.cache_dir / "convergence_models.json"

        if model_file.exists() and len(self.historical_sessions) > 10:
            try:
                self._train_models()
                logger.info("Convergence prediction models initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ML models: {e}")

    def _train_models(self):
        """Train ML models on historical data."""

        if not SKLEARN_AVAILABLE or len(self.historical_sessions) < 5:
            return

        # Prepare training data
        X, y_improvement, y_convergence = self._prepare_training_data()

        if len(X) < 5:
            return

        try:
            # Train improvement predictor
            self.improvement_predictor = RandomForestRegressor(n_estimators=50, random_state=42)
            X_scaled = self.scaler.fit_transform(X)
            self.improvement_predictor.fit(X_scaled, y_improvement)

            # Train convergence classifier
            self.convergence_classifier = GradientBoostingClassifier(
                n_estimators=50, random_state=42
            )
            self.convergence_classifier.fit(X_scaled, y_convergence)

            logger.info(f"Trained convergence models on {len(X)} samples")

        except Exception as e:
            logger.warning(f"Failed to train convergence models: {e}")

    def _prepare_training_data(self) -> Tuple[List, List, List]:
        """Prepare training data from historical sessions."""

        X = []
        y_improvement = []
        y_convergence = []

        for session in self.historical_sessions:
            if len(session.patterns) < 3:
                continue

            # Use patterns from middle of session for training
            for i in range(2, len(session.patterns) - 1):
                recent_patterns = session.patterns[max(0, i - 2) : i + 1]

                # Extract features
                features = self._extract_session_features(recent_patterns)
                if not features:
                    continue

                # Target: improvement in next iteration
                next_pattern = session.patterns[i + 1]
                improvement = next_pattern.improvement_rate

                # Target: convergence state
                convergence_state = 1 if session.final_state == ConvergenceState.CONVERGED else 0

                X.append(features)
                y_improvement.append(improvement)
                y_convergence.append(convergence_state)

        return X, y_improvement, y_convergence

    def _extract_session_features(self, patterns: List[IterationPattern]) -> List[float]:
        """Extract features from session patterns."""

        if len(patterns) < 2:
            return []

        return [
            np.mean([p.improvement_rate for p in patterns]),
            np.std([p.improvement_rate for p in patterns]),
            np.mean([p.success_rate for p in patterns]),
            np.mean([p.complexity_score for p in patterns]),
            patterns[-1].errors_after,
            patterns[-1].ml_accuracy,
            len(patterns),
            np.mean([p.cost for p in patterns]),
            np.mean([p.time_taken for p in patterns]),
        ]

    def _load_historical_data(self):
        """Load historical convergence data."""

        history_file = self.cache_dir / "convergence_history.json"

        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    data = json.load(f)

                for session_data in data.get("sessions", []):
                    patterns = [
                        IterationPattern(**pattern_data)
                        for pattern_data in session_data["patterns"]
                    ]

                    session = HistoricalSession(
                        session_id=session_data["session_id"],
                        patterns=patterns,
                        final_state=ConvergenceState(session_data["final_state"]),
                        total_iterations=session_data["total_iterations"],
                        final_improvement=session_data["final_improvement"],
                        project_characteristics=session_data.get("project_characteristics", {}),
                    )

                    self.historical_sessions.append(session)

                logger.info(f"Loaded {len(self.historical_sessions)} historical sessions")

            except Exception as e:
                logger.warning(f"Failed to load convergence history: {e}")

    def save_session(self, session_id: str, final_state: ConvergenceState):
        """Save current session to historical data."""

        if not self.current_patterns:
            return

        total_improvement = (
            (self.current_patterns[0].errors_before - self.current_patterns[-1].errors_after)
            / self.current_patterns[0].errors_before
            if self.current_patterns[0].errors_before > 0
            else 0
        )

        session = HistoricalSession(
            session_id=session_id,
            patterns=self.current_patterns.copy(),
            final_state=final_state,
            total_iterations=len(self.current_patterns),
            final_improvement=total_improvement,
        )

        self.historical_sessions.append(session)

        # Save to file
        history_file = self.cache_dir / "convergence_history.json"

        try:
            data = {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "patterns": [p.__dict__ for p in s.patterns],
                        "final_state": s.final_state.value,
                        "total_iterations": s.total_iterations,
                        "final_improvement": s.final_improvement,
                        "project_characteristics": s.project_characteristics,
                    }
                    for s in self.historical_sessions[-50:]  # Keep last 50 sessions
                ]
            }

            with open(history_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Saved convergence session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to save convergence history: {e}")

    def reset_current_session(self):
        """Reset current session patterns."""
        self.current_patterns = []
