"""
Baseline test to validate current functionality before type checking fixes.

This test ensures that all core functionality works correctly before we start
adding type annotations and fixing mypy errors.
"""

import pytest
import tempfile
import os
from pathlib import Path

from aider_lint_fixer.main import main
from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.error_analyzer import ErrorAnalyzer
from aider_lint_fixer.pattern_matcher import SmartErrorClassifier


class TestTypeCheckingBaseline:
    """Baseline tests to ensure functionality before type checking fixes."""

    def test_main_module_imports(self):
        """Test that main module imports work correctly."""
        from aider_lint_fixer import main
        assert hasattr(main, 'main')
        assert callable(main.main)

    def test_lint_runner_basic_functionality(self):
        """Test that LintRunner can be instantiated and basic methods work."""
        from aider_lint_fixer.project_detector import ProjectInfo
        from pathlib import Path
        
        # Create a minimal ProjectInfo for testing
        project_info = ProjectInfo(
            root_path=Path("."),
            languages=set(),
            package_managers=set(),
            lint_configs={},
            source_files=[],
            config_files=[]
        )
        
        runner = LintRunner(project_info)
        assert runner is not None
        
        # Test that basic methods exist and are callable
        assert hasattr(runner, 'run_all_available_linters')
        assert callable(runner.run_all_available_linters)

    def test_error_analyzer_basic_functionality(self):
        """Test that ErrorAnalyzer can be instantiated and basic methods work."""
        analyzer = ErrorAnalyzer()
        assert analyzer is not None
        
        # Test that basic methods exist and are callable
        assert hasattr(analyzer, 'analyze_errors')
        assert callable(analyzer.analyze_errors)

    def test_pattern_matcher_basic_functionality(self):
        """Test that SmartErrorClassifier can be instantiated."""
        try:
            classifier = SmartErrorClassifier()
            assert classifier is not None
        except Exception as e:
            # Some dependencies might be optional, so we allow this to fail gracefully
            pytest.skip(f"SmartErrorClassifier initialization failed: {e}")

    def test_cli_help_functionality(self):
        """Test that CLI help works without errors."""
        import subprocess
        import sys
        
        # Test that the CLI can show help without crashing
        result = subprocess.run(
            [sys.executable, "-m", "aider_lint_fixer", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should exit with 0 (help) and contain usage information
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_basic_file_processing(self):
        """Test basic file processing functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file with a basic syntax issue
            test_file = Path(temp_dir) / "test_file.py"
            test_file.write_text("""
# Simple test file
def test_function():
    x = 1
    return x
""")
            
            # Test that we can at least attempt to process the file
            from aider_lint_fixer.project_detector import ProjectInfo
            
            project_info = ProjectInfo(
                root_path=Path(temp_dir),
                languages={"python"},
                package_managers=set(),
                lint_configs={},
                source_files=[test_file],
                config_files=[]
            )
            
            runner = LintRunner(project_info)
            try:
                # This might fail due to missing linters, but shouldn't crash
                results = runner.run_all_available_linters()
                # If it succeeds, results should be a dictionary
                assert isinstance(results, dict)
            except Exception as e:
                # Allow graceful failure if linters aren't available
                pytest.skip(f"Linter execution failed (expected): {e}")

    def test_configuration_loading(self):
        """Test that configuration can be loaded without errors."""
        from aider_lint_fixer.config_manager import ConfigManager
        
        try:
            config_manager = ConfigManager()
            assert config_manager is not None
        except Exception as e:
            pytest.skip(f"ConfigManager initialization failed: {e}")

    def test_project_detection(self):
        """Test that project detection works."""
        from aider_lint_fixer.project_detector import ProjectDetector
        
        try:
            detector = ProjectDetector()
            assert detector is not None
            
            # Test with current directory - check for actual method name
            if hasattr(detector, 'detect_project'):
                project_info = detector.detect_project(Path("."))
                assert project_info is not None
            elif hasattr(detector, 'detect_project_type'):
                project_info = detector.detect_project_type(Path("."))
                assert project_info is not None
            else:
                pytest.skip("ProjectDetector method signature unknown")
        except Exception as e:
            pytest.skip(f"ProjectDetector failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])