#!/usr/bin/env python3
"""
Test script for enhanced progress tracking functionality.

This script demonstrates the new progress tracking features for long-running lint fixes.
"""

import tempfile
import time
from pathlib import Path

import pytest


def test_progress_tracker_import():
    """Test that the progress tracker can be imported."""
    print("🧪 Testing Enhanced Progress Tracking")
    print("=" * 50)

    print("\n1. Testing module imports...")

    try:
        from aider_lint_fixer.progress_tracker import (
            EnhancedProgressTracker,
            ProgressMetrics,
            ProgressStage,
            create_enhanced_progress_callback,
        )

        print("   ✅ Progress tracker modules import successfully")
        assert True  # Test passed
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        pytest.fail(f"Import failed: {e}")


def test_progress_tracker_basic_functionality():
    """Test basic progress tracker functionality."""
    print("\n2. Testing basic functionality...")

    try:
        from aider_lint_fixer.progress_tracker import (
            EnhancedProgressTracker,
            ProgressStage,
        )

        # Test with small project (should not use progress bars)
        small_tracker = EnhancedProgressTracker(".", total_errors=50, verbose=False)
        assert (
            not small_tracker.is_large_project
        ), "50 errors should not be considered large project"
        print("   ✅ Small project detection works")

        # Test with large project (should use progress bars if tqdm available)
        large_tracker = EnhancedProgressTracker(".", total_errors=150, verbose=False)
        assert large_tracker.is_large_project, "150 errors should be considered large project"
        print("   ✅ Large project detection works")

        # Test stage updates
        large_tracker.update_stage(ProgressStage.ANALYZING)
        assert large_tracker.session.metrics.current_stage == ProgressStage.ANALYZING
        print("   ✅ Stage updates work")

        # Test file progress
        large_tracker.set_total_files(10)
        large_tracker.update_file_progress("test_file.py", 5)
        assert large_tracker.session.metrics.processed_files == 1
        print("   ✅ File progress tracking works")

        # Test error progress
        large_tracker.update_error_progress(fixed=3, failed=2)
        assert large_tracker.session.metrics.fixed_errors == 3
        assert large_tracker.session.metrics.failed_errors == 2
        print("   ✅ Error progress tracking works")

        # Clean up
        large_tracker.close()
        small_tracker.close()

        assert True  # Test passed

    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        pytest.fail(f"Basic functionality test failed: {e}")


def test_progress_callback_integration():
    """Test progress callback integration."""
    print("\n3. Testing progress callback integration...")

    try:
        from aider_lint_fixer.progress_tracker import (
            EnhancedProgressTracker,
            create_enhanced_progress_callback,
        )

        # Create tracker
        tracker = EnhancedProgressTracker(".", total_errors=120, verbose=False)
        tracker.set_total_files(5)

        # Create callback
        callback = create_enhanced_progress_callback(tracker, verbose=False)

        # Test callback with different stages
        callback(
            {
                "stage": "processing_file",
                "current_file": 1,
                "total_files": 5,
                "current_file_path": "test1.py",
                "file_errors": 10,
            }
        )

        callback({"stage": "fixing_error_group", "complexity": "trivial", "group_errors": 5})

        callback({"stage": "file_completed", "session_results": 8, "file_errors": 10})

        # Verify tracking
        assert tracker.session.metrics.processed_files == 1
        assert tracker.session.metrics.fixed_errors == 8
        assert tracker.session.metrics.failed_errors == 2

        print("   ✅ Progress callback integration works")

        tracker.close()
        assert True  # Test passed

    except Exception as e:
        print(f"   ❌ Progress callback test failed: {e}")
        pytest.fail(f"Progress callback test failed: {e}")


def test_progress_summary():
    """Test progress summary functionality."""
    print("\n4. Testing progress summary...")

    try:
        from aider_lint_fixer.progress_tracker import EnhancedProgressTracker

        tracker = EnhancedProgressTracker(".", total_errors=100, verbose=False)
        tracker.set_total_files(5)

        # Simulate some progress
        tracker.update_file_progress("file1.py", 20)
        tracker.update_error_progress(fixed=15, failed=5)

        # Get summary
        summary = tracker.get_progress_summary()

        # Verify summary structure
        expected_keys = [
            "session_id",
            "elapsed_time",
            "total_files",
            "processed_files",
            "total_errors",
            "processed_errors",
            "fixed_errors",
            "failed_errors",
            "success_rate",
            "current_stage",
            "is_large_project",
        ]

        for key in expected_keys:
            assert key in summary, f"Missing key in summary: {key}"

        assert summary["total_errors"] == 100
        assert summary["processed_files"] == 1
        assert summary["fixed_errors"] == 15
        assert summary["failed_errors"] == 5
        assert summary["success_rate"] == 75.0  # 15/20 * 100

        print("   ✅ Progress summary works correctly")

        tracker.close()
        assert True  # Test passed

    except Exception as e:
        print(f"   ❌ Progress summary test failed: {e}")
        pytest.fail(f"Progress summary test failed: {e}")


def demonstrate_progress_features():
    """Demonstrate the progress tracking features."""
    print("\n5. Progress Tracking Features Demo:")
    print("   📊 Enhanced Progress Tracking Features:")
    print("      • Automatic detection of large projects (100+ errors)")
    print("      • Visual progress bars with tqdm (when available)")
    print("      • Real-time success rate calculation")
    print("      • Time estimation and ETA")
    print("      • Stage-based progress tracking")
    print("      • Detailed progress summaries")
    print()
    print("   🎯 Usage Examples:")
    print("      # Install with progress tracking support")
    print("      pip install aider-lint-fixer[progress]")
    print()
    print("      # Large projects automatically get enhanced tracking")
    print("      aider-lint-fixer --linters ansible-lint  # 100+ errors")
    print()
    print("      # Force verbose progress for smaller projects")
    print("      aider-lint-fixer --verbose --linters flake8")


def main():
    """Run all progress tracking tests."""
    print("🎯 Enhanced Progress Tracking - Test Suite")
    print("=" * 50)

    tests = [
        test_progress_tracker_import,
        test_progress_tracker_basic_functionality,
        test_progress_callback_integration,
        test_progress_summary,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test error: {e}")

    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Enhanced progress tracking is ready.")
        demonstrate_progress_features()

        print(f"\n💡 Next Steps:")
        print("   1. Install with progress support:")
        print("      pip install aider-lint-fixer[progress]")
        print("   2. Test on a large project (100+ lint errors)")
        print("   3. Watch the enhanced progress bars in action!")

        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
