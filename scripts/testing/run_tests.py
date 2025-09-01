#!/usr/bin/env python3
"""
Enhanced test runner for aider-lint-fixer with coverage analysis and performance tracking.

This script provides comprehensive test execution with coverage reporting,
performance benchmarking, and quality analysis.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Enhanced test runner with coverage and performance tracking."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_threshold = 85
        self.performance_baseline_file = project_root / "performance_baseline.json"
    
    def run_basic_tests(self, test_pattern: Optional[str] = None) -> bool:
        """Run basic test suite with coverage."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--cov=aider_lint_fixer",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            f"--cov-fail-under={self.coverage_threshold}",
            "--tb=short",
            "-v"
        ]
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        print("🧪 Running basic test suite with coverage...")
        return self._run_command(cmd)
    
    def run_parallel_tests(self, workers: int = 4) -> bool:
        """Run tests in parallel for faster execution."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            f"-n", str(workers),
            "--cov=aider_lint_fixer",
            "--cov-report=term-missing",
            f"--cov-fail-under={self.coverage_threshold}",
            "--tb=short"
        ]
        
        print(f"🚀 Running tests in parallel with {workers} workers...")
        return self._run_command(cmd)
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks and regression tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance_benchmarks.py",
            "-v",
            "--tb=short",
            "-m", "performance"
        ]
        
        print("⚡ Running performance benchmarks...")
        return self._run_command(cmd)
    
    def run_property_based_tests(self) -> bool:
        """Run property-based tests using hypothesis."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "-m", "property",
            "--tb=short"
        ]
        
        print("🔬 Running property-based tests...")
        return self._run_command(cmd)
    
    def run_parameterized_tests(self) -> bool:
        """Run parameterized tests for comprehensive coverage."""
        cmd = [
            "python", "-m", "pytest",
            "tests/test_enhanced_parameterized.py",
            "-v",
            "--tb=short"
        ]
        
        print("📊 Running parameterized tests...")
        return self._run_command(cmd)
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "-m", "integration",
            "--tb=short"
        ]
        
        print("🔗 Running integration tests...")
        return self._run_command(cmd)
    
    def run_unit_tests(self) -> bool:
        """Run unit tests only."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v", 
            "-m", "unit",
            "--tb=short"
        ]
        
        print("🧩 Running unit tests...")
        return self._run_command(cmd)
    
    def generate_coverage_report(self) -> bool:
        """Generate detailed coverage reports."""
        print("📊 Generating coverage reports...")
        
        # Generate HTML report
        html_cmd = ["coverage", "html", "--directory", "htmlcov"]
        if not self._run_command(html_cmd):
            return False
        
        # Generate XML report for CI
        xml_cmd = ["coverage", "xml", "-o", "coverage.xml"]
        if not self._run_command(xml_cmd):
            return False
        
        # Show coverage summary
        report_cmd = ["coverage", "report", "--show-missing"]
        return self._run_command(report_cmd)
    
    def run_code_quality_checks(self) -> bool:
        """Run code quality checks on test code."""
        print("🔍 Running code quality checks...")
        
        # Check test code formatting
        black_cmd = ["black", "--check", "tests/"]
        if not self._run_command(black_cmd, fail_on_error=False):
            print("⚠️  Test code formatting issues found")
        
        # Check test code import sorting
        isort_cmd = ["isort", "--check-only", "tests/"]
        if not self._run_command(isort_cmd, fail_on_error=False):
            print("⚠️  Test code import sorting issues found")
        
        # Lint test code
        flake8_cmd = ["flake8", "tests/"]
        if not self._run_command(flake8_cmd, fail_on_error=False):
            print("⚠️  Test code linting issues found")
        
        return True
    
    def run_mutation_testing(self) -> bool:
        """Run mutation testing to assess test quality."""
        try:
            # Check if mutmut is installed
            subprocess.run(["mutmut", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  mutmut not installed. Install with: pip install mutmut")
            return False
        
        print("🧬 Running mutation testing...")
        cmd = [
            "mutmut", "run",
            "--paths-to-mutate", "aider_lint_fixer/",
            "--tests-dir", "tests/",
            "--runner", "pytest"
        ]
        
        return self._run_command(cmd, fail_on_error=False)
    
    def run_full_test_suite(self) -> bool:
        """Run the complete test suite with all checks."""
        print("🎯 Running full test suite...")
        start_time = time.time()
        
        success = True
        
        # Run unit tests first (fastest feedback)
        if not self.run_unit_tests():
            success = False
        
        # Run parameterized tests
        if not self.run_parameterized_tests():
            success = False
        
        # Run integration tests
        if not self.run_integration_tests():
            success = False
        
        # Run performance tests
        if not self.run_performance_tests():
            success = False
        
        # Run property-based tests
        if not self.run_property_based_tests():
            success = False
        
        # Generate coverage reports
        if not self.generate_coverage_report():
            success = False
        
        # Run code quality checks
        if not self.run_code_quality_checks():
            success = False
        
        execution_time = time.time() - start_time
        print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
        
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        return success
    
    def _run_command(self, cmd: List[str], fail_on_error: bool = True) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(cmd, check=True, cwd=self.project_root)
            return True
        except subprocess.CalledProcessError as e:
            if fail_on_error:
                print(f"❌ Command failed: {' '.join(cmd)}")
                print(f"Exit code: {e.returncode}")
            return False
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            return False


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Enhanced test runner for aider-lint-fixer")
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--property", action="store_true", help="Run property-based tests only")
    parser.add_argument("--parameterized", action="store_true", help="Run parameterized tests only")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    parser.add_argument("--mutation", action="store_true", help="Run mutation testing")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--pattern", type=str, help="Test pattern to match")
    parser.add_argument("--threshold", type=int, default=85, help="Coverage threshold")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)
    runner.coverage_threshold = args.threshold
    
    success = True
    
    if args.full:
        success = runner.run_full_test_suite()
    else:
        if args.unit:
            success &= runner.run_unit_tests()
        
        if args.integration:
            success &= runner.run_integration_tests()
        
        if args.performance:
            success &= runner.run_performance_tests()
        
        if args.property:
            success &= runner.run_property_based_tests()
        
        if args.parameterized:
            success &= runner.run_parameterized_tests()
        
        if args.parallel:
            success &= runner.run_parallel_tests(args.workers)
        
        if args.coverage:
            success &= runner.generate_coverage_report()
        
        if args.mutation:
            success &= runner.run_mutation_testing()
        
        if args.quality:
            success &= runner.run_code_quality_checks()
        
        # Default: run basic tests if no specific option given
        if not any([args.unit, args.integration, args.performance, args.property, 
                   args.parameterized, args.parallel, args.coverage, args.mutation, args.quality]):
            success = runner.run_basic_tests(args.pattern)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()