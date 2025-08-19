#!/usr/bin/env python3
"""
Intelligent ML-Powered Force Mode for Chaotic Codebases
This module implements advanced machine learning techniques to safely handle
force mode in codebases with large numbers of lint errors (100+).
Key Features:
- Confidence-based auto-forcing (no confirmation for high-confidence fixes)
- Intelligent batch optimization using clustering algorithms
- Cascade prediction to prevent fixes that break other code
- Progressive learning from fix outcomes
- Special chaos management for large error counts
"""
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .ast_dependency_analyzer import EnhancedDependencyAnalyzer
from .error_analyzer import ErrorAnalysis
from .pattern_matcher import SmartErrorClassifier

logger = logging.getLogger(__name__)


@dataclass
class ForceDecision:
    """Decision about how to handle an error in force mode."""

    error_analysis: ErrorAnalysis
    action: str  # 'auto_force', 'batch_confirm', 'manual_review', 'skip'
    confidence: float
    batch_id: Optional[int] = None
    risk_factors: List[str] = None
    predicted_cascades: List[str] = None


@dataclass
class BatchPlan:
    """Plan for a batch of errors to fix together."""

    batch_id: int
    errors: List[ErrorAnalysis]
    confidence: float
    estimated_time: int  # minutes
    risk_level: str  # 'low', 'medium', 'high'
    dependencies: List[int] = None  # other batch IDs this depends on


class IntelligentForceMode:
    """ML-powered intelligent force mode for chaotic codebases."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        # Confidence thresholds for different actions
        self.auto_force_threshold = 0.90  # Auto-force without confirmation
        self.batch_force_threshold = 0.75  # Batch confirmation
        self.manual_review_threshold = 0.50  # Manual review required
        # Chaos management thresholds
        self.chaos_threshold = 100  # 100+ errors = chaotic codebase
        self.max_auto_force_count = 50  # Max auto-force in chaos mode
        self.optimal_batch_size = 15  # Target batch size
        # ML models
        self.confidence_predictor = RandomForestClassifier(n_estimators=100)
        self.cascade_predictor = RandomForestClassifier(n_estimators=50)
        self.batch_optimizer = KMeans(n_clusters=5)
        self.scaler = StandardScaler()
        # Learning system
        self.fix_history = []  # Track fix outcomes for learning
        self.cascade_history = []  # Track cascade events
        # Code dependency graph for cascade prediction
        self.dependency_graph = nx.DiGraph()
        # Enhanced AST-based dependency analyzer
        self.ast_analyzer = EnhancedDependencyAnalyzer()

    def analyze_force_strategy(self, error_analyses: List[ErrorAnalysis]) -> Dict:
        """Analyze errors and create intelligent force strategy."""
        total_errors = len(error_analyses)
        is_chaotic = total_errors >= self.chaos_threshold
        logger.info(f"Analyzing force strategy for {total_errors} errors")
        logger.info(f"Chaotic codebase: {is_chaotic}")
        # Step 1: Predict confidence for each error
        force_decisions = self._predict_force_decisions(error_analyses)
        # Step 2: Build code dependency graph
        self._build_dependency_graph(error_analyses)
        # Step 3: Predict cascading effects
        self._predict_cascades(force_decisions)
        # Step 4: Optimize batching strategy
        batch_plan = self._optimize_batching(force_decisions, is_chaotic)
        # Step 5: Create execution strategy
        strategy = self._create_execution_strategy(force_decisions, batch_plan, is_chaotic)
        return strategy

    def _predict_force_decisions(self, error_analyses: List[ErrorAnalysis]) -> List[ForceDecision]:
        """Predict confidence and action for each error."""
        decisions = []
        for error_analysis in error_analyses:
            # Extract features for ML prediction
            features = self._extract_error_features(error_analysis)
            # Predict confidence (using existing SmartErrorClassifier as base)
            base_confidence = self._get_base_confidence(error_analysis)
            # Enhance with ML predictions
            ml_confidence = self._predict_ml_confidence(features)
            # Combine confidences
            final_confidence = 0.7 * base_confidence + 0.3 * ml_confidence
            # Enhanced action determination with research-based improvements
            # Special cases: Safe formatting errors should be auto-forced more aggressively
            safe_auto_force_rules = [
                "max-len",
                "semi",
                "no-trailing-spaces",
                "no-unused-vars",
                "quotes",
                "indent",
            ]
            if error_analysis.error.rule_id in safe_auto_force_rules and final_confidence >= 0.70:
                action = "auto_force"
            # Standard action determination
            elif final_confidence >= self.auto_force_threshold:
                action = "auto_force"
            elif final_confidence >= self.batch_force_threshold:
                action = "batch_confirm"
            elif final_confidence >= self.manual_review_threshold:
                action = "manual_review"
            else:
                action = "skip"
            # Identify risk factors
            risk_factors = self._identify_risk_factors(error_analysis, final_confidence)
            decision = ForceDecision(
                error_analysis=error_analysis,
                action=action,
                confidence=final_confidence,
                risk_factors=risk_factors,
            )
            decisions.append(decision)
        return decisions

    def _extract_error_features(self, error_analysis: ErrorAnalysis) -> np.ndarray:
        """Extract ML features from error analysis."""
        features = []
        # Error type features
        error = error_analysis.error
        features.extend(
            [
                1 if error.rule_id == "no-unde" else 0,  # Dangerous undefined variable
                (1 if error.rule_id in ["max-len", "no-unused-vars"] else 0),  # Safe formatting
                1 if error.severity.value == "error" else 0,  # Error vs warning
                len(error.message),  # Message complexity
                error.line,  # Line number (early vs late in file)
            ]
        )
        # Context features
        features.extend(
            [
                (
                    error_analysis.complexity.value
                    if hasattr(error_analysis.complexity, "value")
                    else 1
                ),
                error_analysis.priority,
                1 if error_analysis.fixable else 0,
                error_analysis.estimated_effort,
                len(error_analysis.context_lines),
                len(error_analysis.related_errors),
            ]
        )
        # File features
        file_path = error.file_path
        features.extend(
            [
                1 if "test" in file_path.lower() else 0,  # Test file
                1 if file_path.endswith(".js") else 0,  # JavaScript
                1 if file_path.endswith(".py") else 0,  # Python
                1 if "config" in file_path.lower() else 0,  # Config file
                len(file_path.split("/")),  # Directory depth
            ]
        )
        return np.array(features)

    def _get_base_confidence(self, error_analysis: ErrorAnalysis) -> float:
        """Get base confidence from existing classification."""
        # Use existing fixable classification as base
        if not error_analysis.fixable:
            return 0.2  # Low confidence for unfixable errors
        # Safe error types get higher confidence, with enhanced JavaScript handling
        safe_rules = [
            "max-len",
            "no-unused-vars",
            "no-useless-escape",
            "prefer-const",
            "semi",
            "no-trailing-spaces",
            "quotes",
            "indent",
        ]
        if error_analysis.error.rule_id in safe_rules:
            # Enhanced handling for max-len in JavaScript files
            if error_analysis.error.rule_id == "max-len" and error_analysis.file_path.endswith(
                (".js", ".mjs", ".ts")
            ):
                # Check if this is a complex template literal or string concatenation
                if self._is_complex_javascript_string(error_analysis):
                    return 0.75  # Still high confidence - research shows these are fixable
            return 0.85
        # Dangerous error types get lower confidence
        dangerous_rules = ["no-unde", "no-global-assign", "no-implicit-globals"]
        if error_analysis.error.rule_id in dangerous_rules:
            return 0.3
        # Medium confidence for other errors
        return 0.6

    def _predict_ml_confidence(self, features: np.ndarray) -> float:
        """Predict confidence using ML model."""
        # For now, use rule-based prediction
        # In production, this would use trained ML models
        # Simple heuristic based on features
        if features[1] == 1:  # Safe formatting error
            return 0.9
        elif features[0] == 1:  # Dangerous undefined variable
            return 0.2
        else:
            return 0.6

    def _is_complex_javascript_string(self, error_analysis: ErrorAnalysis) -> bool:
        """Check if this is a complex JavaScript string that needs special handling."""
        try:
            with open(error_analysis.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if error_analysis.error.line <= len(lines):
                    line = lines[error_analysis.error.line - 1]
                    # Check for template literals, string concatenation, or complex patterns
                    return (
                        ("`" in line and "+" in line)
                        or ("REPOSITORY CONTEXT" in line)
                        or (line.count('"') > 4)
                    )
        except Exception:
            pass
        return False

    def _identify_risk_factors(self, error_analysis: ErrorAnalysis, confidence: float) -> List[str]:
        """Identify specific risk factors for this error."""
        risk_factors = []
        error = error_analysis.error
        # Undefined variable risks
        if error.rule_id == "no-unde":
            risk_factors.append("Undefined variable may break runtime")
            risk_factors.append("Could be missing import or global")
        # File type risks
        if "config" in error.file_path.lower():
            risk_factors.append("Configuration file - changes affect entire system")
        if "test" not in error.file_path.lower():
            risk_factors.append("Production code - changes affect users")
        # Complexity risks
        if error_analysis.estimated_effort > 3:
            risk_factors.append("High complexity fix - multiple changes needed")
        # Related error risks
        if len(error_analysis.related_errors) > 2:
            risk_factors.append("Multiple related errors - cascading effects possible")
        return risk_factors

    def _build_dependency_graph(self, error_analyses: List[ErrorAnalysis]):
        """Build enhanced code dependency graph using AST analysis for cascade prediction."""
        self.dependency_graph.clear()
        # Group errors by file
        files_with_errors = defaultdict(list)
        for error_analysis in error_analyses:
            file_path = error_analysis.error.file_path
            files_with_errors[file_path].append(error_analysis)
        file_paths = list(files_with_errors.keys())
        try:
            # Use AST analysis for enhanced dependency detection
            logger.info(f"Building AST-based dependency graph for {len(file_paths)} files")
            enhanced_graph = self.ast_analyzer.analyze_files(file_paths)
            # Merge the enhanced graph with our dependency graph
            self.dependency_graph = enhanced_graph.copy()
            # Add error-specific metadata to nodes
            for file_path, error_list in files_with_errors.items():
                if file_path in self.dependency_graph:
                    self.dependency_graph.nodes[file_path]["error_count"] = len(error_list)
                    self.dependency_graph.nodes[file_path]["error_types"] = [
                        error.error.rule_id for error in error_list
                    ]
                else:
                    # Add node if not found by AST analysis
                    self.dependency_graph.add_node(
                        file_path,
                        type="file",
                        error_count=len(error_list),
                        error_types=[error.error.rule_id for error in error_list],
                    )
            logger.info(
                f"Enhanced dependency graph built with {self.dependency_graph.number_of_nodes()} nodes "
                f"and {self.dependency_graph.number_of_edges()} edges"
            )
        except Exception as e:
            logger.warning(f"AST analysis failed, falling back to simple heuristics: {e}")
            # Fallback to simple heuristic-based approach
            for file_path in files_with_errors:
                self.dependency_graph.add_node(
                    file_path,
                    type="file",
                    error_count=len(files_with_errors[file_path]),
                )
                # Simple heuristic: files in same directory are related
                for other_file in files_with_errors:
                    if (
                        file_path != other_file
                        and file_path.split("/")[:-1] == other_file.split("/")[:-1]
                    ):
                        self.dependency_graph.add_edge(
                            file_path, other_file, type="directory_proximity"
                        )

    def _predict_cascades(self, force_decisions: List[ForceDecision]):
        """Predict cascading effects of fixes using enhanced dependency analysis."""
        for decision in force_decisions:
            if decision.action in ["auto_force", "batch_confirm"]:
                file_path = decision.error_analysis.error.file_path
                error_type = decision.error_analysis.error.rule_id
                predicted_cascades = []
                if file_path in self.dependency_graph:
                    # Get direct dependencies (files that depend on this file)
                    direct_deps = list(self.dependency_graph.successors(file_path))
                    # Get reverse dependencies (files this file depends on)
                    reverse_deps = list(self.dependency_graph.predecessors(file_path))
                    # Prioritize cascades based on error type and dependency strength
                    for dep_file in direct_deps + reverse_deps:
                        edge_data = self.dependency_graph.get_edge_data(
                            file_path, dep_file
                        ) or self.dependency_graph.get_edge_data(dep_file, file_path)
                        if edge_data:
                            # Calculate cascade risk based on dependency type and error type
                            risk_score = self._calculate_cascade_risk(error_type, edge_data)
                            if risk_score > 0.3:  # Only include significant risks
                                predicted_cascades.append(
                                    {
                                        "file": dep_file,
                                        "risk_score": risk_score,
                                        "dependency_type": edge_data.get("type", "unknown"),
                                    }
                                )
                    # Sort by risk score and take top 3
                    predicted_cascades.sort(key=lambda x: x["risk_score"], reverse=True)
                    decision.predicted_cascades = [c["file"] for c in predicted_cascades[:3]]
                    # Add risk information to decision
                    if predicted_cascades:
                        max_risk = predicted_cascades[0]["risk_score"]
                        if max_risk > 0.7:
                            decision.risk_factors.append(
                                f"High cascade risk ({max_risk:.1f}) to {len(predicted_cascades)} files"
                            )
                        elif max_risk > 0.5:
                            decision.risk_factors.append(
                                f"Medium cascade risk ({max_risk:.1f}) to {len(predicted_cascades)} files"
                            )
                # Enhanced cascade prediction for specific error types
                if error_type in ["no-unde", "no-global-assign"]:
                    # Variable-related errors have higher cascade risk
                    function_deps = self.ast_analyzer.get_function_dependencies(file_path)
                    variable_deps = self.ast_analyzer.get_variable_dependencies(file_path)
                    all_deps = set(function_deps + variable_deps)
                    for dep_file in all_deps:
                        if dep_file not in decision.predicted_cascades:
                            decision.predicted_cascades.append(dep_file)
                    # Limit total cascades
                    decision.predicted_cascades = decision.predicted_cascades[:5]

    def _calculate_cascade_risk(self, error_type: str, edge_data: dict) -> float:
        """Calculate cascade risk score based on error type and dependency relationship."""
        base_risk = 0.3
        # Error type risk multipliers
        error_risk_multipliers = {
            "no-unde": 0.8,  # Undefined variables have high cascade risk
            "no-global-assign": 0.7,  # Global assignments affect many files
            "import/no-unresolved": 0.9,  # Import errors cascade heavily
            "unused-import": 0.2,  # Low cascade risk
            "prefer-const": 0.1,  # Very low cascade risk
        }
        # Dependency type risk multipliers
        dep_risk_multipliers = {
            "import": 0.8,  # Import dependencies have high risk
            "calls": 0.6,  # Function calls have medium risk
            "directory_proximity": 0.2,  # Directory proximity has low risk
        }
        error_multiplier = error_risk_multipliers.get(error_type, 0.3)
        dep_multiplier = dep_risk_multipliers.get(edge_data.get("type", "unknown"), 0.3)
        # Calculate final risk score
        risk_score = base_risk * error_multiplier * dep_multiplier
        # Boost risk if there are imported names that might be affected
        if "imported_names" in edge_data and edge_data["imported_names"]:
            risk_score *= 1.2
        return min(risk_score, 1.0)  # Cap at 1.0

    def get_dependency_insights(self) -> Dict[str, any]:
        """Get insights about the dependency structure for recommendations."""
        if not self.dependency_graph.nodes():
            return {}
        insights = {
            "total_files": self.dependency_graph.number_of_nodes(),
            "total_dependencies": self.dependency_graph.number_of_edges(),
            "highly_connected_files": [],
            "isolated_files": [],
            "import_heavy_files": [],
            "dependency_clusters": [],
        }
        # Find highly connected files (potential architectural hotspots)
        for node in self.dependency_graph.nodes():
            in_degree = self.dependency_graph.in_degree(node)
            out_degree = self.dependency_graph.out_degree(node)
            total_degree = in_degree + out_degree
            if total_degree > 5:  # Threshold for "highly connected"
                insights["highly_connected_files"].append(
                    {
                        "file": node,
                        "connections": total_degree,
                        "dependents": in_degree,
                        "dependencies": out_degree,
                    }
                )
            elif total_degree == 0:
                insights["isolated_files"].append(node)
        # Find files with many imports (potential refactoring candidates)
        for node in self.dependency_graph.nodes():
            import_edges = [
                edge
                for edge in self.dependency_graph.out_edges(node, data=True)
                if edge[2].get("type") == "import"
            ]
            if len(import_edges) > 10:  # Threshold for "import heavy"
                insights["import_heavy_files"].append(
                    {"file": node, "import_count": len(import_edges)}
                )
        # Sort by connection count
        insights["highly_connected_files"].sort(key=lambda x: x["connections"], reverse=True)
        insights["import_heavy_files"].sort(key=lambda x: x["import_count"], reverse=True)
        return insights

    def _optimize_batching(
        self, force_decisions: List[ForceDecision], is_chaotic: bool
    ) -> List[BatchPlan]:
        """Optimize batching strategy using ML clustering."""
        # Separate decisions by action type
        auto_force_decisions = [d for d in force_decisions if d.action == "auto_force"]
        batch_decisions = [d for d in force_decisions if d.action == "batch_confirm"]
        batch_plans = []
        # Auto-force decisions don't need batching (they're automatic)
        if auto_force_decisions:
            batch_plans.append(
                BatchPlan(
                    batch_id=0,
                    errors=[d.error_analysis for d in auto_force_decisions],
                    confidence=np.mean([d.confidence for d in auto_force_decisions]),
                    estimated_time=len(auto_force_decisions) * 2,  # 2 min per error
                    risk_level="low",
                )
            )
        # Optimize batching for batch_confirm decisions
        if batch_decisions:
            batches = self._create_optimal_batches(batch_decisions, is_chaotic)
            batch_plans.extend(batches)
        return batch_plans

    def _create_optimal_batches(
        self, decisions: List[ForceDecision], is_chaotic: bool
    ) -> List[BatchPlan]:
        """Create optimal batches using clustering."""
        if not decisions:
            return []
        # Extract features for clustering
        features = []
        for decision in decisions:
            features.append(
                [
                    decision.confidence,
                    len(decision.risk_factors) if decision.risk_factors else 0,
                    decision.error_analysis.priority,
                    decision.error_analysis.estimated_effort,
                ]
            )
        features_array = np.array(features)
        # Determine number of batches
        if is_chaotic:
            n_batches = min(len(decisions) // self.optimal_batch_size + 1, 8)
        else:
            n_batches = min(len(decisions) // 10 + 1, 4)
        # Cluster decisions into batches
        if len(decisions) > n_batches:
            kmeans = KMeans(n_clusters=n_batches, random_state=42)
            cluster_labels = kmeans.fit_predict(features_array)
        else:
            cluster_labels = list(range(len(decisions)))
        # Create batch plans
        batches = []
        for batch_id in range(n_batches):
            batch_decisions = [
                decisions[i] for i, label in enumerate(cluster_labels) if label == batch_id
            ]
            if batch_decisions:
                avg_confidence = np.mean([d.confidence for d in batch_decisions])
                total_risk_factors = sum(
                    len(d.risk_factors) if d.risk_factors else 0 for d in batch_decisions
                )
                # Determine risk level
                if avg_confidence > 0.8 and total_risk_factors < 5:
                    risk_level = "low"
                elif avg_confidence > 0.6 and total_risk_factors < 10:
                    risk_level = "medium"
                else:
                    risk_level = "high"
                batch = BatchPlan(
                    batch_id=batch_id + 1,  # Start from 1 (0 is auto-force)
                    errors=[d.error_analysis for d in batch_decisions],
                    confidence=avg_confidence,
                    estimated_time=len(batch_decisions) * 3,  # 3 min per error
                    risk_level=risk_level,
                )
                batches.append(batch)
        return batches

    def _create_execution_strategy(
        self,
        force_decisions: List[ForceDecision],
        batch_plans: List[BatchPlan],
        is_chaotic: bool,
    ) -> Dict:
        """Create final execution strategy."""
        # Count decisions by action
        action_counts = defaultdict(int)
        for decision in force_decisions:
            action_counts[decision.action] += 1
        # Calculate time estimates
        total_auto_force = action_counts["auto_force"]
        total_batch_confirm = action_counts["batch_confirm"]
        total_manual_review = action_counts["manual_review"]
        estimated_time = (
            total_auto_force * 2  # 2 min per auto-force
            + total_batch_confirm * 3  # 3 min per batch-confirm
            + total_manual_review * 10  # 10 min per manual review
        )
        strategy = {
            "is_chaotic": is_chaotic,
            "total_errors": len(force_decisions),
            "action_breakdown": dict(action_counts),
            "batch_plans": batch_plans,
            "estimated_time_minutes": estimated_time,
            "auto_force_enabled": total_auto_force > 0,
            "recommendations": self._generate_recommendations(force_decisions, is_chaotic),
            "force_decisions": force_decisions,
        }
        return strategy

    def _generate_recommendations(
        self, force_decisions: List[ForceDecision], is_chaotic: bool
    ) -> List[str]:
        """Generate intelligent recommendations for the user."""
        recommendations = []
        auto_force_count = sum(1 for d in force_decisions if d.action == "auto_force")
        dangerous_count = sum(
            1 for d in force_decisions if d.error_analysis.error.rule_id == "no-unde"
        )
        # Get dependency insights for enhanced recommendations
        dep_insights = self.get_dependency_insights()
        if is_chaotic:
            recommendations.append(
                f"🏥 CHAOTIC CODEBASE DETECTED: {len(force_decisions)} errors found"
            )
            recommendations.append(
                f"🤖 {auto_force_count} safe errors will be auto-fixed without confirmation"
            )
            recommendations.append(f"⚠️  {dangerous_count} dangerous errors require manual review")
            recommendations.append("📊 Use progressive fixing: safe errors first, then risky ones")
        if auto_force_count > 50:
            recommendations.append("⚡ Large auto-force batch: Consider running in smaller chunks")
        if dangerous_count > 10:
            recommendations.append(
                "🏗️  Many undefined variables: Consider architect mode for expert review"
            )
        # Add dependency-based recommendations
        if dep_insights:
            if dep_insights.get("highly_connected_files"):
                top_connected = dep_insights["highly_connected_files"][:3]
                recommendations.append(
                    f"🔗 {len(top_connected)} highly connected files detected - "
                    "fixes may have cascading effects"
                )
                for file_info in top_connected:
                    file_name = file_info["file"].split("/")[-1]  # Just filename
                    recommendations.append(
                        f"   📁 {file_name}: {file_info['connections']} connections "
                        f"({file_info['dependents']} dependents)"
                    )
            if dep_insights.get("import_heavy_files"):
                heavy_files = dep_insights["import_heavy_files"][:2]
                recommendations.append(
                    f"📦 {len(heavy_files)} files with many imports - "
                    "potential refactoring candidates"
                )
        # Add cascade-specific recommendations
        high_cascade_decisions = [
            d for d in force_decisions if d.predicted_cascades and len(d.predicted_cascades) > 2
        ]
        if high_cascade_decisions:
            recommendations.append(
                f"🌊 {len(high_cascade_decisions)} fixes may cause cascading changes - "
                "review carefully"
            )
        return recommendations

    def learn_from_outcome(
        self, decision: ForceDecision, success: bool, created_new_errors: bool = False
    ):
        """Learn from fix outcomes to improve future predictions."""
        outcome = {
            "decision": decision,
            "success": success,
            "created_new_errors": created_new_errors,
            "confidence_was_correct": (success and decision.confidence > 0.7)
            or (not success and decision.confidence < 0.7),
        }
        self.fix_history.append(outcome)
        # Update confidence thresholds based on learning
        if len(self.fix_history) > 100:
            self._update_confidence_thresholds()

    def _update_confidence_thresholds(self):
        """Update confidence thresholds based on learning history."""
        # Analyze recent outcomes to adjust thresholds
        recent_outcomes = self.fix_history[-100:]
        # Calculate success rates by confidence range
        high_conf_success = sum(
            1 for o in recent_outcomes if o["decision"].confidence > 0.8 and o["success"]
        )
        high_conf_total = sum(1 for o in recent_outcomes if o["decision"].confidence > 0.8)
        if high_conf_total > 10:
            success_rate = high_conf_success / high_conf_total
            # Adjust auto-force threshold based on success rate
            if success_rate > 0.95:
                self.auto_force_threshold = max(0.85, self.auto_force_threshold - 0.02)
            elif success_rate < 0.85:
                self.auto_force_threshold = min(0.95, self.auto_force_threshold + 0.02)
        logger.info(f"Updated auto-force threshold to {self.auto_force_threshold:.2f}")
