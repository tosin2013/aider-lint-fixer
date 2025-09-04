"""
Enhanced Error Classification Tests - Strategic Priority
=======================================================

This test suite validates intelligent error classification and categorization
based on the MCP framework analysis findings.

Key Classification Areas:
1. Error severity and impact assessment
2. Environment-specific error categorization  
3. Production vs development risk classification
4. Auto-fixable vs manual-fix error separation
5. Security-sensitive error identification
6. Performance vs style issue categorization

Coverage Target: Enhances error_analyzer.py (currently 69.8% coverage)
"""

import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from aider_lint_fixer.error_analyzer import ErrorAnalyzer
from aider_lint_fixer.pattern_matcher import SmartErrorClassifier


@dataclass
class MockLintError:
    """Mock lint error for testing."""
    file_path: str
    line: int
    column: int
    rule_id: str
    message: str
    severity: str
    linter: str
    source_line: str = ""


class TestErrorSeverityClassification:
    """Test error severity and impact classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_critical_error_classification(self):
        """Test identification of critical errors that break functionality."""
        # Create mock LintError objects that match the actual class structure
        from aider_lint_fixer.lint_runner import LintError, ErrorSeverity
        
        critical_errors = [
            LintError(
                file_path="/test/file.ts",
                line=1, column=1,
                rule_id="no-undef",
                message="'process' is not defined",
                severity=ErrorSeverity.ERROR,
                linter="eslint"
            ),
            LintError(
                file_path="/test/file.py", 
                line=5, column=10,
                rule_id="F821",
                message="undefined name 'variable'",
                severity=ErrorSeverity.ERROR,
                linter="flake8"
            ),
            LintError(
                file_path="/test/file.ts",
                line=10, column=5,
                rule_id="no-unused-vars",
                message="'error' is defined but never used",
                severity=ErrorSeverity.ERROR,
                linter="eslint"
            )
        ]
        
        # Test error categorization using existing methods
        for error in critical_errors:
            category = self.error_analyzer._categorize_error(error)
            complexity = self.error_analyzer._determine_complexity(error, category)
            
            # Verify that errors are properly categorized
            assert category is not None
            assert complexity is not None

    def test_warning_vs_error_classification(self):
        """Test distinction between warnings and errors."""
        warning_errors = [
            MockLintError(
                file_path="/test/file.ts",
                line=1, column=1,
                rule_id="@typescript-eslint/no-explicit-any",
                message="Unexpected any. Specify a different type",
                severity="warning",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/file.py",
                line=5, column=1,
                rule_id="E501",
                message="line too long (85 > 79 characters)", 
                severity="warning",
                linter="flake8"
            )
        ]
        
        for error in warning_errors:
            classification = self.error_analyzer.classify_error_severity(error)
            assert classification['severity_level'] in ['low', 'medium']
            assert classification['impact'] in ['style', 'maintainability']

    def test_security_error_classification(self):
        """Test identification of security-sensitive errors."""
        security_errors = [
            MockLintError(
                file_path="/test/auth.py",
                line=10, column=5,
                rule_id="S101",
                message="Use of assert detected",
                severity="error",
                linter="bandit"
            ),
            MockLintError(
                file_path="/test/api.ts", 
                line=15, column=10,
                rule_id="security/detect-object-injection",
                message="Object injection vulnerability detected",
                severity="error",
                linter="eslint-plugin-security"
            )
        ]
        
        for error in security_errors:
            classification = self.error_analyzer.classify_error_severity(error)
            assert classification['category'] == 'security'
            assert classification['severity_level'] == 'critical'
            assert classification['requires_manual_review'] is True


class TestEnvironmentSpecificClassification:
    """Test environment-specific error classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_nodejs_environment_errors(self):
        """Test classification of Node.js specific errors."""
        nodejs_errors = [
            MockLintError(
                file_path="/test/server.ts",
                line=1, column=1,
                rule_id="no-undef",
                message="'process' is not defined",
                severity="error",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/buffer.ts",
                line=5, column=10, 
                rule_id="no-undef",
                message="'Buffer' is not defined",
                severity="error",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/timer.ts",
                line=10, column=5,
                rule_id="no-undef", 
                message="'setTimeout' is not defined",
                severity="error",
                linter="eslint"
            )
        ]
        
        for error in nodejs_errors:
            classification = self.error_analyzer.classify_environment_error(error)
            
            assert classification['environment'] == 'nodejs'
            assert classification['fix_strategy'] == 'environment_config'
            assert classification['auto_fixable'] is True
            assert 'add_nodejs_globals' in classification['recommended_fixes']

    def test_browser_environment_errors(self):
        """Test classification of browser-specific errors."""
        browser_errors = [
            MockLintError(
                file_path="/test/client.ts",
                line=1, column=1,
                rule_id="no-undef",
                message="'window' is not defined", 
                severity="error",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/dom.ts",
                line=5, column=10,
                rule_id="no-undef",
                message="'document' is not defined",
                severity="error",
                linter="eslint"
            )
        ]
        
        for error in browser_errors:
            classification = self.error_analyzer.classify_environment_error(error)
            
            assert classification['environment'] == 'browser'
            assert classification['fix_strategy'] == 'environment_config'
            assert 'add_browser_globals' in classification['recommended_fixes']

    def test_mixed_environment_detection(self):
        """Test detection and classification of mixed environment errors."""
        mixed_errors = [
            MockLintError(
                file_path="/test/universal.ts",
                line=1, column=1,
                rule_id="no-undef",
                message="'fetch' is not defined",  # Could be Node.js or browser
                severity="error",
                linter="eslint"
            )
        ]
        
        error = mixed_errors[0]
        classification = self.error_analyzer.classify_environment_error(error)
        
        # Should detect ambiguous environment
        assert classification['environment'] in ['mixed', 'ambiguous']
        assert classification['requires_manual_review'] is True


class TestAutoFixableClassification:
    """Test classification of auto-fixable vs manual-fix errors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_auto_fixable_formatting_errors(self):
        """Test identification of auto-fixable formatting errors."""
        formatting_errors = [
            MockLintError(
                file_path="/test/file.ts",
                line=1, column=40,
                rule_id="curly",
                message="Expected { after 'if' condition",
                severity="error",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/file.py",
                line=5, column=1,
                rule_id="E302", 
                message="expected 2 blank lines, found 1",
                severity="error",
                linter="flake8"
            ),
            MockLintError(
                file_path="/test/imports.py",
                line=10, column=1,
                rule_id="I001",
                message="import statements are in the wrong order",
                severity="error",
                linter="isort"
            )
        ]
        
        for error in formatting_errors:
            classification = self.error_analyzer.classify_fix_complexity(error)
            
            assert classification['auto_fixable'] is True
            assert classification['fix_confidence'] >= 0.8
            assert classification['risk_level'] == 'low'

    def test_manual_fix_required_errors(self):
        """Test identification of errors requiring manual fixes."""
        manual_errors = [
            MockLintError(
                file_path="/test/logic.ts", 
                line=1, column=1,
                rule_id="no-undef",
                message="'unknownVariable' is not defined",
                severity="error",
                linter="eslint"
            ),
            MockLintError(
                file_path="/test/types.py",
                line=5, column=10,
                rule_id="E1101",
                message="Instance of 'str' has no 'unknown_method' member",
                severity="error", 
                linter="pylint"
            )
        ]
        
        for error in manual_errors:
            classification = self.error_analyzer.classify_fix_complexity(error)
            
            assert classification['auto_fixable'] is False
            assert classification['requires_context'] is True
            assert classification['risk_level'] in ['medium', 'high']

    def test_conditional_auto_fix_classification(self):
        """Test classification of conditionally auto-fixable errors."""
        conditional_errors = [
            MockLintError(
                file_path="/test/imports.py",
                line=1, column=1,
                rule_id="F401",
                message="'os' imported but unused",
                severity="error",
                linter="flake8"
            )
        ]
        
        error = conditional_errors[0]
        classification = self.error_analyzer.classify_fix_complexity(error)
        
        # Should be conditionally auto-fixable (need to check for dynamic usage)
        assert classification['auto_fixable'] is True
        assert classification['fix_confidence'] < 0.8  # Lower confidence
        assert classification['requires_verification'] is True


class TestProductionRiskClassification:
    """Test production vs development risk classification."""

    def setup_method(self):
        """Set up test fixtures.""" 
        self.error_analyzer = ErrorAnalyzer()

    def test_production_critical_errors(self):
        """Test identification of production-critical errors."""
        production_errors = [
            MockLintError(
                file_path="/src/api/auth.py",
                line=1, column=1,
                rule_id="S106",
                message="Possible hardcoded password detected",
                severity="error",
                linter="bandit"
            ),
            MockLintError(
                file_path="/src/database/connection.ts",
                line=10, column=5,
                rule_id="no-console",
                message="Unexpected console statement",
                severity="warning",
                linter="eslint",
                source_line="console.log('Database password:', password)"
            )
        ]
        
        for error in production_errors:
            classification = self.error_analyzer.classify_production_risk(error)
            
            assert classification['production_risk'] == 'high'
            assert classification['deployment_blocker'] is True

    def test_development_only_errors(self):
        """Test identification of development-only errors."""
        dev_errors = [
            MockLintError(
                file_path="/tests/test_api.py",
                line=1, column=1,
                rule_id="E501", 
                message="line too long (85 > 79 characters)",
                severity="warning",
                linter="flake8"
            ),
            MockLintError(
                file_path="/dev/debug.ts",
                line=5, column=10,
                rule_id="no-console",
                message="Unexpected console statement",
                severity="warning",
                linter="eslint"
            )
        ]
        
        for error in dev_errors:
            classification = self.error_analyzer.classify_production_risk(error)
            
            assert classification['production_risk'] == 'low'
            assert classification['deployment_blocker'] is False


class TestErrorGroupingAndPrioritization:
    """Test error grouping and prioritization logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_analyzer = ErrorAnalyzer()

    def test_error_grouping_by_rule(self):
        """Test grouping of similar errors by rule ID."""
        similar_errors = [
            MockLintError("/test/file1.ts", 1, 1, "no-undef", "'process' not defined", "error", "eslint"),
            MockLintError("/test/file2.ts", 5, 10, "no-undef", "'Buffer' not defined", "error", "eslint"),
            MockLintError("/test/file3.ts", 10, 5, "no-undef", "'NodeJS' not defined", "error", "eslint"),
        ]
        
        groups = self.error_analyzer.group_errors_by_pattern(similar_errors)
        
        assert 'no-undef' in groups
        assert len(groups['no-undef']) == 3
        
        # Should identify this as an environment configuration issue
        group_analysis = self.error_analyzer.analyze_error_group(groups['no-undef'])
        assert group_analysis['pattern'] == 'environment_globals'
        assert group_analysis['batch_fixable'] is True

    def test_error_prioritization(self):
        """Test prioritization of errors by severity and impact."""
        mixed_errors = [
            MockLintError("/test/file.py", 1, 1, "E501", "line too long", "warning", "flake8"),
            MockLintError("/test/file.ts", 5, 10, "no-undef", "'process' not defined", "error", "eslint"),
            MockLintError("/test/auth.py", 10, 5, "S106", "hardcoded password", "error", "bandit"),
        ]
        
        prioritized = self.error_analyzer.prioritize_errors(mixed_errors)
        
        # Security error should be highest priority
        assert prioritized[0].rule_id == 'S106'
        # Runtime error should be second
        assert prioritized[1].rule_id == 'no-undef'
        # Style error should be last
        assert prioritized[2].rule_id == 'E501'


class TestMLEnhancedClassification:
    """Test machine learning enhanced error classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pattern_matcher = SmartErrorClassifier()

    def test_pattern_learning_from_fixes(self):
        """Test learning patterns from successful fixes."""
        fix_history = [
            {
                'error': MockLintError("/test/file1.ts", 1, 1, "no-undef", "'process' not defined", "error", "eslint"),
                'fix_applied': 'add_nodejs_environment',
                'success': True,
                'context': {'file_type': 'typescript', 'project_type': 'nodejs'}
            },
            {
                'error': MockLintError("/test/file2.ts", 5, 10, "no-undef", "'Buffer' not defined", "error", "eslint"),
                'fix_applied': 'add_nodejs_environment', 
                'success': True,
                'context': {'file_type': 'typescript', 'project_type': 'nodejs'}
            }
        ]
        
        # Should learn that no-undef in TypeScript + nodejs context = environment config
        self.pattern_matcher.learn_from_fix_history(fix_history)
        
        new_error = MockLintError("/test/file3.ts", 15, 5, "no-undef", "'setTimeout' not defined", "error", "eslint")
        prediction = self.pattern_matcher.predict_fix_strategy(new_error, {'file_type': 'typescript', 'project_type': 'nodejs'})
        
        assert prediction['strategy'] == 'add_nodejs_environment'
        assert prediction['confidence'] > 0.8

    def test_classification_confidence_scoring(self):
        """Test confidence scoring for error classifications."""
        test_error = MockLintError(
            "/test/file.ts", 1, 1, "no-undef", 
            "'someUnknownGlobal' is not defined", "error", "eslint"
        )
        
        classification = self.error_analyzer.classify_error_with_confidence(test_error)
        
        # Should have lower confidence for unknown globals
        assert 'confidence_score' in classification
        assert 0.0 <= classification['confidence_score'] <= 1.0
        
        # Should indicate need for manual review due to uncertainty
        if classification['confidence_score'] < 0.7:
            assert classification['requires_manual_review'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
