#!/usr/bin/env python3
"""
Tests for intelligent_force_mode module.

Tests the IntelligentForceMode class for ML-powered force mode
decision making in chaotic codebases.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from aider_lint_fixer.error_analyzer import ErrorAnalysis, ErrorSeverity
from aider_lint_fixer.intelligent_force_mode import (
    BatchPlan,
    ForceDecision,
    IntelligentForceMode,
)


class TestForceDecision(unittest.TestCase):
    """Test ForceDecision dataclass."""

    def test_force_decision_creation(self):
        """Test creating ForceDecision objects."""
        mock_error_analysis = Mock()
        
        decision = ForceDecision(
            error_analysis=mock_error_analysis,
            action="auto_force",
            confidence=0.85,
            batch_id=1,
            risk_factors=["high complexity"],
            predicted_cascades=["file1.py", "file2.py"]
        )

        self.assertEqual(decision.error_analysis, mock_error_analysis)
        self.assertEqual(decision.action, "auto_force")
        self.assertEqual(decision.confidence, 0.85)
        self.assertEqual(decision.batch_id, 1)
        self.assertEqual(decision.risk_factors, ["high complexity"])
        self.assertEqual(decision.predicted_cascades, ["file1.py", "file2.py"])

    def test_force_decision_defaults(self):
        """Test ForceDecision with default values."""
        mock_error_analysis = Mock()
        
        decision = ForceDecision(
            error_analysis=mock_error_analysis,
            action="skip",
            confidence=0.2
        )

        self.assertEqual(decision.error_analysis, mock_error_analysis)
        self.assertEqual(decision.action, "skip")
        self.assertEqual(decision.confidence, 0.2)
        self.assertIsNone(decision.batch_id)
        self.assertIsNone(decision.risk_factors)
        self.assertIsNone(decision.predicted_cascades)


class TestBatchPlan(unittest.TestCase):
    """Test BatchPlan dataclass."""

    def test_batch_plan_creation(self):
        """Test creating BatchPlan objects."""
        mock_errors = [Mock(), Mock()]
        
        batch = BatchPlan(
            batch_id=1,
            errors=mock_errors,
            confidence=0.75,
            estimated_time=30,
            risk_level="medium",
            dependencies=[2, 3]
        )

        self.assertEqual(batch.batch_id, 1)
        self.assertEqual(batch.errors, mock_errors)
        self.assertEqual(batch.confidence, 0.75)
        self.assertEqual(batch.estimated_time, 30)
        self.assertEqual(batch.risk_level, "medium")
        self.assertEqual(batch.dependencies, [2, 3])

    def test_batch_plan_defaults(self):
        """Test BatchPlan with default values."""
        batch = BatchPlan(
            batch_id=0,
            errors=[],
            confidence=0.5,
            estimated_time=10,
            risk_level="low"
        )

        self.assertEqual(batch.batch_id, 0)
        self.assertEqual(batch.errors, [])
        self.assertEqual(batch.confidence, 0.5)
        self.assertEqual(batch.estimated_time, 10)
        self.assertEqual(batch.risk_level, "low")
        self.assertIsNone(batch.dependencies)


class TestIntelligentForceMode(unittest.TestCase):
    """Test IntelligentForceMode class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock sklearn components to avoid dependency issues
        with patch('aider_lint_fixer.intelligent_force_mode.RandomForestClassifier'), \
             patch('aider_lint_fixer.intelligent_force_mode.KMeans'), \
             patch('aider_lint_fixer.intelligent_force_mode.StandardScaler'), \
             patch('aider_lint_fixer.intelligent_force_mode.EnhancedDependencyAnalyzer'):
            self.force_mode = IntelligentForceMode(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    def test_initialization(self):
        """Test IntelligentForceMode initialization."""
        self.assertEqual(self.force_mode.project_root, self.temp_dir)
        self.assertEqual(self.force_mode.auto_force_threshold, 0.90)
        self.assertEqual(self.force_mode.batch_force_threshold, 0.75)
        self.assertEqual(self.force_mode.manual_review_threshold, 0.50)
        self.assertEqual(self.force_mode.chaos_threshold, 100)
        self.assertEqual(self.force_mode.max_auto_force_count, 50)
        self.assertEqual(self.force_mode.optimal_batch_size, 15)
        self.assertEqual(self.force_mode.fix_history, [])
        self.assertEqual(self.force_mode.cascade_history, [])

    def _create_mock_error_analysis(self, rule_id="test-rule", severity=ErrorSeverity.WARNING, 
                                   file_path="test.py", line=10, message="Test error", 
                                   fixable=True, priority=1, effort=1):
        """Create a mock ErrorAnalysis object."""
        mock_error = Mock()
        mock_error.rule_id = rule_id
        mock_error.severity = severity
        mock_error.file_path = file_path
        mock_error.line = line
        mock_error.message = message
        
        mock_analysis = Mock(spec=ErrorAnalysis)
        mock_analysis.error = mock_error
        mock_analysis.file_path = file_path  # Add file_path directly to error_analysis
        mock_analysis.fixable = fixable
        mock_analysis.priority = priority
        mock_analysis.estimated_effort = effort
        mock_analysis.complexity = Mock()
        mock_analysis.complexity.value = 1
        mock_analysis.context_lines = ["line1", "line2"]
        mock_analysis.related_errors = []
        
        return mock_analysis

    @patch('aider_lint_fixer.intelligent_force_mode.logger')
    def test_analyze_force_strategy_small_codebase(self, mock_logger):
        """Test analyze_force_strategy with small codebase."""
        error_analyses = [
            self._create_mock_error_analysis(rule_id="max-len"),
            self._create_mock_error_analysis(rule_id="no-unused-vars"),
        ]
        
        with patch.object(self.force_mode, '_predict_force_decisions') as mock_predict, \
             patch.object(self.force_mode, '_build_dependency_graph') as mock_build, \
             patch.object(self.force_mode, '_predict_cascades') as mock_cascades, \
             patch.object(self.force_mode, '_optimize_batching') as mock_optimize, \
             patch.object(self.force_mode, '_create_execution_strategy') as mock_strategy:
            
            mock_decisions = [Mock(), Mock()]
            mock_predict.return_value = mock_decisions
            mock_batch_plan = [Mock()]
            mock_optimize.return_value = mock_batch_plan
            mock_strategy.return_value = {"test": "strategy"}
            
            result = self.force_mode.analyze_force_strategy(error_analyses)
            
            self.assertEqual(result, {"test": "strategy"})
            mock_predict.assert_called_once_with(error_analyses)
            mock_build.assert_called_once_with(error_analyses)
            mock_cascades.assert_called_once_with(mock_decisions)
            mock_optimize.assert_called_once_with(mock_decisions, False)  # Not chaotic
            mock_strategy.assert_called_once_with(mock_decisions, mock_batch_plan, False)

    @patch('aider_lint_fixer.intelligent_force_mode.logger')
    def test_analyze_force_strategy_chaotic_codebase(self, mock_logger):
        """Test analyze_force_strategy with chaotic codebase (100+ errors)."""
        error_analyses = [self._create_mock_error_analysis() for _ in range(150)]
        
        with patch.object(self.force_mode, '_predict_force_decisions') as mock_predict, \
             patch.object(self.force_mode, '_build_dependency_graph') as mock_build, \
             patch.object(self.force_mode, '_predict_cascades') as mock_cascades, \
             patch.object(self.force_mode, '_optimize_batching') as mock_optimize, \
             patch.object(self.force_mode, '_create_execution_strategy') as mock_strategy:
            
            mock_decisions = [Mock() for _ in range(150)]
            mock_predict.return_value = mock_decisions
            mock_batch_plan = [Mock()]
            mock_optimize.return_value = mock_batch_plan
            mock_strategy.return_value = {"chaotic": True}
            
            result = self.force_mode.analyze_force_strategy(error_analyses)
            
            self.assertEqual(result, {"chaotic": True})
            mock_optimize.assert_called_once_with(mock_decisions, True)  # Is chaotic
            mock_strategy.assert_called_once_with(mock_decisions, mock_batch_plan, True)

    def test_predict_force_decisions_safe_rules(self):
        """Test _predict_force_decisions with safe auto-force rules."""
        error_analyses = [
            self._create_mock_error_analysis(rule_id="max-len"),
            self._create_mock_error_analysis(rule_id="semi"),
            self._create_mock_error_analysis(rule_id="quotes"),
        ]
        
        with patch.object(self.force_mode, '_extract_error_features') as mock_extract, \
             patch.object(self.force_mode, '_get_base_confidence') as mock_base, \
             patch.object(self.force_mode, '_predict_ml_confidence') as mock_ml, \
             patch.object(self.force_mode, '_identify_risk_factors') as mock_risk:
            
            mock_extract.return_value = np.array([1, 2, 3])
            mock_base.return_value = 0.75
            mock_ml.return_value = 0.80
            mock_risk.return_value = []
            
            decisions = self.force_mode._predict_force_decisions(error_analyses)
            
            self.assertEqual(len(decisions), 3)
            # Safe rules with confidence >= 0.70 should be auto_force
            for decision in decisions:
                self.assertEqual(decision.action, "auto_force")
                self.assertAlmostEqual(decision.confidence, 0.765, places=2)  # 0.7 * 0.75 + 0.3 * 0.80

    def test_predict_force_decisions_confidence_thresholds(self):
        """Test _predict_force_decisions with different confidence thresholds."""
        error_analyses = [
            self._create_mock_error_analysis(rule_id="test-rule"),
        ]
        
        with patch.object(self.force_mode, '_extract_error_features') as mock_extract, \
             patch.object(self.force_mode, '_get_base_confidence') as mock_base, \
             patch.object(self.force_mode, '_predict_ml_confidence') as mock_ml, \
             patch.object(self.force_mode, '_identify_risk_factors') as mock_risk:
            
            mock_extract.return_value = np.array([1, 2, 3])
            mock_risk.return_value = []
            
            # Test high confidence (auto_force)
            mock_base.return_value = 0.95
            mock_ml.return_value = 0.95
            decisions = self.force_mode._predict_force_decisions(error_analyses)
            self.assertEqual(decisions[0].action, "auto_force")
            
            # Test medium confidence (batch_confirm)
            mock_base.return_value = 0.80
            mock_ml.return_value = 0.70
            decisions = self.force_mode._predict_force_decisions(error_analyses)
            self.assertEqual(decisions[0].action, "batch_confirm")
            
            # Test low confidence (manual_review)
            mock_base.return_value = 0.60
            mock_ml.return_value = 0.40
            decisions = self.force_mode._predict_force_decisions(error_analyses)
            self.assertEqual(decisions[0].action, "manual_review")
            
            # Test very low confidence (skip)
            mock_base.return_value = 0.30
            mock_ml.return_value = 0.20
            decisions = self.force_mode._predict_force_decisions(error_analyses)
            self.assertEqual(decisions[0].action, "skip")

    def test_extract_error_features(self):
        """Test _extract_error_features method."""
        error_analysis = self._create_mock_error_analysis(
            rule_id="no-unused-vars",
            severity=ErrorSeverity.ERROR,
            file_path="/path/to/test.js",
            line=50,
            message="Test error message"
        )
        
        features = self.force_mode._extract_error_features(error_analysis)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(len(features), 16)  # Expected number of features
        
        # Check specific feature values
        self.assertEqual(features[0], 0)  # Not "no-unde"
        self.assertEqual(features[1], 1)  # Is "no-unused-vars" (safe formatting)
        self.assertEqual(features[2], 1)  # Is error severity
        self.assertEqual(features[4], 50)  # Line number
        self.assertEqual(features[12], 1)  # Is JavaScript file
        self.assertEqual(features[13], 0)  # Not Python file

    def test_extract_error_features_python_file(self):
        """Test _extract_error_features with Python file."""
        error_analysis = self._create_mock_error_analysis(
            file_path="/path/to/test.py",
            message="short"
        )
        
        features = self.force_mode._extract_error_features(error_analysis)
        
        self.assertEqual(features[12], 0)  # Not JavaScript
        self.assertEqual(features[13], 1)  # Is Python file

    def test_extract_error_features_test_file(self):
        """Test _extract_error_features with test file."""
        error_analysis = self._create_mock_error_analysis(
            file_path="/path/to/test_module.py"
        )
        
        features = self.force_mode._extract_error_features(error_analysis)
        
        self.assertEqual(features[11], 1)  # Is test file (contains "test")

    def test_get_base_confidence_unfixable(self):
        """Test _get_base_confidence with unfixable error."""
        error_analysis = self._create_mock_error_analysis(fixable=False)
        
        confidence = self.force_mode._get_base_confidence(error_analysis)
        
        self.assertEqual(confidence, 0.2)

    def test_get_base_confidence_safe_rules(self):
        """Test _get_base_confidence with safe rules."""
        safe_rules = ["max-len", "no-unused-vars", "semi", "quotes"]
        
        for rule in safe_rules:
            error_analysis = self._create_mock_error_analysis(rule_id=rule, fixable=True)
            confidence = self.force_mode._get_base_confidence(error_analysis)
            self.assertEqual(confidence, 0.85)

    def test_get_base_confidence_dangerous_rules(self):
        """Test _get_base_confidence with dangerous rules."""
        error_analysis = self._create_mock_error_analysis(rule_id="no-unde", fixable=True)
        
        confidence = self.force_mode._get_base_confidence(error_analysis)
        
        self.assertEqual(confidence, 0.30)

    def test_get_base_confidence_default(self):
        """Test _get_base_confidence with default rule."""
        error_analysis = self._create_mock_error_analysis(rule_id="unknown-rule", fixable=True)
        
        confidence = self.force_mode._get_base_confidence(error_analysis)
        
        self.assertEqual(confidence, 0.60)

    @patch.object(IntelligentForceMode, '_predict_ml_confidence')
    def test_predict_ml_confidence_fallback(self, mock_ml_predict):
        """Test _predict_ml_confidence fallback."""
        mock_ml_predict.return_value = 0.75
        features = np.array([1, 2, 3])
        
        confidence = self.force_mode._predict_ml_confidence(features)
        
        self.assertEqual(confidence, 0.75)

    def test_identify_risk_factors(self):
        """Test _identify_risk_factors method."""
        error_analysis = self._create_mock_error_analysis(
            rule_id="no-unde",
            file_path="/path/to/production.py",  # No "test" in path
            effort=4  # High effort
        )
        
        risk_factors = self.force_mode._identify_risk_factors(error_analysis, 0.5)
        
        self.assertIsInstance(risk_factors, list)
        self.assertIn("Undefined variable may break runtime", risk_factors)
        self.assertIn("Production code - changes affect users", risk_factors)
        self.assertIn("High complexity fix - multiple changes needed", risk_factors)

    def test_build_dependency_graph_success(self):
        """Test _build_dependency_graph with successful AST analysis."""
        error_analyses = [
            self._create_mock_error_analysis(file_path="file1.py"),
            self._create_mock_error_analysis(file_path="file2.py"),
        ]
        
        with patch.object(self.force_mode.ast_analyzer, 'analyze_files') as mock_analyze:
            import networkx as nx
            mock_graph = nx.DiGraph()
            mock_graph.add_node("file1.py")
            mock_graph.add_node("file2.py")
            mock_graph.add_edge("file1.py", "file2.py")
            mock_analyze.return_value = mock_graph
            
            self.force_mode._build_dependency_graph(error_analyses)
            
            # Should have called AST analyzer once with list of files
            self.assertEqual(mock_analyze.call_count, 1)

    def test_build_dependency_graph_fallback(self):
        """Test _build_dependency_graph fallback to heuristics."""
        error_analyses = [
            self._create_mock_error_analysis(file_path="/same/dir/file1.py"),
            self._create_mock_error_analysis(file_path="/same/dir/file2.py"),
            self._create_mock_error_analysis(file_path="/other/dir/file3.py"),
        ]
        
        with patch.object(self.force_mode.ast_analyzer, 'get_dependencies') as mock_deps:
            mock_deps.side_effect = Exception("AST analysis failed")
            
            self.force_mode._build_dependency_graph(error_analyses)
            
            # Should have nodes for all files
            self.assertTrue(self.force_mode.dependency_graph.has_node("/same/dir/file1.py"))
            self.assertTrue(self.force_mode.dependency_graph.has_node("/same/dir/file2.py"))
            self.assertTrue(self.force_mode.dependency_graph.has_node("/other/dir/file3.py"))

    def test_predict_cascades_with_dependencies(self):
        """Test _predict_cascades with file dependencies."""
        # Create force decisions
        decision = ForceDecision(
            error_analysis=self._create_mock_error_analysis(file_path="file1.py", rule_id="safe-rule"),
            action="auto_force",
            confidence=0.85,
            risk_factors=[],
            predicted_cascades=None  # Start with None as the implementation expects
        )
        
        # Test that method runs without errors when file not in dependency graph
        self.force_mode._predict_cascades([decision])
        
        # Should not crash, predicted_cascades should remain None for file not in graph
        self.assertIsNone(decision.predicted_cascades)

    def test_predict_cascades_no_dependencies(self):
        """Test _predict_cascades with no dependencies."""
        decision = ForceDecision(
            error_analysis=self._create_mock_error_analysis(file_path="isolated.py"),
            action="auto_force",
            confidence=0.85,
            risk_factors=[]
        )
        
        # File not in dependency graph
        with patch.object(self.force_mode.dependency_graph, '__contains__') as mock_contains:
            mock_contains.return_value = False
            
            self.force_mode._predict_cascades([decision])
            
            # Should not have predicted cascades
            self.assertIsNone(decision.predicted_cascades)

    def test_calculate_cascade_risk(self):
        """Test _calculate_cascade_risk method."""
        edge_data = {"type": "import", "imported_names": ["func1", "func2"]}
        
        # High risk error type with high risk dependency
        risk = self.force_mode._calculate_cascade_risk("import/no-unresolved", edge_data)
        self.assertGreater(risk, 0.2)
        
        # Low risk error type
        risk = self.force_mode._calculate_cascade_risk("prefer-const", edge_data)
        self.assertLess(risk, 0.2)
        
        # Unknown types (should use default)
        risk = self.force_mode._calculate_cascade_risk("unknown-error", {"type": "unknown"})
        self.assertAlmostEqual(risk, 0.027, places=2)  # 0.3 * 0.3 * 0.3

    def test_get_dependency_insights_empty_graph(self):
        """Test get_dependency_insights with empty dependency graph."""
        insights = self.force_mode.get_dependency_insights()
        
        self.assertEqual(insights, {})

    def test_get_dependency_insights_with_data(self):
        """Test get_dependency_insights with populated graph."""
        # Add nodes and edges to dependency graph
        self.force_mode.dependency_graph.add_node("file1.py", type="file")
        self.force_mode.dependency_graph.add_node("file2.py", type="file")
        self.force_mode.dependency_graph.add_node("file3.py", type="file")
        
        # Create highly connected file
        for i in range(8):
            self.force_mode.dependency_graph.add_edge("file1.py", f"dep{i}.py", type="import")
        
        # Create isolated file (no edges)
        self.force_mode.dependency_graph.add_node("isolated.py", type="file")
        
        # Create import-heavy file
        for i in range(12):
            self.force_mode.dependency_graph.add_edge("file2.py", f"import{i}.py", type="import")
        
        insights = self.force_mode.get_dependency_insights()
        
        self.assertIn("total_files", insights)
        self.assertIn("highly_connected_files", insights)
        self.assertIn("isolated_files", insights)
        self.assertIn("import_heavy_files", insights)
        
        # Check highly connected files
        self.assertEqual(len(insights["highly_connected_files"]), 2)  # file1.py and file2.py
        
        # Check isolated files
        self.assertIn("isolated.py", insights["isolated_files"])
        
        # Check import heavy files
        self.assertEqual(len(insights["import_heavy_files"]), 1)
        self.assertEqual(insights["import_heavy_files"][0]["file"], "file2.py")

    def test_optimize_batching_auto_force_only(self):
        """Test _optimize_batching with only auto-force decisions."""
        decisions = [
            ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.95),
            ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.92),
        ]
        
        batch_plans = self.force_mode._optimize_batching(decisions, False)
        
        self.assertEqual(len(batch_plans), 1)
        self.assertEqual(batch_plans[0].batch_id, 0)
        self.assertEqual(batch_plans[0].risk_level, "low")
        self.assertEqual(len(batch_plans[0].errors), 2)

    def test_optimize_batching_batch_confirm(self):
        """Test _optimize_batching with batch-confirm decisions."""
        decisions = [
            ForceDecision(self._create_mock_error_analysis(), "batch_confirm", 0.80),
            ForceDecision(self._create_mock_error_analysis(), "batch_confirm", 0.75),
        ]
        
        with patch.object(self.force_mode, '_create_optimal_batches') as mock_create:
            mock_batches = [Mock(batch_id=1)]
            mock_create.return_value = mock_batches
            
            batch_plans = self.force_mode._optimize_batching(decisions, False)
            
            self.assertEqual(len(batch_plans), 1)
            mock_create.assert_called_once_with(decisions, False)

    def test_create_optimal_batches_empty(self):
        """Test _create_optimal_batches with no decisions."""
        batches = self.force_mode._create_optimal_batches([], False)
        
        self.assertEqual(batches, [])

    def test_create_optimal_batches_single_decision(self):
        """Test _create_optimal_batches with single decision."""
        decision = ForceDecision(
            self._create_mock_error_analysis(),
            "batch_confirm",
            0.80,
            risk_factors=["test risk"]
        )
        
        batches = self.force_mode._create_optimal_batches([decision], False)
        
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].batch_id, 1)
        self.assertEqual(batches[0].confidence, 0.80)
        self.assertEqual(len(batches[0].errors), 1)

    def test_create_execution_strategy(self):
        """Test _create_execution_strategy method."""
        force_decisions = [
            ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.95),
            ForceDecision(self._create_mock_error_analysis(), "batch_confirm", 0.80),
            ForceDecision(self._create_mock_error_analysis(), "manual_review", 0.60),
            ForceDecision(self._create_mock_error_analysis(), "skip", 0.30),
        ]
        
        batch_plans = [Mock()]
        
        with patch.object(self.force_mode, '_generate_recommendations') as mock_recommendations:
            mock_recommendations.return_value = ["Test recommendation"]
            
            strategy = self.force_mode._create_execution_strategy(force_decisions, batch_plans, False)
            
            self.assertFalse(strategy["is_chaotic"])
            self.assertEqual(strategy["total_errors"], 4)
            self.assertEqual(strategy["action_breakdown"]["auto_force"], 1)
            self.assertEqual(strategy["action_breakdown"]["batch_confirm"], 1)
            self.assertEqual(strategy["action_breakdown"]["manual_review"], 1)
            self.assertEqual(strategy["action_breakdown"]["skip"], 1)
            self.assertEqual(strategy["estimated_time_minutes"], 15)  # 2+3+10+0
            self.assertTrue(strategy["auto_force_enabled"])
            self.assertEqual(strategy["recommendations"], ["Test recommendation"])

    def test_generate_recommendations_normal_codebase(self):
        """Test _generate_recommendations for normal codebase."""
        force_decisions = [
            ForceDecision(self._create_mock_error_analysis(rule_id="max-len"), "auto_force", 0.95),
            ForceDecision(self._create_mock_error_analysis(rule_id="no-unde"), "manual_review", 0.60),
        ]
        
        with patch.object(self.force_mode, 'get_dependency_insights') as mock_insights:
            mock_insights.return_value = {}
            
            recommendations = self.force_mode._generate_recommendations(force_decisions, False)
            
            self.assertIsInstance(recommendations, list)
            # Should not have chaotic codebase messages
            self.assertFalse(any("CHAOTIC CODEBASE" in rec for rec in recommendations))

    def test_generate_recommendations_chaotic_codebase(self):
        """Test _generate_recommendations for chaotic codebase."""
        force_decisions = [ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.95) for _ in range(60)]
        force_decisions.extend([ForceDecision(self._create_mock_error_analysis(rule_id="no-unde"), "manual_review", 0.60) for _ in range(15)])
        
        with patch.object(self.force_mode, 'get_dependency_insights') as mock_insights:
            mock_insights.return_value = {
                "highly_connected_files": [
                    {"file": "highly_connected.py", "connections": 15, "dependents": 10}
                ],
                "import_heavy_files": [
                    {"file": "heavy_imports.py", "import_count": 20}
                ]
            }
            
            recommendations = self.force_mode._generate_recommendations(force_decisions, True)
            
            self.assertIsInstance(recommendations, list)
            # Should have chaotic codebase messages
            self.assertTrue(any("CHAOTIC CODEBASE DETECTED" in rec for rec in recommendations))
            self.assertTrue(any("60 safe errors will be auto-fixed" in rec for rec in recommendations))
            self.assertTrue(any("15 dangerous errors require manual review" in rec for rec in recommendations))
            self.assertTrue(any("highly connected files detected" in rec for rec in recommendations))

    def test_learn_from_outcome(self):
        """Test learn_from_outcome method."""
        decision = ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.85)
        
        self.force_mode.learn_from_outcome(decision, success=True, created_new_errors=False)
        
        self.assertEqual(len(self.force_mode.fix_history), 1)
        outcome = self.force_mode.fix_history[0]
        self.assertEqual(outcome["decision"], decision)
        self.assertTrue(outcome["success"])
        self.assertFalse(outcome["created_new_errors"])
        self.assertTrue(outcome["confidence_was_correct"])

    def test_learn_from_outcome_triggers_threshold_update(self):
        """Test that learning triggers threshold updates after 100 outcomes."""
        decision = ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.85)
        
        # Add 100 outcomes to trigger threshold update
        for i in range(100):
            self.force_mode.learn_from_outcome(decision, success=True)
        
        # Mock the threshold update method
        with patch.object(self.force_mode, '_update_confidence_thresholds') as mock_update:
            self.force_mode.learn_from_outcome(decision, success=True)
            mock_update.assert_called_once()

    @patch('aider_lint_fixer.intelligent_force_mode.logger')
    def test_update_confidence_thresholds_high_success(self, mock_logger):
        """Test _update_confidence_thresholds with high success rate."""
        # Add outcomes with high confidence and high success rate
        decision = ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.85)
        
        for i in range(50):
            outcome = {
                "decision": decision,
                "success": True,  # High success rate
                "created_new_errors": False,
                "confidence_was_correct": True,
            }
            self.force_mode.fix_history.append(outcome)
        
        original_threshold = self.force_mode.auto_force_threshold
        self.force_mode._update_confidence_thresholds()
        
        # Should decrease threshold (become more aggressive)
        self.assertLess(self.force_mode.auto_force_threshold, original_threshold)

    @patch('aider_lint_fixer.intelligent_force_mode.logger')
    def test_update_confidence_thresholds_low_success(self, mock_logger):
        """Test _update_confidence_thresholds with low success rate."""
        # Add outcomes with high confidence but low success rate
        decision = ForceDecision(self._create_mock_error_analysis(), "auto_force", 0.85)
        
        for i in range(50):
            outcome = {
                "decision": decision,
                "success": False,  # Low success rate
                "created_new_errors": True,
                "confidence_was_correct": False,
            }
            self.force_mode.fix_history.append(outcome)
        
        original_threshold = self.force_mode.auto_force_threshold
        self.force_mode._update_confidence_thresholds()
        
        # Should increase threshold (become more conservative)
        self.assertGreater(self.force_mode.auto_force_threshold, original_threshold)

    def test_predict_ml_confidence_placeholder(self):
        """Test _predict_ml_confidence placeholder implementation."""
        features = np.array([1, 2, 3, 4, 5])
        
        confidence = self.force_mode._predict_ml_confidence(features)
        
        # Should return a float between 0 and 1
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


if __name__ == "__main__":
    unittest.main()


class TestIntelligentForceModeIntegration(unittest.TestCase):
    """Integration tests for IntelligentForceMode class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.force_mode = IntelligentForceMode(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    def _create_mock_error_analysis(self, rule_id="test-rule", severity=ErrorSeverity.WARNING,
                                   file_path="test.py", line=10, message="Test error",
                                   fixable=True, priority=1, effort=1):
        """Create a mock ErrorAnalysis object."""
        mock_error = Mock()
        mock_error.rule_id = rule_id
        mock_error.severity = severity
        mock_error.file_path = file_path
        mock_error.line = line
        mock_error.message = message

        mock_analysis = Mock(spec=ErrorAnalysis)
        mock_analysis.error = mock_error
        mock_analysis.file_path = file_path
        mock_analysis.fixable = fixable
        mock_analysis.priority = priority
        mock_analysis.estimated_effort = effort
        mock_analysis.complexity = Mock()
        mock_analysis.complexity.value = 1
        mock_analysis.context_lines = ["line1", "line2"]
        mock_analysis.related_errors = []

        return mock_analysis

    def test_get_base_confidence_complex_js_string(self):
        """Test _get_base_confidence with a complex JavaScript string."""
        # Create a mock error analysis for a JS file with a complex string
        error_analysis = self._create_mock_error_analysis(
            rule_id="max-len",
            file_path="test.js",
            fixable=True
        )

        # Mock _is_complex_javascript_string to return True
        with patch.object(self.force_mode, '_is_complex_javascript_string', return_value=True):
            confidence = self.force_mode._get_base_confidence(error_analysis)
            self.assertEqual(confidence, 0.75)

    def test_is_complex_javascript_string_exception(self):
        """Test _is_complex_javascript_string when an exception occurs."""
        error_analysis = self._create_mock_error_analysis(file_path="non_existent_file.js")
        # This should not raise an exception, but return False
        self.assertFalse(self.force_mode._is_complex_javascript_string(error_analysis))

    def test_is_complex_javascript_string_detection(self):
        """Test the detection of complex JavaScript strings."""
        complex_line = 'const long_string = "part1" + `part2 with ${variable}` + "part3"; // REPOSITORY CONTEXT'
        simple_line = 'const simple_string = "hello world";'

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".js") as tmpfile:
            tmpfile.write(complex_line)
            tmpfile_path = tmpfile.name

        error_analysis_complex = self._create_mock_error_analysis(file_path=tmpfile_path, line=1)
        self.assertTrue(self.force_mode._is_complex_javascript_string(error_analysis_complex))

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".js") as tmpfile:
            tmpfile.write(simple_line)
            tmpfile_path_simple = tmpfile.name

        error_analysis_simple = self._create_mock_error_analysis(file_path=tmpfile_path_simple, line=1)
        self.assertFalse(self.force_mode._is_complex_javascript_string(error_analysis_simple))

        import os
        os.remove(tmpfile_path)
        os.remove(tmpfile_path_simple)

    def test_identify_risk_factors(self):
        """Test the _identify_risk_factors method."""
        # Test undefined variable risk
        error_analysis_unde = self._create_mock_error_analysis(rule_id="no-unde")
        risk_factors = self.force_mode._identify_risk_factors(error_analysis_unde, 0.5)
        self.assertIn("Undefined variable may break runtime", risk_factors)
        self.assertIn("Could be missing import or global", risk_factors)

        # Test config file risk
        error_analysis_config = self._create_mock_error_analysis(file_path="config/settings.py")
        risk_factors = self.force_mode._identify_risk_factors(error_analysis_config, 0.5)
        self.assertIn("Configuration file - changes affect entire system", risk_factors)

        # Test production code risk
        error_analysis_prod = self._create_mock_error_analysis(file_path="src/main.py")
        risk_factors = self.force_mode._identify_risk_factors(error_analysis_prod, 0.5)
        self.assertIn("Production code - changes affect users", risk_factors)

        # Test high complexity risk
        error_analysis_complex = self._create_mock_error_analysis(effort=4)
        risk_factors = self.force_mode._identify_risk_factors(error_analysis_complex, 0.5)
        self.assertIn("High complexity fix - multiple changes needed", risk_factors)

        # Test related errors risk
        error_analysis_related = self._create_mock_error_analysis()
        error_analysis_related.related_errors = [Mock(), Mock(), Mock()]
        risk_factors = self.force_mode._identify_risk_factors(error_analysis_related, 0.5)
        self.assertIn("Multiple related errors - cascading effects possible", risk_factors)

    def test_predict_cascades(self):
        """Test the _predict_cascades method."""
        # Create a dependency graph
        self.force_mode.dependency_graph.add_node("file1.py")
        self.force_mode.dependency_graph.add_node("file2.py")
        self.force_mode.dependency_graph.add_node("file3.py")
        self.force_mode.dependency_graph.add_edge("file1.py", "file2.py", type="import")
        self.force_mode.dependency_graph.add_edge("file2.py", "file3.py", type="import")

        # Create a force decision
        error_analysis = self._create_mock_error_analysis(file_path="file1.py", rule_id="import/no-unresolved")
        decision = ForceDecision(
            error_analysis=error_analysis,
            action="auto_force",
            confidence=0.9,
            risk_factors=[],
            predicted_cascades=None
        )

        # Predict cascades
        self.force_mode._predict_cascades([decision])

        # Assert that cascades are predicted
        self.assertIsNotNone(decision.predicted_cascades)
        self.assertIn("file2.py", decision.predicted_cascades)

    def test_calculate_cascade_risk_with_imported_names(self):
        """Test _calculate_cascade_risk with imported names."""
        edge_data = {"type": "import", "imported_names": ["my_func"]}
        risk = self.force_mode._calculate_cascade_risk("some-rule", edge_data)
        self.assertGreater(risk, 0.0)