#!/usr/bin/env python3
"""
Test runner for all new and enhanced modules.

This script runs comprehensive tests for all the new modules and enhancements
implemented based on the research findings.

Usage:
    python tests/test_runner.py [--verbose] [--module MODULE_NAME]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(module_name=None, verbose=False):
    """Run tests for specified module or all modules."""

    test_modules = [
        "test_cost_monitor",
        "test_ast_dependency_analyzer",
        "test_context_manager",
        "test_convergence_analyzer",
        "test_structural_analyzer",
        "test_control_flow_analyzer",
        "test_enhanced_error_analyzer",
    ]

    if module_name:
        if module_name not in test_modules:
            print(f"Error: Module '{module_name}' not found.")
            print(f"Available modules: {', '.join(test_modules)}")
            return False
        test_modules = [module_name]

    print("🧪 Running Enhanced Aider-Lint-Fixer Test Suite")
    print("=" * 50)

    total_passed = 0
    total_failed = 0
    failed_modules = []

    for test_module in test_modules:
        print(f"\n📋 Running tests for {test_module}...")

        cmd = ["python", "-m", "pytest", f"tests/{test_module}.py"]
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
            )

            if result.returncode == 0:
                print(f"✅ {test_module}: PASSED")
                # Count passed tests from output
                if "passed" in result.stdout:
                    passed_count = result.stdout.count(" PASSED")
                    total_passed += passed_count
            else:
                print(f"❌ {test_module}: FAILED")
                failed_modules.append(test_module)
                if verbose:
                    print(f"Error output:\n{result.stdout}\n{result.stderr}")
                # Count failed tests
                if "failed" in result.stdout:
                    failed_count = result.stdout.count(" FAILED")
                    total_failed += failed_count

        except Exception as e:
            print(f"❌ {test_module}: ERROR - {e}")
            failed_modules.append(test_module)
            total_failed += 1

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total modules tested: {len(test_modules)}")
    print(f"Modules passed: {len(test_modules) - len(failed_modules)}")
    print(f"Modules failed: {len(failed_modules)}")

    if total_passed > 0:
        print(f"✅ Total tests passed: {total_passed}")
    if total_failed > 0:
        print(f"❌ Total tests failed: {total_failed}")

    if failed_modules:
        print(f"\n❌ Failed modules: {', '.join(failed_modules)}")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True


def check_dependencies():
    """Check if required test dependencies are installed."""

    required_packages = ["pytest", "pytest-cov", "pytest-mock"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required test dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing dependencies with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True


def run_coverage_report():
    """Run tests with coverage reporting."""

    print("\n📊 Running tests with coverage analysis...")

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=aider_lint_fixer",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "-v",
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            print("\n✅ Coverage report generated successfully!")
            print("📁 HTML coverage report: htmlcov/index.html")
        else:
            print("\n❌ Coverage report generation failed!")

        return result.returncode == 0

    except Exception as e:
        print(f"\n❌ Error generating coverage report: {e}")
        return False


def main():
    """Main test runner function."""

    parser = argparse.ArgumentParser(description="Run enhanced aider-lint-fixer tests")
    parser.add_argument(
        "--module",
        help="Run tests for specific module only",
        choices=[
            "test_cost_monitor",
            "test_ast_dependency_analyzer",
            "test_context_manager",
            "test_convergence_analyzer",
            "test_structural_analyzer",
            "test_control_flow_analyzer",
            "test_enhanced_error_analyzer",
        ],
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies only")

    args = parser.parse_args()

    if args.check_deps:
        if check_dependencies():
            print("✅ All test dependencies are installed!")
            return 0
        else:
            return 1

    # Check dependencies first
    if not check_dependencies():
        return 1

    if args.coverage:
        success = run_coverage_report()
    else:
        success = run_tests(args.module, args.verbose)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
