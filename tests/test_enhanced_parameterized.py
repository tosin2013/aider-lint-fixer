#!/usr/bin/env python3
"""
Enhanced parameterized tests for aider-lint-fixer.

This module demonstrates advanced testing strategies including parameterized
tests and property-based testing to improve coverage efficiency and test quality.
"""

import pytest
from pathlib import Path
from typing import Any, Dict, List, Tuple
import tempfile
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils import (
    TestDataBuilder, MockGenerator, AssertionHelpers, PerformanceHelper
)
from tests.fixtures.sample_lint_data import (
    get_sample_errors_by_linter, get_sample_code_by_language, get_config_template
)

# Try to import hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, assume
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create dummy decorators for when hypothesis is not available
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip("hypothesis not available")(func)
        return decorator
    
    class st:
        text = lambda: None
        integers = lambda min_value=0, max_value=100: None
        lists = lambda elements, min_size=0, max_size=10: None


class TestParameterizedLintErrors:
    """Parameterized tests for lint error handling across different linters."""
    
    @pytest.mark.parametrize("linter_name", [
        "flake8", "pylint", "eslint", "ansible-lint"
    ])
    def test_lint_error_structure_validation(self, linter_name):
        """Test that all sample errors have valid structure."""
        errors = get_sample_errors_by_linter(linter_name)
        assert len(errors) > 0, f"No sample errors found for {linter_name}"
        
        for error in errors:
            AssertionHelpers.assert_lint_error_structure(error)
            assert error["linter"] == linter_name
    
    @pytest.mark.parametrize("linter_name,expected_rules", [
        ("flake8", ["E501", "E302", "F841"]),
        ("pylint", ["C0103", "W0613"]),
        ("eslint", ["semi", "no-unused-vars", "no-console"]),
        ("ansible-lint", ["yaml[line-length]", "name[missing]", "risky-shell-pipe"])
    ])
    def test_sample_errors_contain_expected_rules(self, linter_name, expected_rules):
        """Test that sample errors contain expected rule IDs."""
        errors = get_sample_errors_by_linter(linter_name)
        found_rules = {error["rule_id"] for error in errors}
        
        for expected_rule in expected_rules:
            assert expected_rule in found_rules, (
                f"Expected rule {expected_rule} not found in {linter_name} sample errors"
            )
    
    @pytest.mark.parametrize("severity", [
        "ERROR", "WARNING", "CONVENTION", "MEDIUM"
    ])
    def test_error_severity_handling(self, severity):
        """Test error handling for different severity levels."""
        test_error = TestDataBuilder.create_lint_error(severity=severity)
        
        # Test error structure
        AssertionHelpers.assert_lint_error_structure(test_error)
        assert test_error["severity"] == severity
        
        # Test severity categorization logic (if exists)
        # This would test actual severity handling in the codebase
        assert isinstance(test_error["severity"], str)
        assert len(test_error["severity"]) > 0


class TestParameterizedProjectGeneration:
    """Parameterized tests for project structure generation."""
    
    @pytest.mark.parametrize("language,file_extension", [
        ("python", ".py"),
        ("javascript", ".js"),
        ("ansible", ".yml")
    ])
    def test_sample_code_generation(self, language, file_extension):
        """Test that sample code is generated correctly for each language."""
        clean_code = get_sample_code_by_language(language, clean=True)
        problematic_code = get_sample_code_by_language(language, clean=False)
        
        assert len(clean_code) > 0, f"No clean code generated for {language}"
        assert len(problematic_code) > 0, f"No problematic code generated for {language}"
        assert clean_code != problematic_code, "Clean and problematic code should differ"
    
    @pytest.mark.parametrize("config_type", [
        "flake8", "pylint", "eslint", "ansible-lint", "prettier"
    ])
    def test_config_template_generation(self, config_type):
        """Test that configuration templates are available."""
        config = get_config_template(config_type)
        assert len(config) > 0, f"No config template found for {config_type}"
        assert isinstance(config, str), "Config template should be a string"
    
    @pytest.mark.parametrize("project_type,expected_files", [
        ("python", ["main.py", "module.py", "requirements.txt", "setup.py"]),
        ("javascript", ["index.js", "utils.js", "package.json"]),
        ("ansible", ["playbook.yml", "inventory.ini", "requirements.yml"])
    ])
    def test_project_structure_completeness(self, project_type, expected_files, temp_project_dir):
        """Test that generated project structures contain expected files."""
        from tests.utils import FileSystemFixtures
        
        if project_type == "python":
            created_files = FileSystemFixtures.create_python_project(temp_project_dir)
        elif project_type == "javascript":
            created_files = FileSystemFixtures.create_nodejs_project(temp_project_dir)
        elif project_type == "ansible":
            created_files = FileSystemFixtures.create_ansible_project(temp_project_dir)
        
        for expected_file in expected_files:
            assert expected_file in created_files, f"Missing file: {expected_file}"
            AssertionHelpers.assert_file_exists_and_readable(created_files[expected_file])


class TestParameterizedPerformance:
    """Parameterized performance tests."""
    
    @pytest.mark.parametrize("file_count", [1, 10, 50, 100])
    def test_performance_scales_with_file_count(self, file_count, temp_project_dir):
        """Test that performance scales reasonably with file count."""
        # Create multiple files
        files = {}
        for i in range(file_count):
            files[f"file_{i}.py"] = f"# File {i}\nprint('Hello from file {i}')\n"
        
        created_files = TestDataBuilder.create_project_structure(
            temp_project_dir, files
        )
        
        # Measure time to process all files
        def process_files():
            return [f.read_text() for f in created_files.values()]
        
        result, execution_time = PerformanceHelper.measure_execution_time(process_files)
        
        # Assert reasonable performance scaling
        # For this simple operation, should be under 0.1s per 10 files
        max_time = (file_count / 10) * 0.1
        assert execution_time < max_time, (
            f"Processing {file_count} files took {execution_time:.3f}s, "
            f"exceeding expected {max_time:.3f}s"
        )
    
    @pytest.mark.parametrize("error_count", [1, 10, 100, 1000])
    def test_error_processing_performance(self, error_count):
        """Test performance of error processing with varying error counts."""
        # Generate test errors
        errors = []
        for i in range(error_count):
            errors.append(TestDataBuilder.create_lint_error(
                file_path=f"file_{i % 10}.py",
                line=i + 1,
                message=f"Test error {i}"
            ))
        
        # Simple processing function (in real tests, this would be actual error processing)
        def process_errors(error_list):
            return [error for error in error_list if error["severity"] == "ERROR"]
        
        result, execution_time = PerformanceHelper.measure_execution_time(
            process_errors, errors
        )
        
        # Should process 1000 errors in under 0.1 seconds
        assert execution_time < 0.1, (
            f"Processing {error_count} errors took {execution_time:.3f}s"
        )


# Property-based tests (require hypothesis)
class TestPropertyBasedValidation:
    """Property-based tests for validating invariants."""
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        file_path=st.text(min_size=1, max_size=100),
        line=st.integers(min_value=1, max_value=10000),
        rule_id=st.text(min_size=1, max_size=20),
        message=st.text(min_size=1, max_size=200)
    )
    def test_lint_error_creation_invariants(self, file_path, line, rule_id, message):
        """Test that lint error creation maintains invariants."""
        # Skip invalid inputs
        assume(len(file_path.strip()) > 0)
        assume(len(rule_id.strip()) > 0)
        assume(len(message.strip()) > 0)
        
        error = TestDataBuilder.create_lint_error(
            file_path=file_path,
            line=line,
            rule_id=rule_id,
            message=message
        )
        
        # Invariants that should always hold
        AssertionHelpers.assert_lint_error_structure(error)
        assert error["line"] == line
        assert error["file_path"] == file_path
        assert error["rule_id"] == rule_id
        assert error["message"] == message
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        files=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=20
        )
    )
    def test_project_creation_invariants(self, files):
        """Test properties of project creation operations."""
        # Use temporary directory within the test instead of fixture
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_project_dir = Path(temp_dir)
            
            # Filter to only valid filenames (no path separators)
            valid_files = [f for f in files if "/" not in f and "\\" not in f and f.strip()]
            
            if not valid_files:
                return  # Skip if no valid files
            
            # Create file content map
            file_content = {f"file_{i}.py": f"# Content for {filename}" 
                           for i, filename in enumerate(valid_files)}
            
            created_files = TestDataBuilder.create_project_structure(
                temp_project_dir, file_content
            )
            
            # Invariants
            assert len(created_files) == len(file_content)
            for file_path, path_obj in created_files.items():
                assert path_obj.exists()
                assert path_obj.is_file()
                assert path_obj.read_text().startswith("# Content for")
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        error_lists=st.lists(
            st.dictionaries(
                keys=st.sampled_from(["file_path", "line", "rule_id", "message"]),
                values=st.one_of(st.text(), st.integers(min_value=1)),
                min_size=4,
                max_size=4
            ),
            min_size=0,
            max_size=100
        )
    )
    def test_error_aggregation_properties(self, error_lists):
        """Test properties of error aggregation operations."""
        # Filter to only valid error dictionaries
        valid_errors = []
        for error_dict in error_lists:
            if (isinstance(error_dict.get("line"), int) and 
                isinstance(error_dict.get("file_path"), str) and
                isinstance(error_dict.get("rule_id"), str) and
                isinstance(error_dict.get("message"), str)):
                valid_errors.append(error_dict)
        
        # Test aggregation properties
        files_with_errors = set(error.get("file_path") for error in valid_errors)
        
        # Property: Number of unique files should not exceed total errors
        assert len(files_with_errors) <= len(valid_errors)
        
        # Property: If we group by file, total errors should be preserved
        errors_by_file = {}
        for error in valid_errors:
            file_path = error.get("file_path")
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        total_grouped_errors = sum(len(errors) for errors in errors_by_file.values())
        assert total_grouped_errors == len(valid_errors)


class TestParameterizedMockGeneration:
    """Parameterized tests for mock object generation."""
    
    @pytest.mark.parametrize("provider,model", [
        ("openai", "gpt-4"),
        ("deepseek", "deepseek/deepseek-chat"),
        ("anthropic", "claude-3-sonnet"),
        ("ollama", "llama2")
    ])
    def test_config_mock_generation(self, provider, model):
        """Test config mock generation with different providers."""
        mock_config = MockGenerator.create_config_mock(
            llm_provider=provider,
            llm_model=model
        )
        
        assert mock_config.llm.provider == provider
        assert mock_config.llm.model == model
        assert hasattr(mock_config.llm, "api_key")
    
    @pytest.mark.parametrize("success,error_count", [
        (True, 0),
        (True, 5),
        (False, 3),
        (False, 0)
    ])
    def test_lint_result_mock_generation(self, success, error_count):
        """Test lint result mock generation with different scenarios."""
        errors = [
            TestDataBuilder.create_lint_error(message=f"Error {i}")
            for i in range(error_count)
        ]
        
        mock_result = MockGenerator.create_lint_result_mock(
            errors=errors,
            success=success
        )
        
        assert mock_result.success == success
        assert len(mock_result.errors) == error_count
        assert hasattr(mock_result, "raw_output")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])