#!/usr/bin/env python3
"""
Test script for the enhanced interactive mode integration.

This script tests the new enhanced interactive features:
1. --enhanced-interactive flag for per-error decisions
2. --force flag for overriding all classifications
3. Community learning integration
"""

import subprocess
import sys
from pathlib import Path


def test_enhanced_interactive_help():
    """Test that the enhanced interactive flags are properly exposed."""
    print("🧪 Testing Enhanced Interactive Mode Integration")
    print("=" * 60)

    # Test help output
    print("\n1. Testing CLI flag exposure...")
    result = subprocess.run(
        [sys.executable, "-m", "aider_lint_fixer", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Help command failed: {result.stderr}"

    help_text = result.stdout

    # Check for new flags
    flags_to_check = [
        "--enhanced-interactive",
        "--force",
        "Enhanced per-error interactive mode",
        "Force fix all errors",
    ]

    missing_flags = []
    for flag in flags_to_check:
        if flag not in help_text:
            missing_flags.append(flag)

    if not missing_flags:
        print("   ✅ All enhanced interactive flags are properly exposed")
    else:
        print(f"   ❌ Missing flags: {missing_flags}")

    assert not missing_flags, f"Missing flags: {missing_flags}"


def test_enhanced_interactive_import():
    """Test that the enhanced interactive module can be imported."""
    print("\n2. Testing module imports...")

    from aider_lint_fixer.enhanced_interactive import (
        CommunityLearningIntegration,
        InteractiveChoice,
        UserChoice,
        enhanced_interactive_mode,
    )

    print("   ✅ Enhanced interactive module imports successfully")

    # Test enum values
    choices = [UserChoice.FIX, UserChoice.SKIP, UserChoice.ABORT]
    print(f"   ✅ UserChoice enum has {len(choices)} options: {[c.value for c in choices]}")

    assert len(choices) == 3, "UserChoice enum should have 3 options"
    assert all(
        hasattr(UserChoice, choice.name) for choice in choices
    ), "All choices should be valid enum members"


def test_community_learning_integration():
    """Test that community learning integration works."""
    print("\n3. Testing community learning integration...")

    from aider_lint_fixer.enhanced_interactive import CommunityLearningIntegration

    # Test initialization
    integration = CommunityLearningIntegration(".")
    print("   ✅ CommunityLearningIntegration initializes successfully")

    # Test feedback generation
    feedback = integration.generate_learning_feedback()
    expected_keys = [
        "total_attempts",
        "successful_overrides",
        "failed_overrides",
        "classification_improvements",
    ]

    print("   ✅ Learning feedback structure is correct")
    print(f"      Keys: {list(feedback.keys())}")

    assert all(
        key in feedback for key in expected_keys
    ), f"Missing feedback keys: {set(expected_keys) - set(feedback.keys())}"
    assert isinstance(feedback["total_attempts"], int), "total_attempts should be an integer"
    assert isinstance(
        feedback["successful_overrides"], int
    ), "successful_overrides should be an integer"
    assert isinstance(feedback["failed_overrides"], int), "failed_overrides should be an integer"
    assert isinstance(
        feedback["classification_improvements"], list
    ), "classification_improvements should be a list"


def demonstrate_usage():
    """Demonstrate how to use the new features."""
    print("\n4. Usage Examples:")
    print("   📋 Enhanced Interactive Mode:")
    print("      aider-lint-fixer --enhanced-interactive")
    print("      → Review each error individually with override options")
    print("      → Feed choices back to community learning system")
    print()
    print("   ⚡ Force Mode:")
    print("      aider-lint-fixer --force")
    print("      → Attempt to fix ALL errors (including unfixable ones)")
    print("      → Use with caution - requires confirmation")
    print()
    print("   🎯 For your specific case (trailing spaces):")
    print("      aider-lint-fixer --enhanced-interactive --linters ansible-lint")
    print("      → You can now override the 'unfixable' classification")
    print("      → Choose 'try-fix' for the trailing spaces error")
    print("      → System will learn from your choice")


def main():
    """Run all tests and demonstrate usage."""
    print("🎯 Enhanced Interactive Mode - Integration Test")
    print("=" * 60)

    tests = [
        test_enhanced_interactive_help,
        test_enhanced_interactive_import,
        test_community_learning_integration,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ Test failed: {e}")
        except Exception as e:
            print(f"   ❌ Test error: {e}")

    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Enhanced interactive mode is ready to use.")
        demonstrate_usage()

        print(f"\n💡 Next Steps:")
        print("   1. Try the enhanced interactive mode on your project:")
        print("      aider-lint-fixer --enhanced-interactive --linters ansible-lint")
        print("   2. The system will show you the 'unfixable' trailing spaces error")
        print("   3. Choose 'try-fix' to override the classification")
        print("   4. Your choice will be recorded for community learning")

        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
