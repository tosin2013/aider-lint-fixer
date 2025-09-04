"""
Test Environment Context Awareness for Different Project Types
=============================================================

This test suite validates that aider-lint-fixer correctly detects and configures
linting environments based on project characteristics.

Priority tests identified from MCP framework analysis:
1. Node.js environment detection and global configuration
2. TypeScript project support with proper type checking
3. JSON parsing robustness for different ESLint output formats
4. Production vs development environment risk assessment
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.pre_lint_assessment import PreLintAssessor
from aider_lint_fixer.project_detector import ProjectDetector


class TestEnvironmentContextAwareness:
    """Test environment-specific linting configuration."""

    def test_nodejs_environment_detection(self):
        """Test that Node.js projects are properly detected and configured."""
        # Create mock Node.js project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create package.json
            package_json = {
                "name": "test-nodejs-project",
                "version": "1.0.0",
                "scripts": {"lint": "eslint src/**/*.ts"},
                "devDependencies": {"eslint": "^8.0.0", "@types/node": "^18.0.0"}
            }
            (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
            
            # Create TypeScript source
            (project_path / "src").mkdir()
            (project_path / "src" / "index.ts").write_text("""
process.env.NODE_ENV = 'production';
const url = new URL('https://example.com');
console.log('Server starting...');
            """)
            
            detector = ProjectDetector()
            project_info = detector.detect_project(str(project_path))
            
            # Assertions
            assert 'javascript' in project_info.languages
            assert 'typescript' in project_info.languages  
            assert 'npm' in project_info.package_managers
            assert 'eslint' in project_info.lint_configs
            
    def test_python_environment_detection(self):
        """Test that Python projects are properly detected and configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create Python project structure
            (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-python-project"
dependencies = ["requests>=2.25.0"]

[tool.flake8]
max-line-length = 88
            """)
            
            (project_path / "src").mkdir()
            (project_path / "src" / "main.py").write_text("""
import os
import sys
from typing import Dict, Any

def main() -> None:
    print("Hello World")
            """)
            
            detector = ProjectDetector()
            project_info = detector.detect_project(str(project_path))
            
            # Assertions
            assert 'python' in project_info.languages
            assert 'pip' in project_info.package_managers
            assert 'flake8' in project_info.lint_configs


class TestJSONParsingRobustness:
    """Test robust JSON parsing for different linter outputs."""
    
    def test_eslint_json_parsing_with_warnings(self):
        """Test parsing ESLint output that includes warnings before JSON."""
        # Simulate the exact issue found in MCP framework testing
        mock_output = """
> mcp-url-knowledge-graph@0.1.0 lint
> eslint src/**/*.ts

[{"filePath":"/test/file.ts","messages":[{"ruleId":"no-undef","severity":2,"message":"'process' is not defined","line":1,"column":1}]}]
        """
        
        from unittest.mock import Mock
        mock_project_info = Mock()
        mock_project_info.languages = ['javascript', 'typescript']
        lint_runner = LintRunner(project_info=mock_project_info)
        
        with patch.object(lint_runner, '_run_command') as mock_run:
            mock_run.return_value = (mock_output, "", 1)
            
            # Should handle the npm output prefix gracefully
            result = lint_runner._parse_eslint_json(mock_output)
            
            # Assertions
            assert result is not None
            assert len(result) == 1
            assert result[0]['filePath'] == '/test/file.ts'
            assert result[0]['messages'][0]['ruleId'] == 'no-undef'
    
    def test_eslint_json_parsing_malformed(self):
        """Test handling of completely malformed ESLint output."""
        malformed_output = "Error: ENOENT: no such file or directory"
        
        from unittest.mock import Mock
        mock_project_info = Mock()
        mock_project_info.languages = ['javascript', 'typescript']
        lint_runner = LintRunner(project_info=mock_project_info)
        
        # Should not crash, should return empty list or handle gracefully
        result = lint_runner._parse_eslint_json(malformed_output)
        assert result == [] or result is None


class TestProductionRiskAssessment:
    """Test production environment risk assessment."""
    
    def test_production_file_detection(self):
        """Test detection of production deployment files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create production-indicating files
            (project_path / "Dockerfile").write_text("FROM node:18")
            (project_path / "docker-compose.yml").write_text("version: '3.8'")
            (project_path / "deployment").mkdir()
            (project_path / "deployment" / "production.yml").write_text("apiVersion: apps/v1")
            
            assessment = PreLintAssessor()
            risk_level = assessment._assess_production_risk(str(project_path))
            
            # Should detect production environment
            assert risk_level >= 2  # Medium or High risk
    
    def test_development_environment_detection(self):
        """Test detection of development-only environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create only development files
            (project_path / "package.json").write_text('{"name": "dev-project"}')
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            
            assessment = PreLintAssessor()
            risk_level = assessment._assess_production_risk(str(project_path))
            
            # Should be low risk
            assert risk_level <= 1  # Low risk


class TestEnvironmentSpecificLinting:
    """Test environment-specific linting configurations."""
    
    @pytest.mark.parametrize("project_type,expected_linters", [
        ("nodejs_typescript", ["eslint", "prettier"]),
        ("python_flask", ["flake8", "black", "isort", "mypy"]),
        ("ansible", ["ansible-lint", "yamllint"]),
        ("mixed_polyglot", ["eslint", "flake8", "ansible-lint"])
    ])
    def test_environment_specific_linter_selection(self, project_type, expected_linters):
        """Test that appropriate linters are selected based on project environment."""
        # This would test the smart linter selection logic
        # Implementation depends on current smart_linter_selector.py
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
