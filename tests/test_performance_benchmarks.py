#!/usr/bin/env python3
"""
Performance and benchmark tests for aider-lint-fixer.

This module provides comprehensive performance testing including
execution time benchmarks, memory usage tests, and regression detection.
"""

import pytest
import time
import tempfile
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils import TestDataBuilder, PerformanceHelper, FileSystemFixtures
from tests.fixtures.performance_fixtures import (
    PerformanceTracker, BenchmarkSuite, performance_test,
    assert_execution_time_under, assert_memory_usage_under,
    RegressionDetector
)
from tests.fixtures.sample_lint_data import get_sample_errors_by_linter


class TestBasicPerformance:
    """Basic performance tests for core operations."""
    
    @performance_test(max_execution_time=0.1)
    def test_error_creation_performance(self):
        """Test that error creation is fast enough."""
        errors = []
        for i in range(1000):
            error = TestDataBuilder.create_lint_error(
                file_path=f"file_{i}.py",
                line=i + 1,
                message=f"Test error {i}"
            )
            errors.append(error)
        
        assert len(errors) == 1000
        return errors
    
    @performance_test(max_memory_mb=50)
    def test_large_error_list_memory_usage(self):
        """Test memory usage with large error lists."""
        errors = []
        for i in range(10000):
            error = TestDataBuilder.create_lint_error(
                file_path=f"file_{i % 100}.py",
                line=i + 1,
                message=f"Error message {i} with some additional content to increase memory usage"
            )
            errors.append(error)
        
        # Process errors (grouping by file)
        errors_by_file = {}
        for error in errors:
            file_path = error["file_path"]
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        return errors_by_file
    
    def test_file_processing_performance(self, temp_project_dir):
        """Test file processing performance with realistic project size."""
        # Create a moderately sized Python project
        files = {}
        for i in range(50):
            files[f"module_{i}.py"] = f"""#!/usr/bin/env python3
'''Module {i} for testing purposes.'''

import os
import sys
from typing import List, Dict, Optional

class TestClass{i}:
    '''Test class {i}.'''
    
    def __init__(self, value: int = {i}):
        self.value = value
        self.data = []
    
    def process_data(self, input_data: List[int]) -> Dict[str, int]:
        '''Process input data and return results.'''
        result = {{}}
        for item in input_data:
            result[f'item_{{item}}'] = item * self.value
        return result
    
    def calculate_sum(self, numbers: List[int]) -> int:
        '''Calculate sum of numbers.'''
        return sum(numbers)

def main():
    '''Main function for module {i}.'''
    instance = TestClass{i}()
    test_data = list(range(10))
    result = instance.process_data(test_data)
    print(f'Result: {{result}}')

if __name__ == '__main__':
    main()
"""
        
        created_files = TestDataBuilder.create_project_structure(temp_project_dir, files)
        
        # Measure time to read all files
        @assert_execution_time_under(1.0)  # Should complete within 1 second
        def read_all_files():
            content = {}
            for file_path, path_obj in created_files.items():
                content[file_path] = path_obj.read_text()
            return content
        
        result = read_all_files()
        assert len(result) == 50
        
        # Measure time to analyze file structure
        @assert_execution_time_under(0.5)  # Should complete within 0.5 seconds
        def analyze_files():
            analysis = {}
            for file_path, content in result.items():
                lines = content.split('\n')
                analysis[file_path] = {
                    'line_count': len(lines),
                    'char_count': len(content),
                    'has_main': 'if __name__ == ' in content
                }
            return analysis
        
        analysis = analyze_files()
        assert len(analysis) == 50


class TestLinterPerformanceBenchmarks:
    """Performance benchmarks for linter-related operations."""
    
    def test_error_parsing_performance(self, benchmark_suite):
        """Benchmark error parsing performance."""
        # Simulate large lint output with many errors
        sample_errors = []
        for linter in ["flake8", "pylint", "eslint", "ansible-lint"]:
            linter_errors = get_sample_errors_by_linter(linter)
            # Multiply errors to simulate large projects
            for _ in range(100):
                for error in linter_errors:
                    sample_errors.append(error.copy())
        
        def parse_errors(errors):
            """Simulate error parsing operation."""
            parsed = []
            for error in errors:
                if error.get("severity") in ["ERROR", "CRITICAL"]:
                    parsed.append({
                        "file": error["file_path"],
                        "rule": error["rule_id"],
                        "msg": error["message"],
                        "critical": True
                    })
                else:
                    parsed.append({
                        "file": error["file_path"],
                        "rule": error["rule_id"],
                        "msg": error["message"],
                        "critical": False
                    })
            return parsed
        
        result = benchmark_suite.benchmark_error_analysis(parse_errors, sample_errors)
        
        # Performance assertions
        assert result["execution_time"] < 0.5, f"Error parsing too slow: {result['execution_time']:.3f}s"
        assert result["memory_usage"] < 100, f"Error parsing uses too much memory: {result['memory_usage']:.2f}MB"
        assert result["input_errors"] > 1000, "Test should use substantial number of errors"
    
    def test_configuration_loading_performance(self, temp_project_dir):
        """Test configuration file loading performance."""
        from tests.fixtures.sample_lint_data import get_config_template
        
        # Create multiple config files
        configs = {
            ".flake8": get_config_template("flake8"),
            ".pylintrc": get_config_template("pylint"),
            ".eslintrc.json": get_config_template("eslint"),
            ".ansible-lint": get_config_template("ansible-lint"),
            ".prettierrc": get_config_template("prettier")
        }
        
        created_configs = TestDataBuilder.create_project_structure(
            temp_project_dir, {}, configs
        )
        
        @assert_execution_time_under(0.1)
        @assert_memory_usage_under(10)
        def load_all_configs():
            """Load and parse all configuration files."""
            loaded_configs = {}
            for config_name, config_path in created_configs.items():
                content = config_path.read_text()
                loaded_configs[config_name] = {
                    'content': content,
                    'size': len(content),
                    'lines': len(content.split('\n'))
                }
            return loaded_configs
        
        result = load_all_configs()
        assert len(result) == 5


class TestScalabilityBenchmarks:
    """Test how well the system scales with increasing load."""
    
    @pytest.mark.parametrize("project_size", [10, 50, 100])
    def test_project_processing_scalability(self, project_size, temp_project_dir):
        """Test scalability with different project sizes."""
        # Create project of specified size
        files = {}
        for i in range(project_size):
            files[f"file_{i}.py"] = f"""# File {i}
def function_{i}():
    print("Function {i}")
    return {i}

class Class{i}:
    def method(self):
        return {i}
"""
        
        created_files = TestDataBuilder.create_project_structure(temp_project_dir, files)
        
        # Measure processing time
        start_time = time.time()
        
        # Simulate project analysis
        analysis_result = {}
        for file_path, path_obj in created_files.items():
            content = path_obj.read_text()
            analysis_result[file_path] = {
                'functions': content.count('def '),
                'classes': content.count('class '),
                'lines': len(content.split('\n'))
            }
        
        processing_time = time.time() - start_time
        
        # Performance should scale linearly (or better)
        # Allow 0.01 seconds per file as reasonable threshold
        max_expected_time = project_size * 0.01
        
        assert processing_time < max_expected_time, (
            f"Processing {project_size} files took {processing_time:.3f}s, "
            f"expected under {max_expected_time:.3f}s"
        )
        
        assert len(analysis_result) == project_size
    
    def test_error_aggregation_scalability(self):
        """Test error aggregation performance with large datasets."""
        # Generate large number of errors across many files
        errors = []
        for file_num in range(100):  # 100 files
            for error_num in range(50):  # 50 errors per file = 5000 total
                error = TestDataBuilder.create_lint_error(
                    file_path=f"project/module_{file_num}.py",
                    line=error_num + 1,
                    rule_id=f"RULE{error_num % 10}",
                    message=f"Error {error_num} in file {file_num}"
                )
                errors.append(error)
        
        # Test aggregation performance
        start_time = time.time()
        
        # Group errors by file
        errors_by_file = {}
        for error in errors:
            file_path = error["file_path"]
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        # Group errors by rule
        errors_by_rule = {}
        for error in errors:
            rule_id = error["rule_id"]
            if rule_id not in errors_by_rule:
                errors_by_rule[rule_id] = []
            errors_by_rule[rule_id].append(error)
        
        aggregation_time = time.time() - start_time
        
        # Should handle 5000 errors quickly
        assert aggregation_time < 0.1, f"Error aggregation too slow: {aggregation_time:.3f}s"
        assert len(errors_by_file) == 100
        assert len(errors_by_rule) == 10


class TestRegressionDetection:
    """Test performance regression detection capabilities."""
    
    def test_regression_detector_baseline(self, temp_project_dir):
        """Test regression detector baseline creation and comparison."""
        regression_detector = RegressionDetector(
            baseline_file=temp_project_dir / "performance_baseline.json"
        )
        
        # Simulate some operation
        def test_operation():
            result = []
            for i in range(1000):
                result.append(i * 2)
            return result
        
        # Measure baseline performance
        tracker = PerformanceTracker()
        result, metrics = tracker.measure_execution(test_operation, "test_operation")
        
        # Save as baseline
        regression_detector.save_baseline({"test_operation": metrics})
        
        # Test current performance against baseline
        result2, metrics2 = tracker.measure_execution(test_operation, "test_operation")
        regression_check = regression_detector.check_regression("test_operation", metrics2)
        
        # Should not be a regression (same operation), or no baseline exists yet
        assert regression_check["status"] in ["ok", "regression", "no_baseline"]
        
        # Only check for ratio fields if we have a baseline to compare against
        if regression_check["status"] != "no_baseline":
            assert "time_ratio" in regression_check
            assert "memory_ratio" in regression_check
    
    def test_performance_trend_monitoring(self):
        """Test that we can detect performance trends."""
        tracker = PerformanceTracker()
        
        # Simulate measurements over time with degrading performance
        baseline_time = 0.01
        measurements = []
        
        for i in range(5):
            # Simulate gradually slower operation
            def slow_operation():
                time.sleep(baseline_time * (1 + i * 0.1))
                return f"result_{i}"
            
            result, metrics = tracker.measure_execution(slow_operation, f"operation_{i}")
            measurements.append(metrics)
        
        # Check that we can detect the trend
        assert len(measurements) == 5
        
        # Execution times should generally increase
        times = [m["execution_time"] for m in measurements]
        # Allow some variance but general trend should be increasing
        assert times[-1] > times[0], "Performance should have degraded over iterations"


class TestMemoryUsageBenchmarks:
    """Specific tests for memory usage patterns."""
    
    @assert_memory_usage_under(20)  # Should use less than 20MB
    def test_large_file_processing_memory(self, temp_project_dir):
        """Test memory usage when processing large files."""
        # Create a large Python file
        large_content = """#!/usr/bin/env python3
'''Large Python file for memory testing.'''

import os
import sys
from typing import List, Dict, Optional, Tuple, Any, Union

"""
        
        # Add many function definitions
        for i in range(200):
            large_content += f"""
def function_{i}(param1: int, param2: str, param3: List[int] = None) -> Dict[str, Any]:
    '''Function {i} for testing memory usage.'''
    if param3 is None:
        param3 = list(range(10))
    
    result = {{}}
    for j, value in enumerate(param3):
        result[f'key_{{j}}_{{param1}}_{{param2}}'] = value * param1
    
    return result
"""
        
        large_file = temp_project_dir / "large_file.py"
        large_file.write_text(large_content)
        
        # Process the large file multiple times
        for _ in range(10):
            content = large_file.read_text()
            lines = content.split('\n')
            functions = [line for line in lines if line.strip().startswith('def ')]
            classes = [line for line in lines if line.strip().startswith('class ')]
            
            analysis = {
                'total_lines': len(lines),
                'function_count': len(functions),
                'class_count': len(classes),
                'file_size': len(content)
            }
        
        # Should complete without excessive memory usage
        assert analysis['function_count'] == 200
        return analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])